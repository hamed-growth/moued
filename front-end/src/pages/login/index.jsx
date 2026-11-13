import { useState } from 'react'
import { Alert, Button, Checkbox, FormControlLabel, InputAdornment, Link, Stack, TextField } from '@mui/material'
import { Controller, useForm } from 'react-hook-form'
import { Link as RouterLink, useLocation, useNavigate } from 'react-router'
import { PasswordVisibilityToggle, useAuth } from '../../features/auth'
import { AuthLayout } from '../../widgets/auth-layout'

export function LoginPage() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [showPassword, setShowPassword] = useState(false)
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

  return (
    <AuthLayout
      title="خوش اومدی"
      description="نام کاربری و رمز عبور خودتو وارد کن تا بتونی وارد شی"
      footer={<>حساب نداری؟ <Link component={RouterLink} to="/register">ثبت‌نام کن</Link></>}
    >
      <form className="auth-form" onSubmit={handleSubmit(onSubmit)} noValidate>
        <Stack spacing={2}>
          <Controller name="username" control={control} rules={{ required: 'نام کاربری را وارد کنید.' }} render={({ field }) => (
            <TextField {...field} className="auth-form__field" label="نام کاربری یا ایمیل" placeholder="نام کاربری یا ایمیل خود را وارد کنید" autoComplete="username" fullWidth error={!!errors.username} helperText={errors.username?.message} inputProps={{ dir: 'auto' }} />
          )} />
          <Controller name="password" control={control} rules={{ required: 'رمز عبور را وارد کنید.' }} render={({ field }) => (
            <TextField {...field} className="auth-form__field" label="رمز عبور" placeholder="رمز عبور خود را وارد کنید" type={showPassword ? 'text' : 'password'} autoComplete="current-password" fullWidth error={!!errors.password} helperText={errors.password?.message} inputProps={{ dir: 'ltr' }} InputProps={{ endAdornment: <InputAdornment position="end"><PasswordVisibilityToggle visible={showPassword} onToggle={() => setShowPassword((value) => !value)} /></InputAdornment> }} />
          )} />
          <Controller name="remember_me" control={control} render={({ field }) => <FormControlLabel className="auth-form__remember" control={<Checkbox {...field} checked={field.value} size="small" />} label="مرا به خاطر بسپار" />} />
          {errors.root && <Alert severity="error" role="alert">{errors.root.message}</Alert>}
          <Button className="auth-form__submit" variant="contained" type="submit" disabled={isSubmitting} size="large">{isSubmitting ? 'در حال ورود...' : 'ورود'}</Button>
        </Stack>
      </form>
    </AuthLayout>
  )
}
