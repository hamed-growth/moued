import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'
import { useAuth } from '../../features/auth'

export function LoginPage() {
  const { signIn, status } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    setBusy(true)
    setError('')
    try {
      await signIn({ username: data.get('username'), password: data.get('password') })
      const destination = location.state?.from
      navigate(destination?.pathname === '/' || destination?.pathname === '/login' ? '/account' : destination || '/account', { replace: true })
    } catch (cause) {
      setError(cause.status === 401 ? 'نام کاربری یا رمز عبور درست نیست.' : cause.message || 'ورود انجام نشد.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="page-shell">
      <section className="welcome" aria-labelledby="login-title">
        <h1 id="login-title">ورود</h1>
        {status === 'authenticated' && <p>شما وارد شده‌اید. <Link to="/account">حساب من</Link></p>}
        <form onSubmit={handleSubmit}>
          <label htmlFor="username">نام کاربری</label>
          <input id="username" name="username" autoComplete="username" required />
          <label htmlFor="password">رمز عبور</label>
          <input id="password" name="password" type="password" autoComplete="current-password" required />
          {error && <p role="alert">{error}</p>}
          <button type="submit" disabled={busy}>{busy ? 'در حال ورود...' : 'ورود'}</button>
        </form>
        <Link to="/home">صفحهٔ اصلی</Link>
      </section>
    </main>
  )
}
