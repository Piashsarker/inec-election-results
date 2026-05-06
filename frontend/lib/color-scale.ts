/**
 * Color scale utility for the Nigeria election results map.
 * Computes fill colors for states based on leading party and vote share.
 */

import { PARTY_COLORS, DEFAULT_PARTY_COLOR, NO_DATA_COLOR } from './party-colors';

/** Minimal aggregation data shape needed for color computation */
export interface StateAggregationData {
  stateCode: string;
  stateName: string;
  locationId: string;
  electionTypeId: string;
  electionTypeCode: string;
  partyResults: PartyResult[];
  totalValidVotes: number;
  totalAccreditedVoters: number;
  totalRejectedVotes: number;
  totalPollingUnits: number;
  processedPollingUnits: number;
  flaggedPollingUnits: number;
}

interface PartyResult {
  partyName: string;
  partyCode: string;
  voteCount: number;
  percentage: number;
}

/**
 * Compute fill color for a state based on leading party and vote share.
 *
 * Algorithm:
 * 1. If no data → return NO_DATA_COLOR (gray)
 * 2. Get leading party (rank 1 or highest votes)
 * 3. Get party color from PARTY_COLORS (fallback to DEFAULT_PARTY_COLOR)
 * 4. Calculate vote share percentage from leading party
 * 5. Map vote share to intensity: clamp((voteSharePercent - 30) / 50, 0.3, 1.0)
 * 6. Return color with computed intensity as HSL with adjusted lightness
 */
export function getStateFillColor(aggregation: StateAggregationData | null): string {
  if (!aggregation || !aggregation.partyResults || aggregation.partyResults.length === 0) {
    return NO_DATA_COLOR;
  }

  // Get leading party (highest votes)
  const leadingParty = aggregation.partyResults.reduce((best, current) =>
    current.voteCount > best.voteCount ? current : best
  );

  const baseColor = PARTY_COLORS[leadingParty.partyCode] ?? DEFAULT_PARTY_COLOR;
  const voteSharePercent = leadingParty.percentage;
  const intensity = clamp((voteSharePercent - 30) / 50, 0.3, 1.0);

  return applyIntensity(baseColor, intensity);
}

/**
 * Convert hex color + intensity (0-1) to an HSL string with adjusted lightness.
 * intensity=1 → original color, intensity=0.3 → very light tint
 */
export function applyIntensity(hexColor: string, intensity: number): string {
  const { h, s, l } = hexToHsl(hexColor);
  // Adjust lightness: lower intensity → higher lightness (lighter color)
  const adjustedLightness = 100 - (100 - l) * intensity;
  return `hsl(${Math.round(h)}, ${Math.round(s)}%, ${Math.round(adjustedLightness)}%)`;
}

/** Clamp a value between min and max */
function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/** Convert a hex color string to HSL values */
function hexToHsl(hex: string): { h: number; s: number; l: number } {
  // Remove # prefix if present
  const cleanHex = hex.replace(/^#/, '');

  const r = parseInt(cleanHex.substring(0, 2), 16) / 255;
  const g = parseInt(cleanHex.substring(2, 4), 16) / 255;
  const b = parseInt(cleanHex.substring(4, 6), 16) / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const l = (max + min) / 2;

  if (max === min) {
    // Achromatic
    return { h: 0, s: 0, l: l * 100 };
  }

  const d = max - min;
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);

  let h: number;
  switch (max) {
    case r:
      h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
      break;
    case g:
      h = ((b - r) / d + 2) / 6;
      break;
    default:
      h = ((r - g) / d + 4) / 6;
      break;
  }

  return { h: h * 360, s: s * 100, l: l * 100 };
}
