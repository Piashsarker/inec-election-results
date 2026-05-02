'use client';

import Link from 'next/link';
import { useState } from 'react';
import { State } from '@/types';

interface PageProps {
  params: { type: string };
}

// Nigerian states list
const nigerianStates: State[] = [
  { id: '1', name: 'Abia', code: 'AB', totalLgas: 17 },
  { id: '2', name: 'Adamawa', code: 'AD', totalLgas: 21 },
  { id: '3', name: 'Akwa Ibom', code: 'AK', totalLgas: 31 },
  { id: '4', name: 'Anambra', code: 'AN', totalLgas: 21 },
  { id: '5', name: 'Bauchi', code: 'BA', totalLgas: 20 },
  { id: '6', name: 'Bayelsa', code: 'BY', totalLgas: 8 },
  { id: '7', name: 'Benue', code: 'BE', totalLgas: 23 },
  { id: '8', name: 'Borno', code: 'BO', totalLgas: 27 },
  { id: '9', name: 'Cross River', code: 'CR', totalLgas: 18 },
  { id: '10', name: 'Delta', code: 'DE', totalLgas: 25 },
  { id: '11', name: 'Ebonyi', code: 'EB', totalLgas: 13 },
  { id: '12', name: 'Edo', code: 'ED', totalLgas: 18 },
  { id: '13', name: 'Ekiti', code: 'EK', totalLgas: 16 },
  { id: '14', name: 'Enugu', code: 'EN', totalLgas: 17 },
  { id: '15', name: 'FCT', code: 'FC', totalLgas: 6 },
  { id: '16', name: 'Gombe', code: 'GO', totalLgas: 11 },
  { id: '17', name: 'Imo', code: 'IM', totalLgas: 27 },
  { id: '18', name: 'Jigawa', code: 'JI', totalLgas: 27 },
  { id: '19', name: 'Kaduna', code: 'KD', totalLgas: 23 },
  { id: '20', name: 'Kano', code: 'KN', totalLgas: 44 },
  { id: '21', name: 'Katsina', code: 'KT', totalLgas: 34 },
  { id: '22', name: 'Kebbi', code: 'KE', totalLgas: 21 },
  { id: '23', name: 'Kogi', code: 'KO', totalLgas: 21 },
  { id: '24', name: 'Kwara', code: 'KW', totalLgas: 16 },
  { id: '25', name: 'Lagos', code: 'LA', totalLgas: 20 },
  { id: '26', name: 'Nasarawa', code: 'NA', totalLgas: 13 },
  { id: '27', name: 'Niger', code: 'NI', totalLgas: 25 },
  { id: '28', name: 'Ogun', code: 'OG', totalLgas: 20 },
  { id: '29', name: 'Ondo', code: 'ON', totalLgas: 18 },
  { id: '30', name: 'Osun', code: 'OS', totalLgas: 30 },
  { id: '31', name: 'Oyo', code: 'OY', totalLgas: 33 },
  { id: '32', name: 'Plateau', code: 'PL', totalLgas: 17 },
  { id: '33', name: 'Rivers', code: 'RI', totalLgas: 23 },
  { id: '34', name: 'Sokoto', code: 'SO', totalLgas: 23 },
  { id: '35', name: 'Taraba', code: 'TA', totalLgas: 16 },
  { id: '36', name: 'Yobe', code: 'YO', totalLgas: 17 },
  { id: '37', name: 'Zamfara', code: 'ZA', totalLgas: 14 },
];

function StateCard({ state, electionType }: { state: State; electionType: string }) {
  const stateSlug = state.name.toLowerCase().replace(/\s+/g, '-');
  
  return (
    <Link
      href={`/elections/${electionType}/${stateSlug}`}
      className="block bg-card rounded-lg border border-border p-4 shadow-sm hover:shadow-md hover:border-primary transition-all"
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-foreground">{state.name}</h3>
          <p className="text-sm text-muted-foreground">{state.totalLgas} LGAs</p>
        </div>
        <span className="text-2xl">🏛️</span>
      </div>
    </Link>
  );
}

function formatElectionType(type: string): string {
  return type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function ElectionTypePage({ params }: PageProps) {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredStates = nigerianStates.filter((state) =>
    state.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <nav className="text-sm text-muted-foreground mb-4">
          <Link href="/" className="hover:text-foreground">Dashboard</Link>
          <span className="mx-2">/</span>
          <Link href="/elections" className="hover:text-foreground">Elections</Link>
          <span className="mx-2">/</span>
          <span className="text-foreground">{formatElectionType(params.type)}</span>
        </nav>
        <h1 className="text-3xl font-bold text-foreground capitalize">
          {formatElectionType(params.type)} Election
        </h1>
        <p className="text-muted-foreground mt-2">
          Select a state to view results
        </p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search states..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full max-w-md px-4 py-2 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* States Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {filteredStates.map((state) => (
          <StateCard key={state.id} state={state} electionType={params.type} />
        ))}
      </div>

      {filteredStates.length === 0 && (
        <p className="text-center text-muted-foreground py-8">
          No states found matching &quot;{searchTerm}&quot;
        </p>
      )}
    </main>
  );
}
