export function SearchBar({ searchTerm, roleFilter, onSearchChange, onRoleChange }) {
  return (
    <div style={{
      display: 'flex',
      gap: '1rem',
      marginBottom: '1.5rem',
      alignItems: 'center',
      flexWrap: 'wrap'
    }}>
      <div style={{ flex: '1', minWidth: '250px' }}>
        <input
          type="text"
          placeholder="Search by email, name, or customer ID..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          style={{
            width: '100%',
            padding: '0.625rem 1rem',
            border: '1px solid #ced4da',
            borderRadius: '4px',
            fontSize: '0.875rem',
            boxSizing: 'border-box'
          }}
        />
      </div>
      <div style={{ minWidth: '180px' }}>
        <select
          value={roleFilter}
          onChange={(e) => onRoleChange(e.target.value)}
          style={{
            width: '100%',
            padding: '0.625rem 1rem',
            border: '1px solid #ced4da',
            borderRadius: '4px',
            fontSize: '0.875rem',
            boxSizing: 'border-box',
            backgroundColor: 'white'
          }}
        >
          <option value="">All Roles</option>
          <option value="customer">Customer</option>
          <option value="admin">Admin</option>
          <option value="internal">Internal</option>
          <option value="device">Device</option>
        </select>
      </div>
    </div>
  )
}
