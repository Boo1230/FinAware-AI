from datetime import date

from app.models.schemas import LoanRecommendationRequest, RiskAssessmentRequest
from app.models.schemas import CashLedgerEntryCreate
from app.services.cash_ledger_service import CashLedgerService
from app.services.loan_service import recommend_loans
from app.services.risk_service import analyze_bank_statement
from app.services.risk_service import assess_risk


def test_risk_assessment_smoke() -> None:
    payload = RiskAssessmentRequest(
        monthly_income=30000,
        existing_emis=4000,
        current_savings=45000,
        monthly_expenses=17000,
        cibil_score=680,
        purpose="business expansion",
        loan_amount=120000,
        occupation="street vendor",
        age=33,
    )
    result = assess_risk(payload)
    assert 0 <= result.default_probability <= 100
    assert result.risk_category in {"Low", "Medium", "High"}
    assert result.suggested_tenure_months > 0
    assert result.cibil_estimated is False
    assert result.cibil_score_used == 680


def test_risk_assessment_estimates_cibil_when_missing() -> None:
    payload = RiskAssessmentRequest(
        monthly_income=28000,
        existing_emis=2500,
        current_savings=22000,
        monthly_expenses=16000,
        cibil_score=None,
        purpose="medical emergency",
        loan_amount=80000,
        occupation="self employed",
        age=29,
    )
    result = assess_risk(payload)
    assert result.cibil_estimated is True
    assert 300 <= result.cibil_score_used <= 900


def test_loan_recommendation_smoke(tmp_path, monkeypatch) -> None:
    dataset_path = tmp_path / "india_loans_dataset.csv"
    dataset_path.write_text(
        "loan_id,loan_category,loan_type,sub_type,lender_type,typical_lenders,target_segment,secured,typical_tenure_years,notes\n"
        "1,Government Scheme,MUDRA,Shishu,Bank/MFI,Banks & MFIs,Micro Business,No,1-5,Small ticket\n"
        "2,Retail,Personal Loan,General,Bank/NBFC/Fintech,Banks & Digital Lenders,Individuals,No,1-5,Unsecured loan\n"
        "3,Retail,Home Loan,Home Purchase,Bank/HFC,Banks & HFCs,Individuals,Yes,5-30,Buying property\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("LOAN_DATASET_PATH", str(dataset_path))

    payload = LoanRecommendationRequest(
        requested_amount=120000,
        risk_category="Medium",
        approval_probability=70,
    )
    result = recommend_loans(payload)
    assert len(result["ranked_options"]) > 0
    assert result["best_option"].loan_score >= result["ranked_options"][-1].loan_score


def test_cash_ledger_opening_and_closing(tmp_path) -> None:
    service = CashLedgerService(storage_path=tmp_path / "cash_ledger_test.json")

    service.add_entry(
        CashLedgerEntryCreate(
            user_id="user-1",
            entry_date=date(2026, 2, 25),
            entry_type="inflow",
            amount=1000,
            description="morning sales",
        )
    )
    service.add_entry(
        CashLedgerEntryCreate(
            user_id="user-1",
            entry_date=date(2026, 2, 25),
            entry_type="outflow",
            amount=250,
            description="inventory purchase",
        )
    )
    service.add_entry(
        CashLedgerEntryCreate(
            user_id="user-1",
            entry_date=date(2026, 2, 26),
            entry_type="inflow",
            amount=400,
            description="day 2 sales",
        )
    )

    day1 = service.get_day_summary("user-1", date(2026, 2, 25))
    day2 = service.get_day_summary("user-1", date(2026, 2, 26))

    assert day1.opening_balance == 0
    assert day1.closing_balance == 750
    assert day2.opening_balance == 750
    assert day2.closing_balance == 1150


def test_bank_statement_analyzer_without_fixed_columns() -> None:
    weird_csv = (
        "Txn Date,Narration,CR Amt,DR Amt,Running Bal\n"
        "2026-02-01,Salary credit,45000,0,52000\n"
        "2026-02-02,UPI grocery payment,0,1200,50800\n"
        "2026-02-03,UPI fuel payment,0,800,50000\n"
    ).encode("utf-8")

    result = analyze_bank_statement(weird_csv, filename="statement_anyshape.csv")
    assert result["monthly_income_estimate"] > 0
    assert result["monthly_expense_estimate"] > 0
