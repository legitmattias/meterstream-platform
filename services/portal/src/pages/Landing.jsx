import { Header } from '../components/Header'
import './Landing.css'

export function Landing() {
  return (
    <>
    <div className="landing">
      <Header />

      <section className="landing-hero">
        <div className="hero-content">
          <div className="welcome-section">
            <p className="eyebrow">Welcome to MeterStream</p>
            <h1>Kalmar Energy Monitoring</h1>
            <p className="subtitle">
              Track and analyze your energy consumption data in real-time.
              MeterStream provides comprehensive insights into your power usage,
              helping you make informed decisions about energy efficiency and cost savings.
            </p>
            <p className="description">
              Our platform collects data from smart meters across Kalmar, processes it through
              a secure gateway, and presents it in easy-to-understand visualizations.
              Whether you're monitoring a single building or managing multiple facilities,
              MeterStream gives you the tools you need to optimize your energy consumption.
            </p>
          </div>

          <div className="news-section">
            <div className="news-card">
              <h3 className="news-header">Latest Updates</h3>

              <div className="news-item">
                <span className="news-date">Jan 7, 2026</span>
                <h4>Welcome to MeterStream</h4>
                <p>The new analytics platform is now live for all Kalmar Energy customers.</p>
              </div>

              <div className="news-item">
                <span className="news-date">Dec 28, 2025</span>
                <h4>System Monitoring</h4>
                <p>New system health dashboard shows real-time service status and metrics.</p>
              </div>

              <div className="news-item">
                <span className="news-date">Dec 15, 2025</span>
                <h4>User Management</h4>
                <p>Admins can now create and manage user accounts directly from the portal.</p>
              </div>

              <div className="news-item">
                <span className="news-date">Dec 1, 2025</span>
                <h4>Energy prices</h4>
                <p>Prices of electricity skyrockets, but not for Kalmar!</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
    <footer className="customer-footer">
          <p>Kalmar Energi - Meterstream</p>
    </footer>
    </>
  )
}
