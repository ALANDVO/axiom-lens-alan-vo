/**
 * Axiom Lens - New Analysis page.
 */
import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Layout } from '../components/layout';
import { Card, CardHeader, CardTitle, CardContent, Button, Input } from '../components/ui';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthProvider';
import type { AnalysisCreate, AnalysisType } from '../types';
import { FileCode, Terminal, Cpu, ArrowLeft, Loader2 } from 'lucide-react';
import { ANALYSIS_TYPE_LABELS } from '../types';

const TYPE_CONFIG: Record<AnalysisType, { icon: React.ComponentType<{ className?: string }>; description: string; color: string }> = {
  binary: { icon: FileCode, description: 'Analyze native binaries (ELF, PE, Mach-O) for pseudocode, assembly, symbols, and calls', color: 'purple' },
  javascript: { icon: Terminal, description: 'Inspect JavaScript/Electron applications for modules, imports, IPC boundaries, and native addons', color: 'yellow' },
  process: { icon: Cpu, description: 'Capture and compare process behavior including terminal output, filesystem changes, and exit codes', color: 'green' },
};

export function NewAnalysis() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  
  const initialType = (searchParams.get('type') as AnalysisType) || 'binary';
  const [type, setType] = useState<AnalysisType>(initialType);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [targetPath, setTargetPath] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const createMutation = useMutation({
    mutationFn: (data: AnalysisCreate) => api.createAnalysis(data),
    onSuccess: (analysis) => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
      navigate(`/analyses/${analysis.id}`);
    },
  });

  const createWithUploadMutation = useMutation({
    mutationFn: ({ file, type, name, description }: { file: File; type: string; name: string; description?: string }) =>
      api.createAnalysisWithUpload(file, type as 'binary' | 'javascript' | 'process', name, description),
    onSuccess: (analysis) => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
      navigate(`/analyses/${analysis.id}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    
    if (file) {
      createWithUploadMutation.mutate({
        file,
        type,
        name: name.trim(),
        description: description.trim() || undefined,
      });
    } else {
      createMutation.mutate({
        type,
        name: name.trim(),
        description: description.trim() || undefined,
        target_path: targetPath.trim() || undefined,
      });
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      // Optionally set targetPath to the file name for display
      setTargetPath(e.target.files[0].name);
    }
  };

  const config = TYPE_CONFIG[type];

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

  return (
    <Layout>
      <div className="mb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate('/analyses')}>
          <ArrowLeft className="h-4 w-4" />
          Back to Analyses
        </Button>
      </div>

      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">New Analysis</h1>
          <p className="text-gray-600 mt-1">Create a new reverse engineering analysis</p>
        </div>

        {/* Type Selector */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Analysis Type</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              {(['binary', 'javascript', 'process'] as AnalysisType[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setType(t)}
                  className={clsx(
                    'relative p-4 rounded-lg border-2 transition-all text-left',
                    type === t
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  )}
                  aria-pressed={type === t}
                >
                  <div className={clsx('p-3 rounded-lg mb-3', 
                    t === 'binary' && 'bg-purple-100 text-purple-600',
                    t === 'javascript' && 'bg-yellow-100 text-yellow-600',
                    t === 'process' && 'bg-green-100 text-green-600'
                  )}>
                    <config.icon className="h-6 w-6" />
                  </div>
                  <h3 className="font-medium text-gray-900 mb-1">{ANALYSIS_TYPE_LABELS[t]}</h3>
                  <p className="text-sm text-gray-500">{TYPE_CONFIG[t].description}</p>
                  {type === t && (
                    <div className="absolute inset-0 border-2 border-blue-500 rounded-lg pointer-events-none" />
                  )}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Form */}
        <Card>
          <CardHeader>
            <CardTitle>{ANALYSIS_TYPE_LABELS[type]} Analysis Details</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <Input
                label="Analysis Name"
                placeholder="e.g., Notion Electron App Analysis"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                autoFocus
              />
              <Input
                label="Description (optional)"
                placeholder="Brief description of what you're analyzing"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Upload File (optional)
              </label>
              <input
                type="file"
                onChange={handleFileChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                accept={type === 'binary' ? '.exe,.bin,.elf,.so,.dll,.dylib,.mach-o' : type === 'javascript' ? '.js,.ts,.asar,.json' : '.exe,.bin'}
              />
              {file && (
                <p className="mt-1 text-sm text-gray-500">Selected: {file.name} ({Math.round(file.size / 1024)} KB)</p>
              )}
              <p className="mt-1 text-xs text-gray-400">
                Or enter a path manually below
              </p>
            </div>
            <Input
              label="Target Path (optional)"
              placeholder={type === 'binary' ? '/path/to/binary' : type === 'javascript' ? '/path/to/app.or.asar' : '/path/to/executable'}
              value={targetPath}
              onChange={(e) => setTargetPath(e.target.value)}
            />
            <div className="flex gap-4 pt-4">
              <Button
                type="submit"
                disabled={(createMutation.isPending || createWithUploadMutation.isPending) || !name.trim()}
              >
                {(createMutation.isPending || createWithUploadMutation.isPending) ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Analysis'
                )}
              </Button>
              <Button type="button" variant="secondary" onClick={() => navigate('/analyses')}>
                Cancel
              </Button>
            </div>
            </form>
          </CardContent>
        </Card>

        {/* Info */}
        <Card variant="outlined">
          <CardContent className="pt-6">
            <h3 className="font-medium text-gray-900 mb-3">What happens next?</h3>
            <ol className="space-y-2 text-sm text-gray-600 list-decimal list-inside">
              <li>The analysis will be created with <strong>pending</strong> status</li>
              <li>In a full implementation, the analysis engine would process the target</li>
              <li>Results including pseudocode, symbols, call graphs, or process traces would appear here</li>
              <li>You can view, export, and share the analysis results</li>
            </ol>
            <p className="mt-4 text-sm text-gray-500">
              <strong>Note:</strong> This is the core skeleton implementation. The actual analysis engines 
              (Hopper, Ghidra, JADX, etc.) would be integrated in future rounds.
            </p>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}

import { clsx } from 'clsx';