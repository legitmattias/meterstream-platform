import React from 'react';

export function LogsList({ logs }) {
  return (
    <div className="logs">
      {logs.length === 0 ? (
        <div style={{color:'#64748b',margin:'1em 0'}}>No logs available</div>
      ) : (
        logs.map((log, idx) => (
          <div key={log.id || idx} className={`log-entry`}>
            <span className={`log-badge ${log.level}`}>{log.level.toUpperCase()}</span>
            <span className="log-text">{log.message}</span>
            <span className="log-time">{log.time}</span>
          </div>
        ))
      )}
    </div>
  );
}
