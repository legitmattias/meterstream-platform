import React from 'react';
import { ResponsiveContainer, AreaChart, Area } from 'recharts';
import './MetricCard.css';

export function MetricCard({ title, value, subtitle, trend, color = 'blue', tooltip }) {
  return (
    <div className={`metric-card ${color}`} title={tooltip}>
      <div className="metric-title">{title}</div>
      <div className="metric-value">{value}</div>
      {subtitle && <div className="metric-subtitle">{subtitle}</div>}
      {trend && trend.length > 0 && (
        <div className="metric-sparkline">
          <ResponsiveContainer width="100%" height={40}>
            <AreaChart data={trend} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
              <Area
                type="monotone"
                dataKey="value"
                stroke="#fff"
                fill="rgba(255,255,255,0.3)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
