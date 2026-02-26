from __future__ import annotations

import json
import threading
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.models.schemas import (
    CashLedgerDaySummary,
    CashLedgerEntry,
    CashLedgerEntryCreate,
    CashLedgerEntryResponse,
    CashLedgerReportResponse,
)


class CashLedgerService:
    def __init__(self, storage_path: Path | None = None) -> None:
        default_path = Path(settings.model_artifact_dir) / "cash_ledger_entries.json"
        self.storage_path = storage_path or default_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _load_entries(self) -> list[dict]:
        if not self.storage_path.exists():
            return []
        payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return payload
        return payload.get("entries", [])

    def _save_entries(self, entries: list[dict]) -> None:
        tmp_path = self.storage_path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps({"entries": entries}, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        tmp_path.replace(self.storage_path)

    @staticmethod
    def _sort_entries(entries: list[dict]) -> list[dict]:
        return sorted(
            entries,
            key=lambda x: (
                x["user_id"],
                x["entry_date"],
                x["created_at"],
                x["entry_id"],
            ),
        )

    @staticmethod
    def _user_entries(entries: list[dict], user_id: str) -> list[dict]:
        filtered = [x for x in entries if x["user_id"] == user_id]
        return sorted(filtered, key=lambda x: (x["entry_date"], x["created_at"], x["entry_id"]))

    @staticmethod
    def _to_entry_model(raw: dict) -> CashLedgerEntry:
        return CashLedgerEntry(
            entry_id=raw["entry_id"],
            user_id=raw["user_id"],
            entry_date=date.fromisoformat(raw["entry_date"]),
            entry_type=raw["entry_type"],
            amount=float(raw["amount"]),
            description=raw.get("description", ""),
            created_at=raw["created_at"],
        )

    def _compute_daily_summaries(self, user_entries: list[dict]) -> list[CashLedgerDaySummary]:
        grouped: dict[str, list[dict]] = {}
        for item in user_entries:
            grouped.setdefault(item["entry_date"], []).append(item)

        running_balance = 0.0
        summaries: list[CashLedgerDaySummary] = []
        for day in sorted(grouped.keys()):
            records = grouped[day]
            inflow = sum(float(x["amount"]) for x in records if x["entry_type"] == "inflow")
            outflow = sum(float(x["amount"]) for x in records if x["entry_type"] == "outflow")
            opening = running_balance
            closing = opening + inflow - outflow
            running_balance = closing

            summaries.append(
                CashLedgerDaySummary(
                    user_id=records[0]["user_id"],
                    entry_date=date.fromisoformat(day),
                    opening_balance=round(opening, 2),
                    total_inflow=round(inflow, 2),
                    total_outflow=round(outflow, 2),
                    closing_balance=round(closing, 2),
                    transaction_count=len(records),
                )
            )
        return summaries

    def add_entry(self, payload: CashLedgerEntryCreate) -> CashLedgerEntryResponse:
        user_id = payload.user_id.strip()
        if not user_id:
            raise ValueError("user_id cannot be empty.")

        record = {
            "entry_id": uuid4().hex,
            "user_id": user_id,
            "entry_date": payload.entry_date.isoformat(),
            "entry_type": payload.entry_type,
            "amount": round(float(payload.amount), 2),
            "description": payload.description.strip(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        with self._lock:
            entries = self._load_entries()
            entries.append(record)
            entries = self._sort_entries(entries)
            self._save_entries(entries)

            day_summary = self.get_day_summary(user_id=user_id, entry_date=payload.entry_date)
            return CashLedgerEntryResponse(
                entry=self._to_entry_model(record),
                day_summary=day_summary,
            )

    def get_report(
        self,
        user_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> CashLedgerReportResponse:
        user_id = user_id.strip()
        if not user_id:
            raise ValueError("user_id cannot be empty.")

        with self._lock:
            entries = self._user_entries(self._load_entries(), user_id=user_id)

        all_daily = self._compute_daily_summaries(entries)
        filtered_entries = [self._to_entry_model(x) for x in entries]
        filtered_daily = list(all_daily)

        if start_date:
            filtered_entries = [x for x in filtered_entries if x.entry_date >= start_date]
            filtered_daily = [x for x in filtered_daily if x.entry_date >= start_date]
        if end_date:
            filtered_entries = [x for x in filtered_entries if x.entry_date <= end_date]
            filtered_daily = [x for x in filtered_daily if x.entry_date <= end_date]

        current_balance = all_daily[-1].closing_balance if all_daily else 0.0
        return CashLedgerReportResponse(
            user_id=user_id,
            entries=filtered_entries,
            daily_summaries=filtered_daily,
            current_balance=round(current_balance, 2),
        )

    def get_day_summary(self, user_id: str, entry_date: date) -> CashLedgerDaySummary:
        report = self.get_report(user_id=user_id)
        day_map = {x.entry_date: x for x in report.daily_summaries}
        if entry_date in day_map:
            return day_map[entry_date]

        prior_days = [x for x in report.daily_summaries if x.entry_date < entry_date]
        opening = prior_days[-1].closing_balance if prior_days else 0.0
        return CashLedgerDaySummary(
            user_id=user_id,
            entry_date=entry_date,
            opening_balance=round(opening, 2),
            total_inflow=0.0,
            total_outflow=0.0,
            closing_balance=round(opening, 2),
            transaction_count=0,
        )


cash_ledger_service = CashLedgerService()
