import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import Link from 'next/link';
import { agentApi, taskApi } from '../api';
import { Agent, AgentStatus } from '../types/agent';
import { TaskSummary, TaskStatus } from '../types/task';
import StatusBadge from '../components/StatusBadge';
import Button from '../components/Button';
import { DashboardMetric } from '../components';

interface AgentWithActiveTasks {
  agent: Agent;
  activeTasks: TaskSummary[];
}

interface SystemStats {
  totalAgents: number;
  activeAgents: number;
  idleAgents: number;
  errorAgents: number;
  totalTasks: number;
  pendingTasks: number;
  activeTasks: number;
  completedTasks: number;
  failedTasks: number;
}

export default function MonitoringDashboard(): React.ReactElement {
  const router = useRouter();
  const [agentsWithTasks, setAgentsWithTasks] = useState<AgentWithActiveTasks[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<SystemStats>({
    totalAgents: 0,
    activeAgents: 0,
    idleAgents: 0,
    errorAgents: 0,
    totalTasks: 0,
    pendingTasks: 0,
    activeTasks: 0,
    completedTasks: 0,
    failedTasks: 0,
  });
  const [refreshInterval, setRefreshInterval] = useState<number>(10000);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  const fetchData = async (): Promise<void> => {
    try {
      setLoading(true);
      
      const agentsData = await agentApi.getAgents();
      const agents = agentsData.agents;
      
      const agentsWithTasksPromises = agents.map(async (agent: Agent) => {
        try {
          const tasksData = await taskApi.getAgentTasks(agent.id);
          return {
            agent,
            activeTasks: tasksData.tasks.filter((task: TaskSummary) => 
              ['pending', 'planning', 'executing', 'reflecting'].includes(task.status)
            ),
          };
        } catch (err) {
          console.error(`Error fetching tasks for agent ${agent.id}:`, err);
          return {
            agent,
            activeTasks: [],
          };
        }
      });
      
      const results = await Promise.all(agentsWithTasksPromises);
      setAgentsWithTasks(results);
      
      // Calculate system stats
      const allTasks = results.flatMap((item: AgentWithActiveTasks) => item.activeTasks);
      const totalTasks = allTasks.length;
      
      setStats({
        totalAgents: agents.length,
        activeAgents: agents.filter((a: Agent) => a.status === 'running').length,
        idleAgents: agents.filter((a: Agent) => a.status === 'idle').length,
        errorAgents: agents.filter((a: Agent) => a.status === 'error' || a.status === 'terminated').length,
        totalTasks,
        pendingTasks: allTasks.filter((t: TaskSummary) => t.status === 'pending').length,
        activeTasks: allTasks.filter((t: TaskSummary) => ['planning', 'executing', 'reflecting'].includes(t.status)).length,
        completedTasks: allTasks.filter((t: TaskSummary) => t.status === 'completed').length,
        failedTasks: allTasks.filter((t: TaskSummary) => t.status === 'failed' || t.status === 'cancelled').length,
      });
      
      setLastRefreshed(new Date());
      setError(null);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to load monitoring data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    const interval = setInterval(() => {
      fetchData();
    }, refreshInterval);
    
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const handleRefresh = (): void => {
    fetchData();
  };

  const handleIntervalChange = (e: React.ChangeEvent<HTMLSelectElement>): void => {
    setRefreshInterval(Number(e.target.value));
  };

  return (
    <Layout title="System Monitoring">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Monitoring</h1>
          <p className="text-sm text-gray-500">
            Last refreshed: {lastRefreshed.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex space-x-4 items-center">
          <div>
            <label htmlFor="refreshInterval" className="block text-sm font-medium text-gray-700">
              Refresh every
            </label>
            <select
              id="refreshInterval"
              value={refreshInterval}
              onChange={handleIntervalChange}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
            >
              <option value={5000}>5 seconds</option>
              <option value={10000}>10 seconds</option>
              <option value={30000}>30 seconds</option>
              <option value={60000}>1 minute</option>
            </select>
          </div>
          <Button onClick={handleRefresh} disabled={loading}>
            Refresh
          </Button>
        </div>
      </div>

      {loading && !agentsWithTasks.length ? (
        <div className="text-center py-12">
          <p className="text-gray-500">Loading monitoring data...</p>
        </div>
      ) : error ? (
        <div className="text-center py-12">
          <p className="text-red-500">{error}</p>
          <Button onClick={handleRefresh} className="mt-4">
            Try Again
          </Button>
        </div>
      ) : (
        <>
          <div className="mb-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <DashboardMetric 
              title="Total Agents" 
              value={stats.totalAgents}
              footer={
                <div className="text-sm flex justify-between">
                  <div className="flex items-center">
                    <span className="w-3 h-3 rounded-full bg-green-400 mr-2"></span>
                    <span className="text-gray-500">Idle: {stats.idleAgents}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="w-3 h-3 rounded-full bg-blue-400 mr-2"></span>
                    <span className="text-gray-500">Active: {stats.activeAgents}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="w-3 h-3 rounded-full bg-red-400 mr-2"></span>
                    <span className="text-gray-500">Error: {stats.errorAgents}</span>
                  </div>
                </div>
              }
            />
            
            <DashboardMetric 
              title="Active Tasks" 
              value={stats.activeTasks}
              footer={
                <div className="text-sm flex justify-between">
                  <div className="flex items-center">
                    <span className="text-gray-500">Out of {stats.totalTasks} total tasks</span>
                  </div>
                  <Link href="/tasks" className="text-primary-600 hover:text-primary-900">
                    View all
                  </Link>
                </div>
              }
            />
            
            <DashboardMetric 
              title="Pending Tasks" 
              value={stats.pendingTasks}
              footer={
                <div className="text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Waiting to be processed</span>
                  </div>
                </div>
              }
            />
            
            <DashboardMetric 
              title="Task Completion" 
              value={`${stats.completedTasks} / ${stats.failedTasks}`}
              footer={
                <div className="text-sm flex justify-between">
                  <div className="flex items-center">
                    <span className="w-3 h-3 rounded-full bg-green-400 mr-2"></span>
                    <span className="text-gray-500">Completed</span>
                  </div>
                  <div className="flex items-center">
                    <span className="w-3 h-3 rounded-full bg-red-400 mr-2"></span>
                    <span className="text-gray-500">Failed</span>
                  </div>
                </div>
              }
            />
          </div>

          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Active Agents & Tasks
              </h3>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Currently running agents and their tasks
              </p>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      Agent
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      Status
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      Active Tasks
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      Current Task
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {agentsWithTasks.map(({ agent, activeTasks }) => (
                    <tr key={agent.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="text-sm font-medium text-gray-900">{agent.name}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <StatusBadge status={agent.status} />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {activeTasks.length}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {agent.current_task ? (
                          <div className="max-w-xs truncate">
                            <div className="text-sm text-gray-900 truncate">
                              {agent.current_task.goal}
                            </div>
                            <div className="text-xs text-gray-500">
                              <StatusBadge status={agent.current_task.status} />
                            </div>
                          </div>
                        ) : (
                          <span className="text-sm text-gray-500">None</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <Link href={`/agents/${agent.id}`} className="text-primary-600 hover:text-primary-900 mr-4">
                          Details
                        </Link>
                        <Link href={`/tasks?agent=${agent.id}`} className="text-primary-600 hover:text-primary-900">
                          Tasks
                        </Link>
                      </td>
                    </tr>
                  ))}
                  
                  {agentsWithTasks.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                        No active agents found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
          
          <div className="mt-8 bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
              <div>
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  System Actions
                </h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  Manage your autonomous agent system
                </p>
              </div>
            </div>
            
            <div className="px-4 py-5 sm:p-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Link
                href="/agents/create"
                className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Create New Agent
              </Link>
              
              <Link
                href="/agents"
                className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Manage Agents
              </Link>
              
              <Link
                href="/tasks"
                className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                View All Tasks
              </Link>
            </div>
          </div>
        </>
      )}
    </Layout>
  );
} 