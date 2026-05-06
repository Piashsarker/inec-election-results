'use client';

import { StateAggregationData } from '@/types';

interface StateTooltipProps {
  stateName: string;
  aggregation: StateAggregationData | null;
  position: { x: number; y: number };
  visible: boolean;
}

export function StateTooltip({ stateName, aggregation, position, visible }: StateTooltipProps) {
  if (!visible) {
    return null;
  }

  const sortedParties = aggregation?.partyResults
    ? [...aggregation.partyResults].sort((a, b) => b.voteCount - a.voteCount)
    : [];

  const leadingParty = sortedParties[0] || null;
  const runnerUp = sortedParties[1] || null;

  return (
    <div
      className="pointer-events-none fixed z-50 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-3 min-w-[200px]"
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      <p className="font-bold text-sm text-gray-900 dark:text-gray-100 mb-1">{stateName}</p>

      {aggregation === null ? (
        <p className="text-xs text-gray-500 dark:text-gray-400">No data available</p>
      ) : (
        <div className="space-y-1">
          {leadingParty && (
            <p className="text-xs text-gray-700 dark:text-gray-300">
              <span className="font-medium">{leadingParty.partyCode}</span>:{' '}
              {leadingParty.voteCount.toLocaleString()} votes ({leadingParty.percentage.toFixed(1)}%)
            </p>
          )}
          {runnerUp && (
            <p className="text-xs text-gray-700 dark:text-gray-300">
              <span className="font-medium">{runnerUp.partyCode}</span>:{' '}
              {runnerUp.voteCount.toLocaleString()} votes ({runnerUp.percentage.toFixed(1)}%)
            </p>
          )}
          <p className="text-xs text-gray-500 dark:text-gray-400 pt-1 border-t border-gray-100 dark:border-gray-700">
            {aggregation.processedPollingUnits.toLocaleString()} /{' '}
            {aggregation.totalPollingUnits.toLocaleString()} PUs reported
          </p>
        </div>
      )}
    </div>
  );
}

export default StateTooltip;
