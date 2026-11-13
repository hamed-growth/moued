import { Box, Link, Paper, Stack, Typography } from '@mui/material'
import { Link as RouterLink } from 'react-router'
import { useAuth } from '../../features/auth'

export function HomePage() {
  const { status, user } = useAuth()
  return (
    <Box component="main" className="page-shell">
      <Paper component="section" className="welcome" variant="outlined" aria-labelledby="welcome-title">
        <Stack spacing={2}>
          <Typography color="primary" fontWeight={700}>مود کلاب</Typography>
          <Typography id="welcome-title" component="h1" variant="h4">صفحهٔ اصلی</Typography>
          <Typography color="text.secondary">این صفحه برای همه قابل مشاهده است.</Typography>
          {status === 'authenticated' ? <Typography>سلام، {user.username}. <Link component={RouterLink} to="/account">حساب من</Link></Typography> : <Link component={RouterLink} to="/">ورود</Link>}
        </Stack>
      </Paper>
    </Box>
  )
}
