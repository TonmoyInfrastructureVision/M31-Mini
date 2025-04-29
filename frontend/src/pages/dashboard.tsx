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
import { motion } from 'framer-motion';
import { fadeIn, slideInUp, containerVariants } from '../animations';
import { LineChart, PieChart } from '../components/Charts';
import RefreshIndicator from '../components/RefreshIndicator';
import AgentStatusCard from '../components/AgentStatusCard';
import TaskListItem from '../components/TaskListItem';

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

interface Segment {
  value: number;
  label: string;
  color: string;
}

interface DataPoint {
  value: number;
  label: string;
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
  const [agentStatusData, setAgentStatusData] = useState<Segment[]>([]);
  const [taskStatusData, setTaskStatusData] = useState<Segment[]>([]);
  const [taskHistoryData, setTaskHistoryData] = useState<DataPoint[]>([]);

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
      
      const currentStats = {
        totalAgents: agents.length,
        activeAgents: agents.filter((a: Agent) => a.status === 'running').length,
        idleAgents: agents.filter((a: Agent) => a.status === 'idle').length,
        errorAgents: agents.filter((a: Agent) => a.status === 'error' || a.status === 'terminated').length,
        totalTasks,
        pendingTasks: allTasks.filter((t: TaskSummary) => t.status === 'pending').length,
        activeTasks: allTasks.filter((t: TaskSummary) => ['planning', 'executing', 'reflecting'].includes(t.status)).length,
        completedTasks: allTasks.filter((t: TaskSummary) => t.status === 'completed').length,
        failedTasks: allTasks.filter((t: TaskSummary) => t.status === 'failed' || t.status === 'cancelled').length,
      };
      
      setStats(currentStats);
      
      // Prepare chart data
      const agentChartData: Segment[] = [
        { value: currentStats.activeAgents, label: 'Active', color: '#3b82f6' },
        { value: currentStats.idleAgents, label: 'Idle', color: '#10b981' },
        { value: currentStats.errorAgents, label: 'Error', color: '#ef4444' }
      ].filter(segment => segment.value > 0);
      
      const taskChartData: Segment[] = [
        { value: currentStats.pendingTasks, label: 'Pending', color: '#f59e0b' },
        { value: currentStats.activeTasks, label: 'Active', color: '#3b82f6' },
        { value: currentStats.completedTasks, label: 'Completed', color: '#10b981' },
        { value: currentStats.failedTasks, label: 'Failed', color: '#ef4444' }
      ].filter(segment => segment.value > 0);
      
      setAgentStatusData(agentChartData);
      setTaskStatusData(taskChartData);
      
      // Generate some sample historical data for the line chart
      // In a real application, this would come from the API
      const daysAgo = (days: number): string => {
        const date = new Date();
        date.setDate(date.getDate() - days);
        return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
      };
      
      const taskHistoryPoints: DataPoint[] = [
        { value: 3, label: daysAgo(6) },
        { value: 5, label: daysAgo(5) },
        { value: 4, label: daysAgo(4) },
        { value: 7, label: daysAgo(3) },
        { value: 9, label: daysAgo(2) },
        { value: 8, label: daysAgo(1) },
        { value: totalTasks, label: 'Today' }
      ];
      
      setTaskHistoryData(taskHistoryPoints);
      
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
      <motion.div 
        initial="hidden"
        animate="visible"
        variants={containerVariants}
        className="space-y-6"
      >
        <motion.div 
          variants={fadeIn}
          className="mb-6 flex justify-between items-center"
        >
          <div>
            <h1 className="text-2xl font-bold text-gray-900">System Monitoring</h1>
            <RefreshIndicator 
              lastRefreshed={lastRefreshed} 
              isLoading={loading} 
              onRefresh={handleRefresh} 
            />
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
        </motion.div>

        {loading && !agentsWithTasks.length ? (
          <motion.div 
            variants={fadeIn}
            className="text-center py-12"
          >
            <p className="text-gray-500">Loading monitoring data...</p>
          </motion.div>
        ) : error ? (
          <motion.div 
            variants={fadeIn}
            className="text-center py-12"
          >
            <p className="text-red-500">{error}</p>
            <Button onClick={handleRefresh} className="mt-4">
              Try Again
            </Button>
          </motion.div>
        ) : (
          <>
            <motion.div 
              variants={containerVariants}
              className="mb-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4"
            >
              <motion.div variants={slideInUp}>
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
              </motion.div>
              
              <motion.div variants={slideInUp}>
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
              </motion.div>
              
              <motion.div variants={slideInUp}>
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
              </motion.div>
              
              <motion.div variants={slideInUp}>
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
              </motion.div>
            </motion.div>

            <motion.div 
              variants={containerVariants}
              className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-3"
            >
              <motion.div 
                variants={fadeIn}
                className="bg-white rounded-lg shadow-md p-6 col-span-2"
              >
                <h3 className="text-lg font-medium text-gray-900 mb-4">Task Activity</h3>
                <div className="h-64">
                  <LineChart 
                    data={taskHistoryData}
                    height={220}
                    width={600}
                    showGrid
                    showLabels
                  />
                </div>
              </motion.div>
              
              <motion.div 
                variants={containerVariants}
                className="bg-white rounded-lg shadow-md p-6 grid grid-rows-2 gap-6"
              >
                <motion.div variants={fadeIn} className="flex flex-col items-center">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Agent Status</h3>
                  <PieChart 
                    data={agentStatusData}
                    size={140} 
                    donut
                    showLabels
                    showPercentage
                  />
                </motion.div>
                
                <motion.div variants={fadeIn} className="flex flex-col items-center">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Task Status</h3>
                  <PieChart 
                    data={taskStatusData}
                    size={140}
                    donut
                    showLabels
                    showPercentage
                  />
                </motion.div>
              </motion.div>
            </motion.div>

            <motion.div 
              variants={fadeIn}
              className="bg-white shadow overflow-hidden sm:rounded-lg mb-8"
            >
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
                    {agentsWithTasks.map(({ agent, activeTasks }, index) => (
                      <motion.tr 
                        key={agent.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
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
                                <StatusBadge status={agent.current_task.status} size="sm" />
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
                      </motion.tr>
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
            </motion.div>
            
            <motion.div 
              variants={fadeIn}
              className="bg-white shadow overflow-hidden sm:rounded-lg mb-8"
            >
              <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Latest Tasks
                  </h3>
                  <p className="mt-1 max-w-2xl text-sm text-gray-500">
                    Recently created or active tasks
                  </p>
                </div>
                <Link 
                  href="/tasks" 
                  className="text-primary-600 hover:text-primary-900 text-sm font-medium"
                >
                  View all tasks
                </Link>
              </div>
              
              <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {agentsWithTasks.flatMap(({ activeTasks }) => activeTasks)
                  .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                  .slice(0, 6)
                  .map((task, index) => (
                    <TaskListItem key={task.id} task={task} index={index} />
                  ))}
                  
                {agentsWithTasks.flatMap(({ activeTasks }) => activeTasks).length === 0 && (
                  <div className="col-span-3 py-8 text-center text-gray-500">
                    No active tasks found
                  </div>
                )}
              </div>
            </motion.div>
            
            <motion.div 
              variants={fadeIn}
              className="bg-white shadow overflow-hidden sm:rounded-lg"
            >
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  System Actions
                </h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  Manage your autonomous agent system
                </p>
              </div>
              
              <div className="px-4 py-5 sm:p-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <motion.div 
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Link
                    href="/agents/create"
                    className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 w-full h-full"
                  >
                    Create New Agent
                  </Link>
                </motion.div>
                
                <motion.div 
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Link
                    href="/agents"
                    className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 w-full h-full"
                  >
                    Manage Agents
                  </Link>
                </motion.div>
                
                <motion.div 
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Link
                    href="/tasks"
                    className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 w-full h-full"
                  >
                    View All Tasks
                  </Link>
                </motion.div>
              </div>
            </motion.div>
          </>
        )}
      </motion.div>
    </Layout>
  );
} 