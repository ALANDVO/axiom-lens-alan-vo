/**
 * Axiom Lens - Dashboard page.
 */
import { useQuery } from '@tanstack/react-query';
import { Layout } from '../components/layout';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from '../components/ui';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthProvider';
import { 
  FileCode, Terminal, Cpu, CheckCircle, Plus, ExternalLink, ChevronRight 
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { clsx } from 'clsx';
import { ANALYSIS_TYPE_LABELS, ANALYSIS_STATUS_LABELS, ANALYSIS_STATUS_COLORS, type AnalysisType, type AnalysisStatus } from '../types';

export function Dashboard() {
  const { isAuthenticated, isLoading: authLoading, login } = useAuth();
  
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 30000,
  });

  const { data: analyses, isLoading: analysesLoading } = useQuery({
    queryKey: ['analyses', 'dashboard'],
    queryFn: () => api.listAnalyses({ page: 1, page_size: 10 }),
    enabled: isAuthenticated,
  });

  const stats = analyses?.items.reduce(
    (acc, analysis) => {
      acc.total++;
      if (analysis.status === 'completed') acc.completed++;
      else if (analysis.status === 'failed') acc.failed++;
      else if (analysis.status === 'running') acc.running++;
      else acc.pending++;
      return acc;
    },
    { total: 0, completed: 0, failed: 0, running: 0, pending: 0 }
  ) || { total: 0, completed: 0, failed: 0, running: 0, pending: 0 };

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
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Welcome to Axiom Lens</h1>
          <p className="text-gray-600 mb-8 max-w-lg mx-auto">
            AI-assisted reverse engineering analysis platform for binaries, JavaScript/Electron applications, and process behavior.
          </p>
          <Button onClick={login} size="lg" className="w-auto">
            Sign In
          </Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Overview of your analyses and system health</p>
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="System Health"
          value={health?.status === 'healthy' ? 1 : 0}
          icon={CheckCircle}
          color={health?.status === 'healthy' ? 'green' : 'red'}
        />
        <StatCard
          title="Version"
          value={1}
          icon={ExternalLink}
          color="blue"
        />
        <StatCard
          title="Total Analyses"
          value={stats.total}
          icon={FileCode}
          color="purple"
        />
        <StatCard
          title="Completed"
          value={stats.completed}
          icon={CheckCircle}
          color="green"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        <ActionCard
          title="Binary Analysis"
          description="Analyze ELF, PE, Mach-O binaries with Ghidra, IDA, or Hopper"
          icon={FileCode}
          href="/analyses/new?type=binary"
          color="purple"
        />
        <ActionCard
          title="Process Comparison"
          description="Capture and compare process executions for behavioral differences"
          icon={Terminal}
          href="/analyses/new?type=process"
          color="green"
        />
        <ActionCard
          title="JavaScript Analysis"
          description="Analyze Electron apps, ASAR archives, and Node.js applications"
          icon={Cpu}
          href="/analyses/new?type=javascript"
          color="yellow"
        />
      </div>

      {/* Recent Analyses */}
      <Card>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <CardTitle>Recent Analyses</CardTitle>
          <a href="/analyses" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            View All <ChevronRight className="h-4 w-4 inline" />
          </a>
        </CardHeader>
        <CardContent>
          {analysesLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="spinner" role="status" aria-label="Loading analyses..." />
            </div>
          ) : analyses?.items.length === 0 ? (
            <div className="text-center py-12">
              <FileCode className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No analyses yet</h3>
              <p className="text-gray-600 mb-6">Get started by creating your first analysis</p>
              <Button onClick={() => window.location.href = '/analyses/new'}>
                <Plus className="h-4 w-4 mr-2" />
                New Analysis
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Analysis</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-500 hidden md:table-cell">Type</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Status</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-500 hidden lg:table-cell">Updated</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-500">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {(analyses?.items || []).map((analysis) => (
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
                        {formatDistanceToNow(new Date(analysis.updated_at), { addSuffix: true })}
                      </td>
                      <td className="py-4 px-4 text-right">
                        <a
                          href={`/analyses/${analysis.id}`}
                          className="text-blue-600 hover:text-blue-700 font-medium text-sm flex items-center gap-1 justify-end"
                        >
                          View <ChevronRight className="h-4 w-4" />
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </Layout>
  );
}

function StatCard({ title, value, icon: Icon, color }: { title: string; value: number; icon: React.ComponentType<{ className?: string }>; color: string }) {
  const colors = {
    purple: 'bg-purple-100 text-purple-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    green: 'bg-green-100 text-green-600',
    blue: 'bg-blue-100 text-blue-600',
    red: 'bg-red-100 text-red-600',
  };

  return (
    <Card>
      <CardContent className="flex items-center gap-4">
        <div className={clsx('p-3 rounded-lg', colors[color as keyof typeof colors] || colors.blue)}>
          <Icon className="h-6 w-6" aria-hidden="true" />
        </div>
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function ActionCard({ title, description, icon: Icon, href, color }: { title: string; description: string; icon: React.ComponentType<{ className?: string }>; href: string; color: string }) {
  const colors = {
    purple: 'bg-purple-100 text-purple-600 hover:bg-purple-200',
    yellow: 'bg-yellow-100 text-yellow-600 hover:bg-yellow-200',
    green: 'bg-green-100 text-green-600 hover:bg-green-200',
    blue: 'bg-blue-100 text-blue-600 hover:bg-blue-200',
    red: 'bg-red-100 text-red-600 hover:bg-red-200',
  };

  return (
    <a href={href} className="block">
      <Card className={clsx('transition-all hover:shadow-md', colors[color as keyof typeof colors] || colors.blue)}>
        <CardContent className="flex items-start gap-4">
          <div className="p-3 rounded-lg">
            <Icon className="h-6 w-6" aria-hidden="true" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900">{title}</h3>
            <p className="text-sm text-gray-600 mt-1">{description}</p>
          </div>
          <ExternalLink className="h-5 w-5 text-gray-400 shrink-0 mt-1" aria-hidden="true" />
        </CardContent>
      </Card>
    </a>
  );
}
