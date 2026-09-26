export interface Project {
  project_id: string;
  name: string;
  description: string;
  project_type: string;
  created_at?: string;
  updated_at?: string;
}

export interface Conversation {
  conversation_id: string;
  project_id?: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  messages?: ChatMessage[];
}

export interface Routing {
  model: string;
  purpose: string;
  reason: string;
  capability?: string;
}

export interface ChatMessage {
  message_id?: string;
  conversation_id?: string;
  project_id?: string;
  role: 'user' | 'assistant' | 'system' | 'tuffy';
  content: string;
  execution_mode?: 'chat' | 'agent' | null;
  task_id?: string | null;
  status?: string;
  routing?: Routing | null;
  error?: { code?: string; message?: string } | null;
  created_at: string;
}

export interface Document {
  document_id: string;
  project_id?: string;
  filename?: string;
  original_filename?: string;
  content_type?: string;
  status: string;
  metadata?: any;
  created_at?: string;
  uploaded_at?: string;
  size_bytes?: number;
  content_status?: string;
  index_status?: string;
  error?: { code?: string; message?: string };
}

export interface Model {
  name: string;
  role: string;
  installed: boolean;
  available: boolean;
  size?: number;
  modified_at?: string;
  family?: string;
  parameter_size?: string;
}

export interface Tool {
  name: string;
  description: string;
  available: boolean;
}

export interface RunStep {
  step_id: string;
  description: string;
  capability: string;
  status: string;
  depends_on: string[];
  input: Record<string, any>;
  result?: Record<string, any> | null;
  error?: { code?: string; message?: string } | null;
}

export interface AgentRun {
  task_id: string;
  user_request: string;
  project_id?: string;
  conversation_id?: string;
  status: string;
  current_step?: string | null;
  plan?: { plan_id?: string; steps: RunStep[] } | null;
  observations: any[];
  validation_results: { valid: boolean; step_id?: string; reason?: string; issues: string[] }[];
  replan_count: number;
  max_replans: number;
  step_count: number;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
  final_result?: Record<string, any> | null;
  error?: { code?: string; message?: string } | null;
  cancel_requested?: boolean;
  routing?: Routing | null;
  deliverable_id?: string | null;
  approval_id?: string | null;
}

export interface Approval {
  approval_id: string;
  project_id: string;
  conversation_id?: string | null;
  task_id?: string | null;
  agent_run_id?: string | null;
  deliverable_id?: string | null;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
  submitted_at?: string | null;
  reviewed_at?: string | null;
  approver_name?: string | null;
  employee_id?: string | null;
  review_comment?: string | null;
  rejection_reason?: string | null;
  approval_reason?: string | null;
  signature_status: string;
  source_document_ids: string[];
  output_document_ids: string[];
}

export interface Deliverable {
  deliverable_id: string;
  project_id: string;
  task_id?: string | null;
  approval_id?: string | null;
  type: string;
  filename: string;
  path: string;
  created_at: string;
  size: number;
  status: string;
}

export interface SecuritySummary {
  total_evaluations: number;
  outbound_calls: number;
  blocked_calls: number;
  local_calls: number;
}

export interface SecurityEvent {
  event_id: string;
  timestamp: string;
  event_type: string;
  source: string;
  destination: string;
  allowed: boolean;
  blocked: boolean;
  reason?: string | null;
  project_id?: string | null;
  task_id?: string | null;
  agent_run_id?: string | null;
}
