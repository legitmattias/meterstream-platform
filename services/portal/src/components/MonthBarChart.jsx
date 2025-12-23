import React from 'react';
import { ResponsiveContainer, BarChart, Bar, LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, Legend } from 'recharts';

export function MonthBarChart({ data, type }) {
  return (
    <div style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        {type === 'line' ? (
          <LineChart data={data} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="value" name="kWh" stroke="#22c55e" strokeWidth={3} dot={{ r: 3 }} />
          </LineChart>
        ) : (
          <BarChart data={data} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="value" name="kWh" fill="#22c55e" />
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
