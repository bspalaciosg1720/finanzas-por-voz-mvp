export type StrategyInsight = {
  key: string;
  enabled: boolean;
  recommended: boolean;
  priority: number;
  title: string;
  reason: string;
  benefit: string;
  impact_type: string;
  impact_minor: number | null;
  impact_percent: number | null;
  limitations: string[];
};

export type StrategyAnalysis = {
  period: string;
  currency: string;
  financial_level: "stabilize" | "protect" | "debt_freedom" | "build" | "grow";
  planning_income_minor: number;
  received_income_minor: number;
  priority_order: string[];
  strategies: StrategyInsight[];
};
