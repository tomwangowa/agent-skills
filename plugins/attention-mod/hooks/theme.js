/** Named terminal colours, so the pane follows the user's theme instead of fixed hex values. */
// muted is left out on purpose: gray vanished on the dock's gray background in the 2026-10-05 PoC, so it uses the terminal default.
const COLORS = {accent:'blue', success:'green', warning:'yellow', danger:'red', input:'magenta'};

/** Colour for a semantic tone; unknown tones return undefined, which draws in the terminal default. */
export function colorFor(tone) {
  return Object.hasOwn(COLORS, tone) ? COLORS[tone] : undefined;
}
