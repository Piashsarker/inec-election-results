'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { LGA, Ward, PollingUnit, PartyResult } from '@/types';

interface PageProps {
  params: { type: string; state: string };
}

function formatElectionType(type: string): string {
  return type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatStateName(state: string): string {
  return state.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function LocationCard({
  item,
  type,
  onClick,
}: {
  item: LGA | Ward | PollingUnit;
  type: 'lga' | 'ward' | 'polling_unit';
  onClick: () => void;
}) {
  const icons = {
    lga: '🏘️',
    ward: '📍',
    polling_unit: '🗳️',
  };

  const subtitles = {
    lga: (item as LGA).totalWards ? `${(item as LGA).totalWards} Wards` : '',
    ward: (item as Ward).totalPollingUnits ? `${(item as Ward).totalPollingUnits} Polling Units` : '',
    polling_unit: (item as PollingUnit).delimitation || '',
  };

  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-card rounded-lg border border-border p-4 shadow-sm hover:shadow-md hover:border-primary transition-all"
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-foreground">{item.name}</h3>
          {subtitles[type] && (
            <p className="text-sm text-muted-foreground">{subtitles[type]}</p>
          )}
        </div>
        <span className="text-2xl">{icons[type]}</span>
      </div>
    </button>
  );
}

function ResultsPreview({ results }: { results: PartyResult[] }) {
  if (!results || results.length === 0) {
    return (
      <div className="bg-card rounded-lg border border-border p-6">
        <p className="text-muted-foreground text-center">No results available</p>
      </div>
    );
  }

  const sortedResults = [...results].sort((a, b) => b.voteCount - a.voteCount);
  const totalVotes = sortedResults.reduce((sum, r) => sum + r.voteCount, 0);

  return (
    <div className="bg-card rounded-lg border border-border p-6">
      <h3 className="font-semibold text-foreground mb-4">Results Summary</h3>
      <div className="space-y-3">
        {sortedResults.slice(0, 5).map((result, index) => (
          <div key={result.partyCode} className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                index === 0 ? 'bg-yellow-500 text-white' :
                index === 1 ? 'bg-gray-400 text-white' :
                index === 2 ? 'bg-amber-600 text-white' :
                'bg-secondary text-secondary-foreground'
              }`}>
                {index + 1}
              </span>
              <span className="font-medium text-foreground">{result.partyCode}</span>
            </div>
            <div className="text-right">
              <span className="font-semibold text-foreground">{result.voteCount.toLocaleString()}</span>
              <span className="text-sm text-muted-foreground ml-2">
                ({((result.voteCount / totalVotes) * 100).toFixed(1)}%)
              </span>
            </div>
          </div>
        ))}
      </div>
      {sortedResults.length > 5 && (
        <p className="text-sm text-muted-foreground mt-4 text-center">
          +{sortedResults.length - 5} more parties
        </p>
      )}
    </div>
  );
}

export default function StatePage({ params }: PageProps) {
  const [currentLevel, setCurrentLevel] = useState<'lga' | 'ward' | 'polling_unit'>('lga');
  const [selectedLga, setSelectedLga] = useState<LGA | null>(null);
  const [selectedWard, setSelectedWard] = useState<Ward | null>(null);
  const [selectedPollingUnit, setSelectedPollingUnit] = useState<PollingUnit | null>(null);
  const [items, setItems] = useState<(LGA | Ward | PollingUnit)[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState<PartyResult[]>([]);

  // Load initial LGAs
  useEffect(() => {
    const loadLgas = async () => {
      setLoading(true);
      try {
        const data = await api.getLgas(params.type, params.state);
        setItems(data as LGA[]);
      } catch {
        // Use sample data if API fails
        setItems([
          { id: '1', stateId: '1', name: 'Sample LGA 1', code: 'LGA1', totalWards: 10 },
          { id: '2', stateId: '1', name: 'Sample LGA 2', code: 'LGA2', totalWards: 12 },
          { id: '3', stateId: '1', name: 'Sample LGA 3', code: 'LGA3', totalWards: 8 },
        ]);
      } finally {
        setLoading(false);
      }
    };
    loadLgas();
  }, [params.type, params.state]);

  const handleLgaSelect = async (lga: LGA) => {
    setSelectedLga(lga);
    setCurrentLevel('ward');
    setLoading(true);
    try {
      const data = await api.getWards(params.type, params.state, lga.code);
      setItems(data as Ward[]);
    } catch {
      setItems([
        { id: '1', lgaId: lga.id, name: 'Sample Ward 1', code: 'W1', totalPollingUnits: 15 },
        { id: '2', lgaId: lga.id, name: 'Sample Ward 2', code: 'W2', totalPollingUnits: 20 },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleWardSelect = async (ward: Ward) => {
    setSelectedWard(ward);
    setCurrentLevel('polling_unit');
    setLoading(true);
    try {
      const data = await api.getPollingUnits(
        params.type,
        params.state,
        selectedLga!.code,
        ward.code
      );
      setItems(data as PollingUnit[]);
    } catch {
      setItems([
        { id: '1', wardId: ward.id, name: 'Polling Unit 001', code: 'PU001' },
        { id: '2', wardId: ward.id, name: 'Polling Unit 002', code: 'PU002' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handlePollingUnitSelect = async (pu: PollingUnit) => {
    setSelectedPollingUnit(pu);
    // Load results for this polling unit
    try {
      const data = await api.getResults({ polling_unit: pu.id });
      if (data && (data as { data: { partyResults: PartyResult[] }[] }).data?.[0]) {
        setResults((data as { data: { partyResults: PartyResult[] }[] }).data[0].partyResults);
      }
    } catch {
      // Sample results
      setResults([
        { partyName: 'All Progressives Congress', partyCode: 'APC', voteCount: 245, percentage: 45.2 },
        { partyName: 'Peoples Democratic Party', partyCode: 'PDP', voteCount: 198, percentage: 36.5 },
        { partyName: 'Labour Party', partyCode: 'LP', voteCount: 67, percentage: 12.4 },
        { partyName: 'New Nigeria Peoples Party', partyCode: 'NNPP', voteCount: 32, percentage: 5.9 },
      ]);
    }
  };

  const handleBack = () => {
    if (currentLevel === 'polling_unit') {
      setCurrentLevel('ward');
      setSelectedPollingUnit(null);
      setResults([]);
      // Reload wards
      if (selectedLga) {
        handleLgaSelect(selectedLga);
      }
    } else if (currentLevel === 'ward') {
      setCurrentLevel('lga');
      setSelectedWard(null);
      setSelectedLga(null);
      // Reload LGAs
      setLoading(true);
      api.getLgas(params.type, params.state)
        .then((data) => setItems(data as LGA[]))
        .catch(() => setItems([]))
        .finally(() => setLoading(false));
    }
  };

  const filteredItems = items.filter((item) =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const levelLabels = {
    lga: 'Local Government Areas',
    ward: 'Wards',
    polling_unit: 'Polling Units',
  };

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <nav className="text-sm text-muted-foreground mb-4">
          <Link href="/" className="hover:text-foreground">Dashboard</Link>
          <span className="mx-2">/</span>
          <Link href="/elections" className="hover:text-foreground">Elections</Link>
          <span className="mx-2">/</span>
          <Link href={`/elections/${params.type}`} className="hover:text-foreground">
            {formatElectionType(params.type)}
          </Link>
          <span className="mx-2">/</span>
          <span className="text-foreground">{formatStateName(params.state)}</span>
          {selectedLga && (
            <>
              <span className="mx-2">/</span>
              <span className="text-foreground">{selectedLga.name}</span>
            </>
          )}
          {selectedWard && (
            <>
              <span className="mx-2">/</span>
              <span className="text-foreground">{selectedWard.name}</span>
            </>
          )}
        </nav>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">
              {formatStateName(params.state)}
            </h1>
            <p className="text-muted-foreground mt-2">
              {formatElectionType(params.type)} Election - {levelLabels[currentLevel]}
            </p>
          </div>
          {currentLevel !== 'lga' && (
            <button
              onClick={handleBack}
              className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors"
            >
              ← Back
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Location List */}
        <div className="lg:col-span-2">
          {/* Search */}
          <div className="mb-6">
            <input
              type="text"
              placeholder={`Search ${levelLabels[currentLevel].toLowerCase()}...`}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {loading ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">Loading...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {filteredItems.map((item) => (
                <LocationCard
                  key={item.id}
                  item={item}
                  type={currentLevel}
                  onClick={() => {
                    if (currentLevel === 'lga') handleLgaSelect(item as LGA);
                    else if (currentLevel === 'ward') handleWardSelect(item as Ward);
                    else handlePollingUnitSelect(item as PollingUnit);
                  }}
                />
              ))}
            </div>
          )}

          {!loading && filteredItems.length === 0 && (
            <p className="text-center text-muted-foreground py-8">
              No {levelLabels[currentLevel].toLowerCase()} found
            </p>
          )}
        </div>

        {/* Results Preview */}
        <div>
          {selectedPollingUnit ? (
            <div>
              <h2 className="font-semibold text-foreground mb-4">
                {selectedPollingUnit.name}
              </h2>
              <ResultsPreview results={results} />
              <Link
                href={`/results/${selectedPollingUnit.id}`}
                className="block mt-4 text-center px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              >
                View Full Details
              </Link>
            </div>
          ) : (
            <div className="bg-card rounded-lg border border-border p-6">
              <h3 className="font-semibold text-foreground mb-2">Selection Guide</h3>
              <p className="text-sm text-muted-foreground">
                Navigate through the hierarchy to view polling unit results.
                Select an LGA, then a Ward, then a Polling Unit to see detailed results.
              </p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
