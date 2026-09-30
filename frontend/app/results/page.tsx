'use client';

import Link from 'next/link';
import { useState, useEffect, useMemo } from 'react';
import { api } from '@/lib/api';
import { ElectionResult, ElectionType } from '@/types';

type SortField = 'state' | 'lga' | 'ward' | 'pollingUnit' | 'validVotes' | 'extractedAt' | 'confidenceScore';
type SortDirection = 'asc' | 'desc';

interface FilterState {
  electionType: string;
  state: string;
  lga: string;
  search: string;
}

const electionTypes: { value: ElectionType | ''; label: string }[] = [
  { value: '', label: 'All Election Types' },
  { value: 'presidential', label: 'Presidential' },
  { value: 'governorship', label: 'Governorship' },
  { value: 'senatorial', label: 'Senatorial' },
  { value: 'house_of_reps', label: 'House of Representatives' },
  { value: 'house_of_assembly', label: 'House of Assembly' },
  { value: 'chairmanship', label: 'Chairmanship' },
  { value: 'councilor', label: 'Councilor' },
];

function ResultRow({ result }: { result: ElectionResult }) {
  const topParty = result.partyResults.reduce(
    (max, p) => (p.voteCount > max.voteCount ? p : max),
    result.partyResults[0] || { partyCode: '-', voteCount: 0 }
  );

  return (
    <tr className="border-b border-border hover:bg-accent/50 transition-colors">
      <td className="px-4 py-3">
        <Link
          href={`/results/${result.id}`}
          className="text-primary hover:underline font-medium"
        >
          {result.pollingUnit}
        </Link>
      </td>
      <td className="px-4 py-3 text-muted-foreground">{result.ward}</td>
      <td className="px-4 py-3 text-muted-foreground">{result.lga}</td>
      <td className="px-4 py-3 text-muted-foreground">{result.state}</td>
      <td className="px-4 py-3">
        <span className="font-medium">{topParty.partyCode}</span>
        <span className="text-muted-foreground ml-2">({topParty.voteCount.toLocaleString()})</span>
      </td>
      <td className="px-4 py-3 text-right">{result.validVotes.toLocaleString()}</td>
      <td className="px-4 py-3 text-right">
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          result.confidenceScore >= 0.9 ? 'bg-green-100 text-green-800' :
          result.confidenceScore >= 0.7 ? 'bg-yellow-100 text-yellow-800' :
          'bg-red-100 text-red-800'
        }`}>
          {(result.confidenceScore * 100).toFixed(0)}%
        </span>
      </td>
      <td className="px-4 py-3 text-muted-foreground text-sm">
        {new Date(result.extractedAt).toLocaleDateString()}
      </td>
    </tr>
  );
}

function SortableHeader({
  label,
  field,
  currentSort,
  currentDirection,
  onSort,
}: {
  label: string;
  field: SortField;
  currentSort: SortField;
  currentDirection: SortDirection;
  onSort: (field: SortField) => void;
}) {
  const isActive = currentSort === field;
  
  return (
    <th
      className="px-4 py-3 text-left font-medium text-muted-foreground cursor-pointer hover:text-foreground transition-colors"
      onClick={() => onSort(field)}
    >
      <div className="flex items-center space-x-1">
        <span>{label}</span>
        {isActive && (
          <span className="text-primary">
            {currentDirection === 'asc' ? '↑' : '↓'}
          </span>
        )}
      </div>
    </th>
  );
}

export default function ResultsPage() {
  const [results, setResults] = useState<ElectionResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<FilterState>({
    electionType: '',
    state: '',
    lga: '',
    search: '',
  });
  const [sortField, setSortField] = useState<SortField>('extractedAt');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    const loadResults = async () => {
      setLoading(true);
      try {
        const params: Record<string, string> = {
          page: page.toString(),
          page_size: pageSize.toString(),
        };
        if (filters.electionType) params.election_type = filters.electionType;
        if (filters.state) params.state = filters.state;
        if (filters.lga) params.lga = filters.lga;
        if (filters.search) params.search = filters.search;

        const data = await api.getResults(params);
        const response = data as { data: ElectionResult[]; totalPages: number };
        setResults(response.data || []);
        setTotalPages(response.totalPages || 1);
      } catch {
        // Sample data for development
        setResults([
          {
            id: '1',
            electionType: 'presidential',
            state: 'Lagos',
            lga: 'Ikeja',
            ward: 'Ward 1',
            pollingUnit: 'PU 001',
            partyResults: [
              { partyName: 'APC', partyCode: 'APC', voteCount: 245, percentage: 45.2 },
              { partyName: 'PDP', partyCode: 'PDP', voteCount: 198, percentage: 36.5 },
              { partyName: 'LP', partyCode: 'LP', voteCount: 67, percentage: 12.4 },
            ],
            accreditedVoters: 550,
            validVotes: 510,
            rejectedVotes: 12,
            extractedAt: new Date(),
            confidenceScore: 0.95,
            sourceImagePath: '/images/result1.png',
          },
          {
            id: '2',
            electionType: 'presidential',
            state: 'Lagos',
            lga: 'Ikeja',
            ward: 'Ward 2',
            pollingUnit: 'PU 002',
            partyResults: [
              { partyName: 'PDP', partyCode: 'PDP', voteCount: 312, percentage: 52.1 },
              { partyName: 'APC', partyCode: 'APC', voteCount: 189, percentage: 31.5 },
              { partyName: 'LP', partyCode: 'LP', voteCount: 98, percentage: 16.4 },
            ],
            accreditedVoters: 620,
            validVotes: 599,
            rejectedVotes: 8,
            extractedAt: new Date(),
            confidenceScore: 0.88,
            sourceImagePath: '/images/result2.png',
          },
        ]);
        setTotalPages(1);
      } finally {
        setLoading(false);
      }
    };
    loadResults();
  }, [page, filters]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const sortedResults = useMemo(() => {
    return [...results].sort((a, b) => {
      let aVal: string | number | Date = '';
      let bVal: string | number | Date = '';

      switch (sortField) {
        case 'state':
          aVal = a.state;
          bVal = b.state;
          break;
        case 'lga':
          aVal = a.lga;
          bVal = b.lga;
          break;
        case 'ward':
          aVal = a.ward;
          bVal = b.ward;
          break;
        case 'pollingUnit':
          aVal = a.pollingUnit;
          bVal = b.pollingUnit;
          break;
        case 'validVotes':
          aVal = a.validVotes;
          bVal = b.validVotes;
          break;
        case 'confidenceScore':
          aVal = a.confidenceScore;
          bVal = b.confidenceScore;
          break;
        case 'extractedAt':
          aVal = new Date(a.extractedAt);
          bVal = new Date(b.extractedAt);
          break;
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [results, sortField, sortDirection]);

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <nav className="text-sm text-muted-foreground mb-4">
          <Link href="/" className="hover:text-foreground">Dashboard</Link>
          <span className="mx-2">/</span>
          <span className="text-foreground">Results</span>
        </nav>
        <h1 className="text-3xl font-bold text-foreground">Election Results</h1>
        <p className="text-muted-foreground mt-2">
          Browse and filter polling unit results
        </p>
      </div>

      {/* Filters */}
      <div className="bg-card rounded-lg border border-border p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-1">
              Election Type
            </label>
            <select
              value={filters.electionType}
              onChange={(e) => setFilters({ ...filters, electionType: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {electionTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-1">
              State
            </label>
            <input
              type="text"
              placeholder="Filter by state..."
              value={filters.state}
              onChange={(e) => setFilters({ ...filters, state: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-1">
              LGA
            </label>
            <input
              type="text"
              placeholder="Filter by LGA..."
              value={filters.lga}
              onChange={(e) => setFilters({ ...filters, lga: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-1">
              Search
            </label>
            <input
              type="text"
              placeholder="Search polling units..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>
      </div>

      {/* Results Table */}
      <div className="bg-card rounded-lg border border-border overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <p className="text-muted-foreground">Loading results...</p>
          </div>
        ) : sortedResults.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-muted-foreground">No results found</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-secondary/50">
                  <tr>
                    <SortableHeader
                      label="Polling Unit"
                      field="pollingUnit"
                      currentSort={sortField}
                      currentDirection={sortDirection}
                      onSort={handleSort}
                    />
                    <SortableHeader
                      label="Ward"
                      field="ward"
                      currentSort={sortField}
                      currentDirection={sortDirection}
                      onSort={handleSort}
                    />
                    <SortableHeader
                      label="LGA"
                      field="lga"
                      currentSort={sortField}
                      currentDirection={sortDirection}
                      onSort={handleSort}
                    />
                    <SortableHeader
                      label="State"
                      field="state"
                      currentSort={sortField}
                      currentDirection={sortDirection}
                      onSort={handleSort}
                    />
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      Leading Party
                    </th>
                    <SortableHeader
                      label="Valid Votes"
                      field="validVotes"
                      currentSort={sortField}
                      currentDirection={sortDirection}
                      onSort={handleSort}
                    />
                    <SortableHeader
                      label="Confidence"
                      field="confidenceScore"
                      currentSort={sortField}
                      currentDirection={sortDirection}
                      onSort={handleSort}
                    />
                    <SortableHeader
                      label="Extracted"
                      field="extractedAt"
                      currentSort={sortField}
                      currentDirection={sortDirection}
                      onSort={handleSort}
                    />
                  </tr>
                </thead>
                <tbody>
                  {sortedResults.map((result) => (
                    <ResultRow key={result.id} result={result} />
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between px-4 py-3 border-t border-border">
              <p className="text-sm text-muted-foreground">
                Showing {sortedResults.length} results
              </p>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 rounded border border-input bg-background text-foreground disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent transition-colors"
                >
                  Previous
                </button>
                <span className="text-sm text-muted-foreground">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1 rounded border border-input bg-background text-foreground disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
