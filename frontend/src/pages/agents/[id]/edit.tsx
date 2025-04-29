import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../../components/Layout';
import AgentForm from '../../../components/AgentForm';
import { agentApi } from '../../../api';
import { Agent, AgentCreate } from '../../../types/agent';

export default function EditAgent(): React.ReactElement {
  const router = useRouter();
  const { id } = router.query;
  
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

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

  const handleSubmit = async (data: AgentCreate): Promise<void> => {
    if (!id || typeof id !== 'string') return;
    
    try {
      setIsSubmitting(true);
      setError(null);
      await agentApi.updateAgent(id, data);
      router.push(`/agents/${id}`);
    } catch (err) {
      console.error('Error updating agent:', err);
      setError('Failed to update agent. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Layout title="Edit Agent">
        <div className="text-center py-4">
          <p className="text-gray-500">Loading agent data...</p>
        </div>
      </Layout>
    );
  }

  if (error || !agent) {
    return (
      <Layout title="Edit Agent">
        <div className="text-center py-4">
          <p className="text-red-500">{error || 'Agent not found'}</p>
          <button
            onClick={() => router.back()}
            className="mt-4 btn-primary"
          >
            Back
          </button>
        </div>
      </Layout>
    );
  }

  const initialData: AgentCreate = {
    name: agent.name,
    description: agent.description,
    model: agent.model,
    workspace_dir: agent.workspace_dir,
  };

  return (
    <Layout title={`Edit Agent: ${agent.name}`}>
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg leading-6 font-medium text-gray-900">Edit Agent</h2>
          <p className="mt-1 text-sm text-gray-500">
            Update agent settings
          </p>
        </div>
        
        <div className="card-body">
          {error && (
            <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}
          
          <AgentForm
            initialData={initialData}
            onSubmit={handleSubmit}
            isLoading={isSubmitting}
          />
        </div>
      </div>
    </Layout>
  );
} 