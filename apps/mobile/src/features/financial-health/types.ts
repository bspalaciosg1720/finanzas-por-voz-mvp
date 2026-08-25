export type HealthComponent = {
  key: string;
  label: string;
  score: number;
  maximum: number;
  explanation: string;
};

export type HealthRecommendation = {
  priority: number;
  title: string;
  detail: string;
};

export type FinancialHealthSummary = {
  period: string;
  currency: string;
  score: number | null;
  status: string;
  confidence: "baja" | "media" | "alta";
  income_minor: number;
  essential_expense_minor: number;
  variable_expense_minor: number;
  unclassified_expense_minor: number;
  total_expense_minor: number;
  available_cash_minor: number;
  savings_minor: number;
  total_debt_minor: number;
  minimum_debt_payments_minor: number;
  debt_payments_minor: number;
  emergency_fund_minor: number;
  emergency_fund_months: number | null;
  pending_replenishment_minor: number;
  essential_percent: number | null;
  variable_percent: number | null;
  savings_percent: number | null;
  debt_payment_percent: number | null;
  budget_used_percent: number | null;
  components: HealthComponent[];
  recommendations: HealthRecommendation[];
  limitations: string[];
};

export type HealthHistory = {
  trend: "improving" | "declining" | "stable";
  items: Array<{ period: string; score: number; status: string; formula_version: string; change: number | null }>;
};

export type FinancialPattern = {
  key: string;
  direction: "attention" | "positive" | "info";
  title: string;
  detail: string;
  start_period: string;
  end_period: string;
  previous_amount_minor: number | null;
  current_amount_minor: number | null;
  change_percent: number | null;
  category_name: string | null;
};

export type FinancialPatterns = {
  currency: string;
  months_analyzed: number;
  periods: string[];
  patterns: FinancialPattern[];
  limitations: string[];
};

export type FinancialAlert = {
  key: string;
  kind: string;
  priority: number;
  tone: "attention" | "positive" | "info";
  title: string;
  detail: string;
  action_path: string | null;
};

export type FinancialAlerts = {
  items: FinancialAlert[];
  total_candidates: number;
};

export type IncomeProfile = {
  currency: string;
  classification: "stable" | "variable" | "insufficient_data";
  months_analyzed: number;
  months_with_income: number;
  average_income_minor: number | null;
  median_income_minor: number | null;
  conservative_income_minor: number | null;
  variability_percent: number | null;
  monthly_incomes: Array<{ period: string; amount_minor: number }>;
  explanation: string;
  limitations: string[];
};

export type ExtraIncomeAnalysis = {
  period: string;
  currency: string;
  detected: boolean;
  source: "detected" | "supplied";
  current_income_minor: number;
  conservative_income_minor: number | null;
  extra_income_minor: number;
  applied: false;
  explanation: string;
  allocations: Array<{
    destination: string;
    label: string;
    amount_minor: number;
    rationale: string;
  }>;
  limitations: string[];
};
