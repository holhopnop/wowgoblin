"""Hourly copy of the AHledger price table for our market and the opposite faction."""
import os
import time

import psycopg

from .ahledger import Client

INSERT = """INSERT INTO price_snapshot
 (market,item_id,observed_at,median,min_buyout,quantity,median_7d,median_30d,low_30d,high_30d,sales_per_day)
 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING"""


def sync_market(conn, client: Client, market: str) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT etag FROM sync_state WHERE market=%s", (market,))
        row = cur.fetchone()
        table, etag, _ = client.pricetable(market, row[0] if row else None)
        if table is None:  # 304, nothing new
            cur.execute("UPDATE sync_state SET last_checked_at=now() WHERE market=%s", (market,))
            conn.commit()
            return 0
        cur.executemany(INSERT, [(market, r.item_id, table.observed_at, r.median, r.min_buyout,
                                  r.quantity, r.median_7d, r.median_30d, r.low_30d, r.high_30d,
                                  r.sales_per_day) for r in table.rows])
        cur.execute("""INSERT INTO sync_state (market,etag,last_table_at,last_checked_at)
                       VALUES (%s,%s,%s,now())
                       ON CONFLICT (market) DO UPDATE SET etag=EXCLUDED.etag,
                       last_table_at=EXCLUDED.last_table_at, last_checked_at=now()""",
                    (market, etag, table.observed_at))
        conn.commit()
        return len(table.rows)


def main():
    markets = [m for m in (os.environ["GOBLIN_MARKET"], os.getenv("GOBLIN_OPPOSITE_MARKET")) if m]
    client = Client(os.getenv("AHLEDGER_API_KEY", ""), os.getenv("GOBLIN_CONTACT", ""))
    while True:
        with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
            for m in markets:
                try:
                    print(f"{m}: {sync_market(conn, client, m)} rows stored", flush=True)
                except Exception as e:  # keep the loop alive; show the failure
                    conn.rollback()
                    print(f"{m}: sync failed: {e}", flush=True)
        time.sleep(3600)


if __name__ == "__main__":
    main()
