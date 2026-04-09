import { useState } from 'react';
import { useAdminUsers, AdminUser } from '../hooks/useAdminUsers';
import UserFormModal from '../components/UserFormModal';
import './AdminUsersPage.css';

export default function AdminUsersPage() {
  const {
    users, total, page, setPage,
    setRole, setSearch,
    loading, error,
    deactivate, reactivate,
    reload,
  } = useAdminUsers();

  const [modal, setModal] = useState<null | 'create' | AdminUser>(null);
  const [searchInput, setSearchInput] = useState('');

  const handleSearchChange = (val: string) => {
    setSearchInput(val);
    setSearch(val);
    setPage(1);
  };

  const handleRoleChange = (val: string) => {
    setRole(val);
    setPage(1);
  };

  return (
    <div className="AdminUsersPage">
      <div className="AdminUsersPage__header">
        <h1>User Management</h1>
        <button className="AdminUsersPage__newBtn" onClick={() => setModal('create')}>
          + New User
        </button>
      </div>

      <div className="AdminUsersPage__filters">
        <input
          placeholder="Search name or email"
          value={searchInput}
          onChange={e => handleSearchChange(e.target.value)}
          className="AdminUsersPage__search"
        />
        <select onChange={e => handleRoleChange(e.target.value)} className="AdminUsersPage__roleFilter">
          <option value="">All roles</option>
          <option value="student">Student</option>
          <option value="teacher">Teacher</option>
          <option value="admin">Admin</option>
        </select>
      </div>

      {loading && <p className="AdminUsersPage__loading">Loading...</p>}
      {error   && <p className="AdminUsersPage__error">{error}</p>}

      {!loading && !error && (
        <div className="AdminUsersPage__tableWrap">
          <table className="AdminUsersPage__table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', color: '#888' }}>
                    No users found.
                  </td>
                </tr>
              )}
              {users.map(u => (
                <tr key={u.id}>
                  <td>{u.name}</td>
                  <td>{u.email}</td>
                  <td>
                    <span className={`AdminUsersPage__role AdminUsersPage__role--${u.role}`}>
                      {u.role}
                    </span>
                  </td>
                  <td>
                    <span className={u.is_active ? 'AdminUsersPage__active' : 'AdminUsersPage__inactive'}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="AdminUsersPage__actions">
                    <button onClick={() => setModal(u)}>Edit</button>
                    {u.is_active
                      ? <button className="AdminUsersPage__deactivateBtn" onClick={() => deactivate(u.id)}>
                          Deactivate
                        </button>
                      : <button className="AdminUsersPage__reactivateBtn" onClick={() => reactivate(u.id)}>
                          Reactivate
                        </button>
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="AdminUsersPage__pagination">
        <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
          ← Prev
        </button>
        <span>Page {page}</span>
        <button onClick={() => setPage(p => p + 1)} disabled={users.length < 20}>
          Next →
        </button>
        <span className="AdminUsersPage__total">{total} total users</span>
      </div>

      {modal !== null && (
        <UserFormModal
          user={modal === 'create' ? undefined : modal}
          onClose={() => setModal(null)}
          onSaved={reload}
        />
      )}
    </div>
  );
}
