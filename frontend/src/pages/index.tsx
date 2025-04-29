import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import Link from 'next/link';
import { agentApi } from '../api';
import { Agent } from '../types/agent';

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        setLoading(true);
        const data = await agentApi.getAgents();
        setAgents(data.agents);
        setError(null);
      } catch (err) {
        setError('Failed to load agents');
        console.error('Error fetching agents:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAgents();
  }, []);

  return (
    <Layout title="Dashboard">
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
          <div>
            <h2 className="text-lg leading-6 font-medium text-gray-900">
              Agent Dashboard
            </h2>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Create and manage your autonomous agents
            </p>
          </div>
          <Link
            href="/agents/create"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Create Agent
          </Link>
        </div>
        
        {loading ? (
          <div className="px-4 py-5 sm:p-6 text-center">
            <p className="text-gray-500">Loading agents...</p>
          </div>
        ) : error ? (
          <div className="px-4 py-5 sm:p-6 text-center">
            <p className="text-red-500">{error}</p>
          </div>
        ) : agents.length === 0 ? (
          <div className="px-4 py-5 sm:p-6 text-center">
            <p className="text-gray-500">No agents found. Create your first agent to get started.</p>
          </div>
        ) : (
          <div className="px-4 py-5 sm:p-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
                >
                  <div className="flex-1 min-w-0">
                    <Link
                      href={`/agents/${agent.id}`}
                      className="focus:outline-none"
                    >
                      <span className="absolute inset-0" aria-hidden="true" />
                      <p className="text-sm font-medium text-gray-900">{agent.name}</p>
                      <p className="text-sm text-gray-500 truncate">
                        {agent.description || 'No description'}
                      </p>
                      <div className="mt-2 flex items-center text-sm text-gray-500">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          agent.status === 'idle' 
                            ? 'bg-green-100 text-green-800' 
                            : agent.status === 'running' 
                              ? 'bg-blue-100 text-blue-800' 
                              : 'bg-red-100 text-red-800'
                        }`}>
                          {agent.status}
                        </span>
                      </div>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
} 