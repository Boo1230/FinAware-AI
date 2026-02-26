# FinAware AI

AI-powered financial awareness and microloan risk assessment platform.

## What is implemented
- FastAPI backend with module APIs for:
  - Microloan risk assessment
  - Risk model training (Logistic Regression, Random Forest, optional XGBoost)
  - Loan recommendation engine
  - Tax assistant (deduction suggestions + tax estimate)
  - Goal-based financial planning
  - Budget forecasting + expense categorization
  - Manual cash ledger (persistent entries + daily opening/closing balances)
  - Insurance advisory
  - Financial inclusion recommendations
  - Translation + voice intent classification
- React frontend dashboard with module tabs and API integration.
- Dataset upload flow for model training.

## Project structure
```
backend/
  app/
    api/
    core/
    models/
    services/
frontend/
data/
```

## Run backend (FastAPI)
1. `cd backend`
2. `python -m venv .venv`
3. Windows PowerShell: `.venv\Scripts\Activate.ps1`
4. `pip install -r requirements.txt`
5. `uvicorn app.main:app --reload --port 8000`

## Run frontend (React + Vite)
1. Open new terminal
2. `cd frontend`
3. `npm install`
4. `npm run dev`
5. Open `http://localhost:5173`

If backend runs on another URL, set `VITE_API_BASE_URL` in `frontend/.env`.

## Dataset format for risk training
Upload CSV in UI (`Risk` tab -> `Dataset Training`) or call:
- `POST /api/v1/risk/train`

Required columns:
- `monthly_income`
- `existing_emis`
- `collateral_value`
- `cibil_score`
- `occupation`
- `location`
- `business_type`

Recommended optional columns:
- `active_loans`
- `monthly_expenses`
- `avg_monthly_balance`
- `savings_amount`
- `upi_transaction_frequency`
- `utility_bill_regularity`
- `transaction_consistency_score`
- `income_volatility_index`

Target column:
- default column name: `defaulted`
- binary meaning: `1` default, `0` non-default

Sample training dataset:
- `data/sample_risk_dataset.csv`

## API quick checks
- Health: `GET /api/v1/health`
- Model status: `GET /api/v1/status`
- Training schema: `GET /api/v1/risk/training-schema`

## Flexible bank statement analyzer
- Endpoint: `POST /api/v1/risk/bank-statement/analyze`
- Accepted formats (best-effort parsing): CSV, XLSX/XLS, PDF, DOC/DOCX, TXT/TSV, JSON, XML.
- No fixed column requirement:
  - Analyzer auto-detects date/amount/debit/credit/type/balance/narration columns when possible.
  - For unstructured statements, it falls back to text transaction extraction.

## Manual cash ledger API
- Add entry: `POST /api/v1/budget/cash-ledger/entries`
  - Payload:
    - `user_id` (string)
    - `entry_date` (`YYYY-MM-DD`)
    - `entry_type` (`inflow` or `outflow`)
    - `amount` (positive number)
    - `description` (string)
- Report: `GET /api/v1/budget/cash-ledger/{user_id}?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- Day summary: `GET /api/v1/budget/cash-ledger/{user_id}/day/{entry_date}`
