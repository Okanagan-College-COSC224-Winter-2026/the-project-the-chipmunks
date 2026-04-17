import { useState } from 'react';
import { adminCreateUser, adminUpdateUser, AdminUserPayload } from '../util/api';
import { AdminUser } from '../hooks/useAdminUsers';
import './UserFormModal.css';

interface Props {
  user?: AdminUser;   // undefined = create mode
  onClose: () => void;
  onSaved: () => void;
}

export default function UserFormModal({ user, onClose, onSaved }: Props) {
  const editing = !!user;

  const [form, setForm] = useState({
    name:     user?.name     || '',
    email:    user?.email    || '',
    password: '',
    role:     user?.role     || 'student',
  });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const validate = (): string | null => {
    if (!form.name.trim())  return 'Name is required.';
    if (!form.email.trim()) return 'Email is required.';
    if (!editing && !form.password) return 'Password is required for new users.';
    if (form.password && form.password.length < 8) return 'Password must be at least 8 characters.';
    return null;
  };

  const handleSubmit = async () => {
    const err = validate();
    if (err) { setError(err); return; }

    setSaving(true);
    setError('');
    try {
      const payload: AdminUserPayload = {
        name:  form.name,
        email: form.email,
        role:  form.role,
      };
      if (form.password) payload.password = form.password;

      const res = editing
        ? await adminUpdateUser(user!.id, payload)
        : await adminCreateUser(payload);

      if (res && res.ok) {
        onSaved();
        onClose();
      } else {
        const d = await res?.json().catch(() => ({}));
        setError(d?.msg || d?.error || 'An error occurred.');
      }
    } catch {
      setError('Network error.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="UserFormModal__overlay" onClick={onClose}>
      <div className="UserFormModal__box" onClick={e => e.stopPropagation()}>
        <h2>{editing ? 'Edit User' : 'New User'}</h2>

        {error && <p className="UserFormModal__error">{error}</p>}

        <label>Full Name</label>
        <input
          placeholder="Full name"
          value={form.name}
          onChange={e => setForm({ ...form, name: e.target.value })}
        />

        <label>Email</label>
        <input
          placeholder="Email"
          type="email"
          value={form.email}
          onChange={e => setForm({ ...form, email: e.target.value })}
        />

        <label>{editing ? 'New Password (leave blank to keep current)' : 'Password'}</label>
        <input
          type="password"
          placeholder={editing ? 'New password (optional)' : 'Password'}
          value={form.password}
          onChange={e => setForm({ ...form, password: e.target.value })}
        />

        <label>Role</label>
        <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
          <option value="student">Student</option>
          <option value="teacher">Teacher</option>
          <option value="admin">Admin</option>
        </select>

        <div className="UserFormModal__actions">
          <button onClick={handleSubmit} disabled={saving}>
            {saving ? 'Saving...' : editing ? 'Save Changes' : 'Create User'}
          </button>
          <button onClick={onClose} className="UserFormModal__cancel">Cancel</button>
        </div>
      </div>
    </div>
  );
}
