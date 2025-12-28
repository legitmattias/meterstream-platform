export function Notifications({ successMessage, error }) {
  return (
    <>
      {successMessage && (
        <div style={{
          padding: '0.875rem 1.25rem',
          background: '#d4edda',
          color: '#155724',
          borderRadius: '6px',
          marginBottom: '1rem',
          border: '1px solid #c3e6cb',
          display: 'flex',
          alignItems: 'center',
          fontSize: '0.875rem',
          fontWeight: '500',
          animation: 'slideIn 0.3s ease-out'
        }}>
          ✓ {successMessage}
        </div>
      )}

      {error && (
        <div style={{
          padding: '0.875rem 1.25rem',
          background: '#f8d7da',
          color: '#721c24',
          borderRadius: '6px',
          marginBottom: '1rem',
          border: '1px solid #f5c6cb',
          fontSize: '0.875rem',
          fontWeight: '500'
        }}>
          {error}
        </div>
      )}
    </>
  )
}
