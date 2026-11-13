import { IconButton } from '@mui/material'
import { AppIcon, ICONS } from '../../../shared/ui/app-icon'

export function PasswordVisibilityToggle({ visible, onToggle }) {
  return <IconButton className="auth-form__visibility" aria-label={visible ? 'پنهان کردن رمز عبور' : 'نمایش رمز عبور'} onClick={onToggle} edge="end" type="button">
    <AppIcon icon={visible ? ICONS.eyeOff : ICONS.eye} size={20} />
  </IconButton>
}
