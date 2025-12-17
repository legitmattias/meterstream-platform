import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { config } from '../config';
import './Dashboard.css';

export function Dashboard() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');

  const grafanaUrl = config.grafanaDashboardUid
    ? `${config.grafanaUrl}/d/${config.grafanaDashboardUid}`
    : config.grafanaUrl;

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>MeterStream Dashboard</h1>
        <div className="user-info">
          <span>Welcome, {user?.email || 'User'}</span>
          <button onClick={logout}>Logout</button>
        </div>
      </header>

      <div className="tabs">
        <button
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          System Overview
        </button>
        <button
          className={`tab-button ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          Consumer Analytics
        </button>
      </div>

      <main className="dashboard-content">
        {activeTab === 'overview' && (
          <div className="tab-content">
            <div className="dashboard-section">
              <h2>Real-Time Ingestion Metrics</h2>
              <div className="grafana-embed">
                <iframe
                  src={grafanaUrl}
                  width="100%"
                  height="300"
                  frameBorder="0"
                  title="Ingestion Metrics"
                ></iframe>
              </div>
            </div>

            <div className="dashboard-section">
              <h2>Queue Length</h2>
              <div className="grafana-embed">
                <iframe
                  src={grafanaUrl}
                  width="100%"
                  height="300"
                  frameBorder="0"
                  title="Queue Length"
                ></iframe>
              </div>
            </div>

            <div className="dashboard-section">
              <h2>Processing Rate</h2>
              <div className="grafana-embed">
                <iframe
                  src={grafanaUrl}
                  width="100%"
                  height="300"
                  frameBorder="0"
                  title="Processing Rate"
                ></iframe>
              </div>
            </div>

            <div className="dashboard-section">
              <h2>Logs</h2>
              <div className="logs">
                <div className="log-entry">
                  <span className="log-badge info">INFO</span>
                  <span className="log-text">System operating normally</span>
                  <span className="log-time">13:05</span>
                </div>
                <div className="log-entry">
                  <span className="log-badge warn">WARN</span>
                  <span className="log-text">Queue length elevated</span>
                  <span className="log-time">12:58</span>
                </div>
                <div className="log-entry">
                  <span className="log-badge info">INFO</span>
                  <span className="log-text">Batch processing completed</span>
                  <span className="log-time">12:45</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="tab-content">
            <div className="dashboard-section">
              <h2>Aggregate Energy Consumption</h2>
              <div className="grafana-embed">
                <iframe
                  src={grafanaUrl}
                  width="100%"
                  height="300"
                  frameBorder="0"
                  title="Aggregate Energy Consumption"
                ></iframe>
              </div>
            </div>

            <div className="dashboard-grid">
              <div className="dashboard-section">
                <h2>Top Consumers</h2>
                <div className="table-container">
                  <table className="consumers-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Customer</th>
                        <th>Consumption</th>
                        <th>Change</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>1.</td>
                        <td>Industrial Corp A</td>
                        <td>45 650 kWh</td>
                        <td className="change-positive">+5.7%</td>
                      </tr>
                      <tr>
                        <td>2.</td>
                        <td>Manufacturing Plant B</td>
                        <td>38 940 kWh</td>
                        <td className="change-positive">+2.1%</td>
                      </tr>
                      <tr>
                        <td>3.</td>
                        <td>Datacenter C</td>
                        <td>34 210 kWh</td>
                        <td className="change-negative">-1.3%</td>
                      </tr>
                      <tr>
                        <td>4.</td>
                        <td>Retail Chain D</td>
                        <td>29 850 kWh</td>
                        <td className="change-positive">+8.7%</td>
                      </tr>
                      <tr>
                        <td>5.</td>
                        <td>Office Complex E</td>
                        <td>24 160 kWh</td>
                        <td className="change-positive">+3.4%</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="dashboard-section">
                <h2>Data Quality</h2>
                <div className="quality-metrics">
                  <div className="quality-item">
                    <div className="quality-header">
                      <span>Completeness</span>
                      <span className="quality-value">98.5%</span>
                    </div>
                    <div className="quality-bar">
                      <div className="quality-fill" style={{width: '98.5%'}}></div>
                    </div>
                  </div>
                  <div className="quality-item">
                    <div className="quality-header">
                      <span>Accuracy</span>
                      <span className="quality-value">97.7%</span>
                    </div>
                    <div className="quality-bar">
                      <div className="quality-fill" style={{width: '97.7%'}}></div>
                    </div>
                  </div>
                  <div className="quality-item">
                    <div className="quality-header">
                      <span>Timeliness</span>
                      <span className="quality-value">99.1%</span>
                    </div>
                    <div className="quality-bar">
                      <div className="quality-fill" style={{width: '99.1%'}}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="dashboard-section">
              <h2>Monthly Consumption</h2>
              <div className="grafana-embed">
                <iframe
                  src={grafanaUrl}
                  width="100%"
                  height="300"
                  frameBorder="0"
                  title="Monthly Consumption"
                ></iframe>
              </div>
            </div>

            <div className="summary-cards">
              <div className="summary-card blue">
                <div className="summary-label">Total Consumption</div>
                <div className="summary-value">892 kWh</div>
              </div>
              <div className="summary-card green">
                <div className="summary-label">Cost estimate</div>
                <div className="summary-value">765 SEK</div>
              </div>
              <div className="summary-card purple">
                <div className="summary-label">Average</div>
                <div className="summary-value">892 kWh/day</div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
