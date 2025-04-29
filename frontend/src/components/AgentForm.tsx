import React from 'react';
import { useForm } from 'react-hook-form';
import { AgentCreate } from '../types/agent';

interface AgentFormProps {
  onSubmit: (data: AgentCreate) => void;
  initialData?: Partial<AgentCreate>;
  isLoading?: boolean;
}

export default function AgentForm({ onSubmit, initialData = {}, isLoading = false }: AgentFormProps): React.ReactElement {
  const { register, handleSubmit, formState: { errors } } = useForm<AgentCreate>({
    defaultValues: initialData,
  });

  const models: Array<{ id: string; name: string }> = [
    { id: 'anthropic/claude-3-opus-20240229', name: 'Claude 3 Opus' },
    { id: 'anthropic/claude-3-sonnet-20240229', name: 'Claude 3 Sonnet' },
    { id: 'anthropic/claude-3-haiku-20240307', name: 'Claude 3 Haiku' },
    { id: 'openai/gpt-4o', name: 'GPT-4o' },
    { id: 'openai/gpt-4-turbo', name: 'GPT-4 Turbo' },
    { id: 'mistral/mistral-large-latest', name: 'Mistral Large' },
  ];

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700">
          Name
        </label>
        <div className="mt-1">
          <input
            type="text"
            id="name"
            className={`shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md ${
              errors.name ? 'border-red-300' : ''
            }`}
            placeholder="Agent name"
            {...register('name', { required: 'Name is required' })}
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700">
          Description
        </label>
        <div className="mt-1">
          <textarea
            id="description"
            rows={3}
            className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md"
            placeholder="Agent description (optional)"
            {...register('description')}
          />
        </div>
      </div>

      <div>
        <label htmlFor="model" className="block text-sm font-medium text-gray-700">
          Model
        </label>
        <div className="mt-1">
          <select
            id="model"
            className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md"
            {...register('model')}
          >
            <option value="">Default</option>
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
        </div>
        <p className="mt-1 text-xs text-gray-500">
          Leave empty to use the system default model
        </p>
      </div>

      <div>
        <label htmlFor="workspace_dir" className="block text-sm font-medium text-gray-700">
          Workspace Directory
        </label>
        <div className="mt-1">
          <input
            type="text"
            id="workspace_dir"
            className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md"
            placeholder="/workspace"
            {...register('workspace_dir')}
          />
        </div>
        <p className="mt-1 text-xs text-gray-500">
          Leave empty to use the system default workspace
        </p>
      </div>

      <div className="pt-5">
        <div className="flex justify-end">
          <button
            type="button"
            className="btn-white mr-3"
            onClick={(): void => window.history.back()}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading}
          >
            {isLoading ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </form>
  );
} 