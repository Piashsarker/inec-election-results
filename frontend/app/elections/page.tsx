'use client';

import Link from 'next/link';
import { ElectionType } from '@/types';

interface ElectionTypeInfo {
  type: ElectionType;
  label: string;
  description: string;
  icon: string;
}

const electionTypes: ElectionTypeInfo[] = [
  {
    type: 'presidential',
    label: 'Presidential',
    description: 'National presidential election results',
    icon: '🏛️',
  },
  {
    type: 'governorship',
    label: 'Governorship',
    description: 'State governorship election results',
    icon: '🏢',
  },
  {
    type: 'senatorial',
    label: 'Senatorial',
    description: 'Senate election results by district',
    icon: '🏛️',
  },
  {
    type: 'house_of_reps',
    label: 'House of Representatives',
    description: 'Federal constituency election results',
    icon: '🏠',
  },
  {
    type: 'house_of_assembly',
    label: 'House of Assembly',
    description: 'State assembly election results',
    icon: '🏫',
  },
  {
    type: 'chairmanship',
    label: 'Chairmanship',
    description: 'Local government chairmanship results',
    icon: '👔',
  },
  {
    type: 'councilor',
    label: 'Councilor',
    description: 'Ward councilor election results',
    icon: '👥',
  },
];

function ElectionTypeCard({ election }: { election: ElectionTypeInfo }) {
  return (
    <Link
      href={`/elections/${election.type}`}
      className="block bg-card rounded-lg border border-border p-6 shadow-sm hover:shadow-md hover:border-primary transition-all"
    >
      <div className="flex items-start space-x-4">
        <span className="text-4xl">{election.icon}</span>
        <div>
          <h3 className="font-semibold text-lg text-foreground">{election.label}</h3>
          <p className="text-sm text-muted-foreground mt-1">{election.description}</p>
        </div>
      </div>
    </Link>
  );
}

export default function ElectionsPage() {
  return (
    <main className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <nav className="text-sm text-muted-foreground mb-4">
          <Link href="/" className="hover:text-foreground">Dashboard</Link>
          <span className="mx-2">/</span>
          <span className="text-foreground">Elections</span>
        </nav>
        <h1 className="text-3xl font-bold text-foreground">Election Types</h1>
        <p className="text-muted-foreground mt-2">
          Select an election type to browse results by geographic hierarchy
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {electionTypes.map((election) => (
          <ElectionTypeCard key={election.type} election={election} />
        ))}
      </div>
    </main>
  );
}
