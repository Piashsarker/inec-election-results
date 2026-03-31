/**
 * TypeScript interfaces for INEC Election Results Dashboard
 * Validates: Requirements 5.1, 5.2, 5.3
 */

// Election type enumeration
export type ElectionType =
  | 'presidential'
  | 'governorship'
  | 'senatorial'
  | 'house_of_reps'
  | 'house_of_assembly'
  | 'chairmanship'
  | 'councilor';

// Job status enumeration
export type JobStatus =
  | 'queued'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled';

// Party result for individual polling unit or aggregation
export interface PartyResult {
  partyName: string;
  partyCode: string;
  voteCount: number;
  percentage: number;
}

// Election result from a single polling unit
export interface ElectionResult {
  id: string;
  electionType: ElectionType;
  state: string;
  lga: string;
  ward: string;
  pollingUnit: string;
  partyResults: PartyResult[];
  accreditedVoters: number;
  validVotes: number;
  rejectedVotes: number;
  extractedAt: Date;
  confidenceScore: number;
  sourceImagePath: string;
}

// Aggregated result at ward, LGA, or state level
export interface AggregatedResult {
  level: 'ward' | 'lga' | 'state';
  locationId: string;
  locationName: string;
  partyResults: PartyResult[];
  totalPollingUnits: number;
  processedPollingUnits: number;
  flaggedPollingUnits: number;
}

// Geographic hierarchy types
export interface State {
  id: string;
  name: string;
  code: string;
  totalLgas: number;
}

export interface LGA {
  id: string;
  stateId: string;
  name: string;
  code: string;
  totalWards: number;
}

export interface Ward {
  id: string;
  lgaId: string;
  name: string;
  code: string;
  totalPollingUnits: number;
}

export interface PollingUnit {
  id: string;
  wardId: string;
  name: string;
  code: string;
  delimitation?: string;
}

// Scraping job tracking
export interface ScrapingJob {
  id: string;
  status: JobStatus;
  electionType?: string;
  targetState?: string;
  targetLga?: string;
  targetWard?: string;
  totalPollingUnits: number;
  processedCount: number;
  successCount: number;
  failedCount: number;
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
}

// Flagged result for manual review
export interface FlaggedResult {
  id: string;
  electionResultId: string;
  reason: string;
  status: 'pending' | 'reviewed' | 'resolved';
  reviewNotes?: Record<string, unknown>;
  createdAt: Date;
  reviewedAt?: Date;
}

// API response types
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiError {
  message: string;
  code: string;
  details?: Record<string, unknown>;
}

// Export request types
export interface ExportRequest {
  format: 'csv' | 'json';
  electionType?: ElectionType;
  state?: string;
  lga?: string;
  ward?: string;
}

export interface ExportResponse {
  exportId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  downloadUrl?: string;
}
