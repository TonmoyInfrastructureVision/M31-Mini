import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { agentApi, taskApi } from '../api';
import { Agent } from '../types/agent';
import { TaskSummary } from '../types/task';
import StatusBadge from './StatusBadge';
import Button from './Button';
import { DashboardMetric } from '.';
import { motion } from 'framer-motion';
import { fadeIn, slideInUp, containerVariants } from '../animations';
import { LineChart, PieChart } from './Charts';
import RefreshIndicator from './RefreshIndicator';
import AgentStatusCard from './AgentStatusCard';
import TaskListItem from './TaskListItem';
import { logger } from '../utils/logger';

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

interface SystemMonitorProps {
  className?: string;
}

const SystemMonitor = ({ className }: SystemMonitorProps): React.ReactElement => {
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
          logger.error(`Error fetching tasks for agent ${agent.id}:`, err);
          return {
            agent,
            activeTasks: [],
          };
        }
      });
      
      const results = await Promise.all(agentsWithTasksPromises);
      setAgentsWithTasks(results);
      
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
      logger.error('Error fetching data:', err);
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
    <motion.div 
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className={`space-y-6 ${className}`}
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
              name="refreshInterval"
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              value={refreshInterval}
              onChange={handleIntervalChange}
            >
              <option value={5000}>5 seconds</option>
              <option value={10000}>10 seconds</option>
              <option value={30000}>30 seconds</option>
              <option value={60000}>1 minute</option>
            </select>
          </div>
          <Button
            onClick={handleRefresh}
            disabled={loading}
            isLoading={loading}
          >
            Refresh Now
          </Button>
        </div>
      </motion.div>

      {error && (
        <motion.div variants={fadeIn} className="mb-4 bg-red-50 p-4 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading data</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      <motion.div variants={fadeIn}>
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <DashboardMetric
            title="Total Agents"
            value={stats.totalAgents}
            subtitle="Deployed in the system"
            icon={
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
              </svg>
            }
            color="blue"
          />
          
          <DashboardMetric
            title="Active Agents"
            value={stats.activeAgents}
            subtitle="Currently running"
            change={stats.totalAgents === 0 ? 0 : Math.round((stats.activeAgents / stats.totalAgents) * 100)}
            icon={
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
            color="indigo"
          />
          
          <DashboardMetric
            title="Total Tasks"
            value={stats.totalTasks}
            subtitle="In the system"
            icon={
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            }
            color="purple"
          />
          
          <DashboardMetric
            title="Completed Tasks"
            value={stats.completedTasks}
            subtitle="Successfully finished"
            change={stats.totalTasks === 0 ? 0 : Math.round((stats.completedTasks / stats.totalTasks) * 100)}
            icon={
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            }
            color="green"
          />
        </div>
      </motion.div>
      
      <motion.div variants={fadeIn} className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="bg-white rounded-lg shadow-sm p-6 border border-slate-100">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Agent Status</h2>
          <div className="h-64">
            <PieChart data={agentStatusData} />
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6 border border-slate-100">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Task Status</h2>
          <div className="h-64">
            <PieChart data={taskStatusData} />
          </div>
        </div>
      </motion.div>
      
      <motion.div variants={fadeIn}>
        <div className="bg-white rounded-lg shadow-sm p-6 border border-slate-100">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Task History (7 Days)</h2>
          <div className="h-64">
            <LineChart data={taskHistoryData} />
          </div>
        </div>
      </motion.div>
      
      <motion.div variants={fadeIn}>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Active Agents</h2>
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {agentsWithTasks.map((item) => (
            <AgentStatusCard
              key={item.agent.id}
              agent={item.agent}
              tasksCount={item.activeTasks.length}
            />
          ))}
          
          {agentsWithTasks.length === 0 && (
            <div className="col-span-3 text-center py-8 bg-white rounded-md shadow-sm">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No agents</h3>
              <p className="mt-1 text-sm text-gray-500">Create a new agent to get started.</p>
              <div className="mt-6">
                <Link href="/agents/new" legacyBehavior>
                  <Button>Create New Agent</Button>
                </Link>
              </div>
            </div>
          )}
        </div>
      </motion.div>
      
      <motion.div variants={fadeIn}>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-medium text-gray-900">Recent Tasks</h2>
          <Link href="/tasks" className="text-sm font-medium text-indigo-600 hover:text-indigo-800">
            View all tasks
          </Link>
        </div>
        
        <div className="bg-white overflow-hidden shadow-sm rounded-lg border border-slate-100">
          <ul className="divide-y divide-gray-200">
            {agentsWithTasks.flatMap((item) => 
              item.activeTasks.slice(0, 3).map((task) => (
                <TaskListItem
                  key={task.id}
                  task={task}
                  agentName={item.agent.name}
                />
              ))
            ).slice(0, 5)}
            
            {agentsWithTasks.flatMap((item) => item.activeTasks).length === 0 && (
              <li className="px-6 py-12 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No active tasks</h3>
                <p className="mt-1 text-sm text-gray-500">Get started by creating a new task for an agent.</p>
                <div className="mt-6">
                  <Link href="/tasks/new" legacyBehavior>
                    <Button>Create New Task</Button>
                  </Link>
                </div>
              </li>
            )}
          </ul>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default SystemMonitor; 