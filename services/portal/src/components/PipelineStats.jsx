import React from 'react';
import { MetricCard } from './MetricCard';
import './PipelineStats.css';

function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

export function PipelineStats({ pipeline }) {
  return (
    <div className="pipeline-section">
      <h3>Processing Pipeline</h3>
      <div className="pipeline-grid">
        <MetricCard
          title="Total Processed"
          value={formatNumber(pipeline?.total_processed || 0)}
          subtitle="last 30 days"
          color="green"
          tooltip="Number of meter readings processed and stored in InfluxDB in the last 30 days."
        />
        <MetricCard
          title="Last Hour"
          value={formatNumber(pipeline?.last_hour || 0)}
          subtitle="readings"
          color="blue"
          tooltip="Number of meter readings processed in the last hour. Shows current pipeline throughput."
        />
      </div>
    </div>
  );
}
