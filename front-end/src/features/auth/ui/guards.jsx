import { Navigate, Outlet, useLocation } from 'react-router'
import { useAuth } from '../model/use-auth'

function SessionState() {
  const { status, refresh } = useAuth()
  if (status === 'loading') return <main className="page-shell" role="status">در حال بررسی نشست...</main>
  return (
    <main className="page-shell">
      <div className="welcome" role="alert">
        <p>وضعیت ورود قابل بررسی نیست. اتصال را بررسی کنید.</p>
        <button type="button" onClick={() => refresh()}>تلاش دوباره</button>
      </div>
    </main>
  )
}

// Public pages stay visible to both guests and signed-in users.
export function GuestGuard() {
  return <Outlet />
}

export function AuthGuard() {
  const { status } = useAuth()
  const location = useLocation()
  if (status === 'loading' || status === 'error') return <SessionState />
  if (status === 'guest') return <Navigate to="/" replace state={{ from: location }} />
  return <Outlet />
}
