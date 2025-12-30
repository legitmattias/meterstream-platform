export function Pagination({ currentPage, totalPages, totalUsers, onPageChange }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.75rem', marginTop: '1.5rem' }}>
      <button
        onClick={() => onPageChange(Math.max(1, currentPage - 1))}
        disabled={currentPage === 1}
        style={{
          padding: '0.5rem 1rem',
          background: currentPage === 1 ? '#f8f9fa' : 'white',
          color: currentPage === 1 ? '#adb5bd' : '#495057',
          border: '1px solid #dee2e6',
          borderRadius: '4px',
          cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
          fontSize: '0.875rem'
        }}
      >
        Previous
      </button>
      <span style={{ padding: '0.5rem', fontSize: '0.875rem', color: '#6c757d' }}>
        Page {currentPage} of {totalPages} ({totalUsers} users)
      </span>
      <button
        onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
        disabled={currentPage >= totalPages}
        style={{
          padding: '0.5rem 1rem',
          background: currentPage >= totalPages ? '#f8f9fa' : 'white',
          color: currentPage >= totalPages ? '#adb5bd' : '#495057',
          border: '1px solid #dee2e6',
          borderRadius: '4px',
          cursor: currentPage >= totalPages ? 'not-allowed' : 'pointer',
          fontSize: '0.875rem'
        }}
      >
        Next
      </button>
    </div>
  )
}
