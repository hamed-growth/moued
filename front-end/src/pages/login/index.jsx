import { Alert, Box, Button, Link, Paper, Stack, TextField, Typography } from '@mui/material'
import { Controller, useForm } from 'react-hook-form'
import { Link as RouterLink, useLocation, useNavigate } from 'react-router'
import { useAuth } from '../../features/auth'

export function LoginPage() {
  const { signIn, status } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const { control, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm({
    defaultValues: { username: '', password: '' },
  })

  async function onSubmit(credentials) {
    try {
      await signIn(credentials)
      const destination = location.state?.from
      navigate(destination?.pathname === '/' || destination?.pathname === '/login' ? '/account' : destination || '/account', { replace: true })
    } catch (cause) {
      setError('root', { message: cause.status === 401 ? 'نام کاربری یا رمز عبور درست نیست.' : cause.message || 'ورود انجام نشد.' })
    }
  }

  return (
    <Box component="main" className="page-shell">
      <Paper component="section" className="welcome" variant="outlined" aria-labelledby="login-title">
        <Stack spacing={3}>
          <Typography id="login-title" component="h1" variant="h4">ورود</Typography>
          {status === 'authenticated' && <Alert severity="info">شما وارد شده‌اید. <Link component={RouterLink} to="/account">حساب من</Link></Alert>}
          <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
            <Stack spacing={2}>
              <Controller
                name="username"
                control={control}
                rules={{ required: 'نام کاربری را وارد کنید.' }}
                render={({ field }) => <TextField {...field} label="نام کاربری" autoComplete="username" fullWidth error={!!errors.username} helperText={errors.username?.message} />}
              />
              <Controller
                name="password"
                control={control}
                rules={{ required: 'رمز عبور را وارد کنید.' }}
                render={({ field }) => <TextField {...field} label="رمز عبور" type="password" autoComplete="current-password" fullWidth error={!!errors.password} helperText={errors.password?.message} />}
              />
              {errors.root && <Alert severity="error" role="alert">{errors.root.message}</Alert>}
              <Button variant="contained" type="submit" disabled={isSubmitting} size="large">{isSubmitting ? 'در حال ورود...' : 'ورود'}</Button>
            </Stack>
          </Box>
          <Link component={RouterLink} to="/home">صفحهٔ اصلی</Link>
        </Stack>
      </Paper>
    </Box>
  )
}
