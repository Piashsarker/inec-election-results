'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { PartyResult } from '@/types';

interface VoteDistributionPieProps {
  data: PartyResult[];
  height?: number;
  showLegend?: boolean;
  innerRadius?: number;
  outerRadius?: number;
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

export function VoteDistributionPie({
  data,
  height = 300,
  showLegend = true,
  innerRadius = 60,
  outerRadius = 100,
}: VoteDistributionPieProps) {
  const sortedData = [...data].sort((a, b) => b.voteCount - a.voteCount);
  const totalVotes = sortedData.reduce((sum, d) => sum + d.voteCount, 0);

  // Group small parties into "Others" if more than 6 parties
  let chartData = sortedData;
  if (sortedData.length > 6) {
    const topParties = sortedData.slice(0, 5);
    const otherParties = sortedData.slice(5);
    const othersVotes = otherParties.reduce((sum, p) => sum + p.voteCount, 0);
    const othersPercentage = totalVotes > 0 ? (othersVotes / totalVotes) * 100 : 0;
    
    chartData = [
      ...topParties,
      {
        partyName: 'Others',
        partyCode: 'Others',
        voteCount: othersVotes,
        percentage: othersPercentage,
      },
    ];
  }

  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: PartyResult }> }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <p className="font-semibold text-foreground">{data.partyName}</p>
          <p className="text-sm text-muted-foreground">
            Votes: {data.voteCount.toLocaleString()}
          </p>
          <p className="text-sm text-muted-foreground">
            Share: {data.percentage.toFixed(2)}%
          </p>
        </div>
      );
    }
    return null;
  };

  const renderCustomLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
    partyCode,
  }: {
    cx: number;
    cy: number;
    midAngle: number;
    innerRadius: number;
    outerRadius: number;
    percent: number;
    partyCode: string;
  }) => {
    if (percent < 0.05) return null; // Don't show label for small slices
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor="middle"
        dominantBaseline="central"
        className="text-xs font-medium"
      >
        {partyCode}
      </text>
    );
  };

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderCustomLabel}
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            dataKey="voteCount"
            nameKey="partyCode"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getPartyColor(entry.partyCode)} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          {showLegend && (
            <Legend
              formatter={(value) => (
                <span className="text-foreground text-sm">{value}</span>
              )}
            />
          )}
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export default VoteDistributionPie;
