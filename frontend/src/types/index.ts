/**
 * Axiom Lens - Frontend TypeScript types.
 */

export interface User {
  id: string;
  email: string;
  name?: string;
  roles: string[];
}

export interface CurrentUserResponse {
  id: string;
  email: string;
  name?: string;
  roles: string[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface Analysis {
  id: string;
  user_id: string;
  type: 'binary' | 'javascript' | 'process';
  name: string;
  description?: string;
  target_path?: string;
  target_hash?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: Record<string, unknown>;
  error?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface AnalysisCreate {
  type: 'binary' | 'javascript' | 'process';
  name: string;
  description?: string;
  target_path?: string;
}

export interface AnalysisUpdate {
  name?: string;
  description?: string;
  status?: 'pending' | 'running' | 'completed' | 'failed';
  result?: Record<string, unknown>;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AnalysisListResponse extends PaginatedResponse<Analysis> {}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface VersionResponse {
  name: string;
  version: string;
  description: string;
}

export interface ErrorResponse {
  detail: string;
  error_code?: string;
}

export interface AuditLog {
  id: string;
  user_id?: string;
  event_type: string;
  event_data?: Record<string, unknown>;
  ip_address?: string;
  user_agent?: string;
  success: boolean;
  error_message?: string;
  created_at: string;
}

export type AnalysisType = 'binary' | 'javascript' | 'process';
export type AnalysisStatus = 'pending' | 'running' | 'completed' | 'failed';

export const ANALYSIS_TYPE_LABELS: Record<AnalysisType, string> = {
  binary: 'Binary',
  javascript: 'JavaScript/Electron',
  process: 'Process Behavior',
};

export const ANALYSIS_STATUS_LABELS: Record<AnalysisStatus, string> = {
  pending: 'Pending',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
};

export const ANALYSIS_STATUS_COLORS: Record<AnalysisStatus, 'primary' | 'success' | 'warning' | 'danger' | 'secondary'> = {
  pending: 'secondary',
  running: 'primary',
  completed: 'success',
  failed: 'danger',
};