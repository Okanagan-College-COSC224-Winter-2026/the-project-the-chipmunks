import { useState, ChangeEvent } from "react"
import { changePassword } from "../util/api"
import PasswordToggle from "../components/PasswordToggle"

interface ValidationState {
  minLength: boolean
  hasUpper: boolean
  hasLower: boolean
  hasNumber: boolean
  passwordsMatch: boolean
}

export default function ChangePasswordForm() {
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [status, setStatus] = useState<{ message: string; type: "success" | "error" } | null>(null)
  const [loading, setLoading] = useState(false)

  const validation: ValidationState = {
    minLength: newPassword.length >= 8,
    hasUpper: /[A-Z]/.test(newPassword),
    hasLower: /[a-z]/.test(newPassword),
    hasNumber: /[0-9]/.test(newPassword),
    passwordsMatch: newPassword === confirmPassword && confirmPassword !== "",
  }

  const allValid = Object.values(validation).every(Boolean) && currentPassword !== ""

   const handleSubmit = async () => {
    setLoading(true)
    setStatus(null)
    try {
      await changePassword(currentPassword, newPassword)
      setStatus({ message: "Password changed successfully!", type: "success" })
      setCurrentPassword("")
      setNewPassword("")
      setConfirmPassword("")
    } catch (err) {
      const message = err instanceof Error ? err.message : "Something went wrong."
      setStatus({ message, type: "error" })
    } finally {
      setLoading(false)
    }
  }

  const CriterionRow = ({ met, label }: { met: boolean; label: string }) => (
    <p style={{ color: met ? "green" : "red", margin: "2px 0" }}>
      {met ? "\u2705" : "\u274C"} {label}
    </p>
  )

  return (
    <div style={{ maxWidth: "400px", margin: "2rem auto", padding: "1rem" }}>
      <h2>Change Password</h2>

      <label>Current Password</label>
      <PasswordToggle>
        {(inputType) => (
          <input
            type={inputType}
            value={currentPassword}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setCurrentPassword(e.target.value)}
            placeholder="Enter current password"
            style={{ display: "block", width: "100%", marginBottom: "1rem", padding: "0.5rem" }}
          />
        )}
      </PasswordToggle>

      <label>New Password</label>
      <PasswordToggle>
        {(inputType) => (
          <input
            type={inputType}
            value={newPassword}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setNewPassword(e.target.value)}
            placeholder="Enter new password"
            style={{ display: "block", width: "100%", marginBottom: "0.5rem", padding: "0.5rem" }}
          />
        )}
      </PasswordToggle>

      {newPassword.length > 0 && (
        <div style={{ marginBottom: "1rem", fontSize: "0.9rem" }}>
          <CriterionRow met={validation.minLength} label="At least 8 characters" />
          <CriterionRow met={validation.hasUpper} label="At least one uppercase letter" />
          <CriterionRow met={validation.hasLower} label="At least one lowercase letter" />
          <CriterionRow met={validation.hasNumber} label="At least one number" />
        </div>
      )}

      <label>Confirm New Password</label>
      <PasswordToggle>
        {(inputType) => (
          <input
            type={inputType}
            value={confirmPassword}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setConfirmPassword(e.target.value)}
            placeholder="Confirm new password"
            style={{ display: "block", width: "100%", marginBottom: "0.5rem", padding: "0.5rem" }}
          />
        )}
      </PasswordToggle>
      {confirmPassword.length > 0 && (
        <CriterionRow met={validation.passwordsMatch} label="Passwords match" />
      )}

      {status && (
        <p style={{ color: status.type === "success" ? "green" : "red", marginTop: "1rem" }}>
          {status.message}
        </p>
      )}

      <button
        onClick={handleSubmit}
        disabled={!allValid || loading}
        style={{
          marginTop: "1rem",
          padding: "0.6rem 1.5rem",
          backgroundColor: allValid ? "#007bff" : "#ccc",
          color: "white",
          border: "none",
          borderRadius: "4px",
          cursor: allValid ? "pointer" : "not-allowed",
          width: "100%",
        }}
      >
        {loading ? "Changing..." : "Change Password"}
      </button>
    </div>
  )
}