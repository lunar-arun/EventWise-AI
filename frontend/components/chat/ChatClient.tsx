"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  Bot,
  CheckCircle2,
  Loader2,
  Send,
  ShieldCheck,
  Sparkles,
  User,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { formatINR } from "@/lib/formatting";
import type {
  ChatMessage,
  ChatSessionSummary,
  ProposedBudgetChange,
} from "@/types/chat";
import type { EventSummaryCard } from "@/types/event";
import type { SourceCitation } from "@/types/knowledge";
import {
  CloudSkyBanner,
  ErrorBanner,
  QuestionBlockBadge,
} from "@/components/ui/MarioMotifs";
import { SourceCitationsList } from "@/components/knowledge/SourceCitationsList";

const QUICK_PROMPTS = [
  "Reduce my event budget by ₹5,000.",
  "Suggest three alternative birthday themes.",
  "What tasks remain before my event?",
  "How can I reduce decoration costs?",
  "Suggest a wedding plan for 200 guests.",
  "Adapt my plan for a vegetarian menu.",
];

export function ChatClient({
  fixedEventId,
  onEventModified,
  embedded = false,
}: {
  fixedEventId?: number;
  onEventModified?: () => void;
  embedded?: boolean;
}) {
  const [events, setEvents] = useState<EventSummaryCard[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(
    fixedEventId ?? null
  );
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [latestCitations, setLatestCitations] = useState<SourceCitation[]>([]);
  const [missingNote, setMissingNote] = useState<string | null>(null);
  const [inputText, setInputText] = useState("");
  const [sending, setSending] = useState(false);
  const [applyingProposal, setApplyingProposal] = useState(false);
  const [approvalBanner, setApprovalBanner] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadContext = useCallback(async () => {
    try {
      const evList = await apiClient.listEvents();
      setEvents(evList);
      const targetEvId =
        fixedEventId !== undefined
          ? fixedEventId
          : selectedEventId ?? (evList[0]?.id || null);
      if (targetEvId !== selectedEventId) {
        setSelectedEventId(targetEvId);
      }
      const sessList = await apiClient.listChatSessions(targetEvId);
      setSessions(sessList);
      if (sessList.length > 0) {
        const latestSess = sessList[0];
        setActiveSessionId(latestSess.id);
        const hist = await apiClient.getChatSessionMessages(latestSess.id);
        setMessages(hist);
        const lastAssistant = [...hist]
          .reverse()
          .find((m) => m.role === "assistant");
        if (lastAssistant) {
          setLatestCitations(lastAssistant.citations || []);
        }
      } else {
        setActiveSessionId(null);
        setMessages([]);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load chat context."
      );
    }
  }, [fixedEventId, selectedEventId]);

  useEffect(() => {
    void loadContext();
  }, [loadContext]);

  const handleSelectEvent = async (newEventId: number | null) => {
    setSelectedEventId(newEventId);
    setActiveSessionId(null);
    setMessages([]);
    setLatestCitations([]);
    setApprovalBanner(null);
    try {
      const sessList = await apiClient.listChatSessions(newEventId);
      setSessions(sessList);
      if (sessList.length > 0) {
        setActiveSessionId(sessList[0].id);
        const hist = await apiClient.getChatSessionMessages(sessList[0].id);
        setMessages(hist);
      }
    } catch {
      // Ignore session fetch error
    }
  };

  const handleSendMessage = async (textOverride?: string) => {
    const prompt = (textOverride ?? inputText).trim();
    if (!prompt || sending) return;

    setSending(true);
    setError(null);
    setApprovalBanner(null);
    if (!textOverride) setInputText("");

    try {
      const res = await apiClient.sendChatMessage({
        message: prompt,
        event_id: selectedEventId,
        session_id: activeSessionId,
      });
      setActiveSessionId(res.session_id);
      setMessages(res.history);
      setLatestCitations(res.citations);
      setMissingNote(res.missing_evidence_note);
      const sessList = await apiClient.listChatSessions(selectedEventId);
      setSessions(sessList);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to send chat message."
      );
    } finally {
      setSending(false);
    }
  };

  const handleApproveProposal = async (proposal: ProposedBudgetChange) => {
    if (!selectedEventId) return;
    setApplyingProposal(true);
    setError(null);
    try {
      if (
        proposal.action_type === "propose_budget_reduction" ||
        proposal.action_type === "propose_budget_reallocation"
      ) {
        await apiClient.updateEventBudget(selectedEventId, {
          total_budget: proposal.proposed_total_budget,
          user_approved_total_change: true,
          categories: proposal.proposed_categories,
        });
        setApprovalBanner(
          `Approved & applied! Event total budget is now ${formatINR(
            proposal.proposed_total_budget
          )} with protected Emergency Reserve.`
        );
      } else if (proposal.action_type === "propose_preference_update") {
        await apiClient.updateEvent(selectedEventId, {
          ...proposal.proposed_preferences,
          regenerate_plan: true,
        });
        setApprovalBanner(
          "Approved & applied! Dietary preferences updated and event recommendations refreshed."
        );
      }
      if (onEventModified) onEventModified();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to apply approved proposal."
      );
    } finally {
      setApplyingProposal(false);
    }
  };

  return (
    <div className="space-y-5">
      {!embedded && (
        <CloudSkyBanner
          badgeText="WORLD 4 • PERSISTENT RAG PLANNING CHATBOT"
          title="EventWise AI Planning Assistant"
          subtitle="Ask follow-up questions about budgets, alternative themes, remaining checklist quests, or vegetarian catering. Proposals are calculated deterministically in Python and require your approval before updating persisted data."
        />
      )}

      {error && <ErrorBanner message={error} />}

      {approvalBanner && (
        <div
          role="status"
          className="rounded-xl border-2 border-mario-navy bg-emerald-50 p-4 text-xs font-bold text-mario-navy flex items-center gap-2.5 shadow-retro-sm"
        >
          <CheckCircle2 className="w-5 h-5 text-mario-green shrink-0" />
          <span>{approvalBanner}</span>
        </div>
      )}

      {/* Event Context Selector Bar */}
      {fixedEventId === undefined && (
        <div className="rounded-2xl border-2 border-mario-navy bg-white p-4 shadow-retro-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <QuestionBlockBadge label="?" />
            <div>
              <label
                htmlFor="chat-event-select"
                className="block text-sm font-extrabold text-mario-navy"
              >
                Active Event Context
              </label>
              <p className="text-xs text-mario-muted">
                Select an event so the assistant can inspect its real SQLite budget and tasks
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <select
              id="chat-event-select"
              value={selectedEventId ?? ""}
              onChange={(e) =>
                handleSelectEvent(
                  e.target.value ? Number(e.target.value) : null
                )
              }
              className="rounded-xl border-2 border-mario-navy bg-mario-bg px-3.5 py-2 text-xs font-bold text-mario-navy focus:outline-none focus:ring-2 focus:ring-mario-red"
            >
              <option value="">General Event Planning (No Specific Event)</option>
              {events.map((ev) => (
                <option key={ev.id} value={ev.id}>
                  {ev.name} ({ev.location} • {formatINR(ev.total_budget)})
                </option>
              ))}
            </select>

            <button
              type="button"
              onClick={() => {
                setActiveSessionId(null);
                setMessages([]);
                setLatestCitations([]);
              }}
              className="px-3 py-2 rounded-xl bg-white border-2 border-mario-navy text-xs font-bold hover:bg-mario-gold transition-colors"
            >
              + New Chat Thread
            </button>
          </div>
        </div>
      )}

      {/* Quick Prompt Chips */}
      <div className="flex flex-wrap items-center gap-2">
        {QUICK_PROMPTS.map((q) => (
          <button
            key={q}
            type="button"
            disabled={sending}
            onClick={() => handleSendMessage(q)}
            className="px-3 py-1.5 rounded-full bg-white border-2 border-mario-navy text-xs font-bold text-mario-navy hover:bg-mario-gold transition-colors shadow-retro-sm disabled:opacity-50"
          >
            <Sparkles className="w-3 h-3 inline mr-1 text-mario-red" />
            {q}
          </button>
        ))}
      </div>

      {/* Chat Messages Thread */}
      <div className="rounded-2xl border-2 border-mario-navy bg-white shadow-retro overflow-hidden flex flex-col">
        <div className="max-h-[480px] min-h-[300px] overflow-y-auto p-5 space-y-4 bg-mario-bg/50">
          {messages.length === 0 ? (
            <div className="text-center py-12 space-y-2">
              <div className="mx-auto w-12 h-12 rounded-2xl bg-mario-gold border-2 border-mario-navy flex items-center justify-center shadow-retro-sm">
                <Bot className="w-6 h-6 text-mario-navy" />
              </div>
              <p className="text-sm font-extrabold text-mario-navy">
                Start a Planning Conversation
              </p>
              <p className="text-xs text-mario-muted max-w-md mx-auto">
                Click any prompt chip above or type a question below. EventWise AI uses local RAG + Python budget/timeline services.
              </p>
            </div>
          ) : (
            messages.map((msg) => {
              const isUser = msg.role === "user";
              return (
                <div
                  key={msg.id}
                  className={`flex flex-col ${
                    isUser ? "items-end" : "items-start"
                  }`}
                >
                  <div
                    className={`max-w-3xl rounded-2xl border-2 border-mario-navy p-4 shadow-retro-sm ${
                      isUser
                        ? "bg-mario-navy text-white"
                        : "bg-white text-mario-navy"
                    }`}
                  >
                    <div className="flex items-center gap-2 text-[11px] font-bold mb-1.5 opacity-80">
                      {isUser ? (
                        <>
                          <User className="w-3.5 h-3.5" />
                          <span>You</span>
                        </>
                      ) : (
                        <>
                          <Bot className="w-3.5 h-3.5 text-mario-green" />
                          <span>EventWise AI (Local RAG + Python)</span>
                        </>
                      )}
                    </div>
                    <div className="whitespace-pre-wrap text-xs sm:text-sm leading-relaxed">
                      {msg.content}
                    </div>

                    {/* Interactive Proposal Approval Card */}
                    {!isUser && msg.proposed_changes && selectedEventId && (
                      <div className="mt-4 rounded-xl border-2 border-mario-navy bg-amber-50 p-3.5 text-mario-navy space-y-2.5">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <ShieldCheck className="w-4 h-4 text-mario-green shrink-0" />
                            <span className="font-extrabold text-xs">
                              User Approval Required Before Saving
                            </span>
                          </div>
                          <span className="px-2 py-0.5 rounded bg-mario-gold text-[10px] font-pixel">
                            PROPOSAL
                          </span>
                        </div>
                        <p className="text-xs font-semibold">
                          {msg.proposed_changes.summary}
                        </p>
                        <p className="text-[11px] text-mario-muted">
                          {msg.proposed_changes.warning}
                        </p>
                        <button
                          type="button"
                          disabled={applyingProposal}
                          onClick={() =>
                            handleApproveProposal(msg.proposed_changes!)
                          }
                          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-mario-green text-white text-xs font-extrabold border-2 border-mario-navy shadow-retro-sm hover:bg-[#1f8244] disabled:opacity-50"
                        >
                          {applyingProposal ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <CheckCircle2 className="w-3.5 h-3.5" />
                          )}
                          <span>Approve & Apply Proposal to Event</span>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
          {sending && (
            <div className="flex items-center gap-2 text-xs font-bold text-mario-navy bg-white border-2 border-mario-navy rounded-xl px-4 py-3 w-fit shadow-retro-sm">
              <Loader2 className="w-4 h-4 animate-spin text-mario-red" />
              <span>Retrieving local RAG passages & consulting Ollama...</span>
            </div>
          )}
        </div>

        {/* Message Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void handleSendMessage();
          }}
          className="border-t-2 border-mario-navy bg-white p-3.5 flex items-center gap-2.5"
        >
          <label htmlFor="chat-message-input" className="sr-only">
            Ask a planning question
          </label>
          <input
            id="chat-message-input"
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Ask e.g. 'Reduce my event budget by ₹5,000' or 'What tasks remain before my event?'"
            className="flex-1 rounded-xl border-2 border-mario-navy px-3.5 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-mario-red"
          />
          <button
            type="submit"
            disabled={sending || !inputText.trim()}
            className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-mario-red text-white font-extrabold text-sm border-2 border-mario-navy shadow-retro-sm hover:bg-[#d33b32] disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
            <span>Send</span>
          </button>
        </form>
      </div>

      {/* Citations for latest reply */}
      {latestCitations.length > 0 && (
        <SourceCitationsList
          citations={latestCitations}
          missingEvidenceNote={missingNote}
          title="Retrieved Knowledge Passages Used in Chat"
        />
      )}

      {/* Session Switcher */}
      {!embedded && sessions.length > 1 && (
        <div className="rounded-xl border-2 border-mario-navy bg-white p-4">
          <p className="text-xs font-extrabold text-mario-navy mb-2">
            Previous Chat Sessions ({sessions.length})
          </p>
          <div className="flex flex-wrap gap-2">
            {sessions.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={async () => {
                  setActiveSessionId(s.id);
                  const hist = await apiClient.getChatSessionMessages(s.id);
                  setMessages(hist);
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold border ${
                  activeSessionId === s.id
                    ? "bg-mario-navy text-white border-mario-navy"
                    : "bg-mario-bg text-mario-navy border-slate-300"
                }`}
              >
                {s.title} ({s.message_count} msgs)
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
