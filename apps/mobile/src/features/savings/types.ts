export type SavingsContribution = {
  id: string;
  amount_minor: number;
  contributed_at: string;
  note: string;
};

export type SavingsGoal = {
  id: string;
  name: string;
  target_amount_minor: number;
  saved_amount_minor: number;
  currency: string;
  target_date: string | null;
  status: "active" | "completed";
  progress_percent: number;
  contributions: SavingsContribution[];
};
