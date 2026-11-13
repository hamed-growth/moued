import { useState } from 'react'
import { Alert, Box, Button, Paper, Stack, Typography } from '@mui/material'
import { useNavigate } from 'react-router'
import { useAuth } from '../../features/auth'

export function MissionsPage() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function handleLogout() {
    setBusy(true); setError('')
    try { await signOut(); navigate('/login', { replace: true }) }
    catch (cause) { setError(cause.message || 'خروج انجام نشد.'); setBusy(false) }
  }
  return <Box component="main" className="page-shell"><Paper component="section" className="welcome missions-card" variant="outlined" aria-labelledby="missions-title"><Stack spacing={3}>
    <Typography color="primary" fontWeight={800} className="brand">موعود</Typography>
    <Box><Typography component="p" color="text.secondary">خوش آمدید{user?.username ? `، ${user.username}` : ''}</Typography><Typography id="missions-title" component="h1" variant="h4">مأموریت‌ها به‌زودی</Typography></Box>
    {error && <Alert severity="error" role="alert">{error}</Alert>}
    <Button variant="outlined" onClick={handleLogout} disabled={busy}>{busy ? 'در حال خروج...' : 'خروج از حساب'}</Button>
  </Stack></Paper></Box>
}
