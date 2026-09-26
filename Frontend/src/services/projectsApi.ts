import { api } from './api';
import { Project } from './types';

export const projectsApi = {
  list: (): Promise<Project[]> => api.get('/projects'),
  get: (id: string): Promise<Project> => api.get(`/projects/${id}`),
  create: (data: { name: string; description: string; project_type: string }): Promise<Project> =>
    api.post('/projects', data),
  update: (id: string, data: Partial<Project>): Promise<Project> => api.patch(`/projects/${id}`, data),
  delete: (id: string): Promise<{ status: string }> => api.delete(`/projects/${id}`),
};
