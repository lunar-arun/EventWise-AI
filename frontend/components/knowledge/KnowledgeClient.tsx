"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  BookOpen,
  CheckCircle2,
  Edit3,
  FileText,
  FileUp,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { formatDateDisplay } from "@/lib/formatting";
import type {
  AllowedEventTypeFilter,
  KnowledgeDocument,
  KnowledgeSearchResponse,
} from "@/types/knowledge";
import {
  BrickDivider,
  CloudSkyBanner,
  ErrorBanner,
  QuestionBlockBadge,
} from "@/components/ui/MarioMotifs";
import { SourceCitationsList } from "@/components/knowledge/SourceCitationsList";

export function KnowledgeClient() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Upload File State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadEventType, setUploadEventType] =
    useState<AllowedEventTypeFilter>("general");
  const [uploadCategory, setUploadCategory] = useState("planning");
  const [uploadLocation, setUploadLocation] = useState("General India");
  const [uploadSourceLabel, setUploadSourceLabel] = useState(
    "Uploaded Knowledge Guide (Illustrative)"
  );
  const [uploading, setUploading] = useState(false);

  // Add / Edit Structured Entry State
  const [editingDocId, setEditingDocId] = useState<string | null>(null);
  const [entryTitle, setEntryTitle] = useState("");
  const [entryContent, setEntryContent] = useState("");
  const [entryEventType, setEntryEventType] =
    useState<AllowedEventTypeFilter>("general");
  const [entryCategory, setEntryCategory] = useState("planning");
  const [entryLocation, setEntryLocation] = useState("Chennai");
  const [entrySourceLabel, setEntrySourceLabel] = useState(
    "Structured EventWise Entry (Illustrative)"
  );
  const [savingEntry, setSavingEntry] = useState(false);

  // Semantic Search State
  const [searchQuery, setSearchQuery] = useState(
    "birthday budget 25000 INR allocation Chennai"
  );
  const [searchEventType, setSearchEventType] = useState("all");
  const [searchCategory, setSearchCategory] = useState("all");
  const [searchLocation, setSearchLocation] = useState("");
  const [searchTopK, setSearchTopK] = useState(5);
  const [searching, setSearching] = useState(false);
  const [searchResponse, setSearchResponse] =
    useState<KnowledgeSearchResponse | null>(null);

  const [busyDocId, setBusyDocId] = useState<string | null>(null);

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await apiClient.listKnowledgeDocuments();
      setDocuments(list);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load knowledge documents."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError("Please choose a .pdf, .txt, .csv, or .json file to upload.");
      return;
    }

    setUploading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      if (uploadTitle.trim()) formData.append("title", uploadTitle.trim());
      formData.append("event_type", uploadEventType);
      formData.append("category", uploadCategory.trim() || "general");
      formData.append("location", uploadLocation.trim() || "General India");
      formData.append(
        "source_label",
        uploadSourceLabel.trim() || "Uploaded Guide (Illustrative)"
      );
      formData.append("is_illustrative", "true");

      const doc = await apiClient.uploadKnowledgeDocument(formData);
      setSelectedFile(null);
      setUploadTitle("");
      setSuccessMsg(
        `Indexed '${doc.title}' (${doc.chunk_count} overlapping chunks stored in local ChromaDB).`
      );
      await loadDocuments();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to upload and index document."
      );
    } finally {
      setUploading(false);
    }
  };

  const handleSaveEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (entryTitle.trim().length < 3 || entryContent.trim().length < 20) {
      setError(
        "Title must be at least 3 characters and content at least 20 characters."
      );
      return;
    }

    setSavingEntry(true);
    setError(null);
    setSuccessMsg(null);
    try {
      if (editingDocId) {
        const updated = await apiClient.updateKnowledgeEntry(editingDocId, {
          title: entryTitle.trim(),
          content: entryContent.trim(),
          event_type: entryEventType,
          category: entryCategory.trim(),
          location: entryLocation.trim(),
          source_label: entrySourceLabel.trim(),
          is_illustrative: true,
        });
        setSuccessMsg(
          `Updated and re-indexed '${updated.title}' (${updated.chunk_count} chunks).`
        );
      } else {
        const created = await apiClient.createKnowledgeEntry({
          title: entryTitle.trim(),
          content: entryContent.trim(),
          event_type: entryEventType,
          category: entryCategory.trim(),
          location: entryLocation.trim(),
          source_label: entrySourceLabel.trim(),
          is_illustrative: true,
        });
        setSuccessMsg(
          `Created and indexed '${created.title}' (${created.chunk_count} chunks).`
        );
      }
      setEditingDocId(null);
      setEntryTitle("");
      setEntryContent("");
      await loadDocuments();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to save knowledge entry."
      );
    } finally {
      setSavingEntry(false);
    }
  };

  const handleStartEdit = (doc: KnowledgeDocument) => {
    setEditingDocId(doc.id);
    setEntryTitle(doc.title);
    setEntryContent(doc.raw_content || "");
    setEntryEventType(
      (doc.event_type as AllowedEventTypeFilter) || "general"
    );
    setEntryCategory(doc.category);
    setEntryLocation(doc.location);
    setEntrySourceLabel(doc.source_label);
  };

  const handleReindex = async (docId: string) => {
    setBusyDocId(docId);
    setError(null);
    setSuccessMsg(null);
    try {
      const doc = await apiClient.reindexKnowledgeDocument(docId);
      setSuccessMsg(
        `Re-indexed '${doc.title}' (${doc.chunk_count} deterministic chunks).`
      );
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to re-index.");
    } finally {
      setBusyDocId(null);
    }
  };

  const handleDelete = async (docId: string) => {
    setBusyDocId(docId);
    setError(null);
    setSuccessMsg(null);
    try {
      await apiClient.deleteKnowledgeDocument(docId);
      setSuccessMsg("Deleted document and removed associated vectors from ChromaDB.");
      await loadDocuments();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete document."
      );
    } finally {
      setBusyDocId(null);
    }
  };

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearching(true);
    setError(null);
    try {
      const res = await apiClient.searchKnowledgeBase({
        query: searchQuery.trim(),
        event_type: searchEventType === "all" ? undefined : searchEventType,
        category: searchCategory === "all" ? undefined : searchCategory,
        location: searchLocation.trim() || undefined,
        top_k: searchTopK,
      });
      setSearchResponse(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Knowledge search failed.");
    } finally {
      setSearching(false);
    }
  };

  const totalChunks = documents.reduce((acc, d) => acc + d.chunk_count, 0);

  return (
    <div className="space-y-6">
      <CloudSkyBanner
        badgeText="WORLD 5 • LOCAL RAG KNOWLEDGE BASE MANAGER"
        title="Manage Local Vector Knowledge Base (ChromaDB + Sentence Transformers)"
        subtitle="Upload PDF, TXT, CSV, or JSON files, create or edit structured entries, inspect deterministic chunk counts, and test semantic vector retrieval with metadata filters."
      />

      {error && <ErrorBanner message={error} />}

      {successMsg && (
        <div
          role="status"
          className="rounded-xl border-2 border-mario-navy bg-emerald-50 p-4 text-xs font-bold text-mario-navy flex items-center gap-2 shadow-retro-sm"
        >
          <CheckCircle2 className="w-5 h-5 text-mario-green shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Upload File + Structured Entry Forms */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Document Card */}
        <form
          onSubmit={handleFileUpload}
          className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro space-y-4"
        >
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-lg bg-mario-sky border-2 border-mario-navy">
              <FileUp className="w-4 h-4 text-mario-navy" />
            </span>
            <div>
              <h2 className="text-base font-extrabold text-mario-navy">
                Upload Document (.pdf, .txt, .csv, .json)
              </h2>
              <p className="text-xs text-mario-muted">
                Validated, normalized, chunked, and embedded locally
              </p>
            </div>
          </div>

          <div>
            <label
              htmlFor="kb-file-input"
              className="block text-xs font-bold text-mario-navy mb-1"
            >
              Choose File (Max 10 MB) *
            </label>
            <input
              id="kb-file-input"
              type="file"
              accept=".pdf,.txt,.csv,.json"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full rounded-xl border-2 border-mario-navy bg-mario-bg px-3 py-2 text-xs font-semibold"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-mario-navy mb-1">
                Document Title (Optional)
              </label>
              <input
                type="text"
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
                placeholder="Defaults to filename"
                className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-mario-navy mb-1">
                Event Type Scope
              </label>
              <select
                value={uploadEventType}
                onChange={(e) =>
                  setUploadEventType(e.target.value as AllowedEventTypeFilter)
                }
                className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-bold bg-white"
              >
                <option value="general">General (All Events)</option>
                <option value="birthday">Birthday</option>
                <option value="wedding">Wedding</option>
                <option value="community">Community</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-mario-navy mb-1">
                Category
              </label>
              <input
                type="text"
                value={uploadCategory}
                onChange={(e) => setUploadCategory(e.target.value)}
                placeholder="e.g., budget, catering, decoration"
                className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-mario-navy mb-1">
                Location Scope
              </label>
              <input
                type="text"
                value={uploadLocation}
                onChange={(e) => setUploadLocation(e.target.value)}
                placeholder="e.g., Chennai, General India"
                className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-mario-navy mb-1">
              Source Attribution Label
            </label>
            <input
              type="text"
              value={uploadSourceLabel}
              onChange={(e) => setUploadSourceLabel(e.target.value)}
              className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs"
            />
          </div>

          <button
            type="submit"
            disabled={uploading || !selectedFile}
            className="w-full inline-flex items-center justify-center gap-2 py-2.5 rounded-xl bg-mario-red text-white font-extrabold text-xs border-2 border-mario-navy shadow-retro-sm hover:bg-[#d33b32] disabled:opacity-50"
          >
            {uploading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <FileUp className="w-4 h-4" />
            )}
            <span>Upload, Chunk & Index Locally</span>
          </button>
        </form>

        {/* Add / Edit Structured Knowledge Entry */}
        <form
          onSubmit={handleSaveEntry}
          className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro space-y-3.5"
        >
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2.5">
              <QuestionBlockBadge label={editingDocId ? "✎" : "+"} />
              <div>
                <h2 className="text-base font-extrabold text-mario-navy">
                  {editingDocId
                    ? "Edit Structured Knowledge Entry"
                    : "Add Structured Knowledge Entry"}
                </h2>
                <p className="text-xs text-mario-muted">
                  Author custom checklists, regional tips, or illustrative templates directly
                </p>
              </div>
            </div>
            {editingDocId && (
              <button
                type="button"
                onClick={() => {
                  setEditingDocId(null);
                  setEntryTitle("");
                  setEntryContent("");
                }}
                className="px-2.5 py-1 rounded-lg bg-mario-bg border border-mario-navy text-xs font-bold"
              >
                Cancel Edit
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-mario-navy mb-1">
                Entry Title *
              </label>
              <input
                type="text"
                required
                minLength={3}
                value={entryTitle}
                onChange={(e) => setEntryTitle(e.target.value)}
                placeholder="e.g., Chennai Monsoon Outdoor Venue Checklist"
                className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-medium"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-mario-navy mb-1">
                Event Type
              </label>
              <select
                value={entryEventType}
                onChange={(e) =>
                  setEntryEventType(e.target.value as AllowedEventTypeFilter)
                }
                className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-bold bg-white"
              >
                <option value="general">General</option>
                <option value="birthday">Birthday</option>
                <option value="wedding">Wedding</option>
                <option value="community">Community</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-mario-navy mb-1">
                Category *
              </label>
              <input
                type="text"
                required
                value={entryCategory}
                onChange={(e) => setEntryCategory(e.target.value)}
                className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-mario-navy mb-1">
                Location *
              </label>
              <input
                type="text"
                required
                value={entryLocation}
                onChange={(e) => setEntryLocation(e.target.value)}
                className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-mario-navy mb-1">
              Knowledge Content (Markdown / Structured Text) *
            </label>
            <textarea
              rows={4}
              required
              minLength={20}
              value={entryContent}
              onChange={(e) => setEntryContent(e.target.value)}
              placeholder="Write detailed event planning guidance, checklists, or illustrative INR cost notes..."
              className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-medium"
            />
          </div>

          <button
            type="submit"
            disabled={savingEntry}
            className="w-full inline-flex items-center justify-center gap-2 py-2.5 rounded-xl bg-mario-green text-white font-extrabold text-xs border-2 border-mario-navy shadow-retro-sm hover:bg-[#1f8244] disabled:opacity-50"
          >
            {savingEntry ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Plus className="w-4 h-4" />
            )}
            <span>
              {editingDocId
                ? "Update & Re-Index Entry"
                : "Save & Index Structured Entry"}
            </span>
          </button>
        </form>
      </div>

      <BrickDivider />

      {/* Semantic Search & Retrieval Preview */}
      <section
        aria-labelledby="kb-search-heading"
        className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro space-y-4"
      >
        <div className="flex items-center gap-2.5">
          <Search className="w-5 h-5 text-mario-red" />
          <div>
            <h2
              id="kb-search-heading"
              className="text-lg font-extrabold text-mario-navy"
            >
              Semantic Search & Retrieval Preview
            </h2>
            <p className="text-xs text-mario-muted">
              Query ChromaDB directly using Sentence Transformers embeddings to inspect retrieved chunks and fallback behavior.
            </p>
          </div>
        </div>

        <form
          onSubmit={handleSearch}
          className="grid grid-cols-1 md:grid-cols-6 gap-3 items-end"
        >
          <div className="md:col-span-2">
            <label className="block text-xs font-bold text-mario-navy mb-1">
              Search Query
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="e.g., vegetarian catering buffer or 25000 birthday budget"
              className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-medium"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-mario-navy mb-1">
              Event Type Filter
            </label>
            <select
              value={searchEventType}
              onChange={(e) => setSearchEventType(e.target.value)}
              className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-bold bg-white"
            >
              <option value="all">All Event Types</option>
              <option value="birthday">Birthday</option>
              <option value="wedding">Wedding</option>
              <option value="community">Community</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-mario-navy mb-1">
              Location Filter
            </label>
            <input
              type="text"
              value={searchLocation}
              onChange={(e) => setSearchLocation(e.target.value)}
              placeholder="Optional city"
              className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-mario-navy mb-1">
              Top K Chunks
            </label>
            <input
              type="number"
              min={1}
              max={15}
              value={searchTopK}
              onChange={(e) => setSearchTopK(Number(e.target.value) || 5)}
              className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-bold"
            />
          </div>

          <button
            type="submit"
            disabled={searching}
            className="inline-flex items-center justify-center gap-1.5 py-2.5 px-4 rounded-xl bg-mario-navy text-white font-extrabold text-xs border-2 border-mario-navy hover:bg-mario-red transition-colors"
          >
            {searching ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
            <span>Search Chunks</span>
          </button>
        </form>

        {searchResponse && (
          <SourceCitationsList
            citations={searchResponse.results}
            missingEvidenceNote={searchResponse.fallback_reason}
            title={`Retrieval Preview (${searchResponse.total_found} chunks matched)`}
          />
        )}
      </section>

      {/* Indexed Documents Table / Cards */}
      <section
        aria-labelledby="kb-docs-heading"
        className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro space-y-4"
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <BookOpen className="w-5 h-5 text-mario-green" />
            <div>
              <h2
                id="kb-docs-heading"
                className="text-lg font-extrabold text-mario-navy"
              >
                Indexed Knowledge Documents ({documents.length})
              </h2>
              <p className="text-xs text-mario-muted">
                Total indexed vector chunks across all documents: {totalChunks}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={loadDocuments}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-mario-bg border-2 border-mario-navy text-xs font-bold"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh List</span>
          </button>
        </div>

        {loading && documents.length === 0 ? (
          <div className="h-32 rounded-xl bg-mario-bg animate-pulse" />
        ) : documents.length === 0 ? (
          <p className="text-xs text-mario-muted py-6 text-center">
            No documents indexed in the local knowledge base yet.
          </p>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => {
              const isBusy = busyDocId === doc.id;
              return (
                <div
                  key={doc.id}
                  className="rounded-xl border-2 border-mario-navy/80 bg-mario-bg p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-3"
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <FileText className="w-4 h-4 text-mario-navy shrink-0" />
                      <h3 className="text-sm font-extrabold text-mario-navy">
                        {doc.title}
                      </h3>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-pixel border ${
                          doc.status === "indexed"
                            ? "bg-emerald-100 text-mario-green border-mario-green"
                            : "bg-red-100 text-mario-red border-mario-red"
                        }`}
                      >
                        {doc.status.toUpperCase()}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-mario-gold text-mario-navy text-[10px] font-bold border border-mario-navy">
                        {doc.chunk_count} Chunks
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 text-xs text-mario-muted">
                      <span className="font-mono bg-white px-1.5 py-0.5 rounded border border-slate-300">
                        {doc.filename} ({doc.file_type.toUpperCase()})
                      </span>
                      <span>•</span>
                      <span>Event: {doc.event_type}</span>
                      <span>•</span>
                      <span>Category: {doc.category}</span>
                      <span>•</span>
                      <span>Location: {doc.location}</span>
                      <span>•</span>
                      <span>Updated: {formatDateDisplay(doc.updated_at)}</span>
                    </div>

                    <p className="text-[11px] font-semibold text-mario-navy/80">
                      Source: {doc.source_label}
                    </p>

                    {doc.error_message && (
                      <p className="text-xs font-bold text-mario-red">
                        Ingestion Error: {doc.error_message}
                      </p>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-2 shrink-0">
                    <button
                      type="button"
                      disabled={isBusy}
                      onClick={() => handleStartEdit(doc)}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-white border-2 border-mario-navy text-xs font-bold text-mario-navy hover:bg-mario-gold"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      <span>Edit</span>
                    </button>

                    <button
                      type="button"
                      disabled={isBusy}
                      onClick={() => handleReindex(doc.id)}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-white border-2 border-mario-navy text-xs font-bold text-mario-navy hover:bg-mario-sky"
                    >
                      <RefreshCw
                        className={`w-3.5 h-3.5 ${isBusy ? "animate-spin" : ""}`}
                      />
                      <span>Re-Index</span>
                    </button>

                    <button
                      type="button"
                      disabled={isBusy}
                      onClick={() => handleDelete(doc.id)}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-red-50 border-2 border-mario-red text-xs font-bold text-mario-red hover:bg-mario-red hover:text-white transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>Delete</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
