export type AllowedEventTypeFilter = "wedding" | "birthday" | "community" | "general";

export interface SourceCitation {
  document_id: string;
  chunk_id: string;
  title: string;
  filename: string;
  category: string;
  event_type: string;
  location: string;
  source_label: string;
  is_illustrative: boolean;
  excerpt: string;
  distance: number;
  similarity_score: number;
}

export interface KnowledgeDocument {
  id: string;
  title: string;
  filename: string;
  file_type: string;
  event_type: string;
  category: string;
  location: string;
  source_label: string;
  is_illustrative: boolean;
  status: "indexed" | "processing" | "failed" | string;
  chunk_count: number;
  error_message: string | null;
  raw_content: string | null;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeEntryCreateInput {
  title: string;
  content: string;
  event_type: AllowedEventTypeFilter;
  category: string;
  location: string;
  source_label: string;
  is_illustrative: boolean;
}

export interface KnowledgeEntryUpdateInput {
  title?: string;
  content?: string;
  event_type?: AllowedEventTypeFilter;
  category?: string;
  location?: string;
  source_label?: string;
  is_illustrative?: boolean;
}

export interface KnowledgeSearchRequest {
  query: string;
  event_type?: string;
  category?: string;
  location?: string;
  top_k?: number;
}

export interface KnowledgeSearchResponse {
  query: string;
  results: SourceCitation[];
  fallback_applied: boolean;
  fallback_reason: string | null;
  total_found: number;
}
