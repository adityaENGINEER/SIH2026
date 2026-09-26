import { api } from './api';
import { SecuritySummary, SecurityEvent } from './types';

export const securityApi = {
  getSummary: (): Promise<SecuritySummary> => 
    api.get('/security/summary'),

  getProjectSummary: (projectId: string): Promise<SecuritySummary> => 
    api.get(`/projects/${projectId}/security/summary`),
    
  getEvents: (): Promise<SecurityEvent[]> => 
    api.get('/security/events'),
    
  getProjectEvents: (projectId: string): Promise<SecurityEvent[]> => 
    api.get(`/projects/${projectId}/security/events`),
};
