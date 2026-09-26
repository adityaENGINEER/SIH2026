import { api } from './api';
import { Model } from './types';

export const modelsApi = {
  list: async (): Promise<Model[]> => (await api.get('/models')).models ?? [],
};
