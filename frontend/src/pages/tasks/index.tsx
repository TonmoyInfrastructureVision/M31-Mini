import React, { useEffect, useState } from 'react';
import Layout from '../../components/Layout';
import Link from 'next/link';
import { agentApi, taskApi } from '../../api';
import { Agent } from '../../types/agent';
import { TaskSummary } from '../../types/task';
import StatusBadge from '../../components/StatusBadge';

interface AgentWithTasks {
  agent: Agent;
  tasks: TaskSummary[];
}

export default function TasksList(): React.ReactElement {
  const [agentsWithTasks, setAgentsWithTasks] = useState<AgentWithTasks[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async (): Promise<void> => {
      try {
        setLoading(true);
        
        const agentsData = await agentApi.getAgents();
        
        const agentsWithTasksPromises = agentsData.agents.map(async (agent: Agent) => {
          try {
            const tasksData = await taskApi.getAgentTasks(agent.id);
            return {
              agent,
              tasks: tasksData.tasks,
            };
          } catch (err) {
            console.error(`Error fetching tasks for agent ${agent.id}:`, err);
            return {
              agent,
              tasks: [],
            };
          }
        });
        
        const results = await Promise.all(agentsWithTasksPromises);
        setAgentsWithTasks(results);
        setError(null);
      } catch (err) {
        console.error('Error fetching agents:', err);
        setError('Failed to load agents and tasks');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <Layout title="Tasks">
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg leading-6 font-medium text-gray-900">Tasks</h2>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">
            View and manage tasks across all agents
          </p>
        </div>
        
        <div className="card-body">
          {loading ? (
            <div className="text-center py-4">
              <p className="text-gray-500">Loading tasks...</p>
            </div>
          ) : error ? (
            <div className="text-center py-4">
              <p className="text-red-500">{error}</p>
            </div>
          ) : agentsWithTasks.length === 0 ? (
            <div className="text-center py-4">
              <p className="text-gray-500">No agents found</p>
            </div>
          ) : (
            <div className="space-y-10">
              {agentsWithTasks.map(({ agent, tasks }) => (
                <div key={agent.id} className="space-y-4">
                  <div className="border-b border-gray-200 pb-2">
                    <h3 className="text-lg font-medium text-gray-900">
                      <Link href={`/agents/${agent.id}`} className="hover:text-primary-600">
                        {agent.name}
                      </Link>
                    </h3>
                  </div>
                  
                  {tasks.length === 0 ? (
                    <div className="text-center py-4">
                      <p className="text-gray-500">No tasks found for this agent</p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Goal
                            </th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Status
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
                          {tasks.map((task) => (
                            <tr key={task.id}>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm font-medium text-gray-900">
                                  {task.goal.length > 50 ? `${task.goal.substring(0, 50)}...` : task.goal}
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <StatusBadge status={task.status} />
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {new Date(task.created_at).toLocaleString()}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                <Link href={`/tasks/${task.id}`} className="text-primary-600 hover:text-primary-900">
                                  View
                                </Link>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
} 