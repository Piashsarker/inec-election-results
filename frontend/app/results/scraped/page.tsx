'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Legend,
} from 'recharts';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Party colors
const PARTY_COLORS: Record<string, string> = {
  APC: '#0066CC',
  PDP: '#CC0000',
  LP: '#006600',
  NNPP: '#FF6600',
  APGA: '#660066',
  ADC: '#336699',
  SDP: '#009999',
  YPP: '#CC6600',
  AA: '#999900',
  BP: '#663300',
  PRP: '#CC3399',
  ADP: '#006666',
};

interface PartyResultItem {
  code: string;
  name: string;
  votes: number;
}

interface PollingUnitResult {
  polling_unit_code: string;
  polling_unit_name: string;
  file: string;
  ocr_confidence: number;
  extraction_confidence: number;
  accredited_voters: number;
  valid_votes: number;
  rejected_votes: number;
  parties: PartyResultItem[];
  warnings: string[];
  error?: string | null;
}

interface WardResultSummary {
  election: string;
  date: string;
  state: string;
  lga: string;
  ward: string;
  ward_code: string;
  polling_units_processed: number;
  polling_units_total: number;
  total_accredited_voters: number;
  total_valid_votes: number;
  total_rejected_votes: number;
  party_totals: Record<string, number>;
  results: PollingUnitResult[];
}

function ConfidenceBadge({ value }: { value: number }) {
  const color =
    value >= 70 ? 'bg-green-100 text-green-800' :
    value >= 50 ? 'bg-yellow-100 text-yellow-800' :
    'bg-red-100 text-red-800';

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {value.toFixed(0)}%
    </span>
  );
}

function StatusBadge({ hasError }: { hasError: boolean }) {
  if (hasError) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
        Failed
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
      Extracted
    </span>
  );
}

export default function ScrapedResultsPage() {
  const [data, setData] = useState<WardResultSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch(`${API_BASE_URL}/scraped/osun_governorship_2026`);
        if (!res.ok) {
          throw new Error(`API returned ${res.status}`);
        }
        const json = await res.json();
        setData(json);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch results');
        // Fallback: try loading from static data
        try {
          const fallbackRes = await fetch('/api/scraped-results');
          if (fallbackRes.ok) {
            setData(await fallbackRes.json());
            setError(null);
          }
        } catch {
          // Keep original error
        }
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <main className="container mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/3" />
          <div className="h-64 bg-muted rounded" />
          <div className="h-96 bg-muted rounded" />
        </div>
      </main>
    );
  }

  if (error && !data) {
    return (
      <main className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-800 mb-2">Error Loading Results</h2>
          <p className="text-red-700">{error}</p>
          <p className="text-sm text-red-600 mt-2">
            Make sure the backend is running at {API_BASE_URL}
          </p>
        </div>
      </main>
    );
  }

  if (!data) return null;

  // Prepare chart data
  const partyChartData = Object.entries(data.party_totals)
    .filter(([, votes]) => votes > 0)
    .sort(([, a], [, b]) => b - a)
    .map(([code, votes]) => ({
      party: code,
      votes,
      color: PARTY_COLORS[code] || '#888888',
    }));

  const totalVotes = partyChartData.reduce((sum, d) => sum + d.votes, 0);

  const pieData = partyChartData.map((d) => ({
    name: d.party,
    value: d.votes,
    percentage: totalVotes > 0 ? ((d.votes / totalVotes) * 100).toFixed(1) : '0',
  }));

  return (
    <main className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <nav className="flex items-center space-x-2 text-sm text-muted-foreground mb-2">
          <Link href="/" className="hover:text-foreground">Dashboard</Link>
          <span>/</span>
          <Link href="/results" className="hover:text-foreground">Results</Link>
          <span>/</span>
          <span className="text-foreground">Scraped</span>
        </nav>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">
              {data.state} {data.election} Election
            </h1>
            <p className="text-muted-foreground mt-1">
              {data.ward} Ward • {data.lga} LGA • {data.date}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-muted-foreground">Ward Code</p>
            <p className="text-lg font-mono font-bold">{data.ward_code}</p>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-card rounded-lg border border-border p-4">
          <p className="text-sm text-muted-foreground">Polling Units Processed</p>
          <p className="text-2xl font-bold text-foreground">
            {data.polling_units_processed}/{data.polling_units_total}
          </p>
          <p className="text-xs text-muted-foreground">
            {((data.polling_units_processed / data.polling_units_total) * 100).toFixed(0)}% coverage
          </p>
        </div>
        <div className="bg-card rounded-lg border border-border p-4">
          <p className="text-sm text-muted-foreground">Total Votes (Extracted)</p>
          <p className="text-2xl font-bold text-foreground">
            {totalVotes.toLocaleString()}
          </p>
        </div>
        <div className="bg-card rounded-lg border border-border p-4">
          <p className="text-sm text-muted-foreground">Leading Party</p>
          <p className="text-2xl font-bold" style={{ color: partyChartData[0]?.color }}>
            {partyChartData[0]?.party || 'N/A'}
          </p>
          <p className="text-xs text-muted-foreground">
            {partyChartData[0]?.votes.toLocaleString()} votes
          </p>
        </div>
        <div className="bg-card rounded-lg border border-border p-4">
          <p className="text-sm text-muted-foreground">OCR Method</p>
          <p className="text-2xl font-bold text-foreground">Tesseract</p>
          <p className="text-xs text-yellow-600">⚠️ Low confidence — needs GPT-4 Vision</p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Bar Chart */}
        <div className="bg-card rounded-lg border border-border p-6">
          <h2 className="text-lg font-semibold text-foreground mb-4">
            Party Vote Totals (Ward Level)
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={partyChartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="party" />
              <YAxis />
              <Tooltip
                formatter={(value: number) => [value.toLocaleString(), 'Votes']}
              />
              <Bar dataKey="votes" radius={[4, 4, 0, 0]}>
                {partyChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie Chart */}
        <div className="bg-card rounded-lg border border-border p-6">
          <h2 className="text-lg font-semibold text-foreground mb-4">
            Vote Share Distribution
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percentage }) => `${name} (${percentage}%)`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={PARTY_COLORS[entry.name] || '#888888'}
                  />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => [value.toLocaleString(), 'Votes']} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Results Table */}
      <div className="bg-card rounded-lg border border-border overflow-hidden">
        <div className="p-4 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">
            Polling Unit Results ({data.results.length} units)
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">PU Code</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Name</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">OCR Conf.</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Parties Found</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Top Party</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Top Votes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data.results.map((result) => {
                const topParty = result.parties
                  ?.filter((p) => p.votes > 0)
                  .sort((a, b) => b.votes - a.votes)[0];

                return (
                  <tr key={result.polling_unit_code} className="hover:bg-muted/50">
                    <td className="px-4 py-3 font-mono text-xs">
                      {result.polling_unit_code}
                    </td>
                    <td className="px-4 py-3 text-foreground max-w-[200px] truncate">
                      {result.polling_unit_name}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge hasError={!!result.error} />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <ConfidenceBadge value={result.ocr_confidence} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      {result.parties?.length || 0}
                    </td>
                    <td className="px-4 py-3">
                      {topParty ? (
                        <span
                          className="font-semibold"
                          style={{ color: PARTY_COLORS[topParty.code] || '#666' }}
                        >
                          {topParty.code}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right font-mono">
                      {topParty ? topParty.votes.toLocaleString() : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Warning Notice */}
      <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <span className="text-xl">⚠️</span>
          <div>
            <h3 className="font-semibold text-yellow-800">Low Confidence Notice</h3>
            <p className="text-sm text-yellow-700 mt-1">
              These results were extracted using Tesseract OCR on handwritten result sheets.
              Average confidence is ~48%. For accurate results, re-process with GPT-4 Vision
              by setting a valid <code className="bg-yellow-100 px-1 rounded">OPENAI_API_KEY</code> in
              the backend environment.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
