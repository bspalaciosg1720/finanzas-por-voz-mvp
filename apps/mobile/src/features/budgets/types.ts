export type BudgetStatus = "on_track" | "warning" | "exceeded";

export type Budget = {
  id: string;
  category_id: string;
  category_name: string;
  amount_minor: number;
  spent_minor: number;
  currency: string;
  alert_threshold_percent: number;
  progress_percent: number;
  alert_status: BudgetStatus;
};

export type BudgetAlert = {
  id: string;
  budget_id: string;
  period_start: string;
  level: "warning" | "exceeded";
  category_name: string;
  read_at: string | null;
  created_at: string;
};
