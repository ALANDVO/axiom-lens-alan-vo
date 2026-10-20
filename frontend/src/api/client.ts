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
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // For session cookies
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ErrorResponse>) => {
        if (error.response?.status === 401) {
          this.clearToken();
          // Redirect to login if not already there
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string | null) {
    this.accessToken = token;
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
  }

  getToken(): string | null {
    if (!this.accessToken) {
      this.accessToken = localStorage.getItem('access_token');
    }
    return this.accessToken;
  }

  clearToken() {
    this.accessToken = null;
    localStorage.removeItem('access_token');
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
    const response = await this.client.post<TokenResponse>('/auth/demo-token');
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

  async listAnalyses(params?: {
    page?: number;
    page_size?: number;
    type_filter?: string;
    status_filter?: string;
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