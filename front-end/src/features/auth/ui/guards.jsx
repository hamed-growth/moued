import { Navigate, Outlet, useLocation } from 'react-router'
import { Alert, Box, Button, CircularProgress, Paper, Stack } from '@mui/material'
import { useAuth } from '../model/use-auth'

function SessionState() {
  const { status, refresh } = useAuth()
  if (status === 'loading') return <Box component="main" className="page-shell" role="status"><Stack alignItems="center" spacing={2}><CircularProgress /><span>در حال بررسی نشست...</span></Stack></Box>
  return (
    <Box component="main" className="page-shell">
      <Paper className="welcome" variant="outlined"><Stack spacing={2}>
        <Alert severity="error" role="alert">وضعیت ورود قابل بررسی نیست. اتصال را بررسی کنید.</Alert>
        <Button variant="contained" type="button" onClick={() => refresh()}>تلاش دوباره</Button>
      </Stack></Paper>
    </Box>
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
