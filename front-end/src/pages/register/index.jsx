import { useState } from 'react'
import { Alert, Button, InputAdornment, Link, Stack, TextField } from '@mui/material'
import { Controller, useForm } from 'react-hook-form'
import { Link as RouterLink, useNavigate } from 'react-router'
import { PasswordVisibilityToggle, useAuth } from '../../features/auth'
import { AppIcon, ICONS } from '../../shared/ui/app-icon'
import { AuthLayout } from '../../widgets/auth-layout'

export function RegisterPage() {
  const { register: registerUser } = useAuth()
  const navigate = useNavigate()
  const [showPassword, setShowPassword] = useState(false)
  const { control, handleSubmit, setError, getValues, formState: { errors, isSubmitting } } = useForm({
    defaultValues: { username: '', email: '', password: '', confirmPassword: '' },
  })

  async function onSubmit(formValues) {
    const userData = Object.fromEntries(Object.entries(formValues).filter(([key]) => key !== 'confirmPassword'))
    try {
      await registerUser(userData)
      navigate('/missions', { replace: true })
    } catch (cause) {
      const fields = cause.details?.field_errors
      if (fields) Object.entries(fields).forEach(([field, messages]) => setError(field, { type: 'server', message: messages[0] }))
      else setError('root', { message: cause.status === 403 ? 'درخواست امن تأیید نشد. صفحه را تازه کنید و دوباره تلاش کنید.' : cause.message || 'ثبت‌نام انجام نشد.' })
    }
  }

  return (
    <AuthLayout
      title="ساخت حساب"
      description="حساب کاربری بساز و به جمع موعود بپیوند"
      footer={<>حساب داری؟ <Link component={RouterLink} to="/login">وارد شو</Link></>}
    >
      <form className="auth-form" onSubmit={handleSubmit(onSubmit)} noValidate>
        <Stack spacing={2}>
          <Controller name="username" control={control} rules={{ required: 'نام کاربری را وارد کنید.', minLength: { value: 3, message: 'نام کاربری باید دست‌کم ۳ نویسه باشد.' } }} render={({ field }) => (
            <TextField {...field} className="auth-form__field" label="نام کاربری" autoComplete="username" fullWidth error={!!errors.username} helperText={errors.username?.message} inputProps={{ dir: 'auto' }} />
          )} />
          <Controller name="email" control={control} rules={{ required: 'ایمیل را وارد کنید.', pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'یک نشانی ایمیل معتبر وارد کنید.' } }} render={({ field }) => (
            <TextField {...field} className="auth-form__field" label="ایمیل" type="email" autoComplete="email" fullWidth error={!!errors.email} helperText={errors.email?.message} inputProps={{ dir: 'ltr' }} />
          )} />
          <Controller name="password" control={control} rules={{ required: 'رمز عبور را وارد کنید.' }} render={({ field }) => (
            <TextField {...field} className="auth-form__field" label="رمز عبور" type={showPassword ? 'text' : 'password'} autoComplete="new-password" fullWidth error={!!errors.password} helperText={errors.password?.message} inputProps={{ dir: 'ltr' }} InputProps={{ endAdornment: <InputAdornment position="end"><PasswordVisibilityToggle visible={showPassword} onToggle={() => setShowPassword((value) => !value)} /></InputAdornment> }} />
          )} />
          <Controller name="confirmPassword" control={control} rules={{ required: 'تکرار رمز عبور را وارد کنید.', validate: (value) => value === getValues('password') || 'رمزهای عبور یکسان نیستند.' }} render={({ field }) => (
            <TextField {...field} className="auth-form__field" label="تکرار رمز عبور" type={showPassword ? 'text' : 'password'} autoComplete="new-password" fullWidth error={!!errors.confirmPassword} helperText={errors.confirmPassword?.message} inputProps={{ dir: 'ltr' }} />
          )} />
          {errors.root && <Alert severity="error" role="alert">{errors.root.message}</Alert>}
          <Button className="auth-form__submit" variant="contained" type="submit" disabled={isSubmitting} size="large" startIcon={<AppIcon icon={ICONS.add} size={18} />}>{isSubmitting ? 'در حال ساخت حساب...' : 'ثبت‌نام'}</Button>
        </Stack>
      </form>
    </AuthLayout>
  )
}
