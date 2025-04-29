export interface Memory {
  id: string;
  agent_id: string;
  text: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at?: string;
  memory_type: 'short_term' | 'long_term';
  embedding_id?: string;
  relevance_score?: number;
}

export interface MemorySearchRequest {
  agent_id: string;
  query: string;
  limit?: number;
  memory_type?: 'short_term' | 'long_term' | 'auto';
}

export interface MemorySearchResponse {
  agent_id: string;
  memories: Memory[];
  query: string;
}