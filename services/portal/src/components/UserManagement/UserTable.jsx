export function UserTable({ users, onEdit, onDelete }) {
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
                    padding: '0.375rem 0.5rem',
                    background: 'transparent',
                    color: '#6c757d',
                    border: '1px solid #dee2e6',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '1rem'
                  }}
                >
                  ✏️
                </button>
                <button
                  onClick={() => onDelete(user)}
                  title="Delete user"
                  style={{
                    padding: '0.375rem 0.5rem',
                    background: 'transparent',
                    color: '#dc3545',
                    border: '1px solid #dee2e6',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '1rem'
                  }}
                >
                  🗑️
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
