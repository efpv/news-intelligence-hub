"""Exportação de dados filtrados."""
from io import BytesIO

import pandas as pd


def _flat(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["tags"] = out["tags"].map(lambda t: ", ".join(t))
    out["data"] = out["data"].dt.tz_localize(None)
    return out


def to_csv(df: pd.DataFrame) -> bytes:
    """CSV UTF-8 (com BOM, abre bem no Excel)."""
    return _flat(df).to_csv(index=False).encode("utf-8-sig")


def to_excel(df: pd.DataFrame) -> bytes:
    """Planilha XLSX em memória."""
    buf = BytesIO()
    _flat(df).to_excel(buf, index=False, sheet_name="Notícias", engine="openpyxl")
    return buf.getvalue()
