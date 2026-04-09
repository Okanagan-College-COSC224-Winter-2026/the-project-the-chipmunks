/**
 * PasswordToggle.tsx — Dev 5 (Feature C: Password Management System)
 *
 * Reusable wrapper component that adds a show/hide toggle button
 * to any password input field. Toggles the input type between
 * 'password' and 'text'.
 *
 * Usage:
 *   <PasswordToggle>
 *     {(inputType) => (
 *       <Textbox type={inputType} placeholder="Password..." onInput={setValue} />
 *     )}
 *   </PasswordToggle>
 *
 * Uses a render-prop pattern so it works with the existing Textbox
 * component without modifying it.
 *
 * Place in: frontend/src/components/PasswordToggle.tsx
 */

import { useState } from "react";
import "./PasswordToggle.css";

interface PasswordToggleProps {
  /** Render prop: receives the current input type ('password' or 'text') */
  children: (inputType: "password" | "text") => React.ReactNode;
}

export default function PasswordToggle({ children }: PasswordToggleProps) {
  const [visible, setVisible] = useState(false);

  const toggleVisibility = () => {
    setVisible((prev) => !prev);
  };

  const inputType = visible ? "text" : "password";

  return (
    <div className="password-toggle-wrapper">
      {children(inputType)}
      <button
        type="button"
        className="password-toggle-btn"
        onClick={toggleVisibility}
        aria-label={visible ? "Hide password" : "Show password"}
        tabIndex={0}
      >
        {visible ? (
          // Eye-off icon (password is visible, click to hide)
          <svg
            className="password-toggle-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
            <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
            <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
            <line x1="1" y1="1" x2="23" y2="23" />
          </svg>
        ) : (
          // Eye icon (password is hidden, click to show)
          <svg
            className="password-toggle-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        )}
      </button>
    </div>
  );
}
