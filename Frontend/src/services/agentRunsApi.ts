import { api } from './api';
import { AgentRun } from './types';

export const TERMINAL_RUN_STATUSES = ['completed', 'failed', 'cancelled'];

export const agentRunsApi = {
  list: (projectId: string): Promise<AgentRun[]> => 
    api.get(`/projects/${projectId}/agent-runs`),
    
  get: (projectId: string, runId: string): Promise<AgentRun> => 
    api.get(`/projects/${projectId}/agent-runs/${runId}`),

  cancel: (projectId: string, runId: string): Promise<AgentRun> =>
    api.post(`/projects/${projectId}/agent-runs/${runId}/cancel`, {}),
};
