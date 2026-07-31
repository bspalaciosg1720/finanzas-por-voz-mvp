export type ReportPeriod = "daily" | "weekly" | "monthly" | "annual";

export type ReportSummary = {
  period: ReportPeriod;
  start_date: string;
  end_date: string;
  currency: string;
  income_minor: number;
  expense_minor: number;
  balance_minor: number;
  transaction_count: number;
  previous_income_minor: number;
  previous_expense_minor: number;
  expense_change_percent: number | null;
  categories: Array<{
    category_id: string | null;
    name: string;
    amount_minor: number;
    percentage: number;
  }>;
  series: Array<{
    label: string;
    income_minor: number;
    expense_minor: number;
  }>;
};
