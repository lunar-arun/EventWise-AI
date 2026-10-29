import type { BudgetCategoryAllocationInput } from "./budget";
import type { SourceCitation } from "./knowledge";

export interface ProposedBudgetChange {
  action_type: "propose_budget_reduction" | "propose_budget_reallocation" | "propose_preference_update";
  summary: string;
  current_total_budget: number;
  proposed_total_budget: number;
  proposed_categories: BudgetCategoryAllocationInput[];
  proposed_preferences: Record<string, string>;
  requires_user_approval: boolean;
  warning: string;
}

export interface ChatRequestInput {
  message: string;
  event_id?: number | null;
  session_id?: number | null;
}

export interface ChatMessage {
  id: number;
  session_id: number;
  event_id: number | null;
  role: "user" | "assistant";
  content: string;
  citations: SourceCitation[];
  proposed_changes: ProposedBudgetChange | null;
  created_at: string;
}

export interface ChatResponse {
  session_id: number;
  event_id: number | null;
  reply: string;
  suggestions: string[];
  citations: SourceCitation[];
  proposed_changes: ProposedBudgetChange | null;
  missing_evidence_note: string | null;
  generation_mode: string;
  history: ChatMessage[];
}

export interface ChatSessionSummary {
  id: number;
  event_id: number | null;
  title: string;
  message_count: number;
  updated_at: string;
}
