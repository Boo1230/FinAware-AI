from datetime import date
from typing import Optional
from typing import Literal

from pydantic import BaseModel, Field


class RiskAssessmentRequest(BaseModel):
    monthly_income: float = Field(..., gt=0, description="Estimated monthly income")
    existing_emis: float = Field(..., ge=0)
    current_savings: float = Field(..., ge=0)
    monthly_expenses: float = Field(..., ge=0)
    cibil_score: Optional[int] = Field(default=None, ge=300, le=900)
    purpose: str = Field(..., min_length=2, max_length=120)
    loan_amount: float = Field(..., gt=0)
    occupation: str = Field(..., min_length=2, max_length=80)
    age: int = Field(..., ge=18, le=80)


class RiskAssessmentResponse(BaseModel):
    default_probability: float
    approval_probability: float
    risk_category: Literal["Low", "Medium", "High"]
    cibil_score_used: int
    cibil_estimated: bool
    remarks: list[str]
    recommended_loan_type: str
    suggested_tenure_months: int
    estimated_monthly_emi: float


class RiskTrainingResponse(BaseModel):
    best_model: str
    target_column: str
    samples: int
    metrics: dict[str, dict[str, float]]
    trained_features: list[str]


class LoanOption(BaseModel):
    lender_name: str
    annual_interest_rate: float = Field(..., gt=0)
    tenure_months: int = Field(..., ge=3)
    tax_benefit_score: float = Field(0.0, ge=0, le=100)
    max_amount: float = Field(..., gt=0)
    processing_fee_pct: float = Field(0.0, ge=0, le=10)


class LoanRecommendationRequest(BaseModel):
    requested_amount: float = Field(..., gt=0)
    risk_category: Literal["Low", "Medium", "High"]
    approval_probability: float = Field(..., ge=0, le=100)
    occupation: Optional[str] = Field(default=None, min_length=2, max_length=80)
    purpose: Optional[str] = Field(default=None, min_length=2, max_length=120)


class LoanRecommendationItem(BaseModel):
    lender_name: str
    loan_score: float
    estimated_emi: float
    annual_interest_rate: float
    annual_tax_savings: float
    adjusted_approval_probability: float


class LoanRecommendationResponse(BaseModel):
    best_option: LoanRecommendationItem
    ranked_options: list[LoanRecommendationItem]


class TaxAssistantInput(BaseModel):
    salary_income: float = Field(0, ge=0)
    business_income: float = Field(0, ge=0)
    other_income: float = Field(0, ge=0)
    investments_80c: float = Field(0, ge=0)
    insurance_80d: float = Field(0, ge=0)
    other_deductions: float = Field(0, ge=0)


class TaxAssistantResponse(BaseModel):
    gross_income: float
    taxable_income: float
    estimated_tax: float
    deductions_applied: dict[str, float]
    suggestions: list[str]


class TextExtractionInput(BaseModel):
    text: str = Field(..., min_length=2)


class TextExtractionResponse(BaseModel):
    pan_numbers: list[str]
    amounts: list[float]
    likely_income_amounts: list[float]
    detected_sections: list[str]


class GoalPlanningInput(BaseModel):
    goal_name: str = Field(..., min_length=2)
    target_price: float = Field(..., gt=0)
    time_horizon_months: int = Field(..., ge=1)
    current_saved: float = Field(0, ge=0)
    monthly_income: float = Field(..., gt=0)
    monthly_expenses: float = Field(..., ge=0)


class GoalPlanningResponse(BaseModel):
    goal_name: str
    monthly_saving_target: float
    current_progress_pct: float
    projected_completion_months: float
    adjusted_budget_plan: dict[str, float]
    notes: list[str]


class BudgetForecastInput(BaseModel):
    monthly_expense_history: list[float] = Field(..., min_length=3)


class BudgetForecastResponse(BaseModel):
    next_month_prediction: float
    confidence_band: dict[str, float]
    trend: Literal["rising", "stable", "falling"]


class ExpenseTransaction(BaseModel):
    description: str
    amount: float = Field(..., ge=0)


class ExpenseCategorizationInput(BaseModel):
    transactions: list[ExpenseTransaction] = Field(..., min_length=1)


class ExpenseCategorizationResponse(BaseModel):
    categorized_expenses: dict[str, float]
    uncategorized_count: int


class CashLedgerEntryCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    entry_date: date
    entry_type: Literal["inflow", "outflow"]
    amount: float = Field(..., gt=0)
    description: str = Field("", max_length=200)


class CashLedgerEntry(BaseModel):
    entry_id: str
    user_id: str
    entry_date: date
    entry_type: Literal["inflow", "outflow"]
    amount: float
    description: str
    created_at: str


class CashLedgerDaySummary(BaseModel):
    user_id: str
    entry_date: date
    opening_balance: float
    total_inflow: float
    total_outflow: float
    closing_balance: float
    transaction_count: int


class CashLedgerEntryResponse(BaseModel):
    entry: CashLedgerEntry
    day_summary: CashLedgerDaySummary


class CashLedgerReportResponse(BaseModel):
    user_id: str
    entries: list[CashLedgerEntry]
    daily_summaries: list[CashLedgerDaySummary]
    current_balance: float


class InsuranceInput(BaseModel):
    age: int = Field(..., ge=18, le=80)
    monthly_income: float = Field(..., gt=0)
    family_members: int = Field(..., ge=1, le=12)
    health_conditions: list[str] = Field(default_factory=list)
    occupation_risk_level: Literal["low", "medium", "high"]


class InsuranceResponse(BaseModel):
    risk_profile_score: float
    health_insurance_cover: float
    life_insurance_cover: float
    emergency_fund_target: float
    recommendations: list[str]


class InclusionInput(BaseModel):
    monthly_income: float = Field(..., gt=0)
    cibil_score: int = Field(..., ge=300, le=900)
    location: str = Field("unknown")
    occupation: str = Field("informal worker")


class InclusionResponse(BaseModel):
    alternative_credit_score: float
    eligible_schemes: list[str]
    microloan_options: list[str]
    literacy_content: list[str]


class TranslationInput(BaseModel):
    text: str = Field(..., min_length=1)
    source_lang: str = Field("en")
    target_lang: str = Field("hi")


class TranslationResponse(BaseModel):
    translated_text: str
    used_engine: str


class VoiceIntentInput(BaseModel):
    text: str = Field(..., min_length=1)


class VoiceIntentResponse(BaseModel):
    intent: str
    confidence: float
    matched_keywords: list[str]
