import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';
import { formatNumber, getSwedishMonthName } from '../lib/dashboardUtils';

// Custom tooltip for Swedish display
const CustomTooltip = ({ active, payload, label, year, isMonthly }) => {
  if (!active || !payload || payload.length === 0) return null;

  const monthLabel = isMonthly ? getSwedishMonthName(parseInt(label)) : `Dag ${label}`;

  return (
    <div style={{
      background: 'white',
      border: '1px solid #e5e7eb',
      borderRadius: '8px',
      padding: '12px',
      boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
    }}>
      <p style={{ margin: 0, fontWeight: 600, color: '#374151' }}>
        {monthLabel} {year}
      </p>
      {payload.map((entry, index) => (
        <p key={index} style={{ margin: '4px 0 0', color: entry.color }}>
          {entry.name}: {formatNumber(entry.value, 2)} kWh
        </p>
      ))}
    </div>
  );
};

export function ConsumptionChart({
  data,
  comparisonData = null,
  year,
  comparisonYear = null,
  isMonthly = true,
  height = 350,
}) {
  // Merge current and comparison data
  const chartData = data.map((item, index) => {
    const merged = {
      label: isMonthly ? item.month : item.day,
      displayLabel: isMonthly
        ? getSwedishMonthName(item.month, true)
        : item.day,
      current: item.consumption,
    };

    if (comparisonData && comparisonData[index]) {
      merged.previous = comparisonData[index].consumption;
    }

    return merged;
  });

  const hasComparison = comparisonData && comparisonData.length > 0;

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <ComposedChart
          data={chartData}
          margin={{ top: 20, right: 30, bottom: 20, left: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="displayLabel"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickLine={{ stroke: '#e5e7eb' }}
            axisLine={{ stroke: '#e5e7eb' }}
          />
          <YAxis
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickLine={{ stroke: '#e5e7eb' }}
            axisLine={{ stroke: '#e5e7eb' }}
            tickFormatter={(value) => formatNumber(value, 2)}
            label={{ value: 'kWh', angle: -90, position: 'insideLeft', style: { fill: '#6b7280', fontSize: 12 } }}
            domain={[0, 'auto']}
            allowDecimals={true}
          />
          <Tooltip
            content={<CustomTooltip year={year} isMonthly={isMonthly} />}
          />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
          />

          {/* Previous year bars (behind, lighter) */}
          {hasComparison && (
            <Bar
              dataKey="previous"
              name={`${comparisonYear}`}
              fill="#94a3b8"
              radius={[4, 4, 0, 0]}
              maxBarSize={40}
            />
          )}

          {/* Current year bars (in front, solid) */}
          <Bar
            dataKey="current"
            name={`${year}`}
            fill="#3b82f6"
            radius={[4, 4, 0, 0]}
            maxBarSize={40}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export default ConsumptionChart;
