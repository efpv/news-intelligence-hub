"""Persistência de preferências em Google Sheets (abas users, portfolio e filters)."""
import json
from datetime import datetime
from typing import Any

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

DEFAULT_SPREADSHEET = "news_intelligence_hub_data"
_SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
_FILTER_COLUMNS = ["selected_category", "selected_sources", "sentiment_filter", "search_term", "period", "refresh_option"]
_JSON_COLUMNS = {"selected_sources", "sentiment_filter"}


def is_configured() -> bool:
    try:
        return "gcp_service_account" in st.secrets
    except FileNotFoundError:
        return False


@st.cache_resource(show_spinner=False)
def _spreadsheet() -> gspread.Spreadsheet:
    creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=_SCOPES)
    name = st.secrets.get("sheets_name", DEFAULT_SPREADSHEET)
    return gspread.authorize(creds).open(name)


@st.cache_resource(show_spinner=False)
def _worksheets() -> dict[str, gspread.Worksheet]:
    """Abas em cache: cada `worksheet()` consultaria os metadados e consumiria cota de leitura."""
    sp = _spreadsheet()
    return {name: sp.worksheet(name) for name in ("users", "portfolio", "filters")}


def _read_ranges(ranges: dict[str, str]) -> dict[str, list[list[str]]]:
    """Lê várias abas numa única requisição. `ranges` mapeia aba -> intervalo A1 (sem o nome da aba)."""
    names = list(ranges)
    response = _spreadsheet().values_batch_get([f"{n}!{ranges[n]}" for n in names])
    return {n: vr.get("values", []) for n, vr in zip(names, response["valueRanges"])}


def _row_numbers(values: list[list[str]], user_id: str) -> list[int]:
    """Linhas (1-based) do usuário numa coluna A lida de uma aba, excluindo o cabeçalho."""
    return [i for i, r in enumerate(values, start=1) if i > 1 and r and r[0] == user_id]


def delete_user(user_id: str) -> None:
    """Remove o usuário das três abas."""
    sheets = _worksheets()
    cols = _read_ranges({n: "A:A" for n in sheets})
    for name, ws in sheets.items():
        _delete_rows(ws, _row_numbers(cols[name], user_id))


def _delete_rows(ws: gspread.Worksheet, rows: list[int]) -> None:
    """Remove as linhas em um único batch_update, de baixo para cima."""
    if not rows:
        return
    ranges: list[list[int]] = []
    for r in sorted(rows, reverse=True):
        if ranges and ranges[-1][0] == r + 1:
            ranges[-1][0] = r
        else:
            ranges.append([r, r])
    requests = [
        {"deleteDimension": {"range": {"sheetId": ws.id, "dimension": "ROWS",
                                       "startIndex": start - 1, "endIndex": end}}}
        for start, end in ranges
    ]
    ws.spreadsheet.batch_update({"requests": requests})


def load_preferences(user_id: str) -> dict[str, Any] | None:
    """Preferências do usuário na planilha, ou None se ele ainda não existir."""
    data = _read_ranges({"filters": "A:H", "portfolio": "A:C"})
    filters = next((r for r in data["filters"][1:] if r and r[0] == user_id), None)
    if filters is None:
        return None

    cells = dict(zip(["user_id", *_FILTER_COLUMNS, "last_update"], filters + [""] * 8))
    prefs: dict[str, Any] = {}
    for col in _FILTER_COLUMNS:
        value = cells[col]
        if col in _JSON_COLUMNS:
            try:
                value = json.loads(value) if value != "" else []
            except json.JSONDecodeError:
                value = []
        prefs[col] = value
    prefs["portfolio"] = [r[1].upper() for r in data["portfolio"][1:] if len(r) > 1 and r[0] == user_id]
    prefs["last_update"] = cells["last_update"]
    return prefs


def save_preferences(user_id: str, email: str, prefs: dict[str, Any]) -> None:
    """Grava (upsert) usuário e filtros e substitui a carteira do usuário."""
    sheets = _worksheets()
    ws_users, ws_portfolio, ws_filters = sheets["users"], sheets["portfolio"], sheets["filters"]
    now = prefs.get("last_update") or datetime.now().isoformat()
    cols = _read_ranges({n: "A:A" for n in sheets})

    user_rows = _row_numbers(cols["users"], user_id)
    if user_rows:
        row = user_rows[0]  # preserva created_at (coluna C)
        ws_users.batch_update([{"range": f"B{row}", "values": [[email]]},
                               {"range": f"D{row}", "values": [[now]]}], value_input_option="RAW")
    else:
        ws_users.append_row([user_id, email, now, now], value_input_option="RAW")

    filters_row = [user_id] + [
        json.dumps(prefs.get(c, []), ensure_ascii=False) if c in _JSON_COLUMNS else prefs.get(c, "")
        for c in _FILTER_COLUMNS
    ] + [now]
    existing = _row_numbers(cols["filters"], user_id)
    if existing:
        ws_filters.update(range_name=f"A{existing[0]}:H{existing[0]}", values=[filters_row],
                          value_input_option="RAW")
    else:
        ws_filters.append_row(filters_row, value_input_option="RAW")

    _delete_rows(ws_portfolio, _row_numbers(cols["portfolio"], user_id))
    tickers = prefs.get("portfolio", [])
    if tickers:
        ws_portfolio.append_rows([[user_id, t, now] for t in tickers], value_input_option="RAW")
