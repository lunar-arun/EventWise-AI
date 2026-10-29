import type { EventType } from "@/types/event";
import type { TaskPriority, TaskStatus } from "@/types/task";

const inrFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export function formatINR(amount: number): string {
  if (!Number.isFinite(amount)) {
    return "₹0";
  }
  return inrFormatter.format(Math.round(amount));
}

export function formatDateDisplay(isoDate: string): string {
  if (!isoDate) return "—";
  const parsed = new Date(isoDate);
  if (Number.isNaN(parsed.getTime())) return isoDate;
  return parsed.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatEventTypeLabel(eventType: EventType | string): string {
  switch (eventType) {
    case "birthday":
      return "Birthday Quest";
    case "wedding":
      return "Wedding Odyssey";
    case "community":
      return "Community Festival";
    default:
      return String(eventType);
  }
}

export function formatTaskStatusLabel(status: TaskStatus): string {
  switch (status) {
    case "completed":
      return "Completed (Star Cleared)";
    case "in_progress":
      return "In Progress (Active Quest)";
    case "pending":
    default:
      return "Pending (Upcoming)";
  }
}

export function formatPriorityLabel(priority: TaskPriority): string {
  switch (priority) {
    case "high":
      return "Boss Priority (High)";
    case "medium":
      return "Standard Quest (Medium)";
    case "low":
    default:
      return "Bonus Coin (Low)";
  }
}
