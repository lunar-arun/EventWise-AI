import type {
  BudgetSummary,
  BudgetUpdateRequest,
  ExpenseCreateInput,
} from "@/types/budget";
import type {
  ChatMessage,
  ChatRequestInput,
  ChatResponse,
  ChatSessionSummary,
} from "@/types/chat";
import type {
  DashboardData,
  EventCreateInput,
  EventDetail,
  EventSummaryCard,
  EventUpdateInput,
  LlmHealthStatus,
} from "@/types/event";
import type {
  KnowledgeDocument,
  KnowledgeEntryCreateInput,
  KnowledgeEntryUpdateInput,
  KnowledgeSearchRequest,
  KnowledgeSearchResponse,
} from "@/types/knowledge";
import type {
  TaskCreateInput,
  TaskItem,
  TaskUpdateInput,
  TimelineSummary,
} from "@/types/task";

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
).replace(/\/$/, "");

export class ApiClientError extends Error {
  public status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: {
        ...(init?.body instanceof FormData
          ? {}
          : { "Content-Type": "application/json" }),
        ...(init?.headers || {}),
      },
      cache: "no-store",
    });
  } catch {
    throw new ApiClientError(
      `Unable to reach local FastAPI backend at ${API_BASE_URL}. Ensure the backend server is running.`,
      0
    );
  }

  if (!response.ok) {
    let errorDetail = `Request failed with HTTP ${response.status}`;
    try {
      const errBody = (await response.json()) as {
        detail?: string | Array<{ msg?: string; loc?: Array<string | number> }>;
      };
      if (typeof errBody.detail === "string") {
        errorDetail = errBody.detail;
      } else if (Array.isArray(errBody.detail)) {
        errorDetail = errBody.detail
          .map((item) => `${(item.loc || []).join(".")}: ${item.msg || "Invalid"}`)
          .join("; ");
      }
    } catch {
      // Fallback to status text
    }
    throw new ApiClientError(errorDetail, response.status);
  }

  return (await response.json()) as T;
}

export const apiClient = {
  getHealth: () =>
    requestJson<{
      status: string;
      app: string;
      version: string;
      local_only: boolean;
      embedding_model: string;
      ollama_model: string;
    }>("/api/health"),

  getLlmHealth: () => requestJson<LlmHealthStatus>("/api/health/llm"),

  getDashboard: () => requestJson<DashboardData>("/api/dashboard"),

  listEvents: () => requestJson<EventSummaryCard[]>("/api/events"),

  getEvent: (eventId: number) =>
    requestJson<EventDetail>(`/api/events/${eventId}`),

  createEvent: (payload: EventCreateInput) =>
    requestJson<EventDetail>("/api/events", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateEvent: (eventId: number, payload: EventUpdateInput) =>
    requestJson<EventDetail>(`/api/events/${eventId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  deleteEvent: (eventId: number) =>
    requestJson<{ status: string; message: string }>(`/api/events/${eventId}`, {
      method: "DELETE",
    }),

  generateEventPlan: (
    eventId: number,
    options?: { resetBudget?: boolean; resetTimeline?: boolean }
  ) => {
    const params = new URLSearchParams();
    if (options?.resetBudget) params.set("reset_budget", "true");
    if (options?.resetTimeline) params.set("reset_timeline", "true");
    const qs = params.toString() ? `?${params.toString()}` : "";
    return requestJson<EventDetail>(
      `/api/events/${eventId}/generate-plan${qs}`,
      {
        method: "POST",
      }
    );
  },

  getEventBudget: (eventId: number) =>
    requestJson<BudgetSummary>(`/api/events/${eventId}/budget`),

  updateEventBudget: (eventId: number, payload: BudgetUpdateRequest) =>
    requestJson<BudgetSummary>(`/api/events/${eventId}/budget`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  addExpense: (eventId: number, payload: ExpenseCreateInput) =>
    requestJson<BudgetSummary>(`/api/events/${eventId}/expenses`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  deleteExpense: (eventId: number, expenseId: number) =>
    requestJson<BudgetSummary>(
      `/api/events/${eventId}/expenses/${expenseId}`,
      {
        method: "DELETE",
      }
    ),

  getEventTimeline: (eventId: number) =>
    requestJson<TimelineSummary>(`/api/events/${eventId}/tasks`),

  createEventTask: (eventId: number, payload: TaskCreateInput) =>
    requestJson<TaskItem>(`/api/events/${eventId}/tasks`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateTask: (taskId: number, payload: TaskUpdateInput) =>
    requestJson<TaskItem>(`/api/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  deleteTask: (taskId: number) =>
    requestJson<{ status: string; message: string }>(`/api/tasks/${taskId}`, {
      method: "DELETE",
    }),

  sendChatMessage: (payload: ChatRequestInput) =>
    requestJson<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  listChatSessions: (eventId?: number | null) => {
    const qs = eventId ? `?event_id=${eventId}` : "";
    return requestJson<ChatSessionSummary[]>(`/api/chat/sessions${qs}`);
  },

  getChatSessionMessages: (sessionId: number) =>
    requestJson<ChatMessage[]>(`/api/chat/sessions/${sessionId}`),

  listKnowledgeDocuments: () =>
    requestJson<KnowledgeDocument[]>("/api/knowledge/documents"),

  uploadKnowledgeDocument: (formData: FormData) =>
    requestJson<KnowledgeDocument>("/api/knowledge/upload", {
      method: "POST",
      body: formData,
    }),

  createKnowledgeEntry: (payload: KnowledgeEntryCreateInput) =>
    requestJson<KnowledgeDocument>("/api/knowledge/entries", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateKnowledgeEntry: (
    documentId: string,
    payload: KnowledgeEntryUpdateInput
  ) =>
    requestJson<KnowledgeDocument>(`/api/knowledge/entries/${documentId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  searchKnowledgeBase: (payload: KnowledgeSearchRequest) =>
    requestJson<KnowledgeSearchResponse>("/api/knowledge/search", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  deleteKnowledgeDocument: (documentId: string) =>
    requestJson<{ status: string; document_id: string }>(
      `/api/knowledge/documents/${documentId}`,
      {
        method: "DELETE",
      }
    ),

  reindexKnowledgeDocument: (documentId: string) =>
    requestJson<KnowledgeDocument>(
      `/api/knowledge/documents/${documentId}/reindex`,
      {
        method: "POST",
      }
    ),
};
