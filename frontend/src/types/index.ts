export interface Citation {
  document_id: string;
  document_title: string;
  chunk_index: number;
  score: number;
  snippet: string;
  page?: number;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  citations?: Citation[];
  isStreaming?: boolean;
  cacheHit?: boolean;
  latencyMs?: number;
}

export interface DocumentItem {
  id: string;
  tenant_id: string;
  title: string;
  file_name: string;
  file_hash: string;
  status: "PENDING" | "PROCESSING" | "INDEXED" | "FAILED";
  chunk_count: number;
  created_at: string;
}

export interface SystemMetrics {
  total_queries: number;
  cache_hits: number;
  cache_hit_rate_pct: number;
  avg_latency_ms: number;
  total_documents: number;
  total_chunks: number;
}
