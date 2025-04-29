import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../components/Layout';
import Link from 'next/link';
import { agentApi, taskApi } from '../../api';
import { TaskResponse, TaskResult } from '../../types/task';
import Button from '../../components/Button';
import StatusBadge from '../../components/StatusBadge';

export default function TaskDetail(): React.ReactElement {
  const router = useRouter();
  const { id } = router.query;
  
  const [task, setTask] = useState<TaskResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  const isTaskActive = task?.status === 'planning' || 
                        task?.status === 'executing' || 
                        task?.status === 'pending';

  useEffect(() => {
    const fetchTask = async (): Promise<void> => {
      if (!id || typeof id !== 'string') return;
      
      try {
        setLoading(true);
        const data = await taskApi.getTask(id);
        setTask(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching task:', err);
        setError('Failed to load task data');
      } finally {
        setLoading(false);
      }
    };

    fetchTask();
    
    // Set up polling for active tasks
    const interval = setInterval(() => {
      if (isTaskActive) {
        fetchTask();
      }
    }, 3000);
    
    return () => clearInterval(interval);
  }, [id, isTaskActive]);

  const handleCancelTask = async (): Promise<void> => {
    if (!id || typeof id !== 'string') return;
    
    if (window.confirm('Are you sure you want to cancel this task?')) {
      try {
        await taskApi.cancelTask(id);
        
        // Refetch task to update status
        const updatedTask = await taskApi.getTask(id);
        setTask(updatedTask);
      } catch (err) {
        console.error('Error cancelling task:', err);
        alert('Failed to cancel task');
      }
    }
  };

  if (loading) {
    return (
      <Layout title="Task Details">
        <div className="text-center py-4">
          <p className="text-gray-500">Loading task data...</p>
        </div>
      </Layout>
    );
  }

  if (error || !task) {
    return (
      <Layout title="Task Details">
        <div className="text-center py-4">
          <p className="text-red-500">{error || 'Task not found'}</p>
          <Button 
            variant="primary" 
            onClick={() => router.back()}
            className="mt-4"
          >
            Back
          </Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={`Task Details`}>
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Task: {task.goal.substring(0, 50)}{task.goal.length > 50 ? '...' : ''}</h2>
            <p className="mt-1 text-sm text-gray-500">
              Agent: <Link href={`/agents/${task.agent_id}`} className="text-primary-600 hover:underline">
                {task.agent_id}
              </Link>
            </p>
          </div>
          <div className="flex space-x-2">
            {isTaskActive && (
              <Button
                variant="white"
                className="text-red-600 border-red-300 hover:bg-red-50"
                onClick={handleCancelTask}
              >
                Cancel Task
              </Button>
            )}
            <Button
              variant="white"
              onClick={() => router.back()}
            >
              Back
            </Button>
          </div>
        </div>
        
        <div className="card">
          <div className="card-header flex justify-between items-center">
            <div>
              <h3 className="text-lg leading-6 font-medium text-gray-900">Task Overview</h3>
            </div>
            <StatusBadge status={task.status} />
          </div>
          
          <div className="card-body">
            <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">ID</dt>
                <dd className="mt-1 text-sm text-gray-900">{task.id}</dd>
              </div>
              
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Created At</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {new Date(task.created_at).toLocaleString()}
                </dd>
              </div>
              
              {task.updated_at && (
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {new Date(task.updated_at).toLocaleString()}
                  </dd>
                </div>
              )}
              
              {task.completed_at && (
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-gray-500">Completed At</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {new Date(task.completed_at).toLocaleString()}
                  </dd>
                </div>
              )}
              
              <div className="sm:col-span-2">
                <dt className="text-sm font-medium text-gray-500">Goal</dt>
                <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">{task.goal}</dd>
              </div>
              
              {task.error && (
                <div className="sm:col-span-2">
                  <dt className="text-sm font-medium text-gray-500">Error</dt>
                  <dd className="mt-1 text-sm text-red-600 whitespace-pre-wrap">{task.error}</dd>
                </div>
              )}
            </dl>
          </div>
        </div>
        
        {task.plan && (
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg leading-6 font-medium text-gray-900">Plan</h3>
            </div>
            
            <div className="card-body">
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-500">Thought Process</h4>
                <p className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">{task.plan.thought}</p>
              </div>
              
              <h4 className="text-sm font-medium text-gray-500 mb-2">Steps</h4>
              <div className="border rounded-md divide-y divide-gray-200">
                {task.plan.steps.map((step) => (
                  <div key={step.id} className="p-4">
                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-primary-100 text-primary-800">
                          {step.id}
                        </span>
                      </div>
                      <div className="ml-4 flex-1">
                        <h5 className="text-sm font-medium text-gray-900">{step.description}</h5>
                        {step.tool && (
                          <div className="mt-1">
                            <span className="text-xs font-medium text-gray-500">Tool: {step.tool}</span>
                            {step.tool_args && (
                              <pre className="mt-1 text-xs text-gray-700 bg-gray-50 p-2 rounded overflow-x-auto">
                                {JSON.stringify(step.tool_args, null, 2)}
                              </pre>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        
        {task.results && task.results.length > 0 && (
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg leading-6 font-medium text-gray-900">Results</h3>
            </div>
            
            <div className="card-body">
              <div className="space-y-4">
                {task.results.map((result: TaskResult) => (
                  <div key={result.step_id} className="border rounded-md p-4">
                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <span className={`inline-flex items-center justify-center h-6 w-6 rounded-full ${
                          result.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {result.step_id}
                        </span>
                      </div>
                      <div className="ml-4 flex-1">
                        <div className="flex justify-between">
                          <h5 className="text-sm font-medium text-gray-900">
                            Step {result.step_id}
                            {result.tool_used && ` (${result.tool_used})`}
                          </h5>
                          <span className="text-xs text-gray-500">{new Date(result.timestamp).toLocaleTimeString()}</span>
                        </div>
                        
                        {result.success ? (
                          <div className="mt-2 text-sm text-gray-700 whitespace-pre-wrap overflow-x-auto">
                            {result.result}
                          </div>
                        ) : (
                          <div className="mt-2 text-sm text-red-600 whitespace-pre-wrap overflow-x-auto">
                            Error: {result.error || 'Unknown error'}
                          </div>
                        )}
                        
                        {result.metadata && Object.keys(result.metadata).length > 0 && (
                          <details className="mt-2">
                            <summary className="text-xs font-medium text-gray-500 cursor-pointer">Metadata</summary>
                            <pre className="mt-1 text-xs text-gray-700 bg-gray-50 p-2 rounded overflow-x-auto">
                              {JSON.stringify(result.metadata, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        
        {task.reflection && (
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg leading-6 font-medium text-gray-900">Reflection</h3>
            </div>
            
            <div className="card-body">
              <dl className="grid grid-cols-1 gap-x-4 gap-y-6">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Success</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    <StatusBadge status={task.reflection.success ? 'success' : 'error'}>
                      {task.reflection.success ? 'Yes' : 'No'}
                    </StatusBadge>
                  </dd>
                </div>
                
                <div>
                  <dt className="text-sm font-medium text-gray-500">Reasoning</dt>
                  <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">{task.reflection.reasoning}</dd>
                </div>
                
                <div>
                  <dt className="text-sm font-medium text-gray-500">Learning</dt>
                  <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">{task.reflection.learning}</dd>
                </div>
                
                {task.reflection.next_steps && task.reflection.next_steps.length > 0 && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Next Steps</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      <ul className="list-disc pl-5 space-y-1">
                        {task.reflection.next_steps.map((step, index) => (
                          <li key={index}>{step}</li>
                        ))}
                      </ul>
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
} 