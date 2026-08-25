export type Debt = {
  id: string;
  name: string;
  debt_type: string;
  initial_balance_minor: number;
  current_balance_minor: number;
  minimum_payment_minor: number;
  currency: string;
  annual_interest_rate_bps: number | null;
  payment_day: number | null;
  status: "active" | "paid" | "archived";
  progress_percent: number;
  payments: Array<{
    id: string;
    amount_minor: number;
    payment_type: string;
    paid_at: string;
    note: string;
  }>;
};

export type PayoffPlan = {
  strategy: "snowball" | "avalanche";
  currency: string;
  minimum_payments_minor: number;
  extra_payment_minor: number;
  total_monthly_payment_minor: number;
  estimated_months: number | null;
  estimated_interest_minor: number | null;
  steps: Array<{
    debt_id: string;
    name: string;
    order: number;
    balance_minor: number;
    monthly_payment_minor: number;
    estimated_months: number | null;
  }>;
  limitations: string[];
};
