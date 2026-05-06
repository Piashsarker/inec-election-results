/**
 * Party color constants for the Nigeria election results map.
 * Maps party codes to their official brand hex colors.
 */

/** Party code to hex color mapping */
export const PARTY_COLORS: Record<string, string> = {
  APC: '#008751', // Green (Nigeria flag green)
  PDP: '#E31B23', // Red
  LP: '#5B9BD5', // Light blue
  NNPP: '#FF8C00', // Orange
  APGA: '#006400', // Dark green
  ADC: '#FFD700', // Gold
  SDP: '#FF1493', // Deep pink
  YPP: '#00CED1', // Dark turquoise
};

/** Fallback color for parties not in PARTY_COLORS */
export const DEFAULT_PARTY_COLOR = '#6B7280'; // gray-500

/** Color for states with no aggregation data */
export const NO_DATA_COLOR = '#D1D5DB'; // gray-300
