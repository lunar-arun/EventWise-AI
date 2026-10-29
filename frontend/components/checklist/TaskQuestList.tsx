"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Circle,
  Clock,
  Trash2,
} from "lucide-react";
import { formatDateDisplay, formatPriorityLabel, formatTaskStatusLabel } from "@/lib/formatting";
import type { TaskItem, TaskStatus } from "@/types/task";
import { StarMilestoneIcon } from "@/components/ui/MarioMotifs";

export function TaskQuestList({
  tasks,
  onStatusChange,
  onDeleteTask,
  compact = false,
}: {
  tasks: TaskItem[];
  onStatusChange: (taskId: number, status: TaskStatus) => Promise<void>;
  onDeleteTask?: (taskId: number) => Promise<void>;
  compact?: boolean;
}) {
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const handleStatusClick = async (taskId: number, nextStatus: TaskStatus) => {
    setUpdatingId(taskId);
    try {
      await onStatusChange(taskId, nextStatus);
    } finally {
      setUpdatingId(null);
    }
  };

  if (tasks.length === 0) {
    return (
      <div className="rounded-xl border-2 border-dashed border-mario-navy/40 bg-white p-6 text-center text-sm text-mario-muted">
        No milestone tasks scheduled yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {tasks.map((task) => {
        const isCompleted = task.status === "completed";
        const isInProgress = task.status === "in_progress";
        const isBusy = updatingId === task.id;

        return (
          <div
            key={task.id}
            className={`rounded-xl border-2 border-mario-navy p-4 transition-all shadow-retro-sm ${
              isCompleted
                ? "bg-emerald-50/70"
                : isInProgress
                ? "bg-amber-50/80"
                : "bg-white"
            }`}
          >
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 shrink-0">
                  <StarMilestoneIcon
                    className="w-6 h-6"
                    active={isCompleted || isInProgress}
                  />
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="px-2 py-0.5 rounded-md bg-mario-navy text-mario-gold font-pixel text-[10px]">
                      {task.milestone_label}
                    </span>
                    <span className="px-2 py-0.5 rounded-md bg-mario-bg border border-mario-navy/30 text-[11px] font-semibold text-mario-navy">
                      {task.category}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-md text-[11px] font-bold border ${
                        task.priority === "high"
                          ? "bg-red-100 text-mario-red border-mario-red"
                          : task.priority === "medium"
                          ? "bg-amber-100 text-mario-navy border-amber-500"
                          : "bg-slate-100 text-mario-muted border-slate-300"
                      }`}
                    >
                      {formatPriorityLabel(task.priority)}
                    </span>
                    {task.is_clamped && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-100 border border-amber-600 text-[11px] font-semibold text-amber-900">
                        <AlertTriangle className="w-3 h-3" />
                        Compressed Schedule
                      </span>
                    )}
                  </div>

                  <h4
                    className={`mt-1.5 text-base font-extrabold ${
                      isCompleted ? "line-through text-mario-muted" : "text-mario-navy"
                    }`}
                  >
                    {task.title}
                  </h4>

                  {!compact && task.description && (
                    <p className="mt-1 text-xs text-mario-muted leading-relaxed">
                      {task.description}
                    </p>
                  )}

                  <div className="mt-2 flex flex-wrap items-center gap-3 text-xs font-semibold text-mario-navy">
                    <span className="inline-flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-mario-red" />
                      Due: {formatDateDisplay(task.due_date)} ({task.due_date})
                    </span>
                    <span>•</span>
                    <span>Status: {formatTaskStatusLabel(task.status)}</span>
                  </div>
                </div>
              </div>

              {/* Accessible status control buttons with both icons and explicit labels */}
              <div className="flex flex-wrap items-center gap-1.5 shrink-0">
                <button
                  type="button"
                  disabled={isBusy}
                  onClick={() => handleStatusClick(task.id, "pending")}
                  aria-pressed={task.status === "pending"}
                  className={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-bold border-2 transition-colors ${
                    task.status === "pending"
                      ? "bg-mario-navy text-white border-mario-navy"
                      : "bg-white text-mario-navy border-slate-300 hover:border-mario-navy"
                  }`}
                >
                  <Circle className="w-3.5 h-3.5" />
                  <span>Pending</span>
                </button>

                <button
                  type="button"
                  disabled={isBusy}
                  onClick={() => handleStatusClick(task.id, "in_progress")}
                  aria-pressed={task.status === "in_progress"}
                  className={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-bold border-2 transition-colors ${
                    task.status === "in_progress"
                      ? "bg-mario-gold text-mario-navy border-mario-navy"
                      : "bg-white text-mario-navy border-slate-300 hover:border-mario-navy"
                  }`}
                >
                  <Clock className="w-3.5 h-3.5" />
                  <span>In Progress</span>
                </button>

                <button
                  type="button"
                  disabled={isBusy}
                  onClick={() => handleStatusClick(task.id, "completed")}
                  aria-pressed={task.status === "completed"}
                  className={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-bold border-2 transition-colors ${
                    task.status === "completed"
                      ? "bg-mario-green text-white border-mario-navy"
                      : "bg-white text-mario-navy border-slate-300 hover:border-mario-navy"
                  }`}
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Completed</span>
                </button>

                {onDeleteTask && (
                  <button
                    type="button"
                    disabled={isBusy}
                    onClick={() => onDeleteTask(task.id)}
                    aria-label={`Delete task ${task.title}`}
                    className="p-1.5 rounded-lg border-2 border-transparent text-mario-muted hover:text-mario-red hover:border-mario-red transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
