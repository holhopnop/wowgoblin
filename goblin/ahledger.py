"""AHledger API client. Honors Cache-Control, ETag and Retry-After. Read-only."""
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

BASE = "https://api.ahledger.com"
# pricetable row order, as documented: id:median:minBuyout:qty:med7:med30:low30:high30:salesx10
ROW_FIELDS = ("item_id", "median", "min_buyout", "quantity", "median_7d",
              "median_30d", "low_30d", "high_30d", "sales_x10")


@dataclass
class PriceRow:
    item_id: int
    median: int | None
    min_buyout: int | None
    quantity: int | None
    median_7d: int | None
    median_30d: int | None
    low_30d: int | None
    high_30d: int | None
    sales_per_day: float | None


@dataclass
class PriceTable:
    market: str            # slash form from header
    observed_at: datetime
    declared_rows: int
    rows: list[PriceRow]


def _int(v: str):
    return int(v) if v != "" else None


def parse_pricetable(text: str) -> PriceTable:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    head = lines[0].split("|")
    if len(head) != 4 or head[0] != "AHL1":
        raise ValueError(f"unexpected pricetable header: {lines[0]!r}")
    rows = []
    for ln in lines[1:]:
        f = ln.split(":")
        if len(f) != len(ROW_FIELDS):
            raise ValueError(f"unexpected row shape ({len(f)} fields): {ln!r}")
        v = [_int(x) for x in f]
        rows.append(PriceRow(v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7],
                             None if v[8] is None else v[8] / 10))
    declared = int(head[3])
    if declared != len(rows):
        raise ValueError(f"header declares {declared} rows, got {len(rows)}")
    return PriceTable(head[1], datetime.fromtimestamp(int(head[2]), tz=timezone.utc),
                      declared, rows)


def max_age(cache_control: str | None, default: int = 60) -> int:
    m = re.search(r"max-age=(\d+)", cache_control or "")
    return int(m.group(1)) if m else default


class Client:
    def __init__(self, api_key: str = "", contact: str = ""):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = f"goblin-private/0.1 ({contact})"
        if api_key:
            self.s.headers["Authorization"] = f"Bearer {api_key}"

    def get(self, path: str, etag: str | None = None, **params):
        headers = {"If-None-Match": etag} if etag else {}
        for _ in range(3):
            r = self.s.get(BASE + path, params=params, headers=headers, timeout=30)
            if r.status_code in (429, 503):
                time.sleep(int(r.headers.get("Retry-After", "30")))
                continue
            r.raise_for_status()
            return r
        raise RuntimeError(f"AHledger still unavailable after retries: {path}")

    def pricetable(self, market_dotted: str, etag: str | None = None):
        slash = market_dotted.replace(".", "/")
        r = self.get(f"/v1/pricetable/{slash}", etag=etag)
        if r.status_code == 304:
            return None, etag, max_age(r.headers.get("Cache-Control"))
        return parse_pricetable(r.text), r.headers.get("ETag"), max_age(r.headers.get("Cache-Control"))
