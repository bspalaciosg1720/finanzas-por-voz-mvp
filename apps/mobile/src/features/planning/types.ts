export type EmergencyFund = {
  currency: string;
  target_months: number;
  balance_minor: number;
  pending_replenishment_minor: number;
  essential_expense_minor: number;
  target_amount_minor: number;
  coverage_months: number | null;
  progress_percent: number | null;
  events: Array<{ id: string; event_type: "deposit" | "withdrawal"; amount_minor: number; occurred_at: string; note: string }>;
};

export type CalendarItem = {
  obligation_id: string;
  name: string;
  obligation_type: string;
  amount_minor: number;
  currency: string;
  due_date: string;
  days_until_due: number;
  status: "paid" | "upcoming";
  payment_id: string | null;
  category_id: string | null;
  category_name: string;
};

export type FinancialCalendar = { items: CalendarItem[]; concentrated_weeks: string[] };

export type SimulationResult = {
  scenario: string;
  currency: string;
  current: { available_cash_minor: number; variable_expense_minor: number; savings_minor: number; monthly_goal_amount_minor: number | null; debt_free_months: number | null };
  simulated: { available_cash_minor: number; variable_expense_minor: number; savings_minor: number; monthly_goal_amount_minor: number | null; debt_free_months: number | null };
  limitations: string[];
  applied: false;
};
