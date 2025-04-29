import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../components/Layout';
import Link from 'next/link';
import { agentApi, taskApi } from '../../api';
import { Agent } from '../../types/agent';
import { TaskSummary, TaskCreate } from '../../types/task';
import Button from '../../components/Button';
import StatusBadge from '../../components/StatusBadge';

export default function AgentDetail(): React.ReactElement {
  const router = useRouter();
  const { id } = router.query;
  
  const [agent, setAgent] = useState<Agent | null>(null);
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [taskGoal, setTaskGoal] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  useEffect(() => {
    const fetchAgentData = async (): Promise<void> => {
      if (!id || typeof id !== 'string') return;
      
      try {
        setLoading(true);
        const agentData = await agentApi.getAgent(id);
        setAgent(agentData);
        
        const tasksData = await taskApi.getAgentTasks(id);
        setTasks(tasksData.tasks);
        
        setError(null);
      } catch (err) {
        console.error('Error fetching agent data:', err);
        setError('Failed to load agent data');
      } finally {
        setLoading(false);
      }
    };

    fetchAgentData();
  }, [id]);

  const handleCreateTask = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    
    if (!id || typeof id !== 'string' || !taskGoal.trim()) {
      return;
    }
    
    try {
      setIsSubmitting(true);
      
      const taskData: TaskCreate = {
        agent_id: id,
        goal: taskGoal.trim(),
      };
      
      const newTask = await taskApi.createTask(taskData);
      router.push(`/tasks/${newTask.id}`);
    } catch (err) {
      console.error('Error creating task:', err);
      alert('Failed to create task. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Layout title="Agent Details">
        <div className="text-center py-4">
          <p className="text-gray-500">Loading agent data...</p>
        </div>
      </Layout>
    );
  }

  if (error || !agent) {
    return (
      <Layout title="Agent Details">
        <div className="text-center py-4">
          <p className="text-red-500">{error || 'Agent not found'}</p>
          <Link href="/agents">
            <Button variant="primary" className="mt-4">
              Back to Agents
            </Button>
          </Link>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={`Agent: ${agent.name}`}>
      <div className="space-y-6">
        <div className="card">
          <div className="card-header flex justify-between items-center">
            <div>
              <h2 className="text-lg leading-6 font-medium text-gray-900">{agent.name}</h2>
              <p className="mt-1 text-sm text-gray-500">
                {agent.description || 'No description'}
              </p>
            </div>
            <div className="flex space-x-2">
              <Link href={`/agents/${agent.id}/memories`}>
                <Button variant="secondary">View Memories</Button>
              </Link>
              <Link href={`/agents/${agent.id}/edit`}>
                <Button variant="secondary">Edit</Button>
              </Link>
              <Button
                variant="white"
                onClick={() => router.back()}
              >
                Back
              </Button>
            </div>
          </div>
          
          <div className="card-body">
            <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Status</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  <StatusBadge status={agent.status} />
                </dd>
              </div>
              
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">ID</dt>
                <dd className="mt-1 text-sm text-gray-900">{agent.id}</dd>
              </div>
              
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Model</dt>
                <dd className="mt-1 text-sm text-gray-900">{agent.model || 'Default'}</dd>
              </div>
              
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Created At</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {new Date(agent.created_at).toLocaleString()}
                </dd>
              </div>
              
              <div className="sm:col-span-2">
                <dt className="text-sm font-medium text-gray-500">Workspace Directory</dt>
                <dd className="mt-1 text-sm text-gray-900">{agent.workspace_dir || '/workspace'}</dd>
              </div>
            </dl>
          </div>
        </div>
        
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Run Task</h3>
            <p className="mt-1 text-sm text-gray-500">
              Create a new task for this agent
            </p>
          </div>
          
          <div className="card-body">
            <form onSubmit={handleCreateTask}>
              <div>
                <label htmlFor="goal" className="block text-sm font-medium text-gray-700">
                  Task Goal
                </label>
                <div className="mt-1">
                  <textarea
                    id="goal"
                    name="goal"
                    rows={3}
                    className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    placeholder="Describe what you want the agent to do"
                    value={taskGoal}
                    onChange={(e) => setTaskGoal(e.target.value)}
                    required
                  />
                </div>
              </div>
              
              <div className="mt-4">
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isSubmitting}
                  disabled={!taskGoal.trim()}
                >
                  {isSubmitting ? 'Creating Task...' : 'Run Task'}
                </Button>
              </div>
            </form>
          </div>
        </div>
        
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Recent Tasks</h3>
            <p className="mt-1 text-sm text-gray-500">
              View this agent's task history
            </p>
          </div>
          
          <div className="card-body">
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
        </div>
      </div>
    </Layout>
  );
} 