import { useParams } from 'react-router-dom'
import { useNavigate } from 'react-router-dom'
import './Profile.css'
import { useEffect, useState } from 'react'
import AvatarInitials from '../components/AvatarInitials'
import { updateUserProfile } from '../util/api'

const BASE_URL = 'http://localhost:5000'

function splitName(fullName: string): { first: string; last: string } {
  const parts = (fullName || '').trim().split(/\s+/);
  return { first: parts[0] || '', last: parts.slice(1).join(' ') || '' };
}

function getCurrentUserId(): number | null {
  try {
    const stored = JSON.parse(localStorage.getItem('user') || '{}');
    return stored?.id ?? null;
  } catch {
    return null;
  }
}

export default function Profile() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [profile, setProfile] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({ name: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const currentUserId = getCurrentUserId()
  const isOwnProfile = currentUserId !== null && String(currentUserId) === String(id)

  useEffect(() => {
    ;(async () => {
      try {
        const resp = await fetch(`${BASE_URL}/user/${id}`, { credentials: 'include' })
        if (resp.ok) {
          const data = await resp.json()
          setProfile(data)
          setForm({ name: data.name || '' })
        }
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    })()
  }, [id])

  const save = async () => {
    if (!form.name.trim()) { setError('Name cannot be empty'); return; }
    setSaving(true); setError(''); setSuccess(false);
    try {
      const res = await updateUserProfile({ name: form.name.trim() });
      if (res && res.ok) {
        const updated = await res.json();
        const newName = updated.name || form.name;
        setProfile({ ...profile!, name: newName });
        try {
          const stored = JSON.parse(localStorage.getItem('user') || '{}');
          localStorage.setItem('user', JSON.stringify({ ...stored, name: newName }));
        } catch { /* ignore */ }
        setEditing(false); setSuccess(true);
        window.dispatchEvent(new Event('storage'));
      } else {
        setError('Update failed');
      }
    } catch { setError('Network error'); }
    finally { setSaving(false); }
  }

  if (loading) {
    return <div className="Profile"><p>Loading...</p></div>
  }

  const { first, last } = splitName(profile?.name || '')

  return (
    <div className="Profile">
      <div className="profile-card">

        {/* ── Header band: avatar + name + role ── */}
        <div className="profile-card__header">
          <div className="profile-card__avatar">
            <AvatarInitials
              firstName={first}
              lastName={last}
              userId={profile?.id || 0}
              size={96}
            />
          </div>
          <div className="profile-card__name">{profile?.name || '—'}</div>
          <span className="profile-card__role-badge">
            {profile?.role ?? 'User'}
          </span>
        </div>

        {/* ── Fields ── */}
        <div className="profile-card__body">

          {/* Status messages */}
          {success && <p className="profile-msg profile-msg--success">Profile updated successfully.</p>}
          {error   && <p className="profile-msg profile-msg--error">{error}</p>}

          {/* Full Name */}
          <div className="profile-field">
            <span className="profile-field__label">Full Name</span>
            {!editing ? (
              <div className="profile-field__row">
                <span className="profile-field__value">{profile?.name || '—'}</span>
                {isOwnProfile && (
                  <button className="profile-field__edit-btn" onClick={() => setEditing(true)}>
                    Edit
                  </button>
                )}
              </div>
            ) : (
              <div className="profile-field__edit-wrap">
                <input
                  className="profile-field__input"
                  value={form.name}
                  placeholder="Full name"
                  onChange={e => setForm({ name: e.target.value })}
                />
                <button className="profile-field__save-btn" onClick={save} disabled={saving}>
                  {saving ? 'Saving…' : 'Save'}
                </button>
                <button className="profile-field__cancel-btn" onClick={() => setEditing(false)}>
                  Cancel
                </button>
              </div>
            )}
          </div>

          {/* Email */}
          <div className="profile-field">
            <span className="profile-field__label">Email</span>
            <span className="profile-field__value">{profile?.email ?? '—'}</span>
          </div>

          {/* Role */}
          <div className="profile-field">
            <span className="profile-field__label">Role</span>
            <span className="profile-field__value" style={{ textTransform: 'capitalize' }}>
              {profile?.role ?? '—'}
            </span>
          </div>

        </div>

        {/* ── Footer: Change Password ── */}
        {isOwnProfile && (
          <div className="profile-card__footer">
            <button
              className="profile-change-password-btn"
              onClick={() => navigate('/change-password')}
            >
              Change Password
            </button>
          </div>
        )}

      </div>
    </div>
  )
}
