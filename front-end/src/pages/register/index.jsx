import { useState } from 'react'
import { Alert, Box, Button, IconButton, InputAdornment, Link, Paper, Stack, TextField, Typography } from '@mui/material'
import { Controller, useForm } from 'react-hook-form'
import { Link as RouterLink, useNavigate } from 'react-router'
import { useAuth } from '../../features/auth'

export function RegisterPage() {
  const { register: registerUser } = useAuth()
  const navigate = useNavigate()
  const [showPassword, setShowPassword] = useState(false)
  const { control, handleSubmit, setError, getValues, formState: { errors, isSubmitting } } = useForm({ defaultValues: { username: '', email: '', password: '', confirmPassword: '' } })

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

  return <Box component="main" className="page-shell"><Paper component="section" className="welcome auth-card" variant="outlined" aria-labelledby="register-title"><Stack spacing={3}>
    <Box><Typography color="primary" fontWeight={800} className="brand">موعود</Typography><Typography id="register-title" component="h1" variant="h4">ساخت حساب</Typography><Typography color="text.secondary">به جمع موعود بپیوندید و مأموریت‌ها را آغاز کنید.</Typography></Box>
    <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate><Stack spacing={2}>
      <Controller name="username" control={control} rules={{ required: 'نام کاربری را وارد کنید.', minLength: { value: 3, message: 'نام کاربری باید دست‌کم ۳ نویسه باشد.' } }} render={({ field }) => <TextField {...field} label="نام کاربری" autoComplete="username" fullWidth error={!!errors.username} helperText={errors.username?.message} inputProps={{ dir: 'auto' }} />} />
      <Controller name="email" control={control} rules={{ required: 'ایمیل را وارد کنید.', pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'یک نشانی ایمیل معتبر وارد کنید.' } }} render={({ field }) => <TextField {...field} label="ایمیل" type="email" autoComplete="email" fullWidth error={!!errors.email} helperText={errors.email?.message} inputProps={{ dir: 'ltr' }} />} />
      <Controller name="password" control={control} rules={{ required: 'رمز عبور را وارد کنید.' }} render={({ field }) => <TextField {...field} label="رمز عبور" type={showPassword ? 'text' : 'password'} autoComplete="new-password" fullWidth error={!!errors.password} helperText={errors.password?.message} InputProps={{ endAdornment: <InputAdornment position="end"><IconButton aria-label={showPassword ? 'پنهان کردن رمز عبور' : 'نمایش رمز عبور'} onClick={() => setShowPassword((value) => !value)} edge="end">{showPassword ? 'پنهان' : 'نمایش'}</IconButton></InputAdornment> }} />} />
      <Controller name="confirmPassword" control={control} rules={{ required: 'تکرار رمز عبور را وارد کنید.', validate: (value) => value === getValues('password') || 'رمزهای عبور یکسان نیستند.' }} render={({ field }) => <TextField {...field} label="تکرار رمز عبور" type={showPassword ? 'text' : 'password'} autoComplete="new-password" fullWidth error={!!errors.confirmPassword} helperText={errors.confirmPassword?.message} />} />
      {errors.root && <Alert severity="error" role="alert">{errors.root.message}</Alert>}
      <Button variant="contained" type="submit" disabled={isSubmitting} size="large">{isSubmitting ? 'در حال ساخت حساب...' : 'ثبت‌نام'}</Button>
    </Stack></Box>
    <Typography color="text.secondary">حساب دارید؟ <Link component={RouterLink} to="/login">وارد شوید</Link></Typography>
  </Stack></Paper></Box>
}
