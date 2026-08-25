export type TransactionType = "income" | "expense";

export type Transaction = {
  id: string;
  category_id: string | null;
  type: TransactionType;
  amount_minor: number;
  currency: string;
  description: string;
  occurred_at: string;
  source: "manual" | "voice" | "import" | "integration";
  financial_role: "regular" | "debt_payment" | "savings_transfer" | "obligation_payment";
  status: string;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
};

export type TransactionPage = {
  items: Transaction[];
  next_cursor: string | null;
};

export type Category = {
  id: string;
  name: string;
  slug: string;
  icon: string;
  movement_scope: "income" | "expense" | "both";
  is_system: boolean;
};

export type CreateTransactionInput = {
  type: TransactionType;
  amount_minor: number;
  currency: string;
  category_id: string | null;
  description: string;
  occurred_at: string;
  source: "manual";
};

export type TransactionSuggestion = {
  id: string;
  transaction_id: string | null;
  sender_domain: string;
  type: TransactionType;
  amount_minor: number;
  currency: string;
  description: string;
  occurred_at: string;
  confidence: number;
  status: "pending" | "confirmed" | "discarded";
  created_at: string;
  resolved_at: string | null;
};

export type TransactionInbox = {
  address: string;
};
