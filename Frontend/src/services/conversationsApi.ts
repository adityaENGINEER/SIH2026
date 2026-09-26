import { api } from './api';
import { Conversation, ChatMessage } from './types';

export const conversationsApi = {
  list: (projectId: string): Promise<Conversation[]> => 
    api.get(`/projects/${projectId}/conversations`),
    
  get: (projectId: string, conversationId: string): Promise<Conversation> => 
    api.get(`/projects/${projectId}/conversations/${conversationId}`),
    
  create: (projectId: string, data: { title: string }): Promise<Conversation> => 
    api.post(`/projects/${projectId}/conversations`, data),
    
  sendMessage: (projectId: string, conversationId: string, data: { message: string, mode: string, document_ids?: string[] }): Promise<ChatMessage> => 
    api.post(`/projects/${projectId}/conversations/${conversationId}/messages`, data),

  getHistory: (projectId: string): Promise<(Conversation & { messages: ChatMessage[] })[]> =>
    api.get(`/projects/${projectId}/chat/history`),
};
