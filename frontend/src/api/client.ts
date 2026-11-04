/**
 * Axiom Lens - API client with typed endpoints.
 */
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import type { 
  Analysis, 
  AnalysisCreate, 
  AnalysisUpdate, 
  AnalysisListResponse,
  CurrentUserResponse,
  TokenResponse,
  HealthResponse,
  VersionResponse,
  ErrorResponse 
} from '../types';

/// <reference types="vite/client" />

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

class ApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      withCredentials: true,
    });

    this.client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
      if (this.accessToken) {
        config.headers.Authorization = `Bearer ${this.accessToken}`;
      }
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          this.clearToken();
          if (!window.location.pathname.startsWith('/auth')) {
            window.location.href = '/auth/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string | null) {
    this.accessToken = token;
  }

  getToken(): string | null {
    return this.accessToken;
  }

  clearToken() {
    this.accessToken = null;
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  // Health & Version
  async getHealth(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  async getVersion(): Promise<VersionResponse> {
    const response = await this.client.get<VersionResponse>('/version');
    return response.data;
  }

  // Auth
  async getCurrentUser(): Promise<CurrentUserResponse> {
    const response = await this.client.get<CurrentUserResponse>('/auth/me');
    return response.data;
  }

  async getDemoToken(): Promise<TokenResponse> {
    const response = await this.client.post<TokenResponse>('/auth/demo');
    return response.data;
  }

  async logout(): Promise<void> {
    await this.client.post('/auth/logout');
  }

  // Analyses
  async createAnalysis(data: AnalysisCreate): Promise<Analysis> {
    const response = await this.client.post<Analysis>('/analyses', data);
    return response.data;
  }

  async uploadBinary(file: File, name?: string, description?: string): Promise<Analysis> {
    const formData = new FormData();
    formData.append('file', file);
    if (name) formData.append('name', name);
    if (description) formData.append('description', description);
    
    const response = await this.client.post<Analysis>('/analyses/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }

  async listAnalyses(params?: {
    page?: number;
    page_size?: number;
    type_filter?: string;
    status_filter?: string;
    search?: string;
  }): Promise<AnalysisListResponse> {
    const response = await this.client.get<AnalysisListResponse>('/analyses', { params });
    return response.data;
  }

  async getAnalysis(id: string): Promise<Analysis> {
    const response = await this.client.get<Analysis>(`/analyses/${id}`);
    return response.data;
  }

  async updateAnalysis(id: string, data: AnalysisUpdate): Promise<Analysis> {
    const response = await this.client.patch<Analysis>(`/analyses/${id}`, data);
    return response.data;
  }

  async deleteAnalysis(id: string): Promise<void> {
    await this.client.delete(`/analyses/${id}`);
  }
}

export const api = new ApiClient();
