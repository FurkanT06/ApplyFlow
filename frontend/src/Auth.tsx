
import { useState, type FormEvent } from 'react'
import { loginUser, registerUser, saveToken } from './api'
import './Auth.css'

type AuthProps = {
  onLogin: () => void
}

export default function Auth({ onLogin }: AuthProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (mode === 'register') {
        await registerUser(email, password)
      }

      const response = await loginUser(email, password)
      saveToken(response.access_token)
      onLogin()
    } catch {
      setError(
        mode === 'login'
          ? 'Invalid email or password.'
          : 'Could not create account. Check your details or try another email.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">ApplyFlow</div>

        <h1>
          {mode === 'login' ? 'Welcome back' : 'Create your account'}
        </h1>

        <p>Track your applications. Organize your job search.</p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="auth-email">Email address</label>
          <input
            id="auth-email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />

          <label htmlFor="auth-password">Password</label>
          <input
            id="auth-password"
            type="password"
            autoComplete={
              mode === 'login' ? 'current-password' : 'new-password'
            }
            minLength={mode === 'register' ? 8 : undefined}
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />

          {error && <p className="auth-error" role="alert">{error}</p>}

          <button type="submit" disabled={loading}>
            {loading
              ? 'Please wait...'
              : mode === 'login'
                ? 'Log in'
                : 'Create account'}
          </button>
        </form>

        <p className="auth-switch">
          {mode === 'login'
            ? "Don't have an account?"
            : 'Already have an account?'}{' '}
          <button
            type="button"
            onClick={() => {
              setMode(mode === 'login' ? 'register' : 'login')
              setError('')
            }}
          >
            {mode === 'login' ? 'Sign up' : 'Log in'}
          </button>
        </p>
      </div>
    </div>
  )
}
