export type VoiceInterpretation = {
  interaction_id: string;
  transcript: string;
  movement_type: "income" | "expense" | null;
  amount_minor: number | null;
  currency: string;
  category_id: string | null;
  category_name: string | null;
  description: string;
  occurred_at: string;
  confidence: Record<string, number>;
  ambiguities: string[];
  requires_confirmation: boolean;
};

export type AudioTranscription = {
  transcript: string;
  provider: string;
};
