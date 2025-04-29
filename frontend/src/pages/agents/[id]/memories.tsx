import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../../components/Layout';
import Link from 'next/link';
import { agentApi, memoryApi } from '../../../api';
import { Agent } from '../../../types/agent';
import { Memory } from '../../../types/memory';
import Button from '../../../components/Button';

export default function AgentMemories(): React.ReactElement {
  const router = useRouter();
  const { id } = router.query;
  
  const [agent, setAgent] = useState<Agent | null>(null);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searching, setSearching] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState<string>('');
  const [memoryType, setMemoryType] = useState<'short_term' | 'long_term'>('long_term');

  useEffect(() => {
    const fetchAgent = async (): Promise<void> => {
      if (!id || typeof id !== 'string') return;
      
      try {
        setLoading(true);
        const data = await agentApi.getAgent(id);
        setAgent(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching agent:', err);
        setError('Failed to load agent data');
      } finally {
        setLoading(false);
      }
    };

    fetchAgent();
  }, [id]);

  const handleSearch = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    
    if (!id || typeof id !== 'string' || !query.trim()) {
      return;
    }
    
    try {
      setSearching(true);
      setError(null);
      
      const response = await memoryApi.searchMemories({
        agent_id: id,
        query: query.trim(),
        memory_type: memoryType,
        limit: 10
      });
      
      setMemories(response.memories);
    } catch (err) {
      console.error('Error searching memories:', err);
      setError('Failed to search agent memories');
    } finally {
      setSearching(false);
    }
  };

  if (loading) {
    return (
      <Layout title="Agent Memories">
        <div className="text-center py-4">
          <p className="text-gray-500">Loading agent data...</p>
        </div>
      </Layout>
    );
  }

  if (error || !agent) {
    return (
      <Layout title="Agent Memories">
        <div className="text-center py-4">
          <p className="text-red-500">{error || 'Agent not found'}</p>
          <Button
            variant="primary"
            onClick={() => router.back()}
            className="mt-4"
          >
            Back
          </Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={`${agent.name}: Memories`}>
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{agent.name}: Memories</h2>
            <p className="mt-1 text-sm text-gray-500">
              Search through agent memories
            </p>
          </div>
          <Button
            variant="white"
            onClick={() => router.back()}
          >
            Back
          </Button>
        </div>
        
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Search Memories</h3>
          </div>
          
          <div className="card-body">
            <form onSubmit={handleSearch}>
              <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                <div className="sm:col-span-4">
                  <label htmlFor="query" className="block text-sm font-medium text-gray-700">
                    Search Query
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      name="query"
                      id="query"
                      className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="Enter search terms"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      required
                    />
                  </div>
                </div>
                
                <div className="sm:col-span-2">
                  <label htmlFor="memory-type" className="block text-sm font-medium text-gray-700">
                    Memory Type
                  </label>
                  <div className="mt-1">
                    <select
                      id="memory-type"
                      name="memory-type"
                      className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      value={memoryType}
                      onChange={(e) => setMemoryType(e.target.value as 'short_term' | 'long_term')}
                    >
                      <option value="long_term">Long Term</option>
                      <option value="short_term">Short Term</option>
                    </select>
                  </div>
                </div>
                
                <div className="sm:col-span-6">
                  <Button
                    type="submit"
                    variant="primary"
                    isLoading={searching}
                    disabled={!query.trim()}
                  >
                    Search Memories
                  </Button>
                </div>
              </div>
            </form>
          </div>
        </div>
        
        {memories.length > 0 && (
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg leading-6 font-medium text-gray-900">Search Results</h3>
              <p className="mt-1 text-sm text-gray-500">
                Found {memories.length} memories
              </p>
            </div>
            
            <div className="card-body">
              <div className="space-y-6">
                {memories.map((memory) => (
                  <div key={memory.id} className="border rounded-md p-4">
                    <div className="flex justify-between">
                      <span className="text-xs font-medium text-gray-500">
                        {memory.memory_type === 'long_term' ? 'Long-term Memory' : 'Short-term Memory'}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(memory.created_at).toLocaleString()}
                      </span>
                    </div>
                    
                    <div className="mt-2 text-sm text-gray-900 whitespace-pre-wrap">
                      {memory.text}
                    </div>
                    
                    {memory.metadata && Object.keys(memory.metadata).length > 0 && (
                      <details className="mt-2">
                        <summary className="text-xs font-medium text-gray-500 cursor-pointer">Metadata</summary>
                        <pre className="mt-1 text-xs text-gray-700 bg-gray-50 p-2 rounded overflow-x-auto">
                          {JSON.stringify(memory.metadata, null, 2)}
                        </pre>
                      </details>
                    )}
                    
                    {memory.relevance_score !== undefined && (
                      <div className="mt-2 text-xs text-gray-500">
                        Relevance: {(memory.relevance_score * 100).toFixed(2)}%
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        
        {query && memories.length === 0 && !searching && (
          <div className="card">
            <div className="card-body">
              <div className="text-center py-4">
                <p className="text-gray-500">No memories found matching your query</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
} 