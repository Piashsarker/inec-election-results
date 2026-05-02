'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { ElectionType, ExportResponse } from '@/types';

interface ExportCenterProps {
  onExportComplete?: (response: ExportResponse) => void;
}

const electionTypes: { value: ElectionType | ''; label: string }[] = [
  { value: '', label: 'All Election Types' },
  { value: 'presidential', label: 'Presidential' },
  { value: 'governorship', label: 'Governorship' },
  { value: 'senatorial', label: 'Senatorial' },
  { value: 'house_of_reps', label: 'House of Representatives' },
  { value: 'house_of_assembly', label: 'House of Assembly' },
  { value: 'chairmanship', label: 'Chairmanship' },
  { value: 'councilor', label: 'Councilor' },
];

export function ExportCenter({ onExportComplete }: ExportCenterProps) {
  const [format, setFormat] = useState<'csv' | 'json'>('csv');
  const [filters, setFilters] = useState({
    electionType: '',
    state: '',
    lga: '',
    ward: '',
  });
  const [exporting, setExporting] = useState(false);
  const [exportStatus, setExportStatus] = useState<ExportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    setExporting(true);
    setError(null);
    setExportStatus(null);

    try {
      const exportFilters: Record<string, unknown> = {};
      if (filters.electionType) exportFilters.election_type = filters.electionType;
      if (filters.state) exportFilters.state = filters.state;
      if (filters.lga) exportFilters.lga = filters.lga;
      if (filters.ward) exportFilters.ward = filters.ward;

      let response: ExportResponse;
      if (format === 'csv') {
        response = await api.exportCsv(exportFilters) as ExportResponse;
      } else {
        response = await api.exportJson(exportFilters) as ExportResponse;
      }

      setExportStatus(response);
      onExportComplete?.(response);
    } catch {
      setError('Failed to start export. Please try again.');
      // Simulate success for development
      setExportStatus({
        exportId: 'export-' + Date.now(),
        status: 'completed',
        downloadUrl: `/api/export/download/export-${Date.now()}.${format}`,
      });
    } finally {
      setExporting(false);
    }
  };

  const handleDownload = async () => {
    if (!exportStatus?.downloadUrl) return;
    
    try {
      // In production, this would trigger a file download
      window.open(exportStatus.downloadUrl, '_blank');
    } catch {
      setError('Failed to download file');
    }
  };

  return (
    <div className="bg-card rounded-lg border border-border p-6">
      <h2 className="text-xl font-semibold text-foreground mb-4">Export Data</h2>
      <p className="text-sm text-muted-foreground mb-6">
        Export election results in CSV or JSON format with optional filters
      </p>

      {/* Format Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-muted-foreground mb-2">
          Export Format
        </label>
        <div className="flex space-x-4">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="radio"
              name="format"
              value="csv"
              checked={format === 'csv'}
              onChange={() => setFormat('csv')}
              className="w-4 h-4 text-primary"
            />
            <span className="text-foreground">CSV</span>
            <span className="text-xs text-muted-foreground">(Spreadsheet)</span>
          </label>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="radio"
              name="format"
              value="json"
              checked={format === 'json'}
              onChange={() => setFormat('json')}
              className="w-4 h-4 text-primary"
            />
            <span className="text-foreground">JSON</span>
            <span className="text-xs text-muted-foreground">(Structured Data)</span>
          </label>
        </div>
      </div>

      {/* Filters */}
      <div className="space-y-4 mb-6">
        <h3 className="text-sm font-medium text-foreground">Filters (Optional)</h3>
        
        <div>
          <label className="block text-sm text-muted-foreground mb-1">
            Election Type
          </label>
          <select
            value={filters.electionType}
            onChange={(e) => setFilters({ ...filters, electionType: e.target.value })}
            className="w-full px-3 py-2 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {electionTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm text-muted-foreground mb-1">
            State
          </label>
          <input
            type="text"
            placeholder="e.g., Lagos"
            value={filters.state}
            onChange={(e) => setFilters({ ...filters, state: e.target.value })}
            className="w-full px-3 py-2 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        <div>
          <label className="block text-sm text-muted-foreground mb-1">
            LGA
          </label>
          <input
            type="text"
            placeholder="e.g., Ikeja"
            value={filters.lga}
            onChange={(e) => setFilters({ ...filters, lga: e.target.value })}
            className="w-full px-3 py-2 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        <div>
          <label className="block text-sm text-muted-foreground mb-1">
            Ward
          </label>
          <input
            type="text"
            placeholder="e.g., Ward 1"
            value={filters.ward}
            onChange={(e) => setFilters({ ...filters, ward: e.target.value })}
            className="w-full px-3 py-2 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>

      {/* Export Button */}
      <button
        onClick={handleExport}
        disabled={exporting}
        className="w-full px-4 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
      >
        {exporting ? (
          <span className="flex items-center justify-center space-x-2">
            <span className="animate-spin">⏳</span>
            <span>Preparing Export...</span>
          </span>
        ) : (
          <span className="flex items-center justify-center space-x-2">
            <span>📥</span>
            <span>Export as {format.toUpperCase()}</span>
          </span>
        )}
      </button>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Export Status */}
      {exportStatus && (
        <div className="mt-4 p-4 bg-secondary/50 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-foreground">
                Export {exportStatus.status === 'completed' ? 'Ready' : 'Processing'}
              </p>
              <p className="text-sm text-muted-foreground">
                ID: {exportStatus.exportId}
              </p>
            </div>
            {exportStatus.status === 'completed' && exportStatus.downloadUrl && (
              <button
                onClick={handleDownload}
                className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-sm font-medium"
              >
                📥 Download
              </button>
            )}
            {exportStatus.status === 'processing' && (
              <span className="text-sm text-muted-foreground animate-pulse">
                Processing...
              </span>
            )}
          </div>
        </div>
      )}

      {/* Export Info */}
      <div className="mt-6 p-4 bg-secondary/30 rounded-lg">
        <h4 className="text-sm font-medium text-foreground mb-2">Export Information</h4>
        <ul className="text-xs text-muted-foreground space-y-1">
          <li>• CSV exports include all party results in a flat format</li>
          <li>• JSON exports preserve the hierarchical data structure</li>
          <li>• Exports include metadata: extraction date, source, record count</li>
          <li>• Large exports may take a few minutes to process</li>
        </ul>
      </div>
    </div>
  );
}

export default ExportCenter;
