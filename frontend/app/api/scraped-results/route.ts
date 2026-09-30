import { NextResponse } from 'next/server';
import { readFileSync } from 'fs';
import { join } from 'path';

/**
 * GET /api/scraped-results
 *
 * Fallback API route that serves scraped results from the local JSON file
 * when the backend API is unavailable.
 */
export async function GET() {
  try {
    const filePath = join(
      process.cwd(),
      '..',
      'backend',
      'data',
      'result_sheets',
      'osun_governorship_2026',
      'results_tesseract.json'
    );

    const fileContent = readFileSync(filePath, 'utf-8');
    const data = JSON.parse(fileContent);

    // Transform to match the backend API response shape
    const response = {
      election: data.election,
      date: data.date,
      state: data.state,
      lga: data.lga,
      ward: data.ward,
      ward_code: data.ward_code,
      polling_units_processed: data.polling_units_processed,
      polling_units_total: data.polling_units_total,
      total_accredited_voters: data.total_accredited_voters,
      total_valid_votes: data.total_valid_votes,
      total_rejected_votes: data.total_rejected_votes,
      party_totals: data.party_totals,
      results: data.results,
    };

    return NextResponse.json(response);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json(
      { error: 'Failed to load scraped results', detail: message },
      { status: 500 }
    );
  }
}
