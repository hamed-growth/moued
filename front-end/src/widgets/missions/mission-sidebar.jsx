import { Button } from '@mui/material'
import { Link as RouterLink } from 'react-router'
import { AppIcon, ICONS } from '../../shared/ui/app-icon'
import { MissionBrandMark } from './mission-elements'

const NAV_ITEMS = [
  { label: 'خانه', icon: ICONS.house, action: 'home' },
  { label: 'مأموریت‌ها', icon: ICONS.flag, action: 'missions', active: true },
  { label: 'رتبه‌بندی', icon: ICONS.trophy, disabled: true },
  { label: 'جوایز', icon: ICONS.gift, disabled: true },
  { label: 'پروفایل', icon: ICONS.userRound, action: 'profile' },
]

function NavItems({ mobile = false, onHome }) {
  return <>
    {NAV_ITEMS.map((item) => item.disabled ? (
      <span className="mission-nav__item is-disabled" key={item.label} aria-disabled="true">
        <AppIcon icon={item.icon} size={19} /><span>{item.label}</span><small>به‌زودی</small>
      </span>
    ) : item.action === 'home' ? (
      <button className={`mission-nav__item${mobile ? ' is-mobile' : ''}`} key={item.action} type="button" onClick={onHome}>
        <AppIcon icon={item.icon} size={19} /><span>{item.label}</span>
      </button>
    ) : <RouterLink className={`mission-nav__item${item.active ? ' is-active' : ''}`} to={item.action === 'profile' ? '/account' : '/missions'} key={item.action} aria-current={item.active ? 'page' : undefined}>
      <AppIcon icon={item.icon} size={19} /><span>{item.label}</span>
    </RouterLink>)}
  </>
}

export function MissionSidebar({ onLogout, busy, onHome }) {
  return <aside className="mission-sidebar" aria-label="ناوبری اصلی">
    <RouterLink className="mission-brand" to="/missions" aria-label="موعود، صفحهٔ مأموریت‌ها">
      <MissionBrandMark />
      <span>موعود<small>قدم‌های کوچک، رشد ماندگار</small></span>
    </RouterLink>
    <nav className="mission-nav"><NavItems onHome={onHome} /></nav>
    <div className="mission-sidebar__bottom">
      <RouterLink className="mission-nav__item" to="/account"><AppIcon icon={ICONS.userRound} size={19} /><span>حساب کاربری</span></RouterLink>
      <Button className="mission-logout" onClick={onLogout} disabled={busy} startIcon={<AppIcon icon={ICONS.logOut} size={18} />}>
        {busy ? 'در حال خروج…' : 'خروج از حساب'}
      </Button>
    </div>
  </aside>
}

export function MissionMobileNav({ onHome }) {
  return <nav className="mission-mobile-nav" aria-label="ناوبری موبایل"><NavItems mobile onHome={onHome} /></nav>
}
