import { Link } from 'react-router'
import { useAuth } from '../../features/auth'

export function HomePage() {
  const { status, user } = useAuth()
  return (
    <main className="page-shell">
      <section className="welcome" aria-labelledby="welcome-title">
        <span className="eyebrow">مود کلاب</span>
        <h1 id="welcome-title">صفحهٔ اصلی</h1>
        <p>این صفحه برای همه قابل مشاهده است.</p>
        {status === 'authenticated' ? <p>سلام، {user.username}. <Link to="/account">حساب من</Link></p> : <Link to="/">ورود</Link>}
      </section>
    </main>
  )
}
