"""Baixa a lista de ativos da B3 na brapi e grava em data/b3_tickers.json.

Uso: python scripts/update_b3_tickers.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

URL = "https://brapi.dev/api/quote/list"
OUTPUT = Path(__file__).parent.parent / "data" / "b3_tickers.json"


def fetch_assets() -> list[dict]:
    stocks, page = [], 1
    while True:
        response = requests.get(URL, params={"limit": 2000, "page": page}, timeout=30)
        response.raise_for_status()
        body = response.json()
        stocks.extend(body.get("stocks", []))
        if not body.get("hasNextPage"):
            break
        page += 1
    assets = {
        s["stock"].upper(): {
            "ticker": s["stock"].upper(),
            "name": s.get("name") or s["stock"],
            "sector": s.get("sector") or "",
            "type": s.get("type") or "",
            "subType": s.get("subType") or "",
        }
        for s in stocks
        if s.get("stock")
    }
    return sorted(assets.values(), key=lambda a: a["ticker"])


def main() -> int:
    assets = fetch_assets()
    if not assets:
        print("Resposta sem ativos; arquivo não foi alterado.", file=sys.stderr)
        return 1
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": URL,
        "count": len(assets),
        "assets": assets,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(assets)} ativos gravados em {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
