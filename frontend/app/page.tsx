'use client';

import Link from 'next/link';
import { useState, useEffect, useCallback } from 'react';
import { MapSection } from '@/components/map/MapSection';
import { ElectionHero } from '@/components/dashboard/ElectionHero';
import { api } from '@/lib/api';
import { DEMO_ELECTION_TYPES } from '@/lib/demo-map-data';
import { ElectionTypeOption } from '@/types';

interface DashboardStats {
  totalResults: number;
  totalPollingUnits: number;
  processedToday: number;
  flaggedResults: number;
  activeJobs: number;
}

interface QuickAction {
  title: string;
  description: string;
  href: string;
  icon: string;
  color: string;
}

const quickActions: QuickAction[] = [
  {
    title: 'Start Scraping',
    description: 'Enter an INEC portal URL and scrape result sheet images',
    href: '/scraping',
    icon: '🕷️',
    color: 'bg-indigo-500',
  },
  {
    title: 'Osun Governorship 2026',
    description: 'Latest scraped results — IPETUMODU II ward',
    href: '/results/scraped',
    icon: '🆕',
    color: 'bg-orange-500',
  },
  {
    title: 'Browse Elections',
    description: 'Navigate election types and geographic hierarchy',
    href: '/elections',
    icon: '🗳️',
    color: 'bg-blue-500',
  },
  {
    title: 'View Results',
    description: 'Search and filter polling unit results',
    href: '/results',
    icon: '📋',
    color: 'bg-green-500',
  },
];

function StatCard({
  title,
  value,
  icon,
  trend,
}: {
  title: string;
  value: string | number;
  icon: string;
  trend?: string;
}) {
  return (
    <div className="bg-card rounded-lg border border-border p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold text-foreground mt-1">
            {value.toLocaleString()}
          </p>
          {trend && <p className="text-xs text-green-600 mt-1">{trend}</p>}
        </div>
        <span className="text-3xl">{icon}</span>
      </div>
    </div>
  );
}

function QuickActionCard({ action }: { action: QuickAction }) {
  return (
    <Link
      href={action.href}
      className="block bg-card rounded-lg border border-border p-6 shadow-sm hover:shadow-md transition-shadow"
    >
      <div className="flex items-start space-x-4">
        <div className={`${action.color} rounded-lg p-3 text-white text-2xl`}>
          {action.icon}
        </div>
        <div>
          <h3 className="font-semibold text-foreground">{action.title}</h3>
          <p className="text-sm text-muted-foreground mt-1">{action.description}</p>
        </div>
      </div>
    </Link>
  );
}

function JobStatusWidget() {
  const [jobs, setJobs] = useState<{ id: string; status: string; processed_count: number; total_polling_units: number; election_type: string | null }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchJobs() {
      try {
        const list = await api.listJobs();
        // Show only active/recent jobs
        const recent = list.slice(0, 5);
        setJobs(recent);
      } catch {
        setJobs([]);
      } finally {
        setLoading(false);
      }
    }
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const activeJobs = jobs.filter((j) => j.status === 'running' || j.status === 'queued');

  if (loading) {
    return (
      <div className="bg-card rounded-lg border border-border p-6 shadow-sm">
        <h3 className="font-semibold text-foreground mb-4">Active Jobs</h3>
        <p className="text-muted-foreground text-sm">Loading…</p>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg border border-border p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-foreground">Active Jobs</h3>
        <Link href="/scraping" className="text-xs text-primary hover:underline">
          Manage →
        </Link>
      </div>
      {activeJobs.length === 0 ? (
        <div className="text-center py-4">
          <p className="text-muted-foreground text-sm">No active scraping jobs</p>
          <Link
            href="/scraping"
            className="mt-2 inline-block text-xs text-primary hover:underline"
          >
            Start a new job →
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {activeJobs.map((job) => {
            const pct = job.total_polling_units > 0
              ? Math.round((job.processed_count / job.total_polling_units) * 100)
              : 0;
            return (
              <div key={job.id}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-foreground truncate max-w-[160px]">
                    {job.election_type ?? 'All elections'}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {job.status === 'running' && (
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                    )}
                    <span className="text-xs text-muted-foreground capitalize">{job.status}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="text-xs text-muted-foreground w-8 text-right">{pct}%</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function HomePage() {
  // Shared election type state (lifted from MapSection)
  const [electionTypes, setElectionTypes] = useState<ElectionTypeOption[]>([]);
  const [selectedElectionTypeId, setSelectedElectionTypeId] = useState<string | null>(null);
  const [usingDemoData, setUsingDemoData] = useState<boolean>(false);

  const [stats, setStats] = useState<DashboardStats>({
    totalResults: 0,
    totalPollingUnits: 0,
    processedToday: 0,
    flaggedResults: 0,
    activeJobs: 0,
  });

  // Fetch election types on mount
  useEffect(() => {
    async function fetchElectionTypes() {
      try {
        const types = (await api.getElectionTypes()) as ElectionTypeOption[];
        setElectionTypes(types);
        const presidential = types.find((t) => t.code === 'presidential');
        if (presidential) {
          setSelectedElectionTypeId(presidential.id);
        } else if (types.length > 0) {
          setSelectedElectionTypeId(types[0].id);
        }
      } catch {
        console.info('API unavailable, using demo data');
        setUsingDemoData(true);
        setElectionTypes(DEMO_ELECTION_TYPES);
        setSelectedElectionTypeId(DEMO_ELECTION_TYPES[0].id);
      }
    }
    fetchElectionTypes();
  }, []);

  useEffect(() => {
    setStats({
      totalResults: 0,
      totalPollingUnits: 176846,
      processedToday: 0,
      flaggedResults: 0,
      activeJobs: 0,
    });
  }, []);

  const handleElectionTypeChange = useCallback((id: string) => {
    setSelectedElectionTypeId(id);
  }, []);

  // Derive the selected election type name for the hero
  const selectedElectionTypeName =
    electionTypes.find((t) => t.id === selectedElectionTypeId)?.name || 'Presidential';

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
      </div>

      {/* Election Results Hero Section — top contestants */}
      <ElectionHero
        electionTypeId={selectedElectionTypeId}
        electionTypeName={selectedElectionTypeName}
        usingDemoData={usingDemoData}
      />

      {/* Election Results Map — primary visual element */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-semibold text-foreground">Election Results Map</h2>
          <Link
            href="/map"
            className="text-sm text-primary hover:underline font-medium"
          >
            View Full Map →
          </Link>
        </div>
        <MapSection
          compact
          showHeader={false}
          externalElectionTypeId={selectedElectionTypeId}
          onElectionTypeChange={handleElectionTypeChange}
          externalElectionTypes={electionTypes}
          externalUsingDemoData={usingDemoData}
        />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard title="Total Results" value={stats.totalResults} icon="📊" />
        <StatCard title="Polling Units" value={stats.totalPollingUnits} icon="🏛️" />
        <StatCard title="Processed Today" value={stats.processedToday} icon="✅" />
        <StatCard title="Flagged for Review" value={stats.flaggedResults} icon="⚠️" />
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-foreground mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {quickActions.map((action) => (
            <QuickActionCard key={action.href} action={action} />
          ))}
        </div>
      </div>

      {/* Job Status Widget */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <JobStatusWidget />
        <div className="bg-card rounded-lg border border-border p-6 shadow-sm">
          <h3 className="font-semibold text-foreground mb-4">Recent Activity</h3>
          <p className="text-muted-foreground text-sm">No recent activity</p>
        </div>
      </div>
    </main>
  );
}
