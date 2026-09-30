'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { AggregatedResult, PartyResult } from '@/types';

type AggregationLevel = 'ward' | 'lga' | 'state';

function PartyRankingTable({ results }: { results: PartyResult[] }) {
  const sortedResults = [...results].sort((a, b) => b.voteCount - a.voteCount);
  const totalVotes = sortedResults.reduce((sum, r) => sum + r.voteCount, 0);

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-secondary/50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Rank</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Party</th>
            <th className="px-4 py-3 text-right font-medium text-muted-foreground">Votes</th>
            <th className="px-4 py-3 text-right font-medium text-muted-foreground">Percentage</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Distribution</th>
          </tr>
        </thead>
        <tbody>
          {sortedResults.map((result, index) => {
            const percentage = totalVotes > 0 ? (result.voteCount / totalVotes) * 100 : 0;
            return (
              <tr key={result.partyCode} className="border-b border-border">
                <td className="px-4 py-3">
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                    index === 0 ? 'bg-yellow-500 text-white' :
                    index === 1 ? 'bg-gray-400 text-white' :
                    index === 2 ? 'bg-amber-600 text-white' :
                    'bg-secondary text-secondary-foreground'
                  }`}>
                    {index + 1}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div>
                    <span className="font-medium text-foreground">{result.partyCode}</span>
                    <span className="text-sm text-muted-foreground ml-2">{result.partyName}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-right font-semibold text-foreground">
                  {result.voteCount.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right text-foreground">
                  {percentage.toFixed(2)}%
                </td>
                <td className="px-4 py-3">
                  <div className="w-32 h-4 bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function AggregationStats({ aggregation }: { aggregation: AggregatedResult }) {
  const completionRate = aggregation.totalPollingUnits > 0
    ? (aggregation.processedPollingUnits / aggregation.totalPollingUnits) * 100
    : 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="bg-card rounded-lg border border-border p-4">
        <p className="text-sm text-muted-foreground">Total Polling Units</p>
        <p className="text-2xl font-bold text-foreground">
          {aggregation.totalPollingUnits.toLocaleString()}
        </p>
      </div>
      <div className="bg-card rounded-lg border border-border p-4">
        <p className="text-sm text-muted-foreground">Processed</p>
        <p className="text-2xl font-bold text-foreground">
          {aggregation.processedPollingUnits.toLocaleString()}
        </p>
      </div>
      <div className="bg-card rounded-lg border border-border p-4">
        <p className="text-sm text-muted-foreground">Flagged</p>
        <p className="text-2xl font-bold text-destructive">
          {aggregation.flaggedPollingUnits.toLocaleString()}
        </p>
      </div>
      <div className="bg-card rounded-lg border border-border p-4">
        <p className="text-sm text-muted-foreground">Completion</p>
        <p className="text-2xl font-bold text-foreground">
          {completionRate.toFixed(1)}%
        </p>
        <div className="mt-2 h-2 bg-secondary rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all"
            style={{ width: `${completionRate}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export default function AggregationPage() {
  const [level, setLevel] = useState<AggregationLevel>('lga');
  const [locationId, setLocationId] = useState('');
  const [aggregation, setAggregation] = useState<AggregatedResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [locations, setLocations] = useState<{ id: string; name: string }[]>([]);

  // Load sample locations
  useEffect(() => {
    // In production, fetch from API based on level
    setLocations([
      { id: 'ikeja', name: 'Ikeja LGA' },
      { id: 'surulere', name: 'Surulere LGA' },
      { id: 'eti-osa', name: 'Eti-Osa LGA' },
      { id: 'lagos-island', name: 'Lagos Island LGA' },
      { id: 'alimosho', name: 'Alimosho LGA' },
    ]);
  }, [level]);

  const loadAggregation = async () => {
    if (!locationId) return;
    
    setLoading(true);
    try {
      let data;
      switch (level) {
        case 'ward':
          data = await api.getWardAggregation(locationId);
          break;
        case 'lga':
          data = await api.getLgaAggregation(locationId);
          break;
        case 'state':
          data = await api.getStateAggregation(locationId);
          break;
      }
      setAggregation(data as AggregatedResult);
    } catch {
      // Sample data for development
      setAggregation({
        level,
        locationId,
        locationName: locations.find(l => l.id === locationId)?.name || locationId,
        partyResults: [
          { partyName: 'All Progressives Congress', partyCode: 'APC', voteCount: 45678, percentage: 38.5 },
          { partyName: 'Peoples Democratic Party', partyCode: 'PDP', voteCount: 38234, percentage: 32.2 },
          { partyName: 'Labour Party', partyCode: 'LP', voteCount: 25890, percentage: 21.8 },
          { partyName: 'New Nigeria Peoples Party', partyCode: 'NNPP', voteCount: 5432, percentage: 4.6 },
          { partyName: 'All Progressives Grand Alliance', partyCode: 'APGA', voteCount: 2345, percentage: 2.0 },
          { partyName: 'African Democratic Congress', partyCode: 'ADC', voteCount: 1123, percentage: 0.9 },
        ],
        totalPollingUnits: 250,
        processedPollingUnits: 235,
        flaggedPollingUnits: 8,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <nav className="text-sm text-muted-foreground mb-4">
          <Link href="/" className="hover:text-foreground">Dashboard</Link>
          <span className="mx-2">/</span>
          <span className="text-foreground">Aggregation</span>
        </nav>
        <h1 className="text-3xl font-bold text-foreground">Vote Aggregation</h1>
        <p className="text-muted-foreground mt-2">
          View aggregated results by ward, LGA, or state with party rankings
        </p>
      </div>

      {/* Filters */}
      <div className="bg-card rounded-lg border border-border p-6 mb-8">
        <h2 className="text-lg font-semibold text-foreground mb-4">Select Location</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-1">
              Aggregation Level
            </label>
            <select
              value={level}
              onChange={(e) => {
                setLevel(e.target.value as AggregationLevel);
                setLocationId('');
                setAggregation(null);
              }}
              className="w-full px-3 py-2 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="ward">Ward</option>
              <option value="lga">LGA</option>
              <option value="state">State</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-1">
              Location
            </label>
            <select
              value={locationId}
              onChange={(e) => setLocationId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">Select a location...</option>
              {locations.map((loc) => (
                <option key={loc.id} value={loc.id}>
                  {loc.name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={loadAggregation}
              disabled={!locationId || loading}
              className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Loading...' : 'View Aggregation'}
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {aggregation && (
        <div className="space-y-8">
          {/* Header */}
          <div className="bg-card rounded-lg border border-border p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold text-foreground">{aggregation.locationName}</h2>
                <p className="text-muted-foreground capitalize">{aggregation.level} Level Aggregation</p>
              </div>
              <span className="text-4xl">
                {aggregation.level === 'ward' ? '📍' : aggregation.level === 'lga' ? '🏘️' : '🏛️'}
              </span>
            </div>
            <AggregationStats aggregation={aggregation} />
          </div>

          {/* Party Rankings */}
          <div className="bg-card rounded-lg border border-border overflow-hidden">
            <div className="p-6 border-b border-border">
              <h2 className="text-xl font-semibold text-foreground">Party Rankings</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Parties ranked by total votes in descending order
              </p>
            </div>
            <PartyRankingTable results={aggregation.partyResults} />
          </div>

          {/* Summary */}
          <div className="bg-card rounded-lg border border-border p-6">
            <h2 className="text-xl font-semibold text-foreground mb-4">Summary</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium text-foreground mb-2">Leading Party</h3>
                {aggregation.partyResults.length > 0 && (
                  <div className="flex items-center space-x-3">
                    <span className="text-3xl">🏆</span>
                    <div>
                      <p className="font-bold text-lg text-foreground">
                        {aggregation.partyResults.sort((a, b) => b.voteCount - a.voteCount)[0].partyCode}
                      </p>
                      <p className="text-muted-foreground">
                        {aggregation.partyResults.sort((a, b) => b.voteCount - a.voteCount)[0].voteCount.toLocaleString()} votes
                      </p>
                    </div>
                  </div>
                )}
              </div>
              <div>
                <h3 className="font-medium text-foreground mb-2">Total Valid Votes</h3>
                <p className="text-3xl font-bold text-foreground">
                  {aggregation.partyResults.reduce((sum, r) => sum + r.voteCount, 0).toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {!aggregation && !loading && (
        <div className="bg-card rounded-lg border border-border p-12 text-center">
          <span className="text-6xl mb-4 block">📊</span>
          <h3 className="text-xl font-semibold text-foreground mb-2">No Aggregation Selected</h3>
          <p className="text-muted-foreground">
            Select an aggregation level and location above to view results
          </p>
        </div>
      )}
    </main>
  );
}
