import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import Textbox from '../components/Textbox';
import StatusMessage from '../components/StatusMessage';
import PasswordToggle from '../components/PasswordToggle';
import { changePassword } from '../util/api';
import './LoginPage.css';
import './ChangePassword.css';

interface CriterionRule {
  label: string;
  test: (pw: string) => boolean;
}

const CRITERIA: CriterionRule[] = [
  { label: 'At least 8 characters',          test: pw => pw.length >= 8 },
  { label: 'At least one uppercase letter',   test: pw => /[A-Z]/.test(pw) },
  { label: 'At least one lowercase letter',   test: pw => /[a-z]/.test(pw) },
  { label: 'At least one number',             test: pw => /[0-9]/.test(pw) },
];

export default function ChangePassword() {
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const allCriteriaMet = CRITERIA.every(c => c.test(newPassword));
  const passwordsMatch = newPassword.length > 0 && newPassword === confirmPassword;
  const canSubmit = allCriteriaMet && passwordsMatch && currentPassword.length > 0;

  const handleChangePassword = async () => {
    try {
      setError('');
      setSuccess(false);

      if (!currentPassword || !newPassword || !confirmPassword) {
        setError('All fields are required');
        return;
      }

      if (newPassword !== confirmPassword) {
        setError('New passwords do not match');
        return;
      }

      await changePassword(currentPassword, newPassword);
      setSuccess(true);
      setTimeout(() => navigate('/home'), 2000);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || 'Failed to change password');
      } else {
        setError('Failed to change password');
      }
    }
  };

  return (
    <div className="LoginPage">
      <div className="LoginBlock">
        <h1>Change Password</h1>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          You must change your temporary password before continuing.
        </p>

        {error && (
          <div className="Status-Message Status-Message--error" role="alert">
            {error.split('\n').map((line, i) => <div key={i}>{line}</div>)}
          </div>
        )}
        {success && (
          <StatusMessage
            message="Password changed successfully! Redirecting..."
            type="success"
          />
        )}

        <div className="LoginInner">
          <div className="LoginInputs">
            <div className="LoginInputChunk">
              <span>Current Password</span>
              <PasswordToggle>
                {(inputType) => (
                  <Textbox
                    type={inputType}
                    placeholder='Current password...'
                    onInput={setCurrentPassword}
                    className='LoginInput'
                  />
                )}
              </PasswordToggle>
            </div>

            <div className="LoginInputChunk">
              <span>New Password</span>
              <PasswordToggle>
                {(inputType) => (
                  <Textbox
                    type={inputType}
                    placeholder='New password...'
                    onInput={setNewPassword}
                    className='LoginInput'
                  />
                )}
              </PasswordToggle>
            </div>

            {/* Real-time criteria checklist */}
            {newPassword.length > 0 && (
              <ul className="pw-criteria-list">
                {CRITERIA.map(({ label, test }) => {
                  const met = test(newPassword);
                  return (
                    <li key={label} className={met ? 'pw-criterion met' : 'pw-criterion unmet'}>
                      <span className="pw-criterion-icon">{met ? '✓' : '✗'}</span>
                      {label}
                    </li>
                  );
                })}
                <li className={passwordsMatch ? 'pw-criterion met' : 'pw-criterion unmet'}>
                  <span className="pw-criterion-icon">{passwordsMatch ? '✓' : '✗'}</span>
                  Passwords match
                </li>
              </ul>
            )}

            <div className="LoginInputChunk">
              <span>Confirm New Password</span>
              <PasswordToggle>
                {(inputType) => (
                  <Textbox
                    type={inputType}
                    placeholder='Confirm new password...'
                    onInput={setConfirmPassword}
                    className='LoginInput'
                  />
                )}
              </PasswordToggle>
            </div>
          </div>
        </div>

        <div>
          <Button
            onClick={handleChangePassword}
            disabled={success || !canSubmit}
          >
            Change Password
          </Button>
        </div>
      </div>
    </div>
  );
}
