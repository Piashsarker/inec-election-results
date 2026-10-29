/**
 * API client for INEC Election Results backend
 */

import { StateAggregationData, ScrapingJob } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/** Raw snake_case response shape from the bulk states aggregation endpoint */
interface StateAggregationResponse {
  level: string;
  location_id: string;
  location_name: string;
  election_type_id: string;
  election_type_code: string;
  party_results: {
    party_id: string;
    party_name: string;
    party_code: string;
    total_votes: number;
    percentage: number;
    rank: number;
  }[];
  total_valid_votes: number;
  total_accredited_voters: number;
  total_rejected_votes: number;
  total_polling_units: number;
  processed_polling_units: number;
  flagged_polling_units: number;
}

/** Transform snake_case API response to camelCase StateAggregationData */
export function transformStateAggregation(
  data: StateAggregationResponse[]
): StateAggregationData[] {
  return data.map((item) => ({
    stateCode: '',
    stateName: item.location_name,
    locationId: item.location_id,
    electionTypeId: item.election_type_id,
    electionTypeCode: item.election_type_code,
    partyResults: item.party_results.map((pr) => ({
      partyName: pr.party_name,
      partyCode: pr.party_code,
      voteCount: pr.total_votes,
      percentage: pr.percentage,
    })),
    totalValidVotes: item.total_valid_votes,
    totalAccreditedVoters: item.total_accredited_voters,
    totalRejectedVotes: item.total_rejected_votes,
    totalPollingUnits: item.total_polling_units,
    processedPollingUnits: item.processed_polling_units,
    flaggedPollingUnits: item.flagged_polling_units,
  }));
}

export const api = {
  // Elections endpoints
  getElectionTypes: () => fetchApi('/elections/types'),
  getStates: (electionType: string) => fetchApi(`/elections/${electionType}/states`),
  getLgas: (electionType: string, state: string) =>
    fetchApi(`/elections/${electionType}/${state}/lgas`),
  getWards: (electionType: string, state: string, lga: string) =>
    fetchApi(`/elections/${electionType}/${state}/${lga}/wards`),
  getPollingUnits: (electionType: string, state: string, lga: string, ward: string) =>
    fetchApi(`/elections/${electionType}/${state}/${lga}/${ward}/polling-units`),

  // Results endpoints
  getResults: (params?: Record<string, string>) => {
    const query = params ? `?${new URLSearchParams(params)}` : '';
    return fetchApi(`/results${query}`);
  },
  getResult: (id: string) => fetchApi(`/results/${id}`),
  flagResult: (id: string, reason: string) =>
    fetchApi(`/results/flag/${id}`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),

  // Aggregation endpoints
  getElectionTypeAggregation: (electionTypeId: string) =>
    fetchApi(`/aggregation/election-type/${electionTypeId}`),
  getWardAggregation: (wardId: string) => fetchApi(`/aggregation/ward/${wardId}`),
  getLgaAggregation: (lgaId: string) => fetchApi(`/aggregation/lga/${lgaId}`),
  getStateAggregation: (stateId: string) => fetchApi(`/aggregation/state/${stateId}`),
  getStatesAggregation: async (electionTypeId: string): Promise<StateAggregationData[]> => {
    const data = await fetchApi<StateAggregationResponse[]>(
      `/aggregation/states?election_type_id=${electionTypeId}`
    );
    return transformStateAggregation(data);
  },

  // Jobs endpoints
  startScrapingJob: (config: {
    url?: string;
    election_type?: string;
    target_state?: string;
    target_lga?: string;
    target_ward?: string;
  }) =>
    fetchApi<ScrapingJob>('/jobs/scrape', {
      method: 'POST',
      body: JSON.stringify(config),
    }),
  getJobStatus: (jobId: string) => fetchApi<ScrapingJob>(`/jobs/${jobId}`),
  pauseJob: (jobId: string) =>
    fetchApi<ScrapingJob>(`/jobs/${jobId}/pause`, { method: 'POST' }),
  resumeJob: (jobId: string) =>
    fetchApi<ScrapingJob>(`/jobs/${jobId}/resume`, { method: 'POST' }),
  cancelJob: (jobId: string) =>
    fetchApi<ScrapingJob>(`/jobs/${jobId}`, { method: 'DELETE' }),
  listJobs: () => fetchApi<ScrapingJob[]>('/jobs'),

  // Export endpoints
  exportCsv: (filters: Record<string, unknown>) =>
    fetchApi('/export/csv', {
      method: 'POST',
      body: JSON.stringify(filters),
    }),
  exportJson: (filters: Record<string, unknown>) =>
    fetchApi('/export/json', {
      method: 'POST',
      body: JSON.stringify(filters),
    }),
  downloadExport: (exportId: string) => fetchApi(`/export/${exportId}/download`),
};
