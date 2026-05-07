'use client';

import { useState, useEffect, useCallback } from 'react';
import { NigeriaMap } from '@/components/map/NigeriaMap';
import { StateTooltip } from '@/components/map/StateTooltip';
import { MapLegend } from '@/components/map/MapLegend';
import { StateDetailPanel } from '@/components/map/StateDetailPanel';
import { ElectionTypeSelector } from '@/components/map/ElectionTypeSelector';
import { api } from '@/lib/api';
import { STATES_BY_CODE } from '@/lib/nigeria-map-data';
import { calculateTooltipPosition } from '@/lib/tooltip-position';
import { DEMO_ELECTION_TYPES, generateDemoData } from '@/lib/demo-map-data';
import { StateAggregationData, ElectionTypeOption } from '@/types';

interface MapSectionProps {
  /** Whether to show the header with title and demo data badge */
  showHeader?: boolean;
  /** Optional className for the container */
  className?: string;
  /** When true, constrains map height for embedded usage */
  compact?: boolean;
  /** Externally controlled election type ID (lifts state to parent) */
  externalElectionTypeId?: string | null;
  /** Callback when user changes election type via the selector */
  onElectionTypeChange?: (id: string) => void;
  /** Pre-fetched election types from parent (avoids duplicate fetch) */
  externalElectionTypes?: ElectionTypeOption[];
  /** Whether demo data mode is active (controlled by parent) */
  externalUsingDemoData?: boolean;
}

export function MapSection({
  showHeader = true,
  className = '',
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  compact = false,
  externalElectionTypeId,
  onElectionTypeChange,
  externalElectionTypes,
  externalUsingDemoData,
}: MapSectionProps) {
  const isControlled = externalElectionTypeId !== undefined;

  const [internalElectionTypes, setInternalElectionTypes] = useState<ElectionTypeOption[]>([]);
  const [internalSelectedId, setInternalSelectedId] = useState<string | null>(null);
  const [stateAggregations, setStateAggregations] = useState<Map<string, StateAggregationData>>(
    new Map()
  );
  const [hoveredStateCode, setHoveredStateCode] = useState<string | null>(null);
  const [selectedStateCode, setSelectedStateCode] = useState<string | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<{ x: number; y: number }>({
    x: 0,
    y: 0,
  });
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [internalUsingDemoData, setInternalUsingDemoData] = useState<boolean>(false);

  // Resolve controlled vs uncontrolled state
  const electionTypes = isControlled
    ? externalElectionTypes ?? internalElectionTypes
    : internalElectionTypes;
  const selectedElectionTypeId = isControlled ? externalElectionTypeId : internalSelectedId;
  const usingDemoData = isControlled
    ? externalUsingDemoData ?? internalUsingDemoData
    : internalUsingDemoData;

  // Fetch election types on mount — fall back to demo data if API unavailable
  // Skip if parent is controlling election type state
  useEffect(() => {
    if (isControlled) return;

    async function fetchElectionTypes() {
      try {
        const types = (await api.getElectionTypes()) as ElectionTypeOption[];
        setInternalElectionTypes(types);
        const presidential = types.find((t) => t.code === 'presidential');
        if (presidential) {
          setInternalSelectedId(presidential.id);
        } else if (types.length > 0) {
          setInternalSelectedId(types[0].id);
        }
      } catch {
        // API unavailable — use demo data
        console.info('API unavailable, using demo data');
        setInternalUsingDemoData(true);
        setInternalElectionTypes(DEMO_ELECTION_TYPES);
        setInternalSelectedId(DEMO_ELECTION_TYPES[0].id);
      }
    }
    fetchElectionTypes();
  }, [isControlled]);

  // Fetch state aggregations when election type changes
  useEffect(() => {
    if (!selectedElectionTypeId) return;

    async function fetchAggregations() {
      setLoading(true);
      setError(null);

      // If using demo data (API was unreachable), generate it locally
      if (usingDemoData || selectedElectionTypeId!.startsWith('demo-')) {
        const demoMap = generateDemoData(selectedElectionTypeId!);
        setStateAggregations(demoMap);
        setLoading(false);
        return;
      }

      try {
        const data = await api.getStatesAggregation(selectedElectionTypeId!);
        const aggregationMap = new Map<string, StateAggregationData>();

        for (const item of data) {
          const matchedCode = Object.entries(STATES_BY_CODE).find(
            ([, stateData]) =>
              stateData.name.toLowerCase() === item.stateName.toLowerCase()
          );
          if (matchedCode) {
            aggregationMap.set(matchedCode[0], { ...item, stateCode: matchedCode[0] });
          }
        }

        if (aggregationMap.size === 0 && data.length === 0) {
          console.info('No aggregation data from API, using demo data for preview');
          const demoMap = generateDemoData(selectedElectionTypeId!);
          setStateAggregations(demoMap);
          if (!isControlled) setInternalUsingDemoData(true);
        } else {
          setStateAggregations(aggregationMap);
        }
      } catch {
        console.info('Aggregation API failed, falling back to demo data');
        if (!isControlled) setInternalUsingDemoData(true);
        const demoMap = generateDemoData(selectedElectionTypeId!);
        setStateAggregations(demoMap);
        setError(null);
      } finally {
        setLoading(false);
      }
    }
    fetchAggregations();
  }, [selectedElectionTypeId, usingDemoData, isControlled]);

  const handleStateHover = useCallback(
    (stateCode: string | null, event?: React.MouseEvent) => {
      setHoveredStateCode(stateCode);
      if (event && stateCode) {
        const pos = calculateTooltipPosition(
          event.clientX,
          event.clientY,
          220,
          120,
          window.innerWidth,
          window.innerHeight
        );
        setTooltipPosition(pos);
      }
    },
    []
  );

  const handleStateClick = useCallback((stateCode: string) => {
    setSelectedStateCode(stateCode);
  }, []);

  const handleStateFocus = useCallback((stateCode: string | null) => {
    setHoveredStateCode(stateCode);
  }, []);

  const handleElectionTypeSelect = useCallback((id: string) => {
    if (isControlled && onElectionTypeChange) {
      onElectionTypeChange(id);
    } else {
      setInternalSelectedId(id);
    }
  }, [isControlled, onElectionTypeChange]);

  const handleDetailClose = useCallback(() => {
    setSelectedStateCode(null);
  }, []);

  // Derive tooltip data
  const hoveredStateName = hoveredStateCode
    ? STATES_BY_CODE[hoveredStateCode]?.name ?? ''
    : '';
  const hoveredAggregation = hoveredStateCode
    ? stateAggregations.get(hoveredStateCode) ?? null
    : null;

  // Derive detail panel data
  const selectedStateName = selectedStateCode
    ? STATES_BY_CODE[selectedStateCode]?.name ?? ''
    : '';
  const selectedAggregation = selectedStateCode
    ? stateAggregations.get(selectedStateCode) ?? null
    : null;

  return (
    <section className={className}>
      {showHeader && (
        <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Election Results Map
            </h1>
          </div>
          <ElectionTypeSelector
            electionTypes={electionTypes}
            selectedId={selectedElectionTypeId}
            onSelect={handleElectionTypeSelect}
            loading={electionTypes.length === 0 && !error}
          />
        </header>
      )}

      {!showHeader && (
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3" />
          <ElectionTypeSelector
            electionTypes={electionTypes}
            selectedId={selectedElectionTypeId}
            onSelect={handleElectionTypeSelect}
            loading={electionTypes.length === 0 && !error}
          />
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="flex flex-col lg:flex-row gap-4">
        <div className="flex-1 relative min-h-0">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/60 dark:bg-gray-900/60 z-10 rounded-lg">
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <svg
                  className="animate-spin h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Loading map data...
              </div>
            </div>
          )}
          <NigeriaMap
            stateAggregations={stateAggregations}
            hoveredStateCode={hoveredStateCode}
            selectedStateCode={selectedStateCode}
            onStateHover={handleStateHover}
            onStateClick={handleStateClick}
            onStateFocus={handleStateFocus}
          />
          <StateTooltip
            stateName={hoveredStateName}
            aggregation={hoveredAggregation}
            position={tooltipPosition}
            visible={hoveredStateCode !== null}
          />
        </div>
        <aside className="lg:w-56 shrink-0">
          <MapLegend />
        </aside>
      </div>

      <StateDetailPanel
        open={selectedStateCode !== null}
        onClose={handleDetailClose}
        stateName={selectedStateName}
        aggregation={selectedAggregation}
      />
    </section>
  );
}

export default MapSection;
