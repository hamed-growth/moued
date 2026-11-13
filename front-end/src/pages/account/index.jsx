import { useState } from 'react'
import { Alert, Box, Button, Link, Paper, Stack, Typography } from '@mui/material'
import { Link as RouterLink, useNavigate } from 'react-router'
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
    <Box component="main" className="page-shell">
      <Paper component="section" className="welcome" variant="outlined" aria-labelledby="account-title">
        <Stack spacing={2}>
          <Typography id="account-title" component="h1" variant="h4">حساب من</Typography>
          <Typography>نام کاربری: {user.username}</Typography>
          {error && <Alert severity="error" role="alert">{error}</Alert>}
          <Button variant="contained" type="button" onClick={handleLogout} disabled={busy}>{busy ? 'در حال خروج...' : 'خروج'}</Button>
          <Link component={RouterLink} to="/home">صفحهٔ اصلی</Link>
        </Stack>
      </Paper>
    </Box>
  )
}
