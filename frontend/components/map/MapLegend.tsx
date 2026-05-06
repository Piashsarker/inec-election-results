'use client';

import { PARTY_COLORS, DEFAULT_PARTY_COLOR, NO_DATA_COLOR } from '@/lib/party-colors';

interface MapLegendProps {
  className?: string;
}

const MAIN_PARTIES = [
  { code: 'APC', label: 'APC' },
  { code: 'PDP', label: 'PDP' },
  { code: 'LP', label: 'LP' },
  { code: 'NNPP', label: 'NNPP' },
];

export function MapLegend({ className }: MapLegendProps) {
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 ${className || ''}`}>
      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">Legend</h3>

      {/* Party colors */}
      <div className="space-y-2 mb-4">
        {MAIN_PARTIES.map((party) => (
          <div key={party.code} className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded-sm border border-gray-300"
              style={{ backgroundColor: PARTY_COLORS[party.code] }}
            />
            <span className="text-xs text-gray-700 dark:text-gray-300">{party.label}</span>
          </div>
        ))}
        <div className="flex items-center gap-2">
          <div
            className="w-4 h-4 rounded-sm border border-gray-300"
            style={{ backgroundColor: DEFAULT_PARTY_COLOR }}
          />
          <span className="text-xs text-gray-700 dark:text-gray-300">Others</span>
        </div>
        <div className="flex items-center gap-2">
          <div
            className="w-4 h-4 rounded-sm border border-gray-300"
            style={{ backgroundColor: NO_DATA_COLOR }}
          />
          <span className="text-xs text-gray-700 dark:text-gray-300">No data</span>
        </div>
      </div>

      {/* Intensity scale */}
      <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
        <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">Vote share intensity</p>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-gray-500">Low</span>
          <div
            className="flex-1 h-3 rounded-sm"
            style={{
              background: `linear-gradient(to right, hsl(152, 69%, 85%), hsl(152, 69%, 31%))`,
            }}
          />
          <span className="text-[10px] text-gray-500">High</span>
        </div>
      </div>
    </div>
  );
}

export default MapLegend;
