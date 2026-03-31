'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { PartyResult } from '@/types';

interface PartyBarChartProps {
  data: PartyResult[];
  height?: number;
  showPercentage?: boolean;
}

// Party colors mapping
const partyColors: Record<string, string> = {
  APC: '#0066CC',
  PDP: '#CC0000',
  LP: '#00CC66',
  NNPP: '#9933CC',
  APGA: '#FF6600',
  ADC: '#FFCC00',
  SDP: '#FF3399',
  YPP: '#00CCCC',
  ACCORD: '#996633',
  AAC: '#333333',
};

const getPartyColor = (partyCode: string): string => {
  return partyColors[partyCode] || '#888888';
};

export function PartyBarChart({ data, height = 300, showPercentage = false }: PartyBarChartProps) {
  const sortedData = [...data].sort((a, b) => b.voteCount - a.voteCount);
  const totalVotes = sortedData.reduce((sum, d) => sum + d.voteCount, 0);

  const chartData = sortedData.map((item) => ({
    ...item,
    displayValue: showPercentage
      ? totalVotes > 0 ? (item.voteCount / totalVotes) * 100 : 0
      : item.voteCount,
  }));

  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: PartyResult & { displayValue: number } }> }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <p className="font-semibold text-foreground">{data.partyName}</p>
          <p className="text-sm text-muted-foreground">
            Votes: {data.voteCount.toLocaleString()}
          </p>
          <p className="text-sm text-muted-foreground">
            Percentage: {data.percentage.toFixed(2)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 60, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            type="number"
            tick={{ fill: 'hsl(var(--muted-foreground))' }}
            tickFormatter={(value) =>
              showPercentage ? `${value.toFixed(0)}%` : value.toLocaleString()
            }
          />
          <YAxis
            type="category"
            dataKey="partyCode"
            tick={{ fill: 'hsl(var(--foreground))' }}
            width={50}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="displayValue" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getPartyColor(entry.partyCode)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default PartyBarChart;
