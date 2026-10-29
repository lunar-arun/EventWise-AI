export type TaskStatus = "pending" | "in_progress" | "completed";
export type TaskPriority = "low" | "medium" | "high";

export interface TaskItem {
  id: number;
  event_id: number;
  title: string;
  description: string;
  milestone_label: string;
  due_date: string;
  status: TaskStatus;
  priority: TaskPriority;
  category: string;
  is_clamped: boolean;
  created_at: string;
  updated_at: string;
}

export interface TaskCreateInput {
  title: string;
  description?: string;
  milestone_label?: string;
  due_date: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  category?: string;
}

export interface TaskUpdateInput {
  title?: string;
  description?: string;
  milestone_label?: string;
  due_date?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  category?: string;
}

export interface TimelineSummary {
  event_id: number;
  event_name: string;
  event_type: string;
  event_date: string;
  days_until_event: number;
  schedule_notice: string | null;
  total_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  pending_tasks: number;
  completion_percentage: number;
  tasks: TaskItem[];
}
