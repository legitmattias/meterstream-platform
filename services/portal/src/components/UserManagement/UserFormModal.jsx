export function UserFormModal({
  user,
  formData,
  validationError,
  onSubmit,
  onChange,
  onCancel
}) {
  const isEditing = !!user

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 1000
    }}>
      <div style={{
        background: 'white',
        padding: '2rem',
        borderRadius: '8px',
        width: '90%',
        maxWidth: '500px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
      }}>
        <h3 style={{ marginTop: 0, marginBottom: '1.5rem', fontSize: '1.25rem', fontWeight: '600' }}>
          {isEditing ? 'Edit User' : 'Create User'}
        </h3>

        {validationError && (
          <div style={{
            padding: '0.75rem',
            background: '#fee',
            color: '#c00',
            borderRadius: '4px',
            marginBottom: '1rem',
            fontSize: '0.875rem'
          }}>
            {validationError}
          </div>
        )}

        <form onSubmit={onSubmit}>
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500', color: '#495057' }}>
              Email
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={onChange}
              required
              style={{
                width: '100%',
                padding: '0.625rem',
                border: '1px solid #ced4da',
                borderRadius: '4px',
                fontSize: '0.875rem',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500', color: '#495057' }}>
              Password {isEditing && <span style={{ fontWeight: '400', color: '#6c757d' }}>(leave empty to keep current)</span>}
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={onChange}
              required={!isEditing}
              minLength={8}
              style={{
                width: '100%',
                padding: '0.625rem',
                border: '1px solid #ced4da',
                borderRadius: '4px',
                fontSize: '0.875rem',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500', color: '#495057' }}>
              Name
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={onChange}
              required
              minLength={2}
              style={{
                width: '100%',
                padding: '0.625rem',
                border: '1px solid #ced4da',
                borderRadius: '4px',
                fontSize: '0.875rem',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500', color: '#495057' }}>
              Role
            </label>
            <select
              name="role"
              value={formData.role}
              onChange={onChange}
              style={{
                width: '100%',
                padding: '0.625rem',
                border: '1px solid #ced4da',
                borderRadius: '4px',
                fontSize: '0.875rem',
                boxSizing: 'border-box'
              }}
            >
              <option value="customer">Customer</option>
              <option value="admin">Admin</option>
              <option value="internal">Internal</option>
              <option value="device">Device</option>
            </select>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500', color: '#495057' }}>
              Customer ID {formData.role === 'customer' && <span style={{ color: '#dc3545' }}>*</span>}
            </label>
            <input
              type="text"
              name="customer_id"
              value={formData.customer_id}
              onChange={onChange}
              placeholder={formData.role === 'customer' ? '1060598846 (10 digits required)' : 'Optional for admin/internal'}
              required={formData.role === 'customer'}
              pattern={formData.role === 'customer' ? '\\d{10}' : undefined}
              style={{
                width: '100%',
                padding: '0.625rem',
                border: '1px solid #ced4da',
                borderRadius: '4px',
                fontSize: '0.875rem',
                boxSizing: 'border-box'
              }}
            />
            {formData.role === 'customer' && (
              <div style={{ marginTop: '0.25rem', fontSize: '0.75rem', color: '#6c757d' }}>
                Required: 10-digit customer ID (e.g., 1060598846)
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
            <button
              type="button"
              onClick={onCancel}
              style={{
                padding: '0.625rem 1.25rem',
                background: 'white',
                color: '#6c757d',
                border: '1px solid #dee2e6',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500'
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{
                padding: '0.625rem 1.25rem',
                background: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500'
              }}
            >
              {isEditing ? 'Update User' : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
