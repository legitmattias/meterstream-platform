import React from 'react';
import { MetricCard } from './MetricCard';
import './NatsMetrics.css';

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

export function NatsMetrics({ nats, history }) {
  return (
    <div className="metrics-section">
      <h3>Message Queue (NATS)</h3>
      <div className="metrics-grid">
        <MetricCard
          title="Total Messages"
          value={formatNumber(nats?.messages || 0)}
          subtitle="in stream"
          color="blue"
          trend={history?.map(h => ({ value: h.messages })) || []}
          tooltip="Total number of messages stored in NATS JetStream. Includes both processed and unprocessed messages."
        />
        <MetricCard
          title="Consumer Lag"
          value={formatNumber(nats?.consumer_lag || 0)}
          subtitle="pending"
          color={nats?.consumer_lag > 100 ? 'orange' : 'green'}
          trend={history?.map(h => ({ value: h.lag })) || []}
          tooltip="Number of messages waiting to be processed. High lag indicates the processor cannot keep up with incoming data."
        />
        <MetricCard
          title="Storage Used"
          value={formatBytes(nats?.bytes || 0)}
          color="purple"
          tooltip="Disk space used by NATS JetStream for message persistence."
        />
        <MetricCard
          title="Consumers"
          value={nats?.consumers || 0}
          subtitle={`${nats?.streams || 0} streams`}
          color="teal"
          tooltip="Number of active consumers (processor instances) subscribed to NATS streams."
        />
      </div>
    </div>
  );
}
