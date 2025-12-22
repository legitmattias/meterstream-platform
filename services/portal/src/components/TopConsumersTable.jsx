import React from 'react';

export function TopConsumersTable({ consumers }) {
  return (
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
          {consumers.length === 0 ? (
            <tr><td colSpan={4} style={{textAlign:'center'}}>No data available</td></tr>
          ) : (
            consumers.map((c, idx) => (
              <tr key={c.id || idx}>
                <td>{idx + 1}.</td>
                <td>{c.name}</td>
                <td>{c.consumption} kWh</td>
                <td className={c.change >= 0 ? 'change-positive' : 'change-negative'}>
                  {c.change >= 0 ? `+${c.change}%` : `${c.change}%`}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
