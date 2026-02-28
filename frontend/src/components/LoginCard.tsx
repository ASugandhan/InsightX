import { useState } from "react";
import NexusLogo from "./NexusLogo";

interface LoginCardProps {
  onClose: () => void;
}

export default function LoginCard({ onClose }: LoginCardProps) {
  const [emailFocused, setEmailFocused] = useState(false);
  const [passFocused, setPassFocused] = useState(false);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="login-card" onClick={e => e.stopPropagation()}>
        {/* Top accent bar */}
        <div className="login-card-bar" />

        {/* Close button */}
        <button className="login-card-close" onClick={onClose}>✕</button>

        {/* Brand row */}
        <div className="login-brand">
          <NexusLogo size={38} />
          <div>
            <div className="login-brand-name"><em>NEXUS</em></div>
            <div className="login-brand-tag">Payments Intelligence</div>
          </div>
        </div>

        <div className="login-heading">Welcome back</div>
        <div className="login-subheading">
          Log in to your NEXUS workspace to access live payment analytics and intelligence.
        </div>

        {/* Email field */}
        <div className="login-field">
          <div className="login-field-top">
            <label className="login-label">Work Email</label>
          </div>
          <div className="login-input-wrap">
            <input
              className="login-input"
              type="email"
              placeholder="jane@company.com"
              onFocus={() => setEmailFocused(true)}
              onBlur={() => setEmailFocused(false)}
              style={{
                borderColor: emailFocused ? "rgba(59,130,246,0.55)" : "rgba(255,255,255,0.1)",
                boxShadow: emailFocused ? "0 0 0 3px rgba(59,130,246,0.12)" : "none",
                background: emailFocused ? "rgba(59,130,246,0.04)" : "rgba(255,255,255,0.04)",
              }}
            />
            <span className="login-input-icon" style={{ color: emailFocused ? "var(--accent)" : undefined }}>✉</span>
          </div>
        </div>

        {/* Password field */}
        <div className="login-field">
          <div className="login-field-top">
            <label className="login-label">Password</label>
            <button className="login-forgot">Forgot password?</button>
          </div>
          <div className="login-input-wrap">
            <input
              className="login-input"
              type="password"
              placeholder="••••••••"
              onFocus={() => setPassFocused(true)}
              onBlur={() => setPassFocused(false)}
              style={{
                borderColor: passFocused ? "rgba(59,130,246,0.55)" : "rgba(255,255,255,0.1)",
                boxShadow: passFocused ? "0 0 0 3px rgba(59,130,246,0.12)" : "none",
                background: passFocused ? "rgba(59,130,246,0.04)" : "rgba(255,255,255,0.04)",
              }}
            />
            <span className="login-input-icon" style={{ color: passFocused ? "var(--accent)" : undefined }}>🔒</span>
          </div>
        </div>

        {/* Submit */}
        <button className="login-submit">
          Log in →
        </button>

        {/* Trust footer */}
        <div className="login-trust">
          <span>🔐 Enterprise-grade encryption</span>
          <span className="login-trust-dot" />
          <span>SOC 2 Type II</span>
          <span className="login-trust-dot" />
          <span>ISO 27001</span>
        </div>
      </div>
    </div>
  );
}