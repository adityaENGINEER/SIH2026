import { api, API_BASE_URL } from './api';
import { Document } from './types';

export const documentsApi = {
  list: (projectId: string): Promise<Document[]> => 
    api.get(`/projects/${projectId}/documents`),
    
  upload: (projectId: string, file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_id', projectId);
    return api.post('/documents/upload', formData);
  },
    
  getSources: (projectId: string, documentId: string): Promise<{ document_id: string; sources: any[] }> => 
    api.get(`/projects/${projectId}/documents/${documentId}/sources`),

  delete: (projectId: string, documentId: string): Promise<any> =>
    api.delete(`/projects/${projectId}/documents/${documentId}`),

  downloadUrl: (projectId: string, documentId: string): string => 
    `${API_BASE_URL}/api/projects/${projectId}/documents/${documentId}/download`,
};
