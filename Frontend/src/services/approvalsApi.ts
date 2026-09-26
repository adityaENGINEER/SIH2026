import { api } from './api';
import { Approval } from './types';

export interface ApprovalDecision {
  approver_name: string;
  employee_id: string;
  reason?: string;
  comment?: string;
}

export const approvalsApi = {
  create: (projectId: string, data: any): Promise<Approval> => 
    api.post(`/projects/${projectId}/approvals`, data),
    
  list: (projectId: string): Promise<Approval[]> => 
    api.get(`/projects/${projectId}/approvals`),
    
  get: (projectId: string, approvalId: string): Promise<Approval> => 
    api.get(`/projects/${projectId}/approvals/${approvalId}`),
    
  submitReview: (projectId: string, approvalId: string): Promise<Approval> => 
    api.post(`/projects/${projectId}/approvals/${approvalId}/submit`, {}),
    
  approve: (projectId: string, approvalId: string, decision: ApprovalDecision): Promise<Approval> => 
    api.post(`/projects/${projectId}/approvals/${approvalId}/approve`, decision),
    
  reject: (projectId: string, approvalId: string, decision: ApprovalDecision): Promise<Approval> => 
    api.post(`/projects/${projectId}/approvals/${approvalId}/reject`, decision),
};
