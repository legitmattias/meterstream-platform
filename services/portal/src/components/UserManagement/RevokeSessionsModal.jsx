export function RevokeSessionsModal({ user, onCancel, onConfirm }) {
  if (!user) return null

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '2rem',
        borderRadius: '8px',
        maxWidth: '500px',
        width: '90%',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
      }}>
        <h3 style={{ marginTop: 0, marginBottom: '1rem', color: '#dc3545' }}>
          Revoke All Sessions
        </h3>

        <div style={{ marginBottom: '1.5rem' }}>
          <p style={{ marginBottom: '0.75rem' }}>
            Are you sure you want to revoke all active sessions for:
          </p>
          <div style={{
            padding: '0.75rem',
            backgroundColor: '#f8f9fa',
            borderRadius: '4px',
            border: '1px solid #dee2e6'
          }}>
            <strong>{user.name}</strong>
            <br />
            <span style={{ color: '#6c757d', fontSize: '0.875rem' }}>{user.email}</span>
          </div>
        </div>

        <div style={{
          padding: '1rem',
          backgroundColor: '#fff3cd',
          border: '1px solid #ffc107',
          borderRadius: '4px',
          marginBottom: '1.5rem'
        }}>
          <p style={{ margin: 0, fontSize: '0.875rem', color: '#856404' }}>
            <strong>⚠️ Warning:</strong> This will force the user to log in again on all devices.
            Their current session will remain active for up to 15 minutes.
          </p>
        </div>

        <div style={{
          display: 'flex',
          gap: '0.75rem',
          justifyContent: 'flex-end'
        }}>
          <button
            onClick={onCancel}
            style={{
              padding: '0.625rem 1.25rem',
              background: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500'
            }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            style={{
              padding: '0.625rem 1.25rem',
              background: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500'
            }}
          >
            Revoke Sessions
          </button>
        </div>
      </div>
    </div>
  )
}
