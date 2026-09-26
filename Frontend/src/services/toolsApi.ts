import { api } from './api';
import { Tool } from './types';

export const toolsApi = {
  list: (): Promise<Tool[]> => api.get('/tools'),
};
