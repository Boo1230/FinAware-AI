from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    BudgetForecastInput,
    BudgetForecastResponse,
    CashLedgerDaySummary,
    CashLedgerEntryCreate,
    CashLedgerEntryResponse,
    CashLedgerReportResponse,
    ExpenseCategorizationInput,
    ExpenseCategorizationResponse,
)
from app.services.budget_service import categorize_expenses, forecast_next_month
from app.services.cash_ledger_service import cash_ledger_service

router = APIRouter()


@router.post("/forecast", response_model=BudgetForecastResponse)
def forecast_expenses(payload: BudgetForecastInput) -> BudgetForecastResponse:
    return forecast_next_month(payload)


@router.post("/categorize", response_model=ExpenseCategorizationResponse)
def categorize(payload: ExpenseCategorizationInput) -> ExpenseCategorizationResponse:
    return categorize_expenses(payload)


@router.post("/cash-ledger/entries", response_model=CashLedgerEntryResponse)
def add_cash_ledger_entry(payload: CashLedgerEntryCreate) -> CashLedgerEntryResponse:
    try:
        return cash_ledger_service.add_entry(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/cash-ledger/{user_id}", response_model=CashLedgerReportResponse)
def get_cash_ledger_report(
    user_id: str,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
) -> CashLedgerReportResponse:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date cannot be greater than end_date.")
    try:
        return cash_ledger_service.get_report(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/cash-ledger/{user_id}/day/{entry_date}", response_model=CashLedgerDaySummary)
def get_cash_ledger_day_summary(user_id: str, entry_date: date) -> CashLedgerDaySummary:
    try:
        return cash_ledger_service.get_day_summary(user_id=user_id, entry_date=entry_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
