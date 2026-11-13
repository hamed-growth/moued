import { IconButton } from '@mui/material'

export function PasswordVisibilityToggle({ visible, onToggle }) {
  return <IconButton className="auth-form__visibility" aria-label={visible ? 'پنهان کردن رمز عبور' : 'نمایش رمز عبور'} onClick={onToggle} edge="end" type="button">
    <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      {visible ? <><path d="M3 3l18 18" /><path d="M10.6 10.6a2 2 0 002.8 2.8" /><path d="M9.9 5.2A10.9 10.9 0 0112 5c5 0 8.5 4.5 9.5 7-.4 1-1.2 2.1-2.3 3.1M6.2 6.2C4.3 7.4 3 9.3 2.5 12c.8 2.1 3.8 7 9.5 7 1.2 0 2.3-.2 3.3-.7" /></> : <><path d="M2.5 12S6 5 12 5s9.5 7 9.5 7-3.5 7-9.5 7-9.5-7-9.5-7z" /><circle cx="12" cy="12" r="2.5" /></>}
    </svg>
  </IconButton>
}
