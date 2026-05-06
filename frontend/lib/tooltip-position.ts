/**
 * Tooltip position utility for the Nigeria election results map.
 * Calculates tooltip position ensuring it stays within viewport bounds.
 */

export interface TooltipPosition {
  x: number;
  y: number;
}

/**
 * Calculate tooltip position ensuring it stays within viewport.
 *
 * Default: offset 12px right and 12px below cursor.
 * If tooltip would overflow right edge, flip to left of cursor.
 * If tooltip would overflow bottom edge, flip above cursor.
 * Final position is clamped to ensure x >= 0 and y >= 0.
 *
 * @param cursorX - Current cursor X position
 * @param cursorY - Current cursor Y position
 * @param tooltipWidth - Width of the tooltip element
 * @param tooltipHeight - Height of the tooltip element
 * @param viewportWidth - Width of the viewport
 * @param viewportHeight - Height of the viewport
 * @param offset - Offset from cursor in pixels (default: 12)
 * @returns Calculated tooltip position
 */
export function calculateTooltipPosition(
  cursorX: number,
  cursorY: number,
  tooltipWidth: number,
  tooltipHeight: number,
  viewportWidth: number,
  viewportHeight: number,
  offset: number = 12
): TooltipPosition {
  // Default: position tooltip to the right and below cursor
  let x = cursorX + offset;
  let y = cursorY + offset;

  // If tooltip would overflow right edge, flip to left of cursor
  if (x + tooltipWidth > viewportWidth) {
    x = cursorX - tooltipWidth - offset;
  }

  // If tooltip would overflow bottom edge, flip above cursor
  if (y + tooltipHeight > viewportHeight) {
    y = cursorY - tooltipHeight - offset;
  }

  // Clamp to ensure tooltip stays within viewport
  x = Math.max(0, x);
  y = Math.max(0, y);

  return { x, y };
}
