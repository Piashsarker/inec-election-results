/**
 * API client for INEC Election Results backend
 */

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

  // Jobs endpoints
  startScrapingJob: (config: Record<string, unknown>) =>
    fetchApi('/jobs/scrape', {
      method: 'POST',
      body: JSON.stringify(config),
    }),
  getJobStatus: (jobId: string) => fetchApi(`/jobs/${jobId}`),
  pauseJob: (jobId: string) => fetchApi(`/jobs/${jobId}/pause`, { method: 'POST' }),
  resumeJob: (jobId: string) => fetchApi(`/jobs/${jobId}/resume`, { method: 'POST' }),
  cancelJob: (jobId: string) => fetchApi(`/jobs/${jobId}`, { method: 'DELETE' }),

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
