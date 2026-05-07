'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Trophy } from 'lucide-react';
import { api } from '@/lib/api';
import {
  generateDemoElectionTypeAggregation,
} from '@/lib/demo-map-data';
import { PARTY_COLORS, DEFAULT_PARTY_COLOR } from '@/lib/party-colors';
import { ElectionTypeAggregation } from '@/types';

interface ElectionHeroProps {
  /** Currently selected election type ID */
  electionTypeId: string | null;
  /** Display name of the selected election type */
  electionTypeName: string;
  /** Whether the app is using demo data (API unavailable) */
  usingDemoData: boolean;
}

interface HeroData {
  partyResults: {
    partyName: string;
    partyCode: string;
    totalVotes: number;
    percentage: number;
    rank: number;
  }[];
  totalValidVotes: number;
  totalPollingUnits: number;
  processedPollingUnits: number;
}

/** Format a number with commas (e.g., 4532109 → "4,532,109") */
function formatNumber(n: number): string {
  return n.toLocaleString('en-US');
}

/** Get relative time string (e.g., "Just now", "2 min ago") */
function getRelativeTime(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return 'Just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes === 1) return '1 min ago';
  return `${minutes} min ago`;
}

export function ElectionHero({
  electionTypeId,
  electionTypeName,
  usingDemoData,
}: ElectionHeroProps) {
  const [heroData, setHeroData] = useState<HeroData | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [relativeTime, setRelativeTime] = useState<string>('');
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const timeIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    if (!electionTypeId) return;

    // Use demo data if API is unavailable
    if (usingDemoData || electionTypeId.startsWith('demo-')) {
      const demo = generateDemoElectionTypeAggregation(electionTypeId);
      setHeroData({
        partyResults: demo.partyResults.slice(0, 3),
        totalValidVotes: demo.totalValidVotes,
        totalPollingUnits: demo.totalPollingUnits,
        processedPollingUnits: demo.processedPollingUnits,
      });
      setLastUpdated(new Date());
      return;
    }

    try {
      const data = (await api.getElectionTypeAggregation(
        electionTypeId
      )) as ElectionTypeAggregation;
      setHeroData({
        partyResults: data.party_results.slice(0, 3).map((pr) => ({
          partyName: pr.party_name,
          partyCode: pr.party_code,
          totalVotes: pr.total_votes,
          percentage: pr.percentage,
          rank: pr.rank,
        })),
        totalValidVotes: data.total_valid_votes,
        totalPollingUnits: data.total_polling_units,
        processedPollingUnits: data.processed_polling_units,
      });
      setLastUpdated(new Date());
    } catch {
      // Fallback to demo data
      const demo = generateDemoElectionTypeAggregation(electionTypeId);
      setHeroData({
        partyResults: demo.partyResults.slice(0, 3),
        totalValidVotes: demo.totalValidVotes,
        totalPollingUnits: demo.totalPollingUnits,
        processedPollingUnits: demo.processedPollingUnits,
      });
      setLastUpdated(new Date());
    }
  }, [electionTypeId, usingDemoData]);

  // Fetch on mount and when election type changes
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh every 60 seconds
  useEffect(() => {
    intervalRef.current = setInterval(fetchData, 60000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchData]);

  // Update relative time display every 30 seconds
  useEffect(() => {
    if (lastUpdated) {
      setRelativeTime(getRelativeTime(lastUpdated));
    }
    timeIntervalRef.current = setInterval(() => {
      if (lastUpdated) {
        setRelativeTime(getRelativeTime(lastUpdated));
      }
    }, 30000);
    return () => {
      if (timeIntervalRef.current) clearInterval(timeIntervalRef.current);
    };
  }, [lastUpdated]);

  // Empty state
  if (!heroData || heroData.partyResults.length === 0) {
    return (
      <section
        className="rounded-xl bg-gradient-to-r from-slate-50 to-white dark:from-slate-900 dark:to-slate-800 border border-border p-6 mb-6"
        aria-label="Election results summary"
      >
        <h2 className="text-lg font-semibold text-foreground">
          {electionTypeName || 'Election'} — Live Results
        </h2>
        <p className="text-muted-foreground text-sm mt-2">Awaiting results...</p>
      </section>
    );
  }

  const maxVotes = heroData.partyResults[0]?.totalVotes || 1;
  const completionPercent =
    heroData.totalPollingUnits > 0
      ? Math.round((heroData.processedPollingUnits / heroData.totalPollingUnits) * 100)
      : 0;

  return (
    <section
      className="rounded-xl bg-gradient-to-r from-slate-50 to-white dark:from-slate-900 dark:to-slate-800 border border-border p-5 mb-6 shadow-sm"
      aria-label="Election results summary"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-foreground">
          {electionTypeName} — Live Results
        </h2>
        <div className="flex items-center gap-2">
          {lastUpdated && (
            <span className="text-xs text-muted-foreground">
              Updated {relativeTime}
            </span>
          )}
        </div>
      </div>

      {/* Main content: contestants + stats */}
      <div className="flex flex-col lg:flex-row gap-4">
        {/* Top contestants */}
        <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-3">
          {heroData.partyResults.map((party) => {
            const color = PARTY_COLORS[party.partyCode] ?? DEFAULT_PARTY_COLOR;
            const barWidth = Math.round((party.totalVotes / maxVotes) * 100);
            const isLeading = party.rank === 1;

            return (
              <div
                key={party.partyCode}
                className={`relative rounded-lg border p-3 ${
                  isLeading
                    ? 'border-green-300 dark:border-green-700 bg-green-50/50 dark:bg-green-900/10'
                    : 'border-border bg-card'
                }`}
              >
                {/* Leading badge */}
                {isLeading && (
                  <div className="absolute -top-2 right-2 flex items-center gap-1 bg-green-600 text-white text-[10px] font-semibold px-2 py-0.5 rounded-full">
                    <Trophy className="w-3 h-3" />
                    Leading
                  </div>
                )}

                {/* Party info */}
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className="w-3 h-3 rounded-full shrink-0"
                    style={{ backgroundColor: color }}
                    aria-hidden="true"
                  />
                  <span
                    className={`font-bold ${isLeading ? 'text-base' : 'text-sm'} text-foreground`}
                  >
                    {party.partyCode}
                  </span>
                  <span className="text-xs text-muted-foreground ml-auto">
                    {party.percentage}%
                  </span>
                </div>

                {/* Vote count */}
                <p
                  className={`font-semibold tabular-nums ${
                    isLeading ? 'text-lg' : 'text-base'
                  } text-foreground mb-2`}
                >
                  {formatNumber(party.totalVotes)}
                </p>

                {/* Progress bar */}
                <div
                  className="w-full h-2 bg-secondary rounded-full overflow-hidden"
                  role="progressbar"
                  aria-valuenow={party.totalVotes}
                  aria-valuemax={maxVotes}
                  aria-label={`${party.partyCode} vote share`}
                >
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${barWidth}%`, backgroundColor: color }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* Summary stats */}
        <div className="lg:w-48 shrink-0 flex flex-row lg:flex-col gap-3 lg:gap-2 justify-between lg:justify-center">
          <div>
            <p className="text-xs text-muted-foreground">Total Valid Votes</p>
            <p className="text-sm font-semibold text-foreground tabular-nums">
              {formatNumber(heroData.totalValidVotes)}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Polling Units</p>
            <p className="text-sm font-semibold text-foreground tabular-nums">
              {formatNumber(heroData.processedPollingUnits)} /{' '}
              {formatNumber(heroData.totalPollingUnits)}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Results In</p>
            <div className="flex items-center gap-2">
              <div
                className="flex-1 h-2 bg-secondary rounded-full overflow-hidden"
                role="progressbar"
                aria-valuenow={completionPercent}
                aria-valuemax={100}
                aria-label="Percentage of polling units reported"
              >
                <div
                  className="h-full bg-primary rounded-full transition-all duration-500"
                  style={{ width: `${completionPercent}%` }}
                />
              </div>
              <span className="text-xs font-medium text-foreground tabular-nums">
                {completionPercent}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default ElectionHero;
