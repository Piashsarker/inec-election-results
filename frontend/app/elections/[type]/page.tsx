'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { PartyBarChart } from '@/components/charts/PartyBarChart';
import { ElectionTypeAggregation, PartyResult, State } from '@/types';

interface PageProps {
  params: { type: string };
}

// Nigerian states list
const nigerianStates: State[] = [
  { id: '1', name: 'Abia', code: 'AB', totalLgas: 17 },
  { id: '2', name: 'Adamawa', code: 'AD', totalLgas: 21 },
  { id: '3', name: 'Akwa Ibom', code: 'AK', totalLgas: 31 },
  { id: '4', name: 'Anambra', code: 'AN', totalLgas: 21 },
  { id: '5', name: 'Bauchi', code: 'BA', totalLgas: 20 },
  { id: '6', name: 'Bayelsa', code: 'BY', totalLgas: 8 },
  { id: '7', name: 'Benue', code: 'BE', totalLgas: 23 },
  { id: '8', name: 'Borno', code: 'BO', totalLgas: 27 },
  { id: '9', name: 'Cross River', code: 'CR', totalLgas: 18 },
  { id: '10', name: 'Delta', code: 'DE', totalLgas: 25 },
  { id: '11', name: 'Ebonyi', code: 'EB', totalLgas: 13 },
  { id: '12', name: 'Edo', code: 'ED', totalLgas: 18 },
  { id: '13', name: 'Ekiti', code: 'EK', totalLgas: 16 },
  { id: '14', name: 'Enugu', code: 'EN', totalLgas: 17 },
  { id: '15', name: 'FCT', code: 'FC', totalLgas: 6 },
  { id: '16', name: 'Gombe', code: 'GO', totalLgas: 11 },
  { id: '17', name: 'Imo', code: 'IM', totalLgas: 27 },
  { id: '18', name: 'Jigawa', code: 'JI', totalLgas: 27 },
  { id: '19', name: 'Kaduna', code: 'KD', totalLgas: 23 },
  { id: '20', name: 'Kano', code: 'KN', totalLgas: 44 },
  { id: '21', name: 'Katsina', code: 'KT', totalLgas: 34 },
  { id: '22', name: 'Kebbi', code: 'KE', totalLgas: 21 },
  { id: '23', name: 'Kogi', code: 'KO', totalLgas: 21 },
  { id: '24', name: 'Kwara', code: 'KW', totalLgas: 16 },
  { id: '25', name: 'Lagos', code: 'LA', totalLgas: 20 },
  { id: '26', name: 'Nasarawa', code: 'NA', totalLgas: 13 },
  { id: '27', name: 'Niger', code: 'NI', totalLgas: 25 },
  { id: '28', name: 'Ogun', code: 'OG', totalLgas: 20 },
  { id: '29', name: 'Ondo', code: 'ON', totalLgas: 18 },
  { id: '30', name: 'Osun', code: 'OS', totalLgas: 30 },
  { id: '31', name: 'Oyo', code: 'OY', totalLgas: 33 },
  { id: '32', name: 'Plateau', code: 'PL', totalLgas: 17 },
  { id: '33', name: 'Rivers', code: 'RI', totalLgas: 23 },
  { id: '34', name: 'Sokoto', code: 'SO', totalLgas: 23 },
  { id: '35', name: 'Taraba', code: 'TA', totalLgas: 16 },
  { id: '36', name: 'Yobe', code: 'YO', totalLgas: 17 },
  { id: '37', name: 'Zamfara', code: 'ZA', totalLgas: 14 },
];

function formatElectionType(type: string): string {
  return type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatNumber(num: number): string {
  return num.toLocaleString();
}

function SummaryCard({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div className="bg-card rounded-lg border border-border p-4 shadow-sm">
      <div className="flex items-center space-x-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-xl font-bold text-foreground">{value}</p>
        </div>
      </div>
    </div>
  );
}

function PartyTable({ parties }: { parties: ElectionTypeAggregation['party_results'] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            <th className="text-left py-3 px-4 font-semibold text-muted-foreground">Rank</th>
            <th className="text-left py-3 px-4 font-semibold text-muted-foreground">Party</th>
            <th className="text-right py-3 px-4 font-semibold text-muted-foreground">Votes</th>
            <th className="text-right py-3 px-4 font-semibold text-muted-foreground">
              Percentage
            </th>
          </tr>
        </thead>
        <tbody>
          {parties.map((party) => (
            <tr key={party.party_code} className="border-b border-border/50 hover:bg-muted/50">
              <td className="py-3 px-4 text-foreground">{party.rank}</td>
              <td className="py-3 px-4">
                <div>
                  <span className="font-medium text-foreground">{party.party_code}</span>
                  <span className="text-muted-foreground ml-2">{party.party_name}</span>
                </div>
              </td>
              <td className="py-3 px-4 text-right font-mono text-foreground">
                {formatNumber(party.total_votes)}
              </td>
              <td className="py-3 px-4 text-right font-mono text-foreground">
                {party.percentage.toFixed(2)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StateCard({ state, electionType }: { state: State; electionType: string }) {
  const stateSlug = state.name.toLowerCase().replace(/\s+/g, '-');

  return (
    <Link
      href={`/elections/${electionType}/${stateSlug}`}
      className="block bg-card rounded-lg border border-border p-4 shadow-sm
        hover:shadow-md hover:border-primary transition-all"
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-foreground">{state.name}</h3>
          <p className="text-sm text-muted-foreground">{state.totalLgas} LGAs</p>
        </div>
        <span className="text-2xl">🏛️</span>
      </div>
    </Link>
  );
}

export default function ElectionTypePage({ params }: PageProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [aggregation, setAggregation] = useState<ElectionTypeAggregation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAggregation() {
      try {
        setLoading(true);
        setError(null);

        // First, get election types to find the UUID for this type code
        const electionTypes = await api.getElectionTypes() as Array<{
          id: string;
          name: string;
          code: string;
        }>;
        const matchedType = electionTypes.find(
          (et) =>
            et.code === params.type ||
            et.name.toLowerCase().replace(/\s+/g, '_') === params.type
        );

        if (matchedType) {
          const data = await api.getElectionTypeAggregation(
            matchedType.id
          ) as ElectionTypeAggregation;
          setAggregation(data);
        }
      } catch {
        // Aggregation data may not be available yet
        setError('No aggregation data available for this election type.');
      } finally {
        setLoading(false);
      }
    }

    fetchAggregation();
  }, [params.type]);

  const filteredStates = nigerianStates.filter((state) =>
    state.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Map backend party results to PartyBarChart format
  const chartData: PartyResult[] = aggregation
    ? aggregation.party_results.map((pr) => ({
        partyName: pr.party_name,
        partyCode: pr.party_code,
        voteCount: pr.total_votes,
        percentage: pr.percentage,
      }))
    : [];

  const hasResults = aggregation && aggregation.party_results.length > 0;

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <nav className="text-sm text-muted-foreground mb-4">
          <Link href="/" className="hover:text-foreground">Dashboard</Link>
          <span className="mx-2">/</span>
          <Link href="/elections" className="hover:text-foreground">Elections</Link>
          <span className="mx-2">/</span>
          <span className="text-foreground">{formatElectionType(params.type)}</span>
        </nav>
        <h1 className="text-3xl font-bold text-foreground capitalize">
          {formatElectionType(params.type)} Election
        </h1>
        <p className="text-muted-foreground mt-2">
          Aggregated results and state-by-state breakdown
        </p>
      </div>

      {/* Aggregation Summary Section */}
      {loading && (
        <div className="mb-8 text-center py-8 text-muted-foreground">
          Loading aggregation data...
        </div>
      )}

      {!loading && hasResults && aggregation && (
        <div className="mb-10 space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <SummaryCard
              label="Total Valid Votes"
              value={formatNumber(aggregation.total_valid_votes)}
              icon="✅"
            />
            <SummaryCard
              label="Accredited Voters"
              value={formatNumber(aggregation.total_accredited_voters)}
              icon="👥"
            />
            <SummaryCard
              label="Rejected Votes"
              value={formatNumber(aggregation.total_rejected_votes)}
              icon="❌"
            />
            <SummaryCard
              label="Polling Units"
              value={`${formatNumber(aggregation.processed_polling_units)} / ${formatNumber(aggregation.total_polling_units)}`}
              icon="🏫"
            />
          </div>

          {/* Party Bar Chart */}
          <div className="bg-card rounded-lg border border-border p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-foreground mb-4">
              Votes by Political Party
            </h2>
            <PartyBarChart
              data={chartData}
              height={Math.max(300, chartData.length * 40)}
            />
          </div>

          {/* Party Results Table */}
          <div className="bg-card rounded-lg border border-border p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-foreground mb-4">
              Party Results
            </h2>
            <PartyTable parties={aggregation.party_results} />
          </div>
        </div>
      )}

      {!loading && !hasResults && !error && (
        <div className="mb-8 bg-card rounded-lg border border-border p-8 text-center">
          <p className="text-muted-foreground text-lg">
            No election results available for this election type yet.
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            Results will appear here once polling unit data has been processed.
          </p>
        </div>
      )}

      {!loading && error && (
        <div className="mb-8 bg-card rounded-lg border border-border p-8 text-center">
          <p className="text-muted-foreground">{error}</p>
        </div>
      )}

      {/* Divider */}
      <hr className="border-border mb-8" />

      {/* States Section */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-foreground mb-2">Browse by State</h2>
        <p className="text-muted-foreground text-sm mb-4">
          Select a state to view detailed results
        </p>
        <input
          type="text"
          placeholder="Search states..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full max-w-md px-4 py-2 rounded-lg border border-input bg-background
            text-foreground placeholder:text-muted-foreground focus:outline-none
            focus:ring-2 focus:ring-ring"
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {filteredStates.map((state) => (
          <StateCard key={state.id} state={state} electionType={params.type} />
        ))}
      </div>

      {filteredStates.length === 0 && (
        <p className="text-center text-muted-foreground py-8">
          No states found matching &quot;{searchTerm}&quot;
        </p>
      )}
    </main>
  );
}
