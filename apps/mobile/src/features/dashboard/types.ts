import type { Transaction } from "@/features/transactions/types";

export type DashboardSummary = {
  currency: string;
  period: string;
  balance_minor: number;
  income_minor: number;
  expense_minor: number;
  previous_income_minor: number;
  previous_expense_minor: number;
  expense_change_percent: number | null;
  top_expense_category: {
    category_id: string | null;
    name: string;
    amount_minor: number;
  } | null;
  recent_transactions: Transaction[];
};
