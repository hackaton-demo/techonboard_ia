export type SeniorityLevel = 'junior' | 'mid' | 'senior' | 'staff' | 'lead';

export type AgentCategory = 'dev' | 'ops' | 'qa' | 'ai' | 'data' | 'general';

export type OnboardingStatus =
  | 'payment_pending'
  | 'interviewing'
  | 'provisioning'
  | 'active'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type AuditEventType = 'DENY' | 'REDACT' | 'LOG' | 'HUMAN_REVIEW';

export type AuditSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type AccessState = 'granted' | 'requires_approval' | 'blocked';

export interface Agent {
  id: string;
  name: string;
  category: AgentCategory;
  icon: string | null;
  slug: string | null;
  seniority_levels: SeniorityLevel[];
  stack_keywords: string[];
  tools: Record<string, string[]>;
  access_rules: Record<string, Record<string, unknown>>;
  learning_sequence: string[];
  ticket_criteria: Record<string, string>;
  interview_questions: Record<string, string>;
  lobster_trap_policy_file: string | null;
  system_prompt_template: string | null;
  is_custom: boolean;
  organization_id: string | null;
  created_at: string;
}

export interface OnboardingSession {
  id: string;
  dev_email: string;
  agent_id?: string | null;
  agent_name?: string | null;
  agent_emoji?: string | null;
  seniority: SeniorityLevel;
  status: OnboardingStatus;
  payment_tx_hash?: string | null;
  interview_transcript?: InterviewMessage[];
  plan_generated?: boolean;
  accesses_provisioned?: boolean;
  ticket_assigned?: string | null;
  assigned_ticket_id?: string | null;
  ticket_url?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface InterviewMessage {
  id: string;
  role: 'agent' | 'developer';
  content: string;
  timestamp: string;
  streaming?: boolean;
}

export interface PlanDay {
  day: number;
  title: string;
  description: string;
  tasks: string[];
  is_checkin: boolean;
  completed?: boolean;
}

export interface Plan {
  session_id: string;
  dev_email: string;
  agent_name: string;
  agent_emoji: string;
  seniority: SeniorityLevel;
  days: PlanDay[];
  accesses: AccessItem[];
  ticket?: Ticket;
  checkin_days: number[];
  generated_at: string;
}

export interface AccessItem {
  name: string;
  resource: string;
  state: AccessState;
  via_lobster_trap: boolean;
  icon?: string;
}

export interface Ticket {
  id: string;
  title: string;
  description: string;
  url?: string;
  priority: 'low' | 'medium' | 'high';
  labels: string[];
}

export interface PaymentRequest {
  session_id: string;
  amount_usdc: number;
  wallet_address: string;
  network: string;
  expires_at: string;
  memo?: string;
  payment_url?: string;
}

export interface DashboardStats {
  total: number;
  active: number;
  completed: number;
  payment_pending: number;
  interviewing: number;
  provisioning: number;
}

export interface DashboardData {
  stats: DashboardStats;
  recent_sessions: OnboardingSession[];
  audit_events: AuditEvent[];
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  event_type: AuditEventType;
  severity: AuditSeverity;
  rule_triggered: string;
  action_taken: string;
  session_id?: string;
  agent_id?: string;
  details?: Record<string, unknown>;
}

export interface AuditLogPage {
  items: AuditEvent[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface CreateAgentPayload {
  name: string;
  category: AgentCategory;
  icon?: string | null;
  stack_keywords: string[];
  seniority_levels: SeniorityLevel[];
  tools?: Record<string, string[]>;
  access_rules?: Record<string, Record<string, unknown>>;
}

export interface CreateOnboardingPayload {
  dev_email: string;
  agent_id: string;
  seniority: SeniorityLevel;
  tx_hash?: string;
}

export interface WebSocketMessage {
  type: 'token' | 'message' | 'status' | 'error' | 'done' | 'interview_complete' | 'github_profile';
  content?: string;
  role?: 'agent' | 'developer';
  status?: OnboardingStatus;
  message?: string;
  error?: string;
  session_id?: string;
  result?: Record<string, unknown>;
  data?: Record<string, unknown>;
}
