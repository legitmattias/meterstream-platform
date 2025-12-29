export function UserTable({ users, onEdit, onDelete, onRevokeSessions }) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white', borderRadius: '4px', overflow: 'hidden' }}>
        <thead>
          <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #dee2e6' }}>
            <th style={{ padding: '0.875rem', textAlign: 'left', fontWeight: '600', fontSize: '0.875rem', color: '#495057' }}>Email</th>
            <th style={{ padding: '0.875rem', textAlign: 'left', fontWeight: '600', fontSize: '0.875rem', color: '#495057' }}>Name</th>
            <th style={{ padding: '0.875rem', textAlign: 'left', fontWeight: '600', fontSize: '0.875rem', color: '#495057' }}>Role</th>
            <th style={{ padding: '0.875rem', textAlign: 'left', fontWeight: '600', fontSize: '0.875rem', color: '#495057' }}>Customer ID</th>
            <th style={{ padding: '0.875rem', textAlign: 'left', fontWeight: '600', fontSize: '0.875rem', color: '#495057' }}>Created</th>
            <th style={{ padding: '0.875rem', textAlign: 'right', fontWeight: '600', fontSize: '0.875rem', color: '#495057' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id} style={{ borderBottom: '1px solid #e9ecef' }}>
              <td style={{ padding: '0.875rem', fontSize: '0.875rem' }}>{user.email}</td>
              <td style={{ padding: '0.875rem', fontSize: '0.875rem' }}>{user.name}</td>
              <td style={{ padding: '0.875rem' }}>
                <span style={{
                  padding: '0.25rem 0.625rem',
                  borderRadius: '12px',
                  background: user.role === 'admin' ? '#d1ecf1' :
                              user.role === 'internal' ? '#d4edda' :
                              user.role === 'device' ? '#fff3cd' : '#f8f9fa',
                  color: user.role === 'admin' ? '#0c5460' :
                         user.role === 'internal' ? '#155724' :
                         user.role === 'device' ? '#856404' : '#495057',
                  fontSize: '0.8125rem',
                  fontWeight: '500'
                }}>
                  {user.role}
                </span>
              </td>
              <td style={{ padding: '0.875rem', fontSize: '0.875rem', color: '#6c757d' }}>{user.customer_id || '-'}</td>
              <td style={{ padding: '0.875rem', fontSize: '0.875rem', color: '#6c757d' }}>
                {new Date(user.created_at).toLocaleDateString()}
              </td>
              <td style={{ padding: '0.875rem', textAlign: 'right' }}>
                <button
                  onClick={() => onEdit(user)}
                  title="Edit user"
                  style={{
                    marginRight: '0.5rem',
                    padding: '0.5rem',
                    background: 'transparent',
                    color: '#6c757d',
                    border: '1px solid #dee2e6',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                  </svg>
                </button>
                <button
                  onClick={() => onRevokeSessions(user)}
                  title="Revoke all sessions"
                  style={{
                    marginRight: '0.5rem',
                    padding: '0.5rem',
                    background: 'transparent',
                    color: '#ffc107',
                    border: '1px solid #ffc107',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                </button>
                <button
                  onClick={() => onDelete(user)}
                  title="Delete user"
                  style={{
                    padding: '0.5rem',
                    background: 'transparent',
                    color: '#6c757d',
                    border: '1px solid #dee2e6',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                    <line x1="10" y1="11" x2="10" y2="17" />
                    <line x1="14" y1="11" x2="14" y2="17" />
                  </svg>
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
