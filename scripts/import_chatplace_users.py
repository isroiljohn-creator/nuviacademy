#!/usr/bin/env python3
"""
Import users from cleaned_chatplace_clients.xlsx → Supabase PostgreSQL (users table).
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple

import openpyxl
import asyncpg

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

EXCEL_PATH = "/Users/a1234/Documents/cleaned_chatplace_clients.xlsx"

DATABASE_URL = (
    "postgresql://postgres.btbqxtfxpscwgmoiamyv:SuperApp2024Bot"
    "@aws-1-eu-west-1.pooler.supabase.com:5432/postgres"
)

BATCH_SIZE = 500
NOW = datetime.utcnow()  # naive UTC — matches TIMESTAMP column type


def parse_date(val) -> Optional[datetime]:
    """Return naive UTC datetime (tzinfo stripped) or None."""
    if not val or str(val).strip() in ("nan", "", "None"):
        return None
    try:
        dt = datetime.fromisoformat(str(val).strip())
        # Strip tzinfo — DB column is TIMESTAMP (no tz), asyncpg needs uniform types
        return dt.replace(tzinfo=None)
    except Exception:
        return None


def clean(val) -> Optional[str]:
    s = str(val).strip() if val is not None else ""
    return None if s in ("nan", "", "None") else s


async def flush_batch(conn, batch: List[Tuple]):
    """Each tuple: (telegram_id, name, phone, source, user_status, registered_at, created_at)"""
    try:
        await conn.executemany(
            """
            INSERT INTO users
                (telegram_id, name, phone, source, user_status,
                 lead_score, lead_segment,
                 registered_at, created_at)
            VALUES ($1, $2, $3, $4, $5, 0, 'content_only', $6, $7)
            ON CONFLICT (telegram_id) DO NOTHING
            """,
            batch,
        )
        return len(batch), 0
    except Exception as e:
        log.warning(f"Batch error ({len(batch)} rows): {e}")
        return 0, len(batch)


async def run():
    log.info("Reading Excel…")
    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    log.info(f"Total Excel rows: {len(rows)}")

    log.info("Connecting to database…")
    conn = await asyncpg.connect(DATABASE_URL, ssl="require")

    inserted = 0
    skipped = 0
    errors = 0
    batch = []

    for i, row in enumerate(rows):
        try:
            (rid, firstName, lastName, fullName, username,
             followersCount, hasSubscription, registeredAt,
             phone, email, note, messageStatus, chatStatus, tags) = row

            telegram_id = int(rid) if rid else None
            if not telegram_id:
                skipped += 1
                continue

            name = clean(fullName) or clean(firstName) or "Unknown"
            phone_val = clean(phone)
            registered_at = parse_date(registeredAt)
            created_at = registered_at if registered_at else NOW
            user_status = "registered" if str(hasSubscription).strip() == "+" else "started"

            # $6=registered_at (nullable timestamptz), $7=created_at (non-null timestamptz)
            batch.append((
                telegram_id, name, phone_val,
                "chatplace", user_status,
                registered_at,  # $6 — can be None
                created_at,     # $7 — always datetime
            ))

            if len(batch) >= BATCH_SIZE:
                ok, err = await flush_batch(conn, batch)
                inserted += ok
                errors += err
                batch = []
                log.info(f"  {inserted + errors + skipped}/{len(rows)}  inserted={inserted} errors={errors}")

        except Exception as e:
            log.warning(f"Parse error row {i+2}: {e}")
            skipped += 1

    if batch:
        ok, err = await flush_batch(conn, batch)
        inserted += ok
        errors += err

    await conn.close()
    log.info(f"\n✅ DONE!  inserted={inserted}  skipped={skipped}  errors={errors}\n")


if __name__ == "__main__":
    asyncio.run(run())
