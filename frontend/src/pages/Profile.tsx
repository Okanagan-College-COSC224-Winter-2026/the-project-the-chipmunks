// import { useParams } from 'react-router-dom'
import './Profile.css'
<<<<<<< Updated upstream
// import { useEffect, useState } from 'react'
// import { getProfile } from '../util/api'
=======
import { useEffect, useState } from 'react'
import AvatarInitials from '../components/AvatarInitials'
import { updateUserProfile } from '../util/api'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

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
>>>>>>> Stashed changes

export default function Profile() {
  // const { id } = useParams()

  // const [profile, setProfile] = useState({})

  // useEffect(() => {
  //   const f = async () => {
  //     setProfile(await getProfile(id))
  //   }

  //   f()
  // }, [])

  return (
    <div className="Profile">
      <div className="profile-image">
        <img src={`https://placehold.co/200x200`} alt="profile" />
      </div>

      <div className="profile-info">
        <h1>Full Name</h1>
        <span>Place Holder</span>
        <h1>Email</h1>
        <span>placeholder@email.com</span>
      </div>
    </div>
  )
}