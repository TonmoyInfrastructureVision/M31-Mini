import React, { useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../components/Layout';
import AgentForm from '../../components/AgentForm';
import { agentApi } from '../../api';
import { AgentCreate } from '../../types/agent';

export default function CreateAgent(): React.ReactElement {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: AgentCreate): Promise<void> => {
    try {
      setIsSubmitting(true);
      setError(null);
      const response = await agentApi.createAgent(data);
      router.push(`/agents/${response.id}`);
    } catch (err) {
      console.error('Error creating agent:', err);
      setError('Failed to create agent. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Layout title="Create Agent">
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg leading-6 font-medium text-gray-900">Create Agent</h2>
          <p className="mt-1 text-sm text-gray-500">
            Create a new autonomous agent
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
            onSubmit={handleSubmit}
            isLoading={isSubmitting}
          />
        </div>
      </div>
    </Layout>
  );
} 