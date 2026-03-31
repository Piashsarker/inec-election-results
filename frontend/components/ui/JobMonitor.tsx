'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { ScrapingJob, JobStatus } from '@/types';

interface JobMonitorProps {
  jobId?: string;
  onJobComplete?: (job: ScrapingJob) => void;
  refreshInterval?: number;
}

const statusColors: Record<JobStatus, string> = {
  queued: 'bg-gray-500',
  running: 'bg-blue-500',
  paused: 'bg-yellow-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
  cancelled: 'bg-gray-400',
};

const statusIcons: Record<JobStatus, string> = {
  queued: '⏳',
  running: '🔄',
  paused: '⏸️',
  completed: '✅',
  failed: '❌',
  cancelled: '🚫',
};

function JobCard({ job, onPause, onResume, onCancel }: {
  job: ScrapingJob;
  onPause: () => void;
  onResume: () => void;
  onCancel: () => void;
}) {
  const progress = job.totalPollingUnits > 0
    ? (job.processedCount / job.totalPollingUnits) * 100
    : 0;

  const isActive = job.status === 'running' || job.status === 'paused';

  return (
    <div className="bg-card rounded-lg border border-border p-4 shadow-sm">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xl">{statusIcons[job.status]}</span>
            <h3 className="font-semibold text-foreground">Job {job.id.slice(0, 8)}</h3>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            {job.electionType && <span className="capitalize">{job.electionType.replace(/_/g, ' ')}</span>}
            {job.targetState && <span> • {job.targetState}</span>}
            {job.targetLga && <span> • {job.targetLga}</span>}
          </p>
        </div>
        <span className={`px-2 py-1 rounded text-xs font-medium text-white ${statusColors[job.status]}`}>
          {job.status.toUpperCase()}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex justify-between text-sm text-muted-foreground mb-1">
          <span>Progress</span>
          <span>{progress.toFixed(1)}%</span>
        </div>
        <div className="h-2 bg-secondary rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${
              job.status === 'running' ? 'bg-primary animate-pulse' : 'bg-primary'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 mb-3 text-center">
        <div className="bg-secondary/50 rounded p-2">
          <p className="text-xs text-muted-foreground">Processed</p>
          <p className="font-semibold text-foreground">{job.processedCount.toLocaleString()}</p>
        </div>
        <div className="bg-green-100 rounded p-2">
          <p className="text-xs text-green-700">Success</p>
          <p className="font-semibold text-green-700">{job.successCount.toLocaleString()}</p>
        </div>
        <div className="bg-red-100 rounded p-2">
          <p className="text-xs text-red-700">Failed</p>
          <p className="font-semibold text-red-700">{job.failedCount.toLocaleString()}</p>
        </div>
      </div>

      {/* Timestamps */}
      <div className="text-xs text-muted-foreground mb-3">
        <p>Created: {new Date(job.createdAt).toLocaleString()}</p>
        {job.startedAt && <p>Started: {new Date(job.startedAt).toLocaleString()}</p>}
        {job.completedAt && <p>Completed: {new Date(job.completedAt).toLocaleString()}</p>}
      </div>

      {/* Controls */}
      {isActive && (
        <div className="flex space-x-2">
          {job.status === 'running' ? (
            <button
              onClick={onPause}
              className="flex-1 px-3 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors text-sm font-medium"
            >
              ⏸️ Pause
            </button>
          ) : (
            <button
              onClick={onResume}
              className="flex-1 px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-sm font-medium"
            >
              ▶️ Resume
            </button>
          )}
          <button
            onClick={onCancel}
            className="flex-1 px-3 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 transition-colors text-sm font-medium"
          >
            🚫 Cancel
          </button>
        </div>
      )}
    </div>
  );
}

export function JobMonitor({ jobId, onJobComplete, refreshInterval = 5000 }: JobMonitorProps) {
  const [job, setJob] = useState<ScrapingJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchJobStatus = useCallback(async () => {
    if (!jobId) {
      setLoading(false);
      return;
    }

    try {
      const data = await api.getJobStatus(jobId);
      const jobData = data as ScrapingJob;
      setJob(jobData);
      setError(null);

      if (jobData.status === 'completed' || jobData.status === 'failed' || jobData.status === 'cancelled') {
        onJobComplete?.(jobData);
      }
    } catch (err) {
      setError('Failed to fetch job status');
      // Use sample data for development
      setJob({
        id: jobId,
        status: 'running',
        electionType: 'presidential',
        targetState: 'Lagos',
        totalPollingUnits: 1000,
        processedCount: 450,
        successCount: 440,
        failedCount: 10,
        createdAt: new Date(Date.now() - 3600000),
        startedAt: new Date(Date.now() - 3500000),
      });
    } finally {
      setLoading(false);
    }
  }, [jobId, onJobComplete]);

  useEffect(() => {
    fetchJobStatus();

    // Set up polling for active jobs
    const interval = setInterval(() => {
      if (job && (job.status === 'running' || job.status === 'paused')) {
        fetchJobStatus();
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [fetchJobStatus, job, refreshInterval]);

  const handlePause = async () => {
    if (!jobId) return;
    try {
      await api.pauseJob(jobId);
      fetchJobStatus();
    } catch (err) {
      setError('Failed to pause job');
    }
  };

  const handleResume = async () => {
    if (!jobId) return;
    try {
      await api.resumeJob(jobId);
      fetchJobStatus();
    } catch (err) {
      setError('Failed to resume job');
    }
  };

  const handleCancel = async () => {
    if (!jobId) return;
    if (!confirm('Are you sure you want to cancel this job?')) return;
    try {
      await api.cancelJob(jobId);
      fetchJobStatus();
    } catch (err) {
      setError('Failed to cancel job');
    }
  };

  if (loading) {
    return (
      <div className="bg-card rounded-lg border border-border p-6">
        <p className="text-muted-foreground text-center">Loading job status...</p>
      </div>
    );
  }

  if (!jobId) {
    return (
      <div className="bg-card rounded-lg border border-border p-6">
        <p className="text-muted-foreground text-center">No job selected</p>
      </div>
    );
  }

  if (error && !job) {
    return (
      <div className="bg-card rounded-lg border border-border p-6">
        <p className="text-destructive text-center">{error}</p>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="bg-card rounded-lg border border-border p-6">
        <p className="text-muted-foreground text-center">Job not found</p>
      </div>
    );
  }

  return (
    <JobCard
      job={job}
      onPause={handlePause}
      onResume={handleResume}
      onCancel={handleCancel}
    />
  );
}

export default JobMonitor;
