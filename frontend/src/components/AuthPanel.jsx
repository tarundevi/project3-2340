import { useState } from 'react'

export default function AuthPanel({ onSubmit, loading, error }) {
  const [mode, setMode] = useState('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [roleKey, setRoleKey] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    await onSubmit({ mode, email, password, roleKey })
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <p className="auth-kicker">Account Required</p>
        <h1 className="auth-title">Sign in to use NutriBot</h1>
        <p className="auth-copy">
          Create an account or sign in to access the chat.
        </p>

        <div className="auth-toggle">
          <button
            type="button"
            className={`nav-tab${mode === 'signin' ? ' active' : ''}`}
            onClick={() => setMode('signin')}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`nav-tab${mode === 'signup' ? ' active' : ''}`}
            onClick={() => setMode('signup')}
          >
            Sign Up
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="auth-label">
            Email
            <input
              type="email"
              className="auth-input"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              required
            />
          </label>

          <label className="auth-label">
            Password
            <input
              type="password"
              className="auth-input"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
              minLength={8}
              required
            />
          </label>

          <label className="auth-label">
            Role Key
            <input
              type="text"
              className="auth-input"
              value={roleKey}
              onChange={(event) => setRoleKey(event.target.value)}
              placeholder="Optional: admin or dev"
            />
          </label>

          {error ? <p className="auth-error">{error}</p> : null}

          <button type="submit" className="send-btn auth-submit" disabled={loading}>
            {loading ? 'Working…' : mode === 'signup' ? 'Create Account' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}
