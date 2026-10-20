/**
 * Axiom Lens - Analyses list page.
 */
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Layout } from '../components/layout';
import { Card, CardContent, Badge, Button, Input } from '../components/ui';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthProvider';
import type { AnalysisCreate, AnalysisListResponse } from '../types';
import { 
  FileCode, Plus, ChevronLeft, ChevronRight, Trash2, Edit2, Eye 
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ANALYSIS_TYPE_LABELS, ANALYSIS_STATUS_LABELS, ANALYSIS_STATUS_COLORS, type AnalysisType, type AnalysisStatus } from '../types';

const TYPE_OPTIONS: { value: AnalysisType | ''; label: string }[] = [
  { value: '', label: 'All Types' },
  { value: 'binary', label: 'Binary' },
  { value: 'javascript', label: 'JavaScript/Electron' },
  { value: 'process', label: 'Process' },
];

const STATUS_OPTIONS: { value: AnalysisStatus | ''; label: string }[] = [
  { value: '', label: 'All Statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'running', label: 'Running' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
];

export function Analyses() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<AnalysisType | ''>('');
  const [statusFilter, setStatusFilter] = useState<AnalysisStatus | ''>('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Sync filters with URL
  useEffect(() => {
    const type = searchParams.get('type') as AnalysisType | '' || '';
    const status = searchParams.get('status') as AnalysisStatus | '' || '';
    setTypeFilter(type);
    setStatusFilter(status);
  }, [searchParams]);

  const updateFilters = (newFilters: Partial<{ type: AnalysisType | ''; status: AnalysisStatus | '' }>) => {
    const params = new URLSearchParams(searchParams);
    if (newFilters.type !== undefined) {
      if (newFilters.type) params.set('type', newFilters.type);
      else params.delete('type');
    }
    if (newFilters.status !== undefined) {
      if (newFilters.status) params.set('status', newFilters.status);
      else params.delete('status');
    }
    params.set('page', '1');
    setSearchParams(params);
    setPage(1);
  };

  const { data: analysesData, isLoading, error, refetch } = useQuery<AnalysisListResponse>({
    queryKey: ['analyses', page, searchQuery, typeFilter, statusFilter],
    queryFn: () => api.listAnalyses({ page, page_size: pageSize, type_filter: typeFilter, status_filter: statusFilter }),
    enabled: isAuthenticated,
    placeholderData: (previousData: AnalysisListResponse | undefined) => previousData,
  });

  const createMutation = useMutation({
    mutationFn: (data: AnalysisCreate) => api.createAnalysis(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
      navigate('/analyses');
    },
  });

  // Keep reference to prevent lint warning
  void createMutation;

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteAnalysis(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    const params = new URLSearchParams(searchParams);
    if (searchQuery) params.set('search', searchQuery);
    else params.delete('search');
    params.set('page', '1');
    setSearchParams(params);
  };

  if (authLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="spinner" role="status" aria-label="Loading..." />
        </div>
      </Layout>
    );
  }

  if (!isAuthenticated) {
    return (
      <Layout>
        <div className="max-w-2xl mx-auto text-center py-16">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Sign In Required</h1>
          <p className="text-gray-600 mb-6">Please sign in to view your analyses.</p>
          <Button onClick={() => navigate('/api/v1/auth/login')}>Sign In</Button>
        </div>
      </Layout>
    );
  }

  const analyses = analysesData?.items || [];
  const total = analysesData?.total || 0;
  const totalPages = analysesData?.total_pages || 1;

  return (
    <Layout>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analyses</h1>
          <p className="text-gray-600 mt-1">Manage your reverse engineering analyses</p>
        </div>
        <Button onClick={() => navigate('/analyses/new')}>
          <Plus className="h-4 w-4" />
          New Analysis
        </Button>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search analyses..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                aria-label="Search analyses"
              />
            </div>
            <div className="flex gap-2">
              <select
                value={typeFilter}
                onChange={(e) => {
                  setTypeFilter(e.target.value as AnalysisType | '');
                  updateFilters({ type: e.target.value as AnalysisType | '' });
                }}
                className="px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Filter by type"
              >
                {TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value as AnalysisStatus | '');
                  updateFilters({ status: e.target.value as AnalysisStatus | '' });
                }}
                className="px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Filter by status"
              >
                {STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              <Button type="button" variant="secondary" onClick={() => {
                setSearchQuery('');
                setTypeFilter('');
                setStatusFilter('');
                updateFilters({ type: '', status: '' });
              }}>
                <RefreshCw className="h-4 w-4" />
                Clear
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Analyses Table */}
      <Card>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="spinner" role="status" aria-label="Loading analyses..." />
            </div>
          ) : error ? (
            <div className="text-center py-12 text-red-600">
              <AlertCircle className="mx-auto h-12 w-12 mb-4" />
              <p>Failed to load analyses. <Button variant="ghost" size="sm" onClick={() => refetch()}>Retry</Button></p>
            </div>
          ) : analyses.length === 0 ? (
            <div className="text-center py-12">
              <FileCode className="mx-auto h-12 w-12 text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No analyses found</h3>
              <p className="text-gray-500 mb-4">Create your first analysis or adjust your filters</p>
              <Button onClick={() => navigate('/analyses/new')}>
                <Plus className="h-4 w-4" />
                New Analysis
              </Button>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-medium text-gray-500">Analysis</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-500 hidden md:table-cell">Type</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-500">Status</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-500 hidden lg:table-cell">Created</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-500 hidden lg:table-cell">Updated</th>
                      <th className="text-right py-3 px-4 font-medium text-gray-500">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analyses.map((analysis) => (
                      <tr key={analysis.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-4 px-4">
                          <div>
                            <p className="font-medium text-gray-900">{analysis.name}</p>
                            {analysis.description && (
                              <p className="text-sm text-gray-500 truncate max-w-xs">{analysis.description}</p>
                            )}
                            {analysis.target_path && (
                              <p className="text-xs text-gray-400 font-mono truncate max-w-xs mt-1">{analysis.target_path}</p>
                            )}
                          </div>
                        </td>
                        <td className="py-4 px-4 hidden md:table-cell">
                          <Badge variant={analysis.type === 'binary' ? 'primary' : analysis.type === 'javascript' ? 'warning' : 'success'}>
                            {ANALYSIS_TYPE_LABELS[analysis.type as AnalysisType]}
                          </Badge>
                        </td>
                        <td className="py-4 px-4">
                          <Badge variant={ANALYSIS_STATUS_COLORS[analysis.status as AnalysisStatus]}>
                            {ANALYSIS_STATUS_LABELS[analysis.status as AnalysisStatus]}
                          </Badge>
                        </td>
                        <td className="py-4 px-4 hidden lg:table-cell text-sm text-gray-500">
                          {formatDistanceToNow(new Date(analysis.created_at), { addSuffix: true })}
                        </td>
                        <td className="py-4 px-4 hidden lg:table-cell text-sm text-gray-500">
                          {formatDistanceToNow(new Date(analysis.updated_at), { addSuffix: true })}
                        </td>
                        <td className="py-4 px-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <a href={`/analyses/${analysis.id}`} className="text-blue-600 hover:text-blue-700 p-1.5 rounded hover:bg-blue-50" aria-label="View analysis">
                              <Eye className="h-4 w-4" />
                            </a>
                            <button
                              onClick={() => navigate(`/analyses/${analysis.id}/edit`)}
                              className="text-gray-600 hover:text-gray-900 p-1.5 rounded hover:bg-gray-100"
                              aria-label="Edit analysis"
                            >
                              <Edit2 className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => {
                                if (confirm('Delete this analysis?')) {
                                  deleteMutation.mutate(analysis.id);
                                }
                              }}
                              disabled={deleteMutation.isPending}
                              className="text-gray-600 hover:text-red-600 p-1.5 rounded hover:bg-gray-100"
                              aria-label="Delete analysis"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
                  <p className="text-sm text-gray-500">
                    Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} results
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setPage(page - 1)}
                      disabled={page === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm text-gray-600">Page {page} of {totalPages}</span>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setPage(page + 1)}
                      disabled={page === totalPages}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </Layout>
  );
}

// Need to import these icons
import { AlertCircle, RefreshCw } from 'lucide-react';