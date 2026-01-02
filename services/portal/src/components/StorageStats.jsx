import React from 'react';
import { MetricCard } from './MetricCard';
import './StorageStats.css';

function formatBytes(bytes) {
  if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + ' GB';
  if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB';
  if (bytes >= 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return bytes + ' B';
}

function getStatusColor(status) {
  switch (status) {
    case 'syncing':
      return 'green';
    case 'initializing':
      return 'blue';
    case 'no_replication':
    case 'not_configured':
      return 'gray';
    default:
      return 'red';
  }
}

function getStatusLabel(status) {
  switch (status) {
    case 'syncing':
      return 'Syncing';
    case 'initializing':
      return 'Initializing';
    case 'no_replication':
      return 'No Replication';
    case 'not_configured':
      return 'Not Configured';
    case 'unreachable':
      return 'Unreachable';
    case 'no_org':
      return 'No Org';
    default:
      return 'Error';
  }
}

export function StorageStats({ storage }) {
  const status = storage?.replication_status || 'not_configured';
  const queueBytes = storage?.replication_queue_bytes || 0;
  const remainingBytes = storage?.replication_remaining_bytes || 0;

  return (
    <div className="storage-section">
      <h3>Data Replication (CQRS)</h3>
      <div className="storage-grid">
        <MetricCard
          title="Sync Status"
          value={getStatusLabel(status)}
          subtitle="write → read"
          color={getStatusColor(status)}
          tooltip="Status of data replication from write instance to read instance. 'Syncing' means data is actively being replicated."
        />
        <MetricCard
          title="Queue Size"
          value={formatBytes(queueBytes)}
          subtitle="buffer size"
          color={queueBytes > 10485760 ? 'orange' : 'blue'}
          tooltip="Disk buffer allocated for replication queue. Check 'Remaining' for actual pending data."
        />
        <MetricCard
          title="Remaining"
          value={formatBytes(remainingBytes)}
          subtitle="to sync"
          color={remainingBytes > 0 ? 'orange' : 'green'}
          tooltip="Bytes remaining to be synced to the read instance. Zero means instances are in sync."
        />
      </div>
    </div>
  );
}
