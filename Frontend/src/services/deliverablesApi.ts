import { api, API_BASE_URL } from './api';
import { Deliverable } from './types';

export const deliverablesApi = {
  list: (projectId: string): Promise<Deliverable[]> => 
    api.get(`/projects/${projectId}/deliverables`),
    
  getMetadata: (projectId: string, deliverableId: string): Promise<Deliverable> => 
    api.get(`/projects/${projectId}/deliverables/${deliverableId}`),
    
  getDownloadUrl: (projectId: string, deliverableId: string): string =>
    `${API_BASE_URL}/api/projects/${projectId}/deliverables/${deliverableId}/download`,
};
