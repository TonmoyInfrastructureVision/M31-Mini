import React, { useEffect, useState } from 'react';
import Layout from '../../components/Layout';
import Link from 'next/link';
import { agentApi } from '../../api';
import { Agent } from '../../types/agent';
import StatusBadge from '../../components/StatusBadge';
import Button from '../../components/Button';
import { logger } from '../../utils/logger';

export default function AgentsList(): React.ReactElement {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAgents = async (): Promise<void> => {
      try {
        setLoading(true);
        const data = await agentApi.getAgents();
        setAgents(data.agents);
      } catch (err) {
        logger.error('Error fetching agents:', err);
        setError('Failed to load agents');
      } finally {
        setLoading(false);
      }
    };

    fetchAgents();
  }, []);

  const handleDeleteAgent = async (id: string): Promise<void> => {
    if (window.confirm('Are you sure you want to delete this agent?')) {
      try {
        await agentApi.deleteAgent(id);
        setAgents(agents.filter(agent => agent.id !== id));
      } catch (err) {
        logger.error('Error deleting agent:', err);
        alert('Failed to delete agent');
      }
    }
  };

  return (
    <Layout title="Agents">
      <div className="card">
        <div className="card-header flex justify-between items-center">
          <div>
            <h2 className="text-lg leading-6 font-medium text-gray-900">Agents</h2>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Manage your autonomous agents
            </p>
          </div>
          <Link href="/agents/create">
            <Button variant="primary">Create Agent</Button>
          </Link>
        </div>
        
        <div className="card-body">
          {loading ? (
            <div className="text-center py-4">
              <p className="text-gray-500">Loading agents...</p>
            </div>
          ) : error ? (
            <div className="text-center py-4">
              <p className="text-red-500">{error}</p>
            </div>
          ) : agents.length === 0 ? (
            <div className="text-center py-4">
              <p className="text-gray-500">No agents found. Create your first agent to get started.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Model
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th scope="col" className="relative px-6 py-3">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {agents.map((agent) => (
                    <tr key={agent.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{agent.name}</div>
                            <div className="text-sm text-gray-500">{agent.description || 'No description'}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <StatusBadge status={agent.status} />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {agent.model?.split('/').pop() || 'Default'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(agent.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <Link href={`/agents/${agent.id}`} className="text-primary-600 hover:text-primary-900 mr-4">
                          View
                        </Link>
                        <button
                          onClick={() => handleDeleteAgent(agent.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
} 