import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { ServiceHealthStrip } from './ServiceHealthStrip';
import { NatsMetrics } from './NatsMetrics';
import { StorageStats } from './StorageStats';
import './SystemMonitoring.css';

export function SystemMonitoring() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await api.request('/system/metrics');
        setMetrics(data);
        setError(null);

        // Keep history for sparklines (last 10 data points)
        setHistory(prev => {
          const newPoint = {
            time: new Date().toLocaleTimeString(),
            messages: data.nats?.messages || 0,
            lag: data.nats?.consumer_lag || 0,
          };
          const updated = [...prev, newPoint].slice(-10);
          return updated;
        });
      } catch (err) {
        console.error('Failed to fetch system metrics:', err);
        setError(err.message || 'Failed to load metrics');
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchMetrics();

    // Poll every 10 seconds
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !metrics) {
    return (
      <div className="system-monitoring">
        <div className="loading-state">Loading system metrics...</div>
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div className="system-monitoring">
        <div className="error-state">
          <p>Failed to load system metrics</p>
          <p className="error-detail">{error}</p>
        </div>
      </div>
    );
  }

  const { nats, services, storage } = metrics || {};

  return (
    <div className="system-monitoring">
      <ServiceHealthStrip services={services} nats={nats} />
      <NatsMetrics nats={nats} history={history} />
      <StorageStats storage={storage} />

      <div className="last-updated">
        Last updated: {metrics?.timestamp ? new Date(metrics.timestamp).toLocaleString() : 'N/A'}
        {error && <span className="update-error"> (update failed)</span>}
      </div>
    </div>
  );
}
