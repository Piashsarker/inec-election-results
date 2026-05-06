/**
 * Demo election data for the Nigeria map visualization.
 * Provides realistic sample data for all election categories
 * so the map can be previewed without a live backend.
 */

import { StateAggregationData, ElectionTypeOption } from '@/types';
import { NIGERIA_STATES } from './nigeria-map-data';

/** Demo election types */
export const DEMO_ELECTION_TYPES: ElectionTypeOption[] = [
  { id: 'demo-presidential', name: 'Presidential', code: 'presidential' },
  { id: 'demo-governorship', name: 'Governorship', code: 'governorship' },
  { id: 'demo-senatorial', name: 'Senatorial', code: 'senatorial' },
  { id: 'demo-house-of-reps', name: 'House of Representatives', code: 'house_of_reps' },
  { id: 'demo-house-of-assembly', name: 'State House of Assembly', code: 'house_of_assembly' },
];

// Seeded random number generator for consistent demo data
function seededRandom(seed: number): () => number {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) & 0xffffffff;
    return (s >>> 0) / 0xffffffff;
  };
}

// Party distribution profiles per region
interface RegionProfile {
  apc: number;
  pdp: number;
  lp: number;
  nnpp: number;
  others: number;
}

// Regional voting patterns (approximate real-world tendencies)
const REGION_PROFILES: Record<string, RegionProfile> = {
  // North West - APC dominant
  NW: { apc: 0.55, pdp: 0.25, lp: 0.05, nnpp: 0.12, others: 0.03 },
  // North East - APC dominant
  NE: { apc: 0.50, pdp: 0.30, lp: 0.05, nnpp: 0.10, others: 0.05 },
  // North Central - Mixed
  NC: { apc: 0.35, pdp: 0.35, lp: 0.15, nnpp: 0.08, others: 0.07 },
  // South West - APC leaning
  SW: { apc: 0.40, pdp: 0.20, lp: 0.30, nnpp: 0.03, others: 0.07 },
  // South East - LP dominant
  SE: { apc: 0.10, pdp: 0.20, lp: 0.60, nnpp: 0.03, others: 0.07 },
  // South South - PDP dominant
  SS: { apc: 0.15, pdp: 0.45, lp: 0.30, nnpp: 0.03, others: 0.07 },
};

// Map state codes to geopolitical zones
const STATE_ZONES: Record<string, string> = {
  // North West
  KD: 'NW', KN: 'NW', KT: 'NW', KE: 'NW', SO: 'NW', ZA: 'NW', JI: 'NW',
  // North East
  AD: 'NE', BA: 'NE', BO: 'NE', GO: 'NE', TA: 'NE', YO: 'NE',
  // North Central
  BE: 'NC', KO: 'NC', KW: 'NC', NA: 'NC', NI: 'NC', PL: 'NC', FC: 'NC',
  // South West
  EK: 'SW', LA: 'SW', OG: 'SW', ON: 'SW', OS: 'SW', OY: 'SW',
  // South East
  AB: 'SE', AN: 'SE', EB: 'SE', EN: 'SE', IM: 'SE',
  // South South
  AK: 'SS', BY: 'SS', CR: 'SS', DE: 'SS', ED: 'SS', RI: 'SS',
};

// Polling unit counts per state (approximate real values)
const STATE_PU_COUNTS: Record<string, number> = {
  AB: 3527, AD: 4104, AK: 3523, AN: 5720, BA: 5312,
  BY: 1804, BE: 4496, BO: 5071, CR: 3281, DE: 4332,
  EB: 2940, ED: 4235, EK: 2195, EN: 4145, FC: 2822,
  GO: 2397, IM: 3756, JI: 4523, KD: 8012, KN: 11222,
  KT: 7002, KE: 3482, KO: 3508, KW: 2887, LA: 13325,
  NA: 2780, NI: 5498, OG: 4959, ON: 3933, OS: 3763,
  OY: 6390, PL: 4022, RI: 6866, SO: 4244, TA: 3521,
  YO: 2912, ZA: 3352,
};

function generateStateData(
  stateCode: string,
  electionTypeCode: string,
  electionTypeId: string,
  rand: () => number
): StateAggregationData {
  const zone = STATE_ZONES[stateCode] || 'NC';
  const profile = { ...REGION_PROFILES[zone] };

  // Add variation per election type
  if (electionTypeCode === 'governorship') {
    // More regional variation for governorship
    const shift = (rand() - 0.5) * 0.2;
    profile.apc += shift;
    profile.pdp -= shift * 0.5;
    profile.lp -= shift * 0.5;
  } else if (electionTypeCode === 'senatorial') {
    // Slightly different from presidential
    const shift = (rand() - 0.5) * 0.15;
    profile.pdp += shift;
    profile.apc -= shift;
  }

  // Normalize
  const total = profile.apc + profile.pdp + profile.lp + profile.nnpp + profile.others;
  profile.apc /= total;
  profile.pdp /= total;
  profile.lp /= total;
  profile.nnpp /= total;
  profile.others /= total;

  // Add per-state randomness
  const noise = () => 1 + (rand() - 0.5) * 0.3;
  const rawApc = profile.apc * noise();
  const rawPdp = profile.pdp * noise();
  const rawLp = profile.lp * noise();
  const rawNnpp = profile.nnpp * noise();
  const rawOthers = profile.others * noise();
  const rawTotal = rawApc + rawPdp + rawLp + rawNnpp + rawOthers;

  const totalPUs = STATE_PU_COUNTS[stateCode] || 3000;
  const processedPUs = Math.floor(totalPUs * (0.6 + rand() * 0.35));
  const accreditedVoters = Math.floor(processedPUs * (180 + rand() * 120));
  const validVotes = Math.floor(accreditedVoters * (0.75 + rand() * 0.2));
  const rejectedVotes = Math.floor(validVotes * (0.01 + rand() * 0.03));

  const apcVotes = Math.floor(validVotes * (rawApc / rawTotal));
  const pdpVotes = Math.floor(validVotes * (rawPdp / rawTotal));
  const lpVotes = Math.floor(validVotes * (rawLp / rawTotal));
  const nnppVotes = Math.floor(validVotes * (rawNnpp / rawTotal));
  const othersVotes = validVotes - apcVotes - pdpVotes - lpVotes - nnppVotes;

  const partyResults = [
    { partyName: 'All Progressives Congress', partyCode: 'APC', voteCount: apcVotes, percentage: +(apcVotes / validVotes * 100).toFixed(1) },
    { partyName: 'Peoples Democratic Party', partyCode: 'PDP', voteCount: pdpVotes, percentage: +(pdpVotes / validVotes * 100).toFixed(1) },
    { partyName: 'Labour Party', partyCode: 'LP', voteCount: lpVotes, percentage: +(lpVotes / validVotes * 100).toFixed(1) },
    { partyName: 'New Nigeria Peoples Party', partyCode: 'NNPP', voteCount: nnppVotes, percentage: +(nnppVotes / validVotes * 100).toFixed(1) },
    { partyName: 'Others', partyCode: 'OTH', voteCount: othersVotes, percentage: +(othersVotes / validVotes * 100).toFixed(1) },
  ].sort((a, b) => b.voteCount - a.voteCount);

  const stateName = NIGERIA_STATES.find((s) => s.code === stateCode)?.name || stateCode;

  return {
    stateCode,
    stateName,
    locationId: `demo-${stateCode.toLowerCase()}`,
    electionTypeId,
    electionTypeCode,
    partyResults,
    totalValidVotes: validVotes,
    totalAccreditedVoters: accreditedVoters,
    totalRejectedVotes: rejectedVotes,
    totalPollingUnits: totalPUs,
    processedPollingUnits: processedPUs,
    flaggedPollingUnits: Math.floor(rand() * 15),
  };
}

/**
 * Generate demo aggregation data for all states for a given election type.
 */
export function generateDemoData(electionTypeId: string): Map<string, StateAggregationData> {
  const electionType = DEMO_ELECTION_TYPES.find((t) => t.id === electionTypeId);
  const electionTypeCode = electionType?.code || 'presidential';

  // Use election type as seed for consistent results per category
  const seed = electionTypeId.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const rand = seededRandom(seed);

  const map = new Map<string, StateAggregationData>();

  for (const state of NIGERIA_STATES) {
    const data = generateStateData(state.code, electionTypeCode, electionTypeId, rand);
    map.set(state.code, data);
  }

  return map;
}
