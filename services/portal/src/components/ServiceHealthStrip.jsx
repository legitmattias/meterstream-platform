import React from 'react';
import './ServiceHealthStrip.css';

function ServiceHealthIndicator({ name, status, latencyMs }) {
  const isHealthy = status === 'healthy';
  return (
    <div className={`service-indicator ${isHealthy ? 'healthy' : 'unhealthy'}`}>
      <span className="service-dot"></span>
      <span className="service-name">{name}</span>
      {latencyMs !== undefined && (
        <span className="service-latency">{Math.round(latencyMs)}ms</span>
      )}
    </div>
  );
}

export function ServiceHealthStrip({ services, natsStatus }) {
  return (
    <div className="health-strip">
      <h3>Service Health</h3>
      <div className="health-indicators">
        <ServiceHealthIndicator
          name="Ingestion"
          status={services?.ingestion?.status}
          latencyMs={services?.ingestion?.latency_ms}
        />
        <ServiceHealthIndicator
          name="Processor"
          status={services?.processor?.status}
          latencyMs={services?.processor?.latency_ms}
        />
        <ServiceHealthIndicator
          name="Auth"
          status={services?.auth?.status}
          latencyMs={services?.auth?.latency_ms}
        />
        <ServiceHealthIndicator
          name="Gateway"
          status={services?.gateway?.status}
          latencyMs={services?.gateway?.latency_ms}
        />
        <ServiceHealthIndicator
          name="InfluxDB"
          status={services?.influxdb?.status}
          latencyMs={services?.influxdb?.latency_ms}
        />
        <ServiceHealthIndicator
          name="Grafana"
          status={services?.grafana?.status}
          latencyMs={services?.grafana?.latency_ms}
        />
        <ServiceHealthIndicator
          name="NATS"
          status={natsStatus}
        />
      </div>
    </div>
  );
}
