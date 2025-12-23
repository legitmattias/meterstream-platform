import React from 'react';

function fmtNumber(v, decimals = 0) {
  if (v === null || v === undefined || Number.isNaN(v)) return '—'
  return Number(v).toFixed(decimals)
}

export function SummaryCards({ monthTotal, monthAverage, hourlyMax, weekMax }) {
  return (
    <div className="summary-cards two-up" style={{ margin: '24px 0' }}>
      <div className="summary-card blue">
        <div className="summary-label">Total Monthly Consumption</div>
        <div className="summary-value">{fmtNumber(monthTotal, 0)} kWh</div>
      </div>

      <div className="summary-card purple">
        <div className="summary-label">Average Daily (Month)</div>
        <div className="summary-value">{fmtNumber(monthAverage, 0)} kWh</div>
      </div>

      <div className="summary-card green">
        <div className="summary-label">Max Hourly Consumption</div>
        <div className="summary-value">{fmtNumber(hourlyMax, 0)} kWh</div>
      </div>

      <div className="summary-card yellow">
        <div className="summary-label">Max Daily (Week)</div>
        <div className="summary-value">{fmtNumber(weekMax, 0)} kWh</div>
      </div>
    </div>
  );
}
