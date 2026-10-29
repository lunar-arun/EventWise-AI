"use client";

import React, { useState } from "react";
import { BookOpen, ChevronDown, ChevronUp, FileText, MapPin, ShieldAlert } from "lucide-react";
import type { SourceCitation } from "@/types/knowledge";

export function SourceCitationsList({
  citations,
  missingEvidenceNote,
  title = "Verified RAG Knowledge Sources",
}: {
  citations: SourceCitation[];
  missingEvidenceNote?: string | null;
  title?: string;
}) {
  const [expandedChunkId, setExpandedChunkId] = useState<string | null>(
    citations[0]?.chunk_id || null
  );

  return (
    <div className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2.5">
          <span className="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-mario-sky border-2 border-mario-navy">
            <BookOpen className="w-4 h-4 text-mario-navy" />
          </span>
          <div>
            <h3 className="text-base font-extrabold text-mario-navy">{title}</h3>
            <p className="text-xs text-mario-muted">
              Every citation maps to a real retrieved chunk in local ChromaDB. Vector similarity is a semantic proximity metric, not a probability of truth.
            </p>
          </div>
        </div>
        <span className="px-2.5 py-1 rounded-full bg-mario-bg border border-mario-navy text-xs font-pixel text-mario-navy">
          {citations.length} SOURCE{citations.length === 1 ? "" : "S"}
        </span>
      </div>

      {missingEvidenceNote && (
        <div className="mb-3 rounded-xl border-2 border-amber-600 bg-amber-50 p-3 text-xs text-mario-navy flex items-start gap-2.5">
          <ShieldAlert className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Knowledge Scope Notice: </span>
            <span>{missingEvidenceNote}</span>
          </div>
        </div>
      )}

      {citations.length === 0 ? (
        <div className="rounded-xl border border-dashed border-mario-navy/40 bg-mario-bg p-4 text-xs text-mario-muted">
          No matching passages were retrieved from the local knowledge base for this item. Recommendations above are general planning suggestions with illustrative INR estimates.
        </div>
      ) : (
        <div className="space-y-2.5">
          {citations.map((cite) => {
            const isExpanded = expandedChunkId === cite.chunk_id;
            return (
              <div
                key={cite.chunk_id}
                className="rounded-xl border-2 border-mario-navy/80 bg-mario-bg overflow-hidden"
              >
                <button
                  type="button"
                  onClick={() =>
                    setExpandedChunkId(isExpanded ? null : cite.chunk_id)
                  }
                  aria-expanded={isExpanded}
                  className="w-full px-4 py-3 text-left flex flex-wrap items-center justify-between gap-2 hover:bg-[#E4F3FF] transition-colors"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <FileText className="w-4 h-4 text-mario-green shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-bold text-mario-navy truncate">
                        {cite.title}
                      </p>
                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-mario-muted mt-0.5">
                        <span className="font-mono bg-white px-1.5 py-0.5 rounded border border-slate-300">
                          {cite.filename}
                        </span>
                        <span>•</span>
                        <span className="uppercase font-semibold text-mario-green">
                          {cite.category}
                        </span>
                        <span>•</span>
                        <span className="inline-flex items-center gap-0.5">
                          <MapPin className="w-3 h-3" />
                          {cite.location}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span
                      title="Cosine similarity score and raw vector distance in ChromaDB"
                      className="px-2 py-0.5 rounded-md bg-white border border-mario-navy text-[11px] font-semibold text-mario-navy"
                    >
                      Sim {(cite.similarity_score * 100).toFixed(0)}% (d={cite.distance.toFixed(2)})
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-mario-navy" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-mario-navy" />
                    )}
                  </div>
                </button>

                {isExpanded && (
                  <div className="border-t border-mario-navy/30 bg-white px-4 py-3 text-xs space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-mario-muted">
                      <span>
                        Chunk ID: <code className="font-mono text-mario-navy">{cite.chunk_id}</code>
                      </span>
                      <span className="px-2 py-0.5 rounded bg-mario-gold/40 text-mario-navy font-semibold">
                        {cite.source_label}
                      </span>
                    </div>
                    <pre className="whitespace-pre-wrap font-sans text-xs text-mario-navy bg-mario-bg p-3 rounded-lg border border-slate-200 leading-relaxed">
                      {cite.excerpt}
                    </pre>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
