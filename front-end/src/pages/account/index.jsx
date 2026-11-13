import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { useAuth } from '../../features/auth'

export function AccountPage() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function handleLogout() {
    setBusy(true)
    setError('')
    try {
      await signOut()
      navigate('/', { replace: true })
    } catch (cause) {
      setError(cause.message || 'خروج انجام نشد.')
      setBusy(false)
    }
  }

  return (
    <main className="page-shell">
      <section className="welcome" aria-labelledby="account-title">
        <h1 id="account-title">حساب من</h1>
        <p>نام کاربری: {user.username}</p>
        {error && <p role="alert">{error}</p>}
        <button type="button" onClick={handleLogout} disabled={busy}>{busy ? 'در حال خروج...' : 'خروج'}</button>
        <Link to="/home">صفحهٔ اصلی</Link>
      </section>
    </main>
  )
}
