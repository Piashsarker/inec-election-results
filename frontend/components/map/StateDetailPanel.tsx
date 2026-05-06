'use client';

import * as Dialog from '@radix-ui/react-dialog';
import { StateAggregationData } from '@/types';
import { PARTY_COLORS, DEFAULT_PARTY_COLOR } from '@/lib/party-colors';
import Link from 'next/link';

interface StateDetailPanelProps {
  open: boolean;
  onClose: () => void;
  stateName: string;
  aggregation: StateAggregationData | null;
}

export function StateDetailPanel({
  open,
  onClose,
  stateName,
  aggregation,
}: StateDetailPanelProps) {
  const sortedParties = aggregation?.partyResults
    ? [...aggregation.partyResults].sort((a, b) => b.voteCount - a.voteCount)
    : [];

  const maxVotes = sortedParties.length > 0 ? sortedParties[0].voteCount : 0;

  const progressPercent =
    aggregation && aggregation.totalPollingUnits > 0
      ? (aggregation.processedPollingUnits / aggregation.totalPollingUnits) * 100
      : 0;

  return (
    <Dialog.Root open={open} onOpenChange={(isOpen) => { if (!isOpen) onClose(); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-40" />
        <Dialog.Content className="fixed right-0 top-0 h-full w-[400px] max-w-[90vw] bg-white dark:bg-gray-900 overflow-y-auto p-6 z-50 shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <Dialog.Title className="text-lg font-bold text-gray-900 dark:text-gray-100">
              {stateName}
            </Dialog.Title>
            <Dialog.Close asChild>
              <button
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 p-1 rounded"
                aria-label="Close"
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 5l10 10M15 5L5 15" />
                </svg>
              </button>
            </Dialog.Close>
          </div>

          {aggregation === null ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              No data available for this state.
            </p>
          ) : (
            <div className="space-y-6">
              {/* Summary stats grid */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Valid Votes</p>
                  <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {aggregation.totalValidVotes.toLocaleString()}
                  </p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Rejected</p>
                  <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {aggregation.totalRejectedVotes.toLocaleString()}
                  </p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Accredited</p>
                  <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {aggregation.totalAccreditedVoters.toLocaleString()}
                  </p>
                </div>
              </div>

              {/* Processing progress */}
              <div>
                <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                  <span>Processing Progress</span>
                  <span>
                    {aggregation.processedPollingUnits.toLocaleString()} /{' '}
                    {aggregation.totalPollingUnits.toLocaleString()} PUs
                  </span>
                </div>
                <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full transition-all duration-300"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>

              {/* Party results */}
              <div>
                <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Party Results
                </h4>
                <div className="space-y-2">
                  {sortedParties.map((party) => {
                    const barWidth = maxVotes > 0 ? (party.voteCount / maxVotes) * 100 : 0;
                    const color = PARTY_COLORS[party.partyCode] ?? DEFAULT_PARTY_COLOR;

                    return (
                      <div key={party.partyCode} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="font-medium text-gray-700 dark:text-gray-300">
                            {party.partyCode}
                          </span>
                          <span className="text-gray-500 dark:text-gray-400">
                            {party.voteCount.toLocaleString()} ({party.percentage.toFixed(1)}%)
                          </span>
                        </div>
                        <div className="w-full h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-300"
                            style={{ width: `${barWidth}%`, backgroundColor: color }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Flagged results */}
              {aggregation.flaggedPollingUnits > 0 && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                  <p className="text-xs text-yellow-800 dark:text-yellow-200">
                    ⚠️ {aggregation.flaggedPollingUnits} flagged result
                    {aggregation.flaggedPollingUnits > 1 ? 's' : ''}
                  </p>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-2 border-t border-gray-200 dark:border-gray-700">
                <Link
                  href={`/aggregation?state=${aggregation.locationId}`}
                  className="flex-1 text-center text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 border border-blue-200 dark:border-blue-800 rounded-lg py-2 px-3 transition-colors"
                >
                  View LGA Breakdown
                </Link>
                <button
                  className="flex-1 text-center text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 border border-gray-200 dark:border-gray-700 rounded-lg py-2 px-3 transition-colors"
                  onClick={() => {
                    // Placeholder for export functionality
                  }}
                >
                  Export
                </button>
              </div>
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export default StateDetailPanel;
