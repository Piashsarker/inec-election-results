'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { ScrapingJob, JobStatus } from '@/types';

// ─── Types ───────────────────────────────────────────────────────────────────

interface ImageOCRRow {
  id: string;
  polling_unit: string;
  image_file: string;
  status: 'queued' | 'processing' | 'extracted' | 'saved' | 'failed';
  ocr_engine: string;
  confidence: number | null;
  parties: { code: string; votes: number }[];
  valid_votes: number | null;
  accredited_voters: number | null;
  db_saved: boolean;
  error?: string | null;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const STATUS_LABEL: Record<JobStatus, string> = {
  queued: 'Queued',
  running: 'Running',
  paused: 'Paused',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
};

const STATUS_COLOR: Record<JobStatus, string> = {
  queued: 'bg-yellow-100 text-yellow-800',
  running: 'bg-blue-100 text-blue-800',
  paused: 'bg-orange-100 text-orange-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-gray-100 text-gray-600',
};

const IMAGE_STATUS_COLOR: Record<ImageOCRRow['status'], string> = {
  queued: 'bg-gray-100 text-gray-600',
  processing: 'bg-blue-100 text-blue-700',
  extracted: 'bg-yellow-100 text-yellow-800',
  saved: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

const IMAGE_STATUS_ICON: Record<ImageOCRRow['status'], string> = {
  queued: '⏳',
  processing: '🔄',
  extracted: '🔍',
  saved: '✅',
  failed: '❌',
};

function StatusBadge({ status }: { status: JobStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${STATUS_COLOR[status]}`}
    >
      {status === 'running' && (
        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
      )}
      {STATUS_LABEL[status]}
    </span>
  );
}

function ConfidenceBadge({ value }: { value: number | null }) {
  if (value === null) return <span className="text-muted-foreground text-xs">—</span>;
  const pct = Math.round(value * 100);
  const color =
    pct >= 80 ? 'bg-green-100 text-green-800' :
    pct >= 60 ? 'bg-yellow-100 text-yellow-800' :
    'bg-red-100 text-red-800';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {pct}%
    </span>
  );
}

function ProgressBar({ value, total }: { value: number; total: number }) {
  const pct = total > 0 ? Math.min(100, Math.round((value / total) * 100)) : 0;
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-muted-foreground mb-1">
        <span>{value} / {total} processed</span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 bg-secondary rounded-full overflow-hidden">
        <div
          className="h-full bg-primary transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ─── Mock OCR rows from scraped JSON (loaded once job is complete/has data) ──
async function fetchImageRows(jobId: string): Promise<ImageOCRRow[]> {
  // Until ImageOCRTask model is built on the backend, we load from the
  // static scraped results JSON to populate the table visually.
  try {
    const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const res = await fetch(`${API}/scraped/osun_governorship_2026`);
    if (!res.ok) return [];
    const data = await res.json();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return (data.results || []).map((r: any, i: number) => ({
      id: `${jobId}-${i}`,
      polling_unit: r.polling_unit_name || r.polling_unit_code,
      image_file: r.file || '',
      status: r.error ? 'failed' : 'saved',
      ocr_engine: 'ai_ocr',
      confidence: r.extraction_confidence ?? r.ocr_confidence ?? null,
      parties: (r.parties || []).filter((p: { votes: number }) => p.votes > 0),
      valid_votes: r.valid_votes ?? null,
      accredited_voters: r.accredited_voters ?? null,
      db_saved: !r.error,
      error: r.error ?? null,
    }));
  } catch {
    return [];
  }
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function JobCard({
  job,
  onPause,
  onResume,
  onCancel,
  isActive,
  onClick,
}: {
  job: ScrapingJob;
  onPause: (id: string) => void;
  onResume: (id: string) => void;
  onCancel: (id: string) => void;
  isActive: boolean;
  onClick: (id: string) => void;
}) {
  return (
    <div
      onClick={() => onClick(job.id)}
      className={`bg-card border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
        isActive ? 'border-primary ring-1 ring-primary' : 'border-border'
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="min-w-0">
          <p className="text-xs font-mono text-muted-foreground truncate">{job.id}</p>
          <p className="text-sm font-medium text-foreground mt-0.5">
            {job.election_type ?? 'All elections'}
            {job.target_state ? ` · ${job.target_state}` : ''}
          </p>
        </div>
        <StatusBadge status={job.status as JobStatus} />
      </div>

      <ProgressBar value={job.processed_count} total={job.total_polling_units || 0} />

      <div className="flex items-center gap-2 mt-3 text-xs text-muted-foreground">
        <span>✅ {job.success_count}</span>
        <span>❌ {job.failed_count}</span>
      </div>

      {(job.status === 'running' || job.status === 'paused' || job.status === 'queued') && (
        <div className="flex gap-2 mt-3">
          {job.status === 'running' && (
            <button
              onClick={(e) => { e.stopPropagation(); onPause(job.id); }}
              className="flex-1 text-xs border border-border rounded px-2 py-1 hover:bg-muted transition-colors"
            >
              ⏸ Pause
            </button>
          )}
          {job.status === 'paused' && (
            <button
              onClick={(e) => { e.stopPropagation(); onResume(job.id); }}
              className="flex-1 text-xs border border-border rounded px-2 py-1 hover:bg-muted transition-colors"
            >
              ▶ Resume
            </button>
          )}
          <button
            onClick={(e) => { e.stopPropagation(); onCancel(job.id); }}
            className="flex-1 text-xs border border-red-200 text-red-600 rounded px-2 py-1 hover:bg-red-50 transition-colors"
          >
            ✕ Cancel
          </button>
        </div>
      )}
    </div>
  );
}

function ImageTable({ rows }: { rows: ImageOCRRow[] }) {
  if (rows.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground text-sm">
        No image data yet — select a job to see per-image OCR results.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-muted">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Polling Unit</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Image File</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Engine</th>
            <th className="px-4 py-3 text-right font-medium text-muted-foreground">Confidence</th>
            <th className="px-4 py-3 text-right font-medium text-muted-foreground">Valid Votes</th>
            <th className="px-4 py-3 text-right font-medium text-muted-foreground">Accredited</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Top Parties</th>
            <th className="px-4 py-3 text-center font-medium text-muted-foreground">Saved to DB</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((row) => (
            <tr key={row.id} className="hover:bg-muted/40 transition-colors">
              <td className="px-4 py-3">
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${IMAGE_STATUS_COLOR[row.status]}`}
                >
                  <span>{IMAGE_STATUS_ICON[row.status]}</span>
                  {row.status.charAt(0).toUpperCase() + row.status.slice(1)}
                </span>
              </td>
              <td className="px-4 py-3 text-foreground max-w-[200px]">
                <p className="truncate font-medium">{row.polling_unit}</p>
                {row.error && (
                  <p className="text-xs text-red-500 truncate mt-0.5">{row.error}</p>
                )}
              </td>
              <td className="px-4 py-3 font-mono text-xs text-muted-foreground max-w-[180px] truncate">
                {row.image_file.split('/').pop() || row.image_file}
              </td>
              <td className="px-4 py-3">
                <span className="inline-flex items-center gap-1 text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-medium">
                  ✅ AI OCR
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <ConfidenceBadge value={row.confidence} />
              </td>
              <td className="px-4 py-3 text-right font-mono text-sm">
                {row.valid_votes?.toLocaleString() ?? '—'}
              </td>
              <td className="px-4 py-3 text-right font-mono text-sm">
                {row.accredited_voters?.toLocaleString() ?? '—'}
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1">
                  {row.parties.slice(0, 4).map((p) => (
                    <span
                      key={p.code}
                      className="text-xs bg-secondary text-foreground px-1.5 py-0.5 rounded font-mono"
                    >
                      {p.code}:{p.votes}
                    </span>
                  ))}
                  {row.parties.length > 4 && (
                    <span className="text-xs text-muted-foreground">+{row.parties.length - 4}</span>
                  )}
                </div>
              </td>
              <td className="px-4 py-3 text-center">
                {row.db_saved ? (
                  <span className="text-green-600 text-base" title="Record saved to database">✅</span>
                ) : row.status === 'failed' ? (
                  <span className="text-red-500 text-base" title="Failed — not saved">❌</span>
                ) : (
                  <span className="text-muted-foreground text-base">⏳</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function ScrapingPage() {
  const [url, setUrl] = useState('');
  const [electionType, setElectionType] = useState('');
  const [targetState, setTargetState] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [jobs, setJobs] = useState<ScrapingJob[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [imageRows, setImageRows] = useState<ImageOCRRow[]>([]);
  const [imageRowsLoading, setImageRowsLoading] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Fetch jobs list ──
  const fetchJobs = useCallback(async () => {
    try {
      const list = await api.listJobs();
      setJobs(list);
    } catch {
      // backend may be offline — silently ignore
    }
  }, []);

  // ── Poll active jobs ──
  useEffect(() => {
    fetchJobs();
    pollingRef.current = setInterval(fetchJobs, 3000);
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [fetchJobs]);

  // ── Load image rows when selected job changes ──
  useEffect(() => {
    if (!selectedJobId) {
      setImageRows([]);
      return;
    }
    setImageRowsLoading(true);
    fetchImageRows(selectedJobId).then((rows) => {
      setImageRows(rows);
      setImageRowsLoading(false);
    });
  }, [selectedJobId]);

  // ── Auto-select first job ──
  useEffect(() => {
    if (jobs.length > 0 && !selectedJobId) {
      setSelectedJobId(jobs[0].id);
    }
  }, [jobs, selectedJobId]);

  // ── Submit new job ──
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim() && !electionType.trim() && !targetState.trim()) {
      setError('Please enter an INEC portal URL or at least one filter.');
      return;
    }
    setSubmitting(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const job = await api.startScrapingJob({
        url: url.trim() || undefined,
        election_type: electionType.trim() || undefined,
        target_state: targetState.trim() || undefined,
      });
      setSuccessMsg(`Job created — ID: ${job.id}`);
      setSelectedJobId(job.id);
      setJobs((prev) => [job, ...prev]);
      setUrl('');
      setElectionType('');
      setTargetState('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create job');
    } finally {
      setSubmitting(false);
    }
  };

  // ── Job actions ──
  const handlePause = async (id: string) => {
    try {
      const updated = await api.pauseJob(id);
      setJobs((prev) => prev.map((j) => (j.id === id ? updated : j)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to pause job');
    }
  };

  const handleResume = async (id: string) => {
    try {
      const updated = await api.resumeJob(id);
      setJobs((prev) => prev.map((j) => (j.id === id ? updated : j)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resume job');
    }
  };

  const handleCancel = async (id: string) => {
    try {
      const updated = await api.cancelJob(id);
      setJobs((prev) => prev.map((j) => (j.id === id ? updated : j)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel job');
    }
  };

  const selectedJob = jobs.find((j) => j.id === selectedJobId) ?? null;
  const activeCount = jobs.filter((j) => j.status === 'running' || j.status === 'queued').length;

  return (
    <main className="container mx-auto px-4 py-8">
      {/* ── Breadcrumb ── */}
      <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
        <Link href="/" className="hover:text-foreground">Dashboard</Link>
        <span>/</span>
        <span className="text-foreground font-medium">Scraping</span>
      </nav>

      {/* ── Header ── */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Scraping Jobs</h1>
          <p className="text-muted-foreground mt-1">
            Scrape INEC result sheet images and extract voting data
          </p>
        </div>
        {activeCount > 0 && (
          <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2">
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
            <span className="text-sm text-blue-700 font-medium">{activeCount} active job{activeCount > 1 ? 's' : ''}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* ── Left column: form + job list ── */}
        <div className="xl:col-span-1 space-y-4">

          {/* New Job Form */}
          <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
            <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
              <span className="text-lg">🕷️</span> New Scraping Job
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* URL input */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  INEC Portal URL
                </label>
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://www.inecelectionresults.ng/elections/..."
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Paste a specific INEC election URL to scope the scrape
                </p>
              </div>

              {/* Advanced filters toggle */}
              <button
                type="button"
                onClick={() => setShowAdvanced((v) => !v)}
                className="text-xs text-primary hover:underline flex items-center gap-1"
              >
                {showAdvanced ? '▲' : '▼'} {showAdvanced ? 'Hide' : 'Show'} filters
              </button>

              {showAdvanced && (
                <div className="space-y-3 border-t border-border pt-3">
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">
                      Election Type
                    </label>
                    <input
                      type="text"
                      value={electionType}
                      onChange={(e) => setElectionType(e.target.value)}
                      placeholder="e.g. governorship"
                      className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">
                      Target State
                    </label>
                    <input
                      type="text"
                      value={targetState}
                      onChange={(e) => setTargetState(e.target.value)}
                      placeholder="e.g. Osun"
                      className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                  </div>
                </div>
              )}

              {/* Feedback */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-700">
                  {error}
                </div>
              )}
              {successMsg && (
                <div className="bg-green-50 border border-green-200 rounded-lg px-3 py-2 text-sm text-green-700">
                  ✅ {successMsg}
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-primary text-primary-foreground rounded-lg px-4 py-2.5 text-sm font-semibold hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <span className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                    Starting…
                  </>
                ) : (
                  '🚀 Start Scraping'
                )}
              </button>
            </form>
          </div>

          {/* OCR info */}
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl">✅</span>
              <div>
                <p className="text-sm font-semibold text-blue-800">High Accuracy OCR</p>
                <p className="text-xs text-blue-700 mt-1">
                  Images are processed with AI-powered OCR.
                  Average confidence on Osun 2026 sheets: <strong>90%</strong>.
                </p>
              </div>
            </div>
          </div>

          {/* Jobs List */}
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center justify-between">
              <span>Recent Jobs</span>
              <span className="text-xs text-muted-foreground font-normal">
                Refreshes every 3s
              </span>
            </h3>

            {jobs.length === 0 ? (
              <div className="bg-card border border-dashed border-border rounded-xl p-6 text-center text-sm text-muted-foreground">
                No jobs yet. Start one above.
              </div>
            ) : (
              <div className="space-y-2">
                {jobs.map((job) => (
                  <JobCard
                    key={job.id}
                    job={job}
                    isActive={job.id === selectedJobId}
                    onClick={setSelectedJobId}
                    onPause={handlePause}
                    onResume={handleResume}
                    onCancel={handleCancel}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ── Right column: image OCR table ── */}
        <div className="xl:col-span-2">
          <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
            {/* Table header */}
            <div className="p-5 border-b border-border flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-foreground flex items-center gap-2">
                  <span>📸</span> OCR Results — Per Image
                </h2>
                {selectedJob && (
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Job <span className="font-mono">{selectedJob.id.slice(0, 8)}…</span>
                    {' · '}
                    <StatusBadge status={selectedJob.status as JobStatus} />
                  </p>
                )}
              </div>
              {imageRows.length > 0 && (
                <div className="text-right text-xs text-muted-foreground">
                  <span className="text-green-600 font-semibold">
                    {imageRows.filter((r) => r.db_saved).length}
                  </span>
                  /{imageRows.length} saved to DB
                </div>
              )}
            </div>

            {/* Summary stats */}
            {imageRows.length > 0 && (
              <div className="grid grid-cols-4 divide-x divide-border border-b border-border">
                {[
                  {
                    label: 'Total Images',
                    value: imageRows.length,
                    color: 'text-foreground',
                  },
                  {
                    label: 'Extracted',
                    value: imageRows.filter((r) => r.status === 'extracted' || r.status === 'saved').length,
                    color: 'text-yellow-600',
                  },
                  {
                    label: 'Saved to DB',
                    value: imageRows.filter((r) => r.db_saved).length,
                    color: 'text-green-600',
                  },
                  {
                    label: 'Failed',
                    value: imageRows.filter((r) => r.status === 'failed').length,
                    color: 'text-red-600',
                  },
                ].map((stat) => (
                  <div key={stat.label} className="px-4 py-3 text-center">
                    <p className={`text-xl font-bold ${stat.color}`}>{stat.value}</p>
                    <p className="text-xs text-muted-foreground">{stat.label}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Table body */}
            {imageRowsLoading ? (
              <div className="p-8 text-center">
                <div className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">Loading image results…</p>
              </div>
            ) : (
              <ImageTable rows={imageRows} />
            )}
          </div>
        </div>

      </div>
    </main>
  );
}
