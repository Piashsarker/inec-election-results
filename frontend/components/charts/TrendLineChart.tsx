'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface TrendDataPoint {
  label: string;
  [partyCode: string]: number | string;
}

interface TrendLineChartProps {
  data: TrendDataPoint[];
  parties: string[];
  height?: number;
  showLegend?: boolean;
  xAxisLabel?: string;
  yAxisLabel?: string;
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

export function TrendLineChart({
  data,
  parties,
  height = 300,
  showLegend = true,
  xAxisLabel,
  yAxisLabel,
}: TrendLineChartProps) {
  const CustomTooltip = ({
    active,
    payload,
    label,
  }: {
    active?: boolean;
    payload?: Array<{ name: string; value: number; color: string }>;
    label?: string;
  }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <p className="font-semibold text-foreground mb-2">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toLocaleString()}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            dataKey="label"
            tick={{ fill: 'hsl(var(--muted-foreground))' }}
            label={
              xAxisLabel
                ? {
                    value: xAxisLabel,
                    position: 'insideBottom',
                    offset: -5,
                    fill: 'hsl(var(--muted-foreground))',
                  }
                : undefined
            }
          />
          <YAxis
            tick={{ fill: 'hsl(var(--muted-foreground))' }}
            tickFormatter={(value) => value.toLocaleString()}
            label={
              yAxisLabel
                ? {
                    value: yAxisLabel,
                    angle: -90,
                    position: 'insideLeft',
                    fill: 'hsl(var(--muted-foreground))',
                  }
                : undefined
            }
          />
          <Tooltip content={<CustomTooltip />} />
          {showLegend && (
            <Legend
              formatter={(value) => (
                <span className="text-foreground text-sm">{value}</span>
              )}
            />
          )}
          {parties.map((party) => (
            <Line
              key={party}
              type="monotone"
              dataKey={party}
              stroke={getPartyColor(party)}
              strokeWidth={2}
              dot={{ fill: getPartyColor(party), strokeWidth: 2 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default TrendLineChart;
