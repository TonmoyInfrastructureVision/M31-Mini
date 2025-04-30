import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { agentApi, taskApi } from '../api';
import { Agent } from '../types/agent';
import { TaskSummary } from '../types/task';
import { Button, DashboardMetric, Alert } from '.';
import * as Accordion from '@radix-ui/react-accordion';
import * as Avatar from '@radix-ui/react-avatar';
import Link from 'next/link';
import { fadeIn, slideInUp } from '../animations';
import { logger } from '../utils/logger';

interface DashboardProps {
  className?: string;
}

interface QuickStats {
  totalAgents: number;
  activeAgents: number;
  pendingTasks: number;
  completedTasks: number;
}

interface RecentActivity {
  type: 'task_created' | 'task_completed' | 'agent_created' | 'agent_status';
  timestamp: Date;
  details: {
    id: string;
    name: string;
    status?: string;
    agentId?: string;
    agentName?: string;
  };
}

const Dashboard = ({ className }: DashboardProps): React.ReactElement => {
  const [quickStats, setQuickStats] = useState<QuickStats>({
    totalAgents: 0,
    activeAgents: 0,
    pendingTasks: 0,
    completedTasks: 0,
  });
  const [recentAgents, setRecentAgents] = useState<Agent[]>([]);
  const [recentTasks, setRecentTasks] = useState<TaskSummary[]>([]);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async (): Promise<void> => {
      try {
        setLoading(true);
        
        // Fetch agents
        const agentsData = await agentApi.getAgents();
        const agents = agentsData.agents;
        
        // Get recent agents (last 3)
        const sortedAgents = [...agents].sort((a, b) => {
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        });
        setRecentAgents(sortedAgents.slice(0, 3));
        
        // Fetch all tasks
        let allTasks: TaskSummary[] = [];
        for (const agent of agents) {
          try {
            const tasksData = await taskApi.getAgentTasks(agent.id);
            allTasks = [...allTasks, ...tasksData.tasks.map(task => ({
              ...task,
              agentName: agent.name
            }))];
          } catch (err) {
            logger.error(`Error fetching tasks for agent ${agent.id}:`, err);
          }
        }
        
        // Get recent tasks (last 5)
        const sortedTasks = [...allTasks].sort((a, b) => {
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        });
        setRecentTasks(sortedTasks.slice(0, 5));
        
        // Calculate quick stats
        setQuickStats({
          totalAgents: agents.length,
          activeAgents: agents.filter(a => a.status === 'running').length,
          pendingTasks: allTasks.filter(t => ['pending', 'planning', 'executing'].includes(t.status)).length,
          completedTasks: allTasks.filter(t => t.status === 'completed').length,
        });
        
        // Create activity feed
        const activities: RecentActivity[] = [];
        
        // Add agent activities
        sortedAgents.slice(0, 5).forEach(agent => {
          activities.push({
            type: 'agent_created',
            timestamp: new Date(agent.created_at),
            details: {
              id: agent.id,
              name: agent.name,
            }
          });
          
          if (agent.status !== 'idle') {
            activities.push({
              type: 'agent_status',
              timestamp: new Date(agent.updated_at || agent.created_at),
              details: {
                id: agent.id,
                name: agent.name,
                status: agent.status,
              }
            });
          }
        });
        
        // Add task activities
        sortedTasks.slice(0, 10).forEach(task => {
          activities.push({
            type: 'task_created',
            timestamp: new Date(task.created_at),
            details: {
              id: task.id,
              name: task.goal,
              agentId: task.agent_id,
              agentName: task.agentName,
            }
          });
          
          if (task.status === 'completed') {
            activities.push({
              type: 'task_completed',
              timestamp: new Date(task.updated_at || task.created_at),
              details: {
                id: task.id,
                name: task.goal,
                agentId: task.agent_id,
                agentName: task.agentName,
              }
            });
          }
        });
        
        // Sort activities by timestamp (most recent first)
        activities.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
        setRecentActivity(activities.slice(0, 10));
        
        setError(null);
      } catch (err) {
        logger.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchDashboardData();
  }, []);

  const getActivityIcon = (type: string): JSX.Element => {
    switch (type) {
      case 'agent_created':
        return (
          <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
            <svg className="h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </div>
        );
      case 'agent_status':
        return (
          <div className="h-8 w-8 rounded-full bg-purple-100 flex items-center justify-center">
            <svg className="h-5 w-5 text-purple-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
        );
      case 'task_created':
        return (
          <div className="h-8 w-8 rounded-full bg-green-100 flex items-center justify-center">
            <svg className="h-5 w-5 text-green-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
        );
      case 'task_completed':
        return (
          <div className="h-8 w-8 rounded-full bg-amber-100 flex items-center justify-center">
            <svg className="h-5 w-5 text-amber-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center">
            <svg className="h-5 w-5 text-gray-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        );
    }
  };

  const formatActivityText = (activity: RecentActivity): { title: string; description: string } => {
    switch (activity.type) {
      case 'agent_created':
        return {
          title: `Agent Created: ${activity.details.name}`,
          description: `A new agent was added to the system`,
        };
      case 'agent_status':
        return {
          title: `Agent Status Change: ${activity.details.name}`,
          description: `Status changed to ${activity.details.status}`,
        };
      case 'task_created':
        return {
          title: `New Task: ${activity.details.name}`,
          description: `Assigned to ${activity.details.agentName}`,
        };
      case 'task_completed':
        return {
          title: `Task Completed: ${activity.details.name}`,
          description: `By ${activity.details.agentName}`,
        };
      default:
        return {
          title: 'Activity',
          description: 'System activity recorded',
        };
    }
  };

  const formatRelativeTime = (date: Date): string => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.round(diffMs / 1000);
    const diffMins = Math.round(diffSecs / 60);
    const diffHours = Math.round(diffMins / 60);
    const diffDays = Math.round(diffHours / 24);

    if (diffSecs < 60) {
      return `${diffSecs} sec${diffSecs !== 1 ? 's' : ''} ago`;
    } else if (diffMins < 60) {
      return `${diffMins} min${diffMins !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 30) {
      return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      <motion.div
        initial="hidden"
        animate="visible"
        variants={{
          hidden: { opacity: 0 },
          visible: {
            opacity: 1,
            transition: {
              staggerChildren: 0.1
            }
          }
        }}
      >
        <div className="mb-6">
          <motion.h1 
            variants={fadeIn}
            className="text-2xl font-bold text-gray-900"
          >
            Dashboard
          </motion.h1>
          <motion.p 
            variants={fadeIn}
            className="text-sm text-gray-500 mt-1"
          >
            Welcome to the M31-Mini Autonomous Agent Framework.
          </motion.p>
        </div>

        {error && (
          <motion.div variants={fadeIn} className="mb-4">
            <Alert 
              variant="error" 
              title="Error loading dashboard data" 
              icon={
                <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              }
            >
              {error}
            </Alert>
          </motion.div>
        )}

        <motion.div 
          variants={fadeIn}
          className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-6"
        >
          <DashboardMetric
            title="Total Agents"
            value={quickStats.totalAgents}
            icon={
              <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
              </svg>
            }
            color="blue"
          />
          
          <DashboardMetric
            title="Active Agents"
            value={quickStats.activeAgents}
            change={quickStats.totalAgents ? Math.round((quickStats.activeAgents / quickStats.totalAgents) * 100) : 0}
            icon={
              <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
            color="indigo"
          />
          
          <DashboardMetric
            title="Pending Tasks"
            value={quickStats.pendingTasks}
            icon={
              <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            color="orange"
          />
          
          <DashboardMetric
            title="Completed Tasks"
            value={quickStats.completedTasks}
            icon={
              <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            color="green"
          />
        </motion.div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <motion.div 
              variants={slideInUp}
              className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden mb-6"
            >
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg p-5 border border-indigo-100">
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        <div className="h-10 w-10 rounded-lg bg-indigo-500 flex items-center justify-center">
                          <svg className="h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                          </svg>
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium text-gray-900">Create New Agent</h3>
                        <p className="text-xs text-gray-500 mt-1">Add an agent to your framework</p>
                      </div>
                    </div>
                    <div className="mt-4">
                      <Link href="/agents/new" legacyBehavior>
                        <Button 
                          fullWidth 
                          variant="primary"
                        >
                          Create Agent
                        </Button>
                      </Link>
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-5 border border-blue-100">
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        <div className="h-10 w-10 rounded-lg bg-blue-500 flex items-center justify-center">
                          <svg className="h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                          </svg>
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium text-gray-900">Create New Task</h3>
                        <p className="text-xs text-gray-500 mt-1">Assign a task to an agent</p>
                      </div>
                    </div>
                    <div className="mt-4">
                      <Link href="/tasks/new" legacyBehavior>
                        <Button 
                          fullWidth 
                          variant="primary"
                        >
                          Create Task
                        </Button>
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
            
            <motion.div 
              variants={slideInUp}
              className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden"
            >
              <div className="px-6 py-5 border-b border-slate-100">
                <h2 className="text-lg font-semibold text-gray-900">Recent Agents</h2>
              </div>
              
              {recentAgents.length > 0 ? (
                <ul className="divide-y divide-slate-100">
                  {recentAgents.map((agent) => (
                    <li key={agent.id} className="px-6 py-4">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <Avatar.Root className={`h-10 w-10 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center`}>
                            <Avatar.Fallback className="text-sm font-medium text-white">
                              {agent.name.substring(0, 2).toUpperCase()}
                            </Avatar.Fallback>
                          </Avatar.Root>
                        </div>
                        <div className="ml-4 flex-1">
                          <div className="flex items-center justify-between">
                            <div>
                              <h3 className="text-sm font-medium text-gray-900">{agent.name}</h3>
                              <p className="text-xs text-gray-500 mt-1">
                                {agent.description ? agent.description.substring(0, 60) + (agent.description.length > 60 ? '...' : '') : 'No description'}
                              </p>
                            </div>
                            <div>
                              <Link href={`/agents/${agent.id}`} legacyBehavior>
                                <Button variant="outline" size="xs">
                                  View
                                </Button>
                              </Link>
                            </div>
                          </div>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="py-12 text-center px-6">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No agents yet</h3>
                  <p className="mt-1 text-sm text-gray-500">Create your first agent to get started.</p>
                  <div className="mt-6">
                    <Link href="/agents/new" legacyBehavior>
                      <Button>Create New Agent</Button>
                    </Link>
                  </div>
                </div>
              )}
              
              {recentAgents.length > 0 && (
                <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 text-center">
                  <Link href="/agents" className="text-sm font-medium text-indigo-600 hover:text-indigo-700">
                    View all agents
                  </Link>
                </div>
              )}
            </motion.div>
          </div>

          <motion.div variants={slideInUp}>
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
              <div className="px-6 py-5 border-b border-slate-100">
                <h2 className="text-lg font-semibold text-gray-900">Activity Feed</h2>
              </div>
              
              {recentActivity.length > 0 ? (
                <div className="px-6 py-4">
                  <div className="flow-root">
                    <ul className="-mb-8">
                      {recentActivity.map((activity, activityIdx) => {
                        const { title, description } = formatActivityText(activity);
                        return (
                          <li key={activityIdx}>
                            <div className="relative pb-8">
                              {activityIdx !== recentActivity.length - 1 ? (
                                <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-slate-200" aria-hidden="true" />
                              ) : null}
                              <div className="relative flex space-x-3">
                                <div>{getActivityIcon(activity.type)}</div>
                                <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                                  <div>
                                    <p className="text-sm text-gray-900">{title}</p>
                                    <p className="text-xs text-gray-500">{description}</p>
                                  </div>
                                  <div className="text-right text-xs whitespace-nowrap text-gray-500">
                                    <time dateTime={activity.timestamp.toISOString()}>{formatRelativeTime(activity.timestamp)}</time>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                </div>
              ) : (
                <div className="py-12 text-center px-6">
                  <svg className="mx-auto h-12 w-12 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No activity yet</h3>
                  <p className="mt-1 text-sm text-gray-500">Activity will appear here as you work with the system.</p>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
};

export default Dashboard; 