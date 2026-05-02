'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { ElectionResult, PartyResult } from '@/types';

interface PageProps {
  params: { id: string };
}

function PartyResultBar({ result, maxVotes }: { result: PartyResult; maxVotes: number }) {
  const percentage = maxVotes > 0 ? (result.voteCount / maxVotes) * 100 : 0;
  
  // Party colors (simplified)
  const partyColors: Record<string, string> = {
    APC: 'bg-blue-500',
    PDP: 'bg-red-500',
    LP: 'bg-green-500',
    NNPP: 'bg-purple-500',
    APGA: 'bg-orange-500',
    ADC: 'bg-yellow-500',
  };

  const color = partyColors[result.partyCode] || 'bg-gray-500';

  return (
    <div className="flex items-center space-x-4 py-2">
      <div className="w-16 font-medium text-foreground">{result.partyCode}</div>
      <div className="flex-1">
        <div className="h-8 bg-secondary rounded-lg overflow-hidden">
          <div
            className={`h-full ${color} transition-all duration-500`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
      <div className="w-24 text-right">
        <span className="font-semibold text-foreground">{result.voteCount.toLocaleString()}</span>
        <span className="text-sm text-muted-foreground ml-1">
          ({result.percentage.toFixed(1)}%)
        </span>
      </div>
    </div>
  );
}

function StatBox({ label, value, icon }: { label: string; value: string | number; icon: string }) {
  return (
    <div className="bg-card rounded-lg border border-border p-4">
      <div className="flex items-center space-x-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-xl font-bold text-foreground">{value.toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
}

export default function ResultDetailPage({ params }: PageProps) {
  const [result, setResult] = useState<ElectionResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [flagging, setFlagging] = useState(false);
  const [flagReason, setFlagReason] = useState('');
  const [showFlagModal, setShowFlagModal] = useState(false);

  useEffect(() => {
    const loadResult = async () => {
      setLoading(true);
      try {
        const data = await api.getResult(params.id);
        setResult(data as ElectionResult);
      } catch {
        // Sample data for development
        setResult({
          id: params.id,
          electionType: 'presidential',
          state: 'Lagos',
          lga: 'Ikeja',
          ward: 'Ward 1',
          pollingUnit: 'Polling Unit 001',
          partyResults: [
            { partyName: 'All Progressives Congress', partyCode: 'APC', voteCount: 245, percentage: 45.2 },
            { partyName: 'Peoples Democratic Party', partyCode: 'PDP', voteCount: 198, percentage: 36.5 },
            { partyName: 'Labour Party', partyCode: 'LP', voteCount: 67, percentage: 12.4 },
            { partyName: 'New Nigeria Peoples Party', partyCode: 'NNPP', voteCount: 22, percentage: 4.1 },
            { partyName: 'All Progressives Grand Alliance', partyCode: 'APGA', voteCount: 10, percentage: 1.8 },
          ],
          accreditedVoters: 580,
          validVotes: 542,
          rejectedVotes: 15,
          extractedAt: new Date(),
          confidenceScore: 0.92,
          sourceImagePath: '/images/result_sheet.png',
        });
      } finally {
        setLoading(false);
      }
    };
    loadResult();
  }, [params.id]);

  const handleFlag = async () => {
    if (!flagReason.trim()) return;
    
    setFlagging(true);
    try {
      await api.flagResult(params.id, flagReason);
      setShowFlagModal(false);
      setFlagReason('');
      alert('Result flagged for review');
    } catch {
      alert('Failed to flag result');
    } finally {
      setFlagging(false);
    }
  };

  if (loading) {
    return (
      <main className="container mx-auto px-4 py-8">
        <p className="text-muted-foreground">Loading result details...</p>
      </main>
    );
  }

  if (!result) {
    return (
      <main className="container mx-auto px-4 py-8">
        <p className="text-muted-foreground">Result not found</p>
        <Link href="/results" className="text-primary hover:underline mt-4 inline-block">
          ← Back to Results
        </Link>
      </main>
    );
  }

  const sortedPartyResults = [...result.partyResults].sort((a, b) => b.voteCount - a.voteCount);
  const maxVotes = sortedPartyResults[0]?.voteCount || 0;

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <nav className="text-sm text-muted-foreground mb-4">
          <Link href="/" className="hover:text-foreground">Dashboard</Link>
          <span className="mx-2">/</span>
          <Link href="/results" className="hover:text-foreground">Results</Link>
          <span className="mx-2">/</span>
          <span className="text-foreground">{result.pollingUnit}</span>
        </nav>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">{result.pollingUnit}</h1>
            <p className="text-muted-foreground mt-2">
              {result.ward} • {result.lga} • {result.state}
            </p>
            <p className="text-sm text-muted-foreground mt-1 capitalize">
              {result.electionType.replace(/_/g, ' ')} Election
            </p>
          </div>
          <button
            onClick={() => setShowFlagModal(true)}
            className="px-4 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 transition-colors"
          >
            🚩 Flag for Review
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatBox label="Accredited Voters" value={result.accreditedVoters} icon="👥" />
        <StatBox label="Valid Votes" value={result.validVotes} icon="✅" />
        <StatBox label="Rejected Votes" value={result.rejectedVotes} icon="❌" />
        <StatBox
          label="Confidence Score"
          value={`${(result.confidenceScore * 100).toFixed(0)}%`}
          icon={result.confidenceScore >= 0.9 ? '🟢' : result.confidenceScore >= 0.7 ? '🟡' : '🔴'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Party Results */}
        <div className="lg:col-span-2">
          <div className="bg-card rounded-lg border border-border p-6">
            <h2 className="text-xl font-semibold text-foreground mb-4">Party Results</h2>
            <div className="space-y-2">
              {sortedPartyResults.map((partyResult, index) => (
                <div key={partyResult.partyCode} className="flex items-center">
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mr-3 ${
                    index === 0 ? 'bg-yellow-500 text-white' :
                    index === 1 ? 'bg-gray-400 text-white' :
                    index === 2 ? 'bg-amber-600 text-white' :
                    'bg-secondary text-secondary-foreground'
                  }`}>
                    {index + 1}
                  </span>
                  <div className="flex-1">
                    <PartyResultBar result={partyResult} maxVotes={maxVotes} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Metadata */}
        <div>
          <div className="bg-card rounded-lg border border-border p-6">
            <h2 className="text-xl font-semibold text-foreground mb-4">Details</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm text-muted-foreground">Result ID</dt>
                <dd className="font-mono text-sm text-foreground">{result.id}</dd>
              </div>
              <div>
                <dt className="text-sm text-muted-foreground">Extracted At</dt>
                <dd className="text-foreground">
                  {new Date(result.extractedAt).toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-muted-foreground">Source Image</dt>
                <dd className="text-foreground text-sm break-all">
                  {result.sourceImagePath}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-muted-foreground">Vote Validation</dt>
                <dd className="text-foreground">
                  {(() => {
                    const partySum = result.partyResults.reduce((sum, p) => sum + p.voteCount, 0);
                    const diff = Math.abs(partySum - result.validVotes);
                    return diff <= 2 ? (
                      <span className="text-green-600">✓ Valid (±{diff})</span>
                    ) : (
                      <span className="text-red-600">⚠ Mismatch ({diff} votes)</span>
                    );
                  })()}
                </dd>
              </div>
            </dl>
          </div>

          <div className="mt-4">
            <Link
              href="/results"
              className="block text-center px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors"
            >
              ← Back to Results
            </Link>
          </div>
        </div>
      </div>

      {/* Flag Modal */}
      {showFlagModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card rounded-lg border border-border p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-foreground mb-4">Flag Result for Review</h3>
            <textarea
              value={flagReason}
              onChange={(e) => setFlagReason(e.target.value)}
              placeholder="Describe the issue with this result..."
              className="w-full px-3 py-2 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring h-32 resize-none"
            />
            <div className="flex justify-end space-x-3 mt-4">
              <button
                onClick={() => setShowFlagModal(false)}
                className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleFlag}
                disabled={flagging || !flagReason.trim()}
                className="px-4 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 transition-colors disabled:opacity-50"
              >
                {flagging ? 'Flagging...' : 'Submit Flag'}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
