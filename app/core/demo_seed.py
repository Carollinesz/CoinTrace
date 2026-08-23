"""Loads the demo dataset into an empty demo database, right after the schema is created."""

import json
import re
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine


DATASET_PATH = Path(__file__).resolve().parents[1] / "constants" / "dataset demo.xlsx"
EXCEL_EPOCH = date(1899, 12, 30)
DECIMAL_COMMA = re.compile(r"(?<=\d),(?=\d)")  # some `details` values were exported with a comma separator


def handle_seed_demo_data(engine: Engine) -> None:
    from app.models.models import bank_account, fixed_expense, transaction

    with engine.begin() as conn:
        if conn.execute(text("SELECT 1 FROM bank_accounts LIMIT 1")).scalar():
            return

        sheets = _read_dataset()
        conn.execute(bank_account.__table__.insert(), _build_accounts(sheets["accounts"]))
        conn.execute(fixed_expense.__table__.insert(), _build_fixed_expenses(sheets["fixed"]))
        conn.execute(transaction.__table__.insert(), _build_transactions(sheets["transactions"]))


def _read_dataset() -> dict[str, pd.DataFrame]:
    """Sheet headers are stripped because some of them carry trailing spaces."""
    with pd.ExcelFile(DATASET_PATH) as workbook:
        return {
            name: workbook.parse(name).rename(columns=str.strip)
            for name in ("accounts", "fixed", "transactions")
        }

def _build_accounts(df: pd.DataFrame) -> list[dict]:
    return [
        {
            "bank_id": int(row["bank_id"]),
            "account_name": row["account_name"],
            "account_type": row["account_type"],
            "start_value": Decimal(str(row["start_value"])),
        }
        for row in df.to_dict("records")
    ]


def _build_fixed_expenses(df: pd.DataFrame) -> list[dict]:
    return [
        {
            "name": row["name"],
            "value": Decimal(str(row["value"])),
            "due_day": int(row["due_day"]),
            "category": row["category"],
            "account_id": int(row["account_id"]),
            "is_active": bool(row["is_active"]),
        }
        for row in df.to_dict("records")
    ]


def _build_transactions(df: pd.DataFrame) -> list[dict]:
    return [
        {
            "account_id": int(row["account_id"]),
            "transaction_date": row["transaction_date"].date(),
            "value": Decimal(str(row["value"])),
            "description": row["description"],
            "category": row["category"],
            "type": row["type"],
            "details": _build_details(row["details"]),
            "tracking": bool(row["tracking"]),
        }
        for row in df.to_dict("records")
    ]

def _build_details(raw: str | None) -> dict | None:
    if not isinstance(raw, str):
        return None
    details = json.loads(DECIMAL_COMMA.sub(".", raw))
    return {**details, "first_payment": _to_iso_date(details["first_payment"])}


def _to_iso_date(value: str | int | float) -> str:
    """`first_payment` comes from the spreadsheet as an Excel serial date."""
    if isinstance(value, str):
        return value
    return (EXCEL_EPOCH + timedelta(days=int(value))).isoformat()
