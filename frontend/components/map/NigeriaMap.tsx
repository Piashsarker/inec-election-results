'use client';

import { useRef, useState, useCallback, useEffect } from 'react';
import { NIGERIA_STATES, NIGERIA_VIEWBOX } from '@/lib/nigeria-map-data';
import { getStateFillColor } from '@/lib/color-scale';
import { StateAggregationData } from '@/types';

interface NigeriaMapProps {
  stateAggregations: Map<string, StateAggregationData>;
  hoveredStateCode: string | null;
  selectedStateCode: string | null;
  onStateHover: (stateCode: string | null, event?: React.MouseEvent) => void;
  onStateClick: (stateCode: string) => void;
  onStateFocus: (stateCode: string | null) => void;
}

function getLeadingPartyLabel(aggregation: StateAggregationData | null): string {
  if (!aggregation || !aggregation.partyResults || aggregation.partyResults.length === 0) {
    return 'No data';
  }
  const leading = aggregation.partyResults.reduce((best, current) =>
    current.voteCount > best.voteCount ? current : best
  );
  return `${leading.partyCode} ${leading.percentage.toFixed(1)}%`;
}

const MIN_ZOOM = 1;
const MAX_ZOOM = 5;
const ZOOM_STEP = 0.3;

export function NigeriaMap({
  stateAggregations,
  hoveredStateCode,
  selectedStateCode,
  onStateHover,
  onStateClick,
  onStateFocus,
}: NigeriaMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });

  // Reset zoom/pan when container resizes (responsive fit)
  useEffect(() => {
    const handleResize = () => {
      setZoom(1);
      setPan({ x: 0, y: 0 });
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleZoomIn = useCallback(() => {
    setZoom((prev) => Math.min(prev + ZOOM_STEP, MAX_ZOOM));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom((prev) => {
      const newZoom = Math.max(prev - ZOOM_STEP, MIN_ZOOM);
      // Reset pan if zooming back to 1
      if (newZoom <= 1) {
        setPan({ x: 0, y: 0 });
      }
      return newZoom;
    });
  }, []);

  const handleResetZoom = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, []);

  // Mouse wheel zoom
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    if (e.deltaY < 0) {
      setZoom((prev) => Math.min(prev + ZOOM_STEP * 0.5, MAX_ZOOM));
    } else {
      setZoom((prev) => {
        const newZoom = Math.max(prev - ZOOM_STEP * 0.5, MIN_ZOOM);
        if (newZoom <= 1) setPan({ x: 0, y: 0 });
        return newZoom;
      });
    }
  }, []);

  // Pan handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (zoom <= 1) return;
    // Only pan with middle mouse button or when holding space (we'll use left click when zoomed)
    if (e.button === 0) {
      setIsPanning(true);
      setPanStart({ x: e.clientX, y: e.clientY });
      setPanOffset(pan);
      e.preventDefault();
    }
  }, [zoom, pan]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isPanning) return;
    const dx = e.clientX - panStart.x;
    const dy = e.clientY - panStart.y;
    setPan({ x: panOffset.x + dx, y: panOffset.y + dy });
  }, [isPanning, panStart, panOffset]);

  const handleMouseUp = useCallback(() => {
    setIsPanning(false);
  }, []);

  // Touch support for pinch zoom and pan
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 1 && zoom > 1) {
      setIsPanning(true);
      setPanStart({ x: e.touches[0].clientX, y: e.touches[0].clientY });
      setPanOffset(pan);
    }
  }, [zoom, pan]);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!isPanning || e.touches.length !== 1) return;
    const dx = e.touches[0].clientX - panStart.x;
    const dy = e.touches[0].clientY - panStart.y;
    setPan({ x: panOffset.x + dx, y: panOffset.y + dy });
  }, [isPanning, panStart, panOffset]);

  const handleTouchEnd = useCallback(() => {
    setIsPanning(false);
  }, []);

  return (
    <div className="relative w-full" ref={containerRef}>
      {/* Zoom controls */}
      <div className="absolute top-3 right-3 z-20 flex flex-col gap-1">
        <button
          onClick={handleZoomIn}
          disabled={zoom >= MAX_ZOOM}
          className="w-8 h-8 flex items-center justify-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed text-gray-700 dark:text-gray-300 text-lg font-bold transition-colors"
          aria-label="Zoom in"
          title="Zoom in"
        >
          +
        </button>
        <button
          onClick={handleZoomOut}
          disabled={zoom <= MIN_ZOOM}
          className="w-8 h-8 flex items-center justify-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed text-gray-700 dark:text-gray-300 text-lg font-bold transition-colors"
          aria-label="Zoom out"
          title="Zoom out"
        >
          −
        </button>
        <button
          onClick={handleResetZoom}
          disabled={zoom === 1}
          className="w-8 h-8 flex items-center justify-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed text-gray-700 dark:text-gray-300 text-xs font-medium transition-colors"
          aria-label="Reset zoom"
          title="Reset zoom"
        >
          ⟲
        </button>
      </div>

      {/* Zoom level indicator */}
      {zoom > 1 && (
        <div className="absolute bottom-3 right-3 z-20 bg-white/80 dark:bg-gray-800/80 border border-gray-200 dark:border-gray-700 rounded px-2 py-1 text-xs text-gray-600 dark:text-gray-400">
          {Math.round(zoom * 100)}%
        </div>
      )}

      {/* Map container with overflow hidden for zoom */}
      <div
        className="w-full overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900"
        style={{ aspectRatio: '744.24 / 599.93' }}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <svg
          ref={svgRef}
          viewBox={NIGERIA_VIEWBOX}
          role="img"
          aria-label="Interactive map of Nigeria showing election results by state"
          className="w-full h-full"
          style={{
            transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
            transformOrigin: 'center center',
            transition: isPanning ? 'none' : 'transform 0.2s ease-out',
            cursor: zoom > 1 ? (isPanning ? 'grabbing' : 'grab') : 'default',
          }}
        >
          {NIGERIA_STATES.map((state) => {
            const aggregation = stateAggregations.get(state.code) || null;
            const fill = getStateFillColor(aggregation);
            const isHighlighted =
              hoveredStateCode === state.code || selectedStateCode === state.code;
            const ariaLabel = `${state.name} - ${getLeadingPartyLabel(aggregation)}`;

            return (
              <path
                key={state.code}
                d={state.path}
                fill={fill}
                data-state-code={state.code}
                tabIndex={0}
                aria-label={ariaLabel}
                stroke="#ffffff"
                strokeWidth={isHighlighted ? 3 : 1}
                className="cursor-pointer transition-all duration-150 outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                onMouseEnter={(e) => {
                  if (!isPanning) onStateHover(state.code, e);
                }}
                onMouseLeave={() => {
                  if (!isPanning) onStateHover(null);
                }}
                onClick={(e) => {
                  if (!isPanning) {
                    e.stopPropagation();
                    onStateClick(state.code);
                  }
                }}
                onFocus={() => onStateFocus(state.code)}
                onBlur={() => onStateFocus(null)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onStateClick(state.code);
                  }
                }}
              />
            );
          })}
        </svg>
      </div>

      {/* Pan hint when zoomed */}
      {zoom > 1 && !isPanning && (
        <p className="text-center text-xs text-gray-500 dark:text-gray-400 mt-2">
          Drag to pan • Scroll to zoom • Click reset to fit
        </p>
      )}
    </div>
  );
}

export default NigeriaMap;
