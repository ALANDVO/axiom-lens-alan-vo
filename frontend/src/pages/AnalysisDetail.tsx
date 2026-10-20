/**
 * Axiom Lens - Analysis detail page.
 */
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Layout } from '../components/layout';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button, Input } from '../components/ui';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthProvider';
import type { Analysis, AnalysisUpdate } from '../types';
import { 
  FileCode, Terminal, Cpu, AlertCircle, 
  ArrowLeft, Download, Copy, Edit2, Trash2, ExternalLink 
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
import { ANALYSIS_TYPE_LABELS, ANALYSIS_STATUS_LABELS, ANALYSIS_STATUS_COLORS, type AnalysisType, type AnalysisStatus } from '../types';
import { clsx } from 'clsx';
import { useState } from 'react';

export function AnalysisDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({ name: '', description: '' });

  const { data: analysis, isLoading, error, refetch } = useQuery<Analysis>({
    queryKey: ['analysis', id],
    queryFn: () => api.getAnalysis(id!),
    enabled: isAuthenticated && !!id,
  });

  const updateMutation = useMutation({
    mutationFn: (data: AnalysisUpdate) => api.updateAnalysis(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis', id] });
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
      setEditing(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteAnalysis(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
      navigate('/analyses');
    },
  });

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
          <Button onClick={() => navigate('/api/v1/auth/login')}>Sign In</Button>
        </div>
      </Layout>
    );
  }

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="spinner" role="status" aria-label="Loading analysis..." />
        </div>
      </Layout>
    );
  }

  if (error || !analysis) {
    return (
      <Layout>
        <div className="max-w-2xl mx-auto text-center py-16">
          <AlertCircle className="mx-auto h-12 w-12 text-red-600 mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Analysis Not Found</h1>
          <p className="text-gray-600 mb-6">The requested analysis could not be found.</p>
          <Button onClick={() => navigate('/analyses')}>Back to Analyses</Button>
        </div>
      </Layout>
    );
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate({ name: editForm.name, description: editForm.description });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // Could show toast here
  };
  return (
    <Layout>
      <div className="mb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate('/analyses')}>
          <ArrowLeft className="h-4 w-4" />
          Back to Analyses
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Header */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className={clsx(
                    'p-3 rounded-lg',
                    analysis.type === 'binary' && 'bg-purple-100 text-purple-600',
                    analysis.type === 'javascript' && 'bg-yellow-100 text-yellow-600',
                    analysis.type === 'process' && 'bg-green-100 text-green-600'
                  )}>
                    {analysis.type === 'binary' && <FileCode className="h-6 w-6" />}
                    {analysis.type === 'javascript' && <Terminal className="h-6 w-6" />}
                    {analysis.type === 'process' && <Cpu className="h-6 w-6" />}
                  </div>
                  <div>
                    {editing ? (
                      <form onSubmit={handleSubmit} className="flex flex-col gap-2 w-full sm:w-96">
                        <Input
                          value={editForm.name}
                          onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                          placeholder="Analysis name"
                          required
                        />
                        <Input
                          value={editForm.description}
                          onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                          placeholder="Description (optional)"
                        />
                        <div className="flex gap-2">
                          <Button type="submit" size="sm" disabled={updateMutation.isPending}>
                            Save
                          </Button>
                          <Button type="button" variant="secondary" size="sm" onClick={() => {
                            setEditForm({ name: analysis.name, description: analysis.description || '' });
                            setEditing(false);
                          }}>
                            Cancel
                          </Button>
                        </div>
                      </form>
                    ) : (
                      <>
                        <h1 className="text-2xl font-bold text-gray-900">{analysis.name}</h1>
                        {analysis.description && (
                          <p className="text-gray-600 mt-1">{analysis.description}</p>
                        )}
                      </>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={ANALYSIS_STATUS_COLORS[analysis.status as AnalysisStatus]}>
                    {ANALYSIS_STATUS_LABELS[analysis.status as AnalysisStatus]}
                  </Badge>
                  {!editing && (
                    <>
                      <Button variant="ghost" size="sm" onClick={() => { setEditForm({ name: analysis.name, description: analysis.description || '' }); setEditing(true); }}>
                        <Edit2 className="h-4 w-4" />
                        Edit
                      </Button>
                      <Button variant="danger" size="sm" onClick={() => {
                        if (confirm('Delete this analysis? This cannot be undone.')) {
                          deleteMutation.mutate();
                        }
                      }}>
                        <Trash2 className="h-4 w-4" />
                        Delete
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Details */}
          <Card>
            <CardHeader>
              <CardTitle>Details</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm text-gray-500">Type</dt>
                  <dd className="mt-1 font-medium">
                    <Badge variant={analysis.type === 'binary' ? 'primary' : analysis.type === 'javascript' ? 'warning' : 'success'}>
                      {ANALYSIS_TYPE_LABELS[analysis.type as AnalysisType]}
                    </Badge>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Status</dt>
                  <dd className="mt-1 font-medium">
                    <Badge variant={ANALYSIS_STATUS_COLORS[analysis.status as AnalysisStatus]}>
                      {ANALYSIS_STATUS_LABELS[analysis.status as AnalysisStatus]}
                    </Badge>
                  </dd>
                </div>
                {analysis.target_path && (
                  <div className="sm:col-span-2">
                    <dt className="text-sm text-gray-500">Target Path</dt>
                    <dd className="mt-1 font-mono text-sm text-gray-900 break-all">{analysis.target_path}</dd>
                  </div>
                )}
                {analysis.target_hash && (
                  <div className="sm:col-span-2">
                    <dt className="text-sm text-gray-500">Target Hash (SHA-256)</dt>
                    <dd className="mt-1 flex items-center gap-2">
                      <code className="font-mono text-sm text-gray-900 bg-gray-100 px-2 py-1 rounded">{analysis.target_hash}</code>
                      <Button variant="ghost" size="sm" onClick={() => copyToClipboard(analysis.target_hash!)}>
                        <Copy className="h-4 w-4" />
                      </Button>
                    </dd>
                  </div>
                )}
                <div>
                  <dt className="text-sm text-gray-500">Created</dt>
                  <dd className="mt-1 font-medium">
                    {format(new Date(analysis.created_at), 'PPp')} ({formatDistanceToNow(new Date(analysis.created_at), { addSuffix: true })})
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Updated</dt>
                  <dd className="mt-1 font-medium">
                    {format(new Date(analysis.updated_at), 'PPp')} ({formatDistanceToNow(new Date(analysis.updated_at), { addSuffix: true })})
                  </dd>
                </div>
                {analysis.completed_at && (
                  <div>
                    <dt className="text-sm text-gray-500">Completed</dt>
                    <dd className="mt-1 font-medium">
                      {format(new Date(analysis.completed_at), 'PPp')} ({formatDistanceToNow(new Date(analysis.completed_at), { addSuffix: true })})
                    </dd>
                  </div>
                )}
              </dl>
            </CardContent>
          </Card>

          {/* Results */}
          {analysis.result && (
            <Card>
              <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <CardTitle>Results</CardTitle>
                <Button variant="secondary" size="sm" onClick={() => {
                  const blob = new Blob([JSON.stringify(analysis.result, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `${analysis.name}-results.json`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}>
                  <Download className="h-4 w-4" />
                  Export JSON
                </Button>
              </CardHeader>
              <CardContent>
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm max-h-96">
                  <code>{JSON.stringify(analysis.result, null, 2)}</code>
                </pre>
              </CardContent>
            </Card>
          )}

          {/* Error */}
          {analysis.error && (
            <Card className="border-red-200">
              <CardHeader>
                <CardTitle className="text-red-600 flex items-center gap-2">
                  <AlertCircle className="h-5 w-5" />
                  Error
                </CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="bg-red-50 text-red-900 p-4 rounded-lg overflow-x-auto text-sm">
                  <code>{analysis.error}</code>
                </pre>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button className="w-full justify-start" onClick={() => refetch()}>
                <ExternalLink className="h-4 w-4" />
                Refresh
              </Button>
              {analysis.result && (
                <Button variant="secondary" className="w-full justify-start" onClick={() => {
                  const blob = new Blob([JSON.stringify(analysis.result, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `${analysis.name}-results.json`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}>
                  <Download className="h-4 w-4" />
                  Export Results
                </Button>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <p className="text-gray-600">
                This analysis was created on <strong>{format(new Date(analysis.created_at), 'PP')}</strong>.
              </p>
              {analysis.status === 'pending' && (
                <p className="text-yellow-600">Analysis is queued and will start soon.</p>
              )}
              {analysis.status === 'running' && (
                <p className="text-blue-600">Analysis is currently running.</p>
              )}
              {analysis.status === 'completed' && (
                <p className="text-green-600">Analysis completed successfully.</p>
              )}
              {analysis.status === 'failed' && (
                <p className="text-red-600">Analysis failed. Check the error details above.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}