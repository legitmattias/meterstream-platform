import { useState, useEffect } from 'react'
import { api } from '../../lib/api'
import { Notifications } from './Notifications'
import { SearchBar } from './SearchBar'
import { UserTable } from './UserTable'
import { UserFormModal } from './UserFormModal'
import { DeleteConfirmModal } from './DeleteConfirmModal'
import { RevokeSessionsModal } from './RevokeSessionsModal'
import { Pagination } from './Pagination'

export function UserManagement() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [successMessage, setSuccessMessage] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [deletingUser, setDeletingUser] = useState(null)
  const [revokingUser, setRevokingUser] = useState(null)
  const [page, setPage] = useState(1)
  const [totalUsers, setTotalUsers] = useState(0)
  const [validationError, setValidationError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const pageSize = 20

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm)
    }, 400) // Wait 400ms after user stops typing

    return () => clearTimeout(timer)
  }, [searchTerm])

  // Form state
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    role: 'customer',
    customer_id: '',
  })

  useEffect(() => {
    loadUsers()
  }, [page, debouncedSearchTerm, roleFilter])

  const loadUsers = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getUsers(page, pageSize, debouncedSearchTerm, roleFilter)
      setUsers(data.users)
      setTotalUsers(data.total)
    } catch (err) {
      setError('Failed to load users: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSearchChange = (value) => {
    setSearchTerm(value)
    setPage(1) // Reset to page 1 when searching
  }

  const handleRoleChange = (value) => {
    setRoleFilter(value)
    setPage(1) // Reset to page 1 when filtering
  }

  const validateCustomerId = (customerId, role) => {
    if (!customerId) return true // Optional field

    // Customer role requires 10-digit customer_id
    if (role === 'customer') {
      if (!/^\d{10}$/.test(customerId)) {
        return 'Customer ID must be exactly 10 digits for customer role (e.g., 1060598846)'
      }
    }
    return true
  }

  const handleCreateUser = async (e) => {
    e.preventDefault()
    setValidationError('')

    const validation = validateCustomerId(formData.customer_id, formData.role)
    if (validation !== true) {
      setValidationError(validation)
      return
    }

    try {
      await api.createUser(formData)
      setShowCreateModal(false)
      resetForm()
      showSuccess('User created successfully')
      loadUsers()
    } catch (err) {
      setValidationError('Failed to create user: ' + err.message)
    }
  }

  const handleUpdateUser = async (e) => {
    e.preventDefault()
    setValidationError('')

    const validation = validateCustomerId(formData.customer_id, formData.role)
    if (validation !== true) {
      setValidationError(validation)
      return
    }

    try {
      const updateData = { ...formData }
      // Remove password if empty (don't update it)
      if (!updateData.password) {
        delete updateData.password
      }
      await api.updateUser(editingUser.id, updateData)
      setEditingUser(null)
      resetForm()
      showSuccess('User updated successfully')
      loadUsers()
    } catch (err) {
      setValidationError('Failed to update user: ' + err.message)
    }
  }

  const handleDeleteUser = async () => {
    if (!deletingUser) return

    try {
      await api.deleteUser(deletingUser.id)
      const userName = deletingUser.name
      setDeletingUser(null)
      showSuccess(`User "${userName}" deleted successfully`)
      loadUsers()
    } catch (err) {
      setError('Failed to delete user: ' + err.message)
    }
  }

  const handleRevokeUserSessions = async () => {
    if (!revokingUser) return

    try {
      const result = await api.revokeUserSessions(revokingUser.id)
      const userName = revokingUser.name
      setRevokingUser(null)
      showSuccess(`Revoked ${result.revoked_count} session(s) for "${userName}"`)
    } catch (err) {
      setError('Failed to revoke sessions: ' + err.message)
      setRevokingUser(null)
    }
  }

  const showSuccess = (message) => {
    setSuccessMessage(message)
    setTimeout(() => setSuccessMessage(''), 3000) // Clear after 3 seconds
  }

  const openEditModal = (user) => {
    setEditingUser(user)
    setValidationError('')
    setFormData({
      email: user.email,
      password: '', // Don't show password
      name: user.name,
      role: user.role,
      customer_id: user.customer_id || '',
    })
  }

  const resetForm = () => {
    setFormData({
      email: '',
      password: '',
      name: '',
      role: 'customer',
      customer_id: '',
    })
    setValidationError('')
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    setValidationError('')
  }

  const handleCloseModal = () => {
    setShowCreateModal(false)
    setEditingUser(null)
    resetForm()
  }

  const totalPages = Math.ceil(totalUsers / pageSize)

  if (loading && users.length === 0) {
    return <div className="dashboard-section">Loading users...</div>
  }

  return (
    <div className="dashboard-section">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ margin: 0 }}>User Management</h2>
        <button
          onClick={() => {
            setShowCreateModal(true)
            setValidationError('')
          }}
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
          + Create User
        </button>
      </div>

      <Notifications successMessage={successMessage} error={error} />

      <SearchBar
        searchTerm={searchTerm}
        roleFilter={roleFilter}
        onSearchChange={handleSearchChange}
        onRoleChange={handleRoleChange}
      />

      <UserTable
        users={users}
        onEdit={openEditModal}
        onDelete={setDeletingUser}
        onRevokeSessions={setRevokingUser}
      />

      <Pagination
        currentPage={page}
        totalPages={totalPages}
        totalUsers={totalUsers}
        onPageChange={setPage}
      />

      {/* Create/Edit Modal */}
      {(showCreateModal || editingUser) && (
        <UserFormModal
          user={editingUser}
          formData={formData}
          validationError={validationError}
          onSubmit={editingUser ? handleUpdateUser : handleCreateUser}
          onChange={handleInputChange}
          onCancel={handleCloseModal}
        />
      )}

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        user={deletingUser}
        onCancel={() => setDeletingUser(null)}
        onConfirm={handleDeleteUser}
      />

      {/* Revoke Sessions Confirmation Modal */}
      <RevokeSessionsModal
        user={revokingUser}
        onCancel={() => setRevokingUser(null)}
        onConfirm={handleRevokeUserSessions}
      />
    </div>
  )
}
