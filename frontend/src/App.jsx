import { useEffect, useMemo, useState } from "react";
import { getJson, postFile, postJson } from "./api";

const TABS = [
  { id: "risk", label: "Risk" },
  { id: "loan", label: "Loans" },
  { id: "tax", label: "Tax CA" },
  { id: "planning", label: "Planning" },
  { id: "budget", label: "Budget" },
  { id: "insurance", label: "Insurance" },
  { id: "inclusion", label: "Inclusion" },
  { id: "assist", label: "Voice+Lang" },
];

function toNumber(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function formatKey(key) {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatPlainText(data, indent = 0) {
  const pad = " ".repeat(indent);

  if (data === null || data === undefined) {
    return `${pad}N/A`;
  }

  if (typeof data !== "object") {
    return `${pad}${String(data)}`;
  }

  if (Array.isArray(data)) {
    if (data.length === 0) {
      return `${pad}None`;
    }
    return data
      .map((item, index) => {
        if (item !== null && typeof item === "object") {
          return `${pad}${index + 1})\n${formatPlainText(item, indent + 2)}`;
        }
        return `${pad}${index + 1}) ${String(item)}`;
      })
      .join("\n");
  }

  const entries = Object.entries(data);
  if (entries.length === 0) {
    return `${pad}None`;
  }

  return entries
    .map(([key, value]) => {
      const label = formatKey(key);
      if (value !== null && typeof value === "object") {
        return `${pad}${label}:\n${formatPlainText(value, indent + 2)}`;
      }
      return `${pad}${label}: ${value}`;
    })
    .join("\n");
}

function formatMoney(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return String(value);
  return `INR ${n.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
}

function formatPct(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return String(value);
  return `${n.toFixed(2)}%`;
}

function todayDateString() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function JsonBox({ data, error }) {
  if (error) {
    return <pre className="json-box error-box">{error}</pre>;
  }
  if (!data) {
    return <pre className="json-box muted-box">No result yet.</pre>;
  }
  return <pre className="json-box">{formatPlainText(data)}</pre>;
}

function RiskResultBox({ data, error }) {
  if (error) {
    return <pre className="json-box error-box">{error}</pre>;
  }
  if (!data) {
    return <pre className="json-box muted-box">No result yet.</pre>;
  }

  const remarks = Array.isArray(data.remarks) ? data.remarks.filter(Boolean) : [];
  const riskCategory = String(data.risk_category || "").toLowerCase();
  const cibilNote = data.cibil_estimated ? "Estimated from profile" : "Provided by user";

  return (
    <div className="risk-result-box">
      <div className="risk-metrics-grid">
        <div className="risk-metric">
          <span>Default Probability</span>
          <strong>{formatPct(data.default_probability)}</strong>
        </div>
        <div className="risk-metric">
          <span>Approval Probability</span>
          <strong>{formatPct(data.approval_probability)}</strong>
        </div>
        <div className="risk-metric">
          <span>Risk Category</span>
          <strong className={`risk-badge ${riskCategory || "unknown"}`}>
            {data.risk_category || "N/A"}
          </strong>
        </div>
        <div className="risk-metric">
          <span>CIBIL Score Used</span>
          <strong>{data.cibil_score_used ?? "N/A"}</strong>
          <small>{cibilNote}</small>
        </div>
      </div>

      <div className="risk-loan-grid">
        <div className="loan-point">
          <span>Suggested Loan Type</span>
          <strong>{data.recommended_loan_type || "N/A"}</strong>
        </div>
        <div className="loan-point">
          <span>Suggested Tenure</span>
          <strong>
            {data.suggested_tenure_months ? `${data.suggested_tenure_months} months` : "N/A"}
          </strong>
        </div>
        <div className="loan-point">
          <span>Estimated Monthly EMI</span>
          <strong>{formatMoney(data.estimated_monthly_emi)}</strong>
        </div>
      </div>

      {remarks.length > 0 && (
        <div className="risk-remarks">
          <h4>Remarks</h4>
          <ul>
            {remarks.map((remark, index) => (
              <li key={`remark-${index}`}>{remark}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function LoanResultBox({ data, error }) {
  if (error) {
    return <pre className="json-box error-box">{error}</pre>;
  }
  if (!data) {
    return <pre className="json-box muted-box">No result yet.</pre>;
  }

  const ranked = Array.isArray(data.ranked_options) ? data.ranked_options : [];
  const best = data.best_option;
  if (ranked.length === 0 || !best) {
    return <pre className="json-box muted-box">No result yet.</pre>;
  }

  return (
    <div className="loan-result-box">
      <div className="loan-best-line">
        <strong>Best Loan:</strong> {best.lender_name}
      </div>
      <div className="loan-table-wrap">
        <table className="loan-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Loan Option</th>
              <th>Score</th>
              <th>Est. EMI</th>
              <th>Rate</th>
              <th>Approval</th>
              <th>Tax Savings</th>
            </tr>
          </thead>
          <tbody>
            {ranked.map((item, index) => (
              <tr key={`${item.lender_name}-${index}`} className={index === 0 ? "best-row" : ""}>
                <td>{index + 1}</td>
                <td className="loan-name">{item.lender_name}</td>
                <td>{toNumber(item.loan_score).toFixed(2)}</td>
                <td>{formatMoney(item.estimated_emi)}</td>
                <td>{formatPct(item.annual_interest_rate)}</td>
                <td>{formatPct(item.adjusted_approval_probability)}</td>
                <td>{formatMoney(item.annual_tax_savings)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SectionCard({ title, subtitle, children }) {
  return (
    <section className="card">
      <div className="card-head">
        <h3>{title}</h3>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {children}
    </section>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState("risk");
  const [status, setStatus] = useState(null);
  const [globalError, setGlobalError] = useState("");

  const [riskForm, setRiskForm] = useState({
    monthly_income: "30000",
    existing_emis: "3500",
    current_savings: "45000",
    monthly_expenses: "17000",
    cibil_score: "",
    purpose: "Business expansion",
    loan_amount: "120000",
    occupation: "Street vendor",
    age: "32",
  });
  const [riskResult, setRiskResult] = useState(null);
  const [riskError, setRiskError] = useState("");

  const [statementFile, setStatementFile] = useState(null);

  const [loanForm, setLoanForm] = useState({
    requested_amount: "100000",
    risk_category: "Medium",
    approval_probability: "65",
  });
  const [loanResult, setLoanResult] = useState(null);
  const [loanError, setLoanError] = useState("");

  const [taxForm, setTaxForm] = useState({
    salary_income: "450000",
    business_income: "120000",
    other_income: "15000",
    investments_80c: "80000",
    insurance_80d: "12000",
    other_deductions: "10000",
  });
  const [taxResult, setTaxResult] = useState(null);
  const [taxError, setTaxError] = useState("");

  const [extractText, setExtractText] = useState(
    "PAN ABCDE1234F, salary INR 550000, deduction 80C INR 65000 and 80D INR 12000."
  );
  const [extractResult, setExtractResult] = useState(null);

  const [goalForm, setGoalForm] = useState({
    goal_name: "Bike",
    target_price: "90000",
    time_horizon_months: "12",
    current_saved: "10000",
    monthly_income: "30000",
    monthly_expenses: "22000",
  });
  const [goalResult, setGoalResult] = useState(null);
  const [goalError, setGoalError] = useState("");

  const [budgetHistory, setBudgetHistory] = useState("18000,19500,21000,20500,22000,23000");
  const [budgetResult, setBudgetResult] = useState(null);
  const [budgetError, setBudgetError] = useState("");
  const [transactionsText, setTransactionsText] = useState(
    "Grocery Store,2400\nElectricity Bill,1800\nMetro Card,900\nRestaurant Dinner,1100\nMedicine Shop,650"
  );
  const [categorizeResult, setCategorizeResult] = useState(null);
  const [cashLedgerForm, setCashLedgerForm] = useState({
    user_id: "demo-user",
    entry_date: todayDateString(),
    entry_type: "inflow",
    amount: "1000",
    description: "Cash sale",
  });
  const [cashLedgerFilter, setCashLedgerFilter] = useState({
    user_id: "demo-user",
    start_date: "",
    end_date: "",
  });
  const [cashLedgerEntryResult, setCashLedgerEntryResult] = useState(null);
  const [cashLedgerReport, setCashLedgerReport] = useState(null);

  const [insuranceForm, setInsuranceForm] = useState({
    age: "32",
    monthly_income: "38000",
    family_members: "4",
    health_conditions: "diabetes",
    occupation_risk_level: "medium",
  });
  const [insuranceResult, setInsuranceResult] = useState(null);
  const [insuranceError, setInsuranceError] = useState("");

  const [inclusionForm, setInclusionForm] = useState({
    monthly_income: "18000",
    cibil_score: "620",
    location: "Pune",
    occupation: "small shop owner",
  });
  const [inclusionResult, setInclusionResult] = useState(null);
  const [inclusionError, setInclusionError] = useState("");

  const [translateForm, setTranslateForm] = useState({
    text: "I want to apply for a small business loan.",
    source_lang: "en",
    target_lang: "hi",
  });
  const [translateResult, setTranslateResult] = useState(null);
  const [assistError, setAssistError] = useState("");

  const [voiceText, setVoiceText] = useState("How much EMI will I pay for a loan?");
  const [voiceResult, setVoiceResult] = useState(null);

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const apiStatus = await getJson("/status");
        setStatus(apiStatus);
      } catch (error) {
        setGlobalError(error.message);
      }
    })();
  }, []);

  const statusBadge = useMemo(() => {
    if (!status) return "Checking API";
    if (status.risk_model_trained) return `Risk model: ${status.risk_best_model}`;
    return "Risk model: heuristic fallback";
  }, [status]);

  async function handleRiskSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setRiskError("");
    try {
      const cibilRaw = String(riskForm.cibil_score || "").trim();
      const payload = {
        monthly_income: toNumber(riskForm.monthly_income),
        existing_emis: toNumber(riskForm.existing_emis),
        current_savings: toNumber(riskForm.current_savings),
        monthly_expenses: toNumber(riskForm.monthly_expenses),
        cibil_score: cibilRaw ? Math.round(toNumber(cibilRaw)) : null,
        purpose: riskForm.purpose.trim(),
        loan_amount: toNumber(riskForm.loan_amount),
        occupation: riskForm.occupation.trim(),
        age: Math.round(toNumber(riskForm.age)),
      };
      if (statementFile) {
        const statementData = await postFile("/risk/bank-statement/analyze", statementFile);
        // Always prioritize parsed statement values when a statement is provided.
        payload.monthly_income = toNumber(statementData.monthly_income_estimate, 0);
        payload.monthly_expenses = toNumber(statementData.monthly_expense_estimate, 0);
        payload.current_savings = toNumber(statementData.avg_monthly_balance, 0);
      }

      const result = await postJson("/risk/assess", payload);
      setRiskResult(result);
      setLoanForm((prev) => ({
        ...prev,
        approval_probability: String(result.approval_probability),
        risk_category: result.risk_category,
      }));
    } catch (error) {
      setRiskError(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleLoanSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setLoanError("");
    try {
      const result = await postJson("/loans/recommend", {
        requested_amount: toNumber(loanForm.requested_amount),
        risk_category: loanForm.risk_category,
        approval_probability: toNumber(loanForm.approval_probability),
        occupation: riskForm.occupation.trim(),
        purpose: riskForm.purpose.trim(),
      });
      setLoanResult(result);
    } catch (error) {
      setLoanError(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleTaxSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setTaxError("");
    try {
      const result = await postJson("/tax/estimate", {
        salary_income: toNumber(taxForm.salary_income),
        business_income: toNumber(taxForm.business_income),
        other_income: toNumber(taxForm.other_income),
        investments_80c: toNumber(taxForm.investments_80c),
        insurance_80d: toNumber(taxForm.insurance_80d),
        other_deductions: toNumber(taxForm.other_deductions),
      });
      setTaxResult(result);
    } catch (error) {
      setTaxError(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleExtractSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setTaxError("");
    try {
      const result = await postJson("/tax/extract", { text: extractText });
      setExtractResult(result);
    } catch (error) {
      setTaxError(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleGoalSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setGoalError("");
    try {
      const result = await postJson("/planning/goal-plan", {
        goal_name: goalForm.goal_name,
        target_price: toNumber(goalForm.target_price),
        time_horizon_months: Math.max(1, Math.round(toNumber(goalForm.time_horizon_months, 1))),
        current_saved: toNumber(goalForm.current_saved),
        monthly_income: toNumber(goalForm.monthly_income),
        monthly_expenses: toNumber(goalForm.monthly_expenses),
      });
      setGoalResult(result);
    } catch (error) {
      setGoalError(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleBudgetSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setBudgetError("");
    try {
      const history = budgetHistory
        .split(",")
        .map((x) => toNumber(x.trim()))
        .filter((x) => x > 0);
      const result = await postJson("/budget/forecast", { monthly_expense_history: history });
      setBudgetResult(result);
    } catch (error) {
      setBudgetError(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCategorizeSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setBudgetError("");
    try {
      const transactions = transactionsText
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => {
          const [description, amount] = line.split(",");
          return { description: description?.trim() || "Unknown", amount: toNumber(amount?.trim()) };
        });
      const result = await postJson("/budget/categorize", { transactions });
      setCategorizeResult(result);
    } catch (error) {
      setBudgetError(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCashLedgerEntrySubmit(event) {
    event.preventDefault();
    setLoading(true);
    setBudgetError("");
    try {
      const payload = {
        user_id: cashLedgerForm.user_id.trim(),
        entry_date: cashLedgerForm.entry_date,
        entry_type: cashLedgerForm.entry_type,
        amount: toNumber(cashLedgerForm.amount),
        description: cashLedgerForm.description,
      };
      const result = await postJson("/budget/cash-ledger/entries", payload);
      setCashLedgerEntryResult(result);

      const report = await getJson(`/budget/cash-ledger/${payload.user_id}`);
      setCashLedgerReport(report);
      setCashLedgerFilter((prev) => ({ ...prev, user_id: payload.user_id }));
    } catch (error) {
      setBudgetError(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCashLedgerReportSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setBudgetError("");
    try {
      const userId = cashLedgerFilter.user_id.trim();
      if (!userId) {
        setBudgetError("Please enter a user ID.");
        return;
      }
      const params = new URLSearchParams();
      if (cashLedgerFilter.start_date) params.set("start_date", cashLedgerFilter.start_date);
      if (cashLedgerFilter.end_date) params.set("end_date", cashLedgerFilter.end_date);
      const suffix = params.toString() ? `?${params.toString()}` : "";
      const report = await getJson(`/budget/cash-ledger/${userId}${suffix}`);
      setCashLedgerReport(report);
    } catch (error) {
      setBudgetError(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleInsuranceSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setInsuranceError("");
    try {
      const result = await postJson("/insurance/advise", {
        age: Math.round(toNumber(insuranceForm.age)),
        monthly_income: toNumber(insuranceForm.monthly_income),
        family_members: Math.round(toNumber(insuranceForm.family_members)),
        health_conditions: insuranceForm.health_conditions
          .split(",")
          .map((x) => x.trim())
          .filter(Boolean),
        occupation_risk_level: insuranceForm.occupation_risk_level,
      });
      setInsuranceResult(result);
    } catch (error) {
      setInsuranceError(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleInclusionSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setInclusionError("");
    try {
      const result = await postJson("/inclusion/recommend", {
        monthly_income: toNumber(inclusionForm.monthly_income),
        cibil_score: Math.round(toNumber(inclusionForm.cibil_score)),
        location: inclusionForm.location,
        occupation: inclusionForm.occupation,
      });
      setInclusionResult(result);
    } catch (error) {
      setInclusionError(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleTranslateSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setAssistError("");
    try {
      const result = await postJson("/assist/translate", translateForm);
      setTranslateResult(result);
    } catch (error) {
      setAssistError(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleVoiceSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setAssistError("");
    try {
      const result = await postJson("/assist/voice-intent", { text: voiceText });
      setVoiceResult(result);
    } catch (error) {
      setAssistError(error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <h1>FinAware AI</h1>
        <p>AI-Powered Financial Awareness and Microloan Risk Platform</p>
        <div className="hero-metadata">
          <span>{statusBadge}</span>
          {loading && <span>Processing...</span>}
          {globalError && <span className="danger-text">{globalError}</span>}
        </div>
      </header>

      <nav className="tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={activeTab === tab.id ? "tab active" : "tab"}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {activeTab === "risk" && (
        <div className="grid">
          <SectionCard
            title="Risk Assessment"
            subtitle="Use manual values or upload a statement; statement metrics are used directly in risk calculation"
          >
            <form onSubmit={handleRiskSubmit} className="form-grid">
              <label className="field">
                <span>Monthly Income (Estimate)</span>
                <input
                  value={riskForm.monthly_income}
                  onChange={(e) => setRiskForm((p) => ({ ...p, monthly_income: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>Existing EMIs</span>
                <input
                  value={riskForm.existing_emis}
                  onChange={(e) => setRiskForm((p) => ({ ...p, existing_emis: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>Current Savings</span>
                <input
                  value={riskForm.current_savings}
                  onChange={(e) => setRiskForm((p) => ({ ...p, current_savings: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>Monthly Expenses</span>
                <input
                  value={riskForm.monthly_expenses}
                  onChange={(e) => setRiskForm((p) => ({ ...p, monthly_expenses: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>CIBIL Score (Optional)</span>
                <input
                  value={riskForm.cibil_score}
                  onChange={(e) => setRiskForm((p) => ({ ...p, cibil_score: e.target.value }))}
                  placeholder="Leave blank if unavailable"
                />
              </label>
              <label className="field">
                <span>Purpose</span>
                <input
                  value={riskForm.purpose}
                  onChange={(e) => setRiskForm((p) => ({ ...p, purpose: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>Loan Amount</span>
                <input
                  value={riskForm.loan_amount}
                  onChange={(e) => setRiskForm((p) => ({ ...p, loan_amount: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>Occupation</span>
                <input
                  value={riskForm.occupation}
                  onChange={(e) => setRiskForm((p) => ({ ...p, occupation: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>Age</span>
                <input
                  value={riskForm.age}
                  onChange={(e) => setRiskForm((p) => ({ ...p, age: e.target.value }))}
                />
              </label>
              <label className="field wide">
                <span>Bank Statement (Optional, any format)</span>
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls,.pdf,.doc,.docx,.txt,.tsv,.json,.xml"
                  onChange={(e) => setStatementFile(e.target.files?.[0] || null)}
                />
              </label>
              <button type="submit">Assess Risk</button>
            </form>
            <RiskResultBox data={riskResult} error={riskError} />
          </SectionCard>
        </div>
      )}

      {activeTab === "loan" && (
        <div className="grid two-col">
          <SectionCard
            title="Loan Recommendation"
            subtitle="Ranks loans directly from the India loans dataset using weighted suitability scoring"
          >
            <form onSubmit={handleLoanSubmit} className="form-grid">
              <label className="field">
                <span>Requested Amount</span>
                <input
                  value={loanForm.requested_amount}
                  onChange={(e) => setLoanForm((p) => ({ ...p, requested_amount: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>Risk Category</span>
                <select
                  value={loanForm.risk_category}
                  onChange={(e) => setLoanForm((p) => ({ ...p, risk_category: e.target.value }))}
                >
                  <option>Low</option>
                  <option>Medium</option>
                  <option>High</option>
                </select>
              </label>
              <label className="field">
                <span>Approval Probability</span>
                <input
                  value={loanForm.approval_probability}
                  onChange={(e) => setLoanForm((p) => ({ ...p, approval_probability: e.target.value }))}
                />
              </label>
              <button type="submit">Recommend Best Loan</button>
            </form>
            <LoanResultBox data={loanResult} error={loanError} />
          </SectionCard>
        </div>
      )}

      {activeTab === "tax" && (
        <div className="grid two-col">
          <SectionCard title="AI Tax Assistant" subtitle="Estimate tax and identify deductions">
            <form onSubmit={handleTaxSubmit} className="form-grid">
              {Object.keys(taxForm).map((key) => (
                <label key={key} className="field">
                  <span>{key}</span>
                  <input
                    value={taxForm[key]}
                    onChange={(e) => setTaxForm((p) => ({ ...p, [key]: e.target.value }))}
                  />
                </label>
              ))}
              <button type="submit">Estimate Tax</button>
            </form>
            <JsonBox data={taxResult} error={taxError} />
          </SectionCard>

          <SectionCard title="Document Entity Extractor" subtitle="Text-based NLP extraction">
            <form onSubmit={handleExtractSubmit} className="form-grid">
              <label className="field wide">
                <span>Document Text</span>
                <textarea
                  rows={8}
                  value={extractText}
                  onChange={(e) => setExtractText(e.target.value)}
                />
              </label>
              <button type="submit">Extract Entities</button>
            </form>
            <JsonBox data={extractResult} error={taxError} />
          </SectionCard>
        </div>
      )}

      {activeTab === "planning" && (
        <div className="grid two-col">
          <SectionCard title="Goal-Based Planning" subtitle="Generate monthly savings target">
            <form onSubmit={handleGoalSubmit} className="form-grid">
              {Object.keys(goalForm).map((key) => (
                <label key={key} className="field">
                  <span>{key}</span>
                  <input
                    value={goalForm[key]}
                    onChange={(e) => setGoalForm((p) => ({ ...p, [key]: e.target.value }))}
                  />
                </label>
              ))}
              <button type="submit">Generate Plan</button>
            </form>
            <JsonBox data={goalResult} error={goalError} />
          </SectionCard>
        </div>
      )}

      {activeTab === "budget" && (
        <div className="grid two-col">
          <SectionCard title="Expense Forecast" subtitle="Predict next month spending">
            <form onSubmit={handleBudgetSubmit} className="form-grid">
              <label className="field wide">
                <span>Monthly History (comma separated)</span>
                <textarea
                  rows={3}
                  value={budgetHistory}
                  onChange={(e) => setBudgetHistory(e.target.value)}
                />
              </label>
              <button type="submit">Forecast Budget</button>
            </form>
            <JsonBox data={budgetResult} error={budgetError} />
          </SectionCard>

          <SectionCard title="Expense Categorization" subtitle="Description + amount per line">
            <form onSubmit={handleCategorizeSubmit} className="form-grid">
              <label className="field wide">
                <span>Transactions</span>
                <textarea
                  rows={8}
                  value={transactionsText}
                  onChange={(e) => setTransactionsText(e.target.value)}
                />
              </label>
              <button type="submit">Categorize</button>
            </form>
            <JsonBox data={categorizeResult} error={budgetError} />
          </SectionCard>

          <SectionCard
            title="Manual Cash Ledger"
            subtitle="Enter cash transactions and compute day-wise opening/closing balances"
          >
            <form onSubmit={handleCashLedgerEntrySubmit} className="form-grid">
              <label className="field">
                <span>User ID</span>
                <input
                  value={cashLedgerForm.user_id}
                  onChange={(e) => setCashLedgerForm((p) => ({ ...p, user_id: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>Entry Date</span>
                <input
                  type="date"
                  value={cashLedgerForm.entry_date}
                  onChange={(e) =>
                    setCashLedgerForm((p) => ({ ...p, entry_date: e.target.value }))
                  }
                />
              </label>
              <label className="field">
                <span>Entry Type</span>
                <select
                  value={cashLedgerForm.entry_type}
                  onChange={(e) =>
                    setCashLedgerForm((p) => ({ ...p, entry_type: e.target.value }))
                  }
                >
                  <option value="inflow">inflow (sales/receipt)</option>
                  <option value="outflow">outflow (purchase/expense)</option>
                </select>
              </label>
              <label className="field">
                <span>Amount</span>
                <input
                  value={cashLedgerForm.amount}
                  onChange={(e) => setCashLedgerForm((p) => ({ ...p, amount: e.target.value }))}
                />
              </label>
              <label className="field wide">
                <span>Description</span>
                <input
                  value={cashLedgerForm.description}
                  onChange={(e) =>
                    setCashLedgerForm((p) => ({ ...p, description: e.target.value }))
                  }
                />
              </label>
              <button type="submit">Add Cash Entry</button>
            </form>

            <form onSubmit={handleCashLedgerReportSubmit} className="form-grid">
              <label className="field">
                <span>Report User ID</span>
                <input
                  value={cashLedgerFilter.user_id}
                  onChange={(e) => setCashLedgerFilter((p) => ({ ...p, user_id: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>Start Date (optional)</span>
                <input
                  type="date"
                  value={cashLedgerFilter.start_date}
                  onChange={(e) =>
                    setCashLedgerFilter((p) => ({ ...p, start_date: e.target.value }))
                  }
                />
              </label>
              <label className="field">
                <span>End Date (optional)</span>
                <input
                  type="date"
                  value={cashLedgerFilter.end_date}
                  onChange={(e) =>
                    setCashLedgerFilter((p) => ({ ...p, end_date: e.target.value }))
                  }
                />
              </label>
              <button type="submit">Load Ledger Report</button>
            </form>

            <JsonBox data={cashLedgerEntryResult} error={budgetError} />
            <JsonBox data={cashLedgerReport} error={budgetError} />
          </SectionCard>
        </div>
      )}

      {activeTab === "insurance" && (
        <div className="grid two-col">
          <SectionCard title="Insurance Advisory" subtitle="Risk profile and coverage target">
            <form onSubmit={handleInsuranceSubmit} className="form-grid">
              <label className="field">
                <span>Age</span>
                <input
                  value={insuranceForm.age}
                  onChange={(e) => setInsuranceForm((p) => ({ ...p, age: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>Monthly Income</span>
                <input
                  value={insuranceForm.monthly_income}
                  onChange={(e) =>
                    setInsuranceForm((p) => ({ ...p, monthly_income: e.target.value }))
                  }
                />
              </label>
              <label className="field">
                <span>Family Members</span>
                <input
                  value={insuranceForm.family_members}
                  onChange={(e) =>
                    setInsuranceForm((p) => ({ ...p, family_members: e.target.value }))
                  }
                />
              </label>
              <label className="field">
                <span>Health Conditions (comma separated)</span>
                <input
                  value={insuranceForm.health_conditions}
                  onChange={(e) =>
                    setInsuranceForm((p) => ({ ...p, health_conditions: e.target.value }))
                  }
                />
              </label>
              <label className="field">
                <span>Occupation Risk</span>
                <select
                  value={insuranceForm.occupation_risk_level}
                  onChange={(e) =>
                    setInsuranceForm((p) => ({ ...p, occupation_risk_level: e.target.value }))
                  }
                >
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                </select>
              </label>
              <button type="submit">Get Insurance Advice</button>
            </form>
            <JsonBox data={insuranceResult} error={insuranceError} />
          </SectionCard>
        </div>
      )}

      {activeTab === "inclusion" && (
        <div className="grid two-col">
          <SectionCard title="Financial Inclusion Support" subtitle="Alternative credit and scheme matching">
            <form onSubmit={handleInclusionSubmit} className="form-grid">
              {Object.keys(inclusionForm).map((key) => (
                <label key={key} className="field">
                  <span>{key}</span>
                  <input
                    value={inclusionForm[key]}
                    onChange={(e) => setInclusionForm((p) => ({ ...p, [key]: e.target.value }))}
                  />
                </label>
              ))}
              <button type="submit">Get Support Options</button>
            </form>
            <JsonBox data={inclusionResult} error={inclusionError} />
          </SectionCard>
        </div>
      )}

      {activeTab === "assist" && (
        <div className="grid two-col">
          <SectionCard title="Multilingual Assistant" subtitle="Translate guidance text">
            <form onSubmit={handleTranslateSubmit} className="form-grid">
              <label className="field wide">
                <span>Text</span>
                <textarea
                  rows={5}
                  value={translateForm.text}
                  onChange={(e) => setTranslateForm((p) => ({ ...p, text: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>Source</span>
                <input
                  value={translateForm.source_lang}
                  onChange={(e) => setTranslateForm((p) => ({ ...p, source_lang: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>Target</span>
                <input
                  value={translateForm.target_lang}
                  onChange={(e) => setTranslateForm((p) => ({ ...p, target_lang: e.target.value }))}
                />
              </label>
              <button type="submit">Translate</button>
            </form>
            <JsonBox data={translateResult} error={assistError} />
          </SectionCard>

          <SectionCard title="Voice Intent Classifier" subtitle="Text proxy for voice command intent">
            <form onSubmit={handleVoiceSubmit} className="form-grid">
              <label className="field wide">
                <span>Voice Transcript</span>
                <textarea rows={4} value={voiceText} onChange={(e) => setVoiceText(e.target.value)} />
              </label>
              <button type="submit">Classify Intent</button>
            </form>
            <JsonBox data={voiceResult} error={assistError} />
          </SectionCard>
        </div>
      )}
    </main>
  );
}
