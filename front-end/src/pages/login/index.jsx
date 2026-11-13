import { Alert, Box, Button, Checkbox, FormControlLabel, IconButton, InputAdornment, Link, Paper, Stack, TextField, Typography } from '@mui/material'
import { useState } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { Link as RouterLink, useLocation, useNavigate } from 'react-router'
import { useAuth } from '../../features/auth'

export function LoginPage() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const { control, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm({
    defaultValues: { username: '', password: '', remember_me: false },
  })

  async function onSubmit(credentials) {
    try {
      await signIn(credentials)
      const destination = location.state?.from
      const target = typeof destination === 'string' ? destination : destination?.pathname
      navigate(target?.startsWith('/') && !['/', '/login', '/register'].includes(target) ? target : '/missions', { replace: true })
    } catch (cause) {
      setError('root', { message: cause.status === 401 ? 'نام کاربری یا رمز عبور درست نیست.' : cause.message || 'ورود انجام نشد.' })
    }
  }

  const [showPassword, setShowPassword] = useState(false)
  return (
    <Box component="main" className="page-shell">
      <Paper component="section" className="welcome" variant="outlined" aria-labelledby="login-title">
        <Stack spacing={3}>
          <Box><Typography color="primary" fontWeight={800} className="brand">موعود</Typography><Typography id="login-title" component="h1" variant="h4">خوش آمدید</Typography><Typography color="text.secondary">برای ادامه، وارد حساب خود شوید.</Typography></Box>
          <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
            <Stack spacing={2}>
              <Controller
                name="username"
                control={control}
                rules={{ required: 'نام کاربری را وارد کنید.' }}
                render={({ field }) => <TextField {...field} label="نام کاربری یا ایمیل" autoComplete="username" fullWidth error={!!errors.username} helperText={errors.username?.message} inputProps={{ dir: 'auto' }} />}
              />
              <Controller
                name="password"
                control={control}
                rules={{ required: 'رمز عبور را وارد کنید.' }}
                render={({ field }) => <TextField {...field} label="رمز عبور" type={showPassword ? 'text' : 'password'} autoComplete="current-password" fullWidth error={!!errors.password} helperText={errors.password?.message} InputProps={{ endAdornment: <InputAdornment position="end"><IconButton aria-label={showPassword ? 'پنهان کردن رمز عبور' : 'نمایش رمز عبور'} onClick={() => setShowPassword((value) => !value)} edge="end">{showPassword ? 'پنهان' : 'نمایش'}</IconButton></InputAdornment> }} />}
              />
              <Controller name="remember_me" control={control} render={({ field }) => <FormControlLabel control={<Checkbox {...field} checked={field.value} />} label="مرا به خاطر بسپار" />} />
              {errors.root && <Alert severity="error" role="alert">{errors.root.message}</Alert>}
              <Button variant="contained" type="submit" disabled={isSubmitting} size="large">{isSubmitting ? 'در حال ورود...' : 'ورود'}</Button>
            </Stack>
          </Box>
          <Typography color="text.secondary">حساب ندارید؟ <Link component={RouterLink} to="/register">ثبت‌نام کنید</Link></Typography>
        </Stack>
      </Paper>
    </Box>
  )
}
