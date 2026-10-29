import type { BudgetSummary } from "./budget";
import type { SourceCitation } from "./knowledge";
import type { TaskItem } from "./task";

export type EventType = "wedding" | "birthday" | "community";

export interface ThemeRecommendation {
  title: string;
  tagline: string;
  description: string;
  decor_highlights: string[];
  catering_notes: string;
  estimated_tier: string;
  source_Backed: boolean;
}

export interface EventCreateInput {
  name: string;
  event_type: EventType;
  location: string;
  total_budget: number;
  guest_count: number;
  event_date: string;
  preferred_theme?: string;
  dietary_requirements?: string;
  additional_preferences?: string;
  generate_initial_plan?: boolean;
}

export interface EventUpdateInput {
  name?: string;
  event_type?: EventType;
  location?: string;
  total_budget?: number;
  user_approved_budget_change?: boolean;
  guest_count?: number;
  event_date?: string;
  preferred_theme?: string;
  dietary_requirements?: string;
  additional_preferences?: string;
  regenerate_plan?: boolean;
}

export interface EventSummaryCard {
  id: number;
  name: string;
  event_type: EventType;
  location: string;
  total_budget: number;
  guest_count: number;
  event_date: string;
  preferred_theme: string;
  dietary_requirements: string;
  summary: string;
  total_tasks: number;
  completed_tasks: number;
  completion_percentage: number;
  planned_spending: number;
  actual_spending: number;
  remaining_budget: number;
  level_badge: string;
  created_at: string;
  updated_at: string;
}

export interface EventDetail {
  id: number;
  name: string;
  event_type: EventType;
  location: string;
  total_budget: number;
  guest_count: number;
  event_date: string;
  preferred_theme: string;
  dietary_requirements: string;
  additional_preferences: string;
  summary: string;
  theme_recommendations: ThemeRecommendation[];
  ai_suggestions: string[];
  citations: SourceCitation[];
  missing_evidence_note: string;
  generation_mode: string;
  illustrative_price_notice: string;
  budget: BudgetSummary;
  tasks: TaskItem[];
  created_at: string;
  updated_at: string;
}

export interface ActivityItem {
  id: string;
  category: "event" | "task" | "expense" | "knowledge" | "chat";
  title: string;
  detail: string;
  timestamp: string;
  event_id: number | null;
}

export interface DashboardData {
  total_events: number;
  upcoming_events_count: number;
  total_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  overall_completion_percentage: number;
  total_budget_across_events: number;
  total_planned_across_events: number;
  total_actual_across_events: number;
  remaining_budget_across_events: number;
  indexed_documents_count: number;
  upcoming_events: EventSummaryCard[];
  upcoming_quests: TaskItem[];
  recent_activity: ActivityItem[];
}

export interface LlmHealthStatus {
  status: string;
  ollama_reachable: boolean;
  configured_model: string;
  configured_model_available: boolean;
  available_models: string[];
  detail?: string;
}
