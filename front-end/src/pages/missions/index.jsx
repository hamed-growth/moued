import { useEffect, useMemo, useRef, useState } from 'react'
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Drawer, Snackbar, useMediaQuery } from '@mui/material'
import { Link as RouterLink, useNavigate } from 'react-router'
import { DEMO_MISSIONS, DEMO_PROFILE, formatPersianDate, getCurrentPersianMonth, getDemoMissionStatus, getTehranTime, getTehranTodayISO, isMissionInTime, TODAY_MISSION_IDS } from '../../entities/mission'
import { useAuth } from '../../features/auth'
import { AppIcon, ICONS } from '../../shared/ui/app-icon'
import { MissionJourney, MissionMobileNav, MissionSidePanel, MissionSidebar, StatsBar } from '../../widgets/missions'
import { missionsDescendantSx, missionsSx } from './missions-sx'
import { MissionMonthPicker } from './mission-month-picker'

export function MissionsPage() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const isMobile = useMediaQuery('(max-width: 1023px)')
  const [todayISO] = useState(() => getTehranTodayISO())
  const [time, setTime] = useState(() => getTehranTime())
  const currentMonth = useMemo(() => getCurrentPersianMonth(todayISO), [todayISO])
  const [month, setMonth] = useState(() => currentMonth)
  const [selectedISO, setSelectedISO] = useState(todayISO)
  const [view, setView] = useState('overview')
  const [selectedMissionId, setSelectedMissionId] = useState(null)
  const [submissions, setSubmissions] = useState({})
  const [profile, setProfile] = useState(DEMO_PROFILE)
  const [mobilePanelOpen, setMobilePanelOpen] = useState(false)
  const [startDialogOpen, setStartDialogOpen] = useState(false)
  const [logoutBusy, setLogoutBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const pathRef = useRef(null)

  const isCurrentMonth = month.firstISO === currentMonth.firstISO
  const todayMissions = TODAY_MISSION_IDS.map((id) => DEMO_MISSIONS.find((mission) => mission.id === id)).filter(Boolean)
  const todayStatuses = Object.fromEntries(todayMissions.map((mission) => {
    const submitted = submissions[`${todayISO}|${mission.id}`]
    return [mission.id, submitted?.status || submitted || getDemoMissionStatus(todayISO, mission.id, todayISO, true)]
  }))
  const selectedMission = DEMO_MISSIONS.find((mission) => mission.id === selectedMissionId) || null
  const currentSelectedStatus = selectedMission
    ? submissions[`${selectedISO}|${selectedMission.id}`]?.status || submissions[`${selectedISO}|${selectedMission.id}`] || getDemoMissionStatus(selectedISO, selectedMission.id, todayISO, isCurrentMonth)
    : 'available'
  const selectedStatus = view === 'reward' ? 'completed' : currentSelectedStatus
  const canSubmit = Boolean(selectedMission && isCurrentMonth && selectedISO === todayISO
    && ['available', 'rejected'].includes(currentSelectedStatus) && isMissionInTime(selectedMission, time))
  useEffect(() => {
    const path = pathRef.current
    const today = path?.querySelector('[data-today="true"]')
    if (!path) return
    if (!today) {
      path.scrollTo({ top: 0, behavior: 'instant' })
      return
    }

    const dayBounds = today.getBoundingClientRect()
    const pathBounds = path.getBoundingClientRect()
    const top = path.scrollTop + dayBounds.top - pathBounds.top
      + (dayBounds.height - path.clientHeight) / 2
    const behavior = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'
    path.scrollTo({ top: Math.max(0, top), behavior })
  }, [month.firstISO])

  useEffect(() => {
    const interval = window.setInterval(() => setTime(getTehranTime()), 60_000)
    return () => window.clearInterval(interval)
  }, [])

  function openOverview() {
    setMonth(currentMonth)
    setSelectedISO(todayISO)
    setSelectedMissionId(null)
    setView('overview')
    setMobilePanelOpen(false)
  }

  function openMission(mission) {
    setSelectedMissionId(mission.id)
    setView('detail')
    if (isMobile) setMobilePanelOpen(true)
  }

  function selectMonth(dateISO) {
    const nextMonth = getCurrentPersianMonth(dateISO)
    if (nextMonth.firstISO === month.firstISO) return

    const isTodayMonth = nextMonth.firstISO === currentMonth.firstISO
    setMonth(nextMonth)
    setSelectedISO(isTodayMonth ? todayISO : nextMonth.firstISO)
    setSelectedMissionId(null)
    setView(isTodayMonth ? 'overview' : 'archive')
    setMobilePanelOpen(false)
  }

  function selectDay(iso) {
    setSelectedISO(iso)
    if (isCurrentMonth) {
      const mission = DEMO_MISSIONS.find((item) => item.id === 'daily-learning')
      setSelectedMissionId(mission.id)
      setView('detail')
    } else {
      setView('archive')
      setSelectedMissionId(null)
    }
    if (isMobile) setMobilePanelOpen(true)
  }

  function selectChest(iso, chestState) {
    setSelectedISO(iso)
    if (chestState === 'ready') {
      setNotice('صندوق هفتگی آماده است؛ با یک قدم دیگر مسیر جایزه را کامل کن.')
    } else if (isArchiveMonth) {
      setView('archive')
      if (isMobile) setMobilePanelOpen(true)
    }
  }

  const isArchiveMonth = !isCurrentMonth

  function startMission() {
    if (canSubmit) setStartDialogOpen(true)
  }

  function completeMission() {
    if (!selectedMission || !canSubmit) return
    setStartDialogOpen(false)
    setView('reward')
    if (isMobile) setMobilePanelOpen(true)
  }

  function claimReward() {
    if (!selectedMission) return
    setSubmissions((previous) => ({ ...previous, [`${todayISO}|${selectedMission.id}`]: { status: 'approved' } }))
    setProfile((previous) => ({
      ...previous,
      points: previous.points + selectedMission.points,
      coins: previous.coins + selectedMission.coins,
      streak: previous.streak + 1,
      activeDays: Math.min(month.dates.length, previous.activeDays + 1),
    }))
    setNotice(`+${selectedMission.points.toLocaleString('fa-IR')} امتیاز و +${selectedMission.coins.toLocaleString('fa-IR')} سکه دریافت شد.`)
    setView('overview')
    setSelectedMissionId(null)
    setMobilePanelOpen(false)
  }

  async function handleLogout() {
    setLogoutBusy(true)
    setError('')
    try {
      await signOut()
      navigate('/login', { replace: true })
    } catch (cause) {
      setError(cause.message || 'خروج انجام نشد.')
      setLogoutBusy(false)
    }
  }

  const panel = <MissionSidePanel
    view={view} user={user} level={profile.level} todayMissions={todayMissions} todayStatuses={todayStatuses}
    selectedMission={selectedMission} selectedStatus={selectedStatus} canSubmit={canSubmit}
    month={month} activeDays={profile.activeDays} monthDays={currentMonth.dates.length}
    onSelectMission={openMission} onStart={startMission} onClaim={claimReward}
    dateLabel={formatPersianDate(selectedISO, { day: 'numeric', month: 'long' })} isToday={selectedISO === todayISO}
    onBack={openOverview}
  />

  return <Box component="div" className="missions-app" sx={missionsSx}>
    <MissionSidebar onLogout={handleLogout} busy={logoutBusy} onHome={openOverview} />
    <main className="missions-main">
      <div className="mission-mobile-statsbar"><StatsBar hearts={profile.hearts} points={profile.points} coins={profile.coins} streak={profile.streak} /></div>
      <header className="mission-mobile-header">
        <RouterLink className="mission-brand" to="/missions"><span className="mission-brand__mark"><AppIcon icon={ICONS.route} size={21} /></span><span>موعود<small>مأموریت‌های من</small></span></RouterLink>
      </header>
      {error && <Alert className="mission-global-error" severity="error" role="alert">{error}</Alert>}
      <h1 className="mission-sr-only">مأموریت‌ها</h1>
      <div className="mission-path-toolbar">
        <MissionMonthPicker monthISO={month.firstISO} todayISO={todayISO} onSelect={selectMonth} />
        <div className="mission-main-heading__chips"><span><AppIcon icon={ICONS.target} size={16} />{todayMissions.length.toLocaleString('fa-IR')} مأموریت امروز</span><span><AppIcon icon={ICONS.calendarDays} size={16} />{profile.activeDays.toLocaleString('fa-IR')} روز فعال</span></div>
      </div>
      <MissionJourney
        month={month} todayISO={todayISO} selectedISO={selectedISO}
        isCurrentMonth={isCurrentMonth} isArchive={isArchiveMonth} isMobile={isMobile}
        onSelect={selectDay} onSelectChest={selectChest} scrollRef={pathRef}
      />
    </main>
    <aside className="mission-insights">
      <StatsBar hearts={profile.hearts} points={profile.points} coins={profile.coins} streak={profile.streak} />
      <div className="mission-desktop-panel">{panel}</div>
    </aside>
    <MissionMobileNav onHome={openOverview} />
    <Drawer anchor="bottom" open={isMobile && mobilePanelOpen} onClose={() => setMobilePanelOpen(false)} className="mission-mobile-drawer" sx={{ '& .MuiBackdrop-root': { bgcolor: 'rgb(51 46 33 / 30%)', backdropFilter: 'blur(3px)' } }} PaperProps={{
      className: 'mission-mobile-drawer__paper',
      sx: { ...missionsDescendantSx, bottom: 'calc(61px + env(safe-area-inset-bottom))', maxHeight: '78svh', p: '8px 17px 15px', overflow: 'auto', border: '1px solid #eee2c7', borderRadius: '28px 28px 0 0', bgcolor: 'var(--mission-bg)', boxShadow: '0 -8px 35px rgb(90 70 20 / 16%)', '& .mission-side-panel': { gap: 1.1 }, '& .mission-greeting-card': { minHeight: 64, p: '9px 12px' }, '& .mission-greeting-avatar': { width: 34, height: 34, flexBasis: 34 }, '& .mission-nearest-card': { minHeight: 75 }, '& .mission-side-card, & .mission-detail-card, & .mission-review-card, & .mission-celebration-card': { p: 1.5 } },
    }}>
      <Box component="span" className="mission-mobile-drawer__handle" aria-hidden="true" sx={{ display: 'block', width: 42, height: 4, mx: 'auto', mt: '2px', mb: 1.5, borderRadius: 999, bgcolor: '#cfc5ad' }} />{panel}
    </Drawer>
    <Dialog open={startDialogOpen} onClose={() => setStartDialogOpen(false)} fullWidth maxWidth="xs" aria-labelledby="mission-start-title" sx={{ '& .MuiDialogTitle-root': { color: 'var(--mission-text)', fontFamily: 'var(--font-family)', fontSize: 16, fontWeight: 800 }, '& .MuiDialogContent-root, & .MuiDialogActions-root': { fontFamily: 'var(--font-family)' }, '& .MuiDialogActions-root': { p: '12px 20px 18px' }, '& .MuiDialogActions-root .MuiButton-root': { minHeight: 43, borderRadius: '12px', fontFamily: 'var(--font-family)' }, '& .mission-submit-copy': { m: 0, color: '#6d695b', fontSize: 12, lineHeight: 1.9 } }}>
      <DialogTitle id="mission-start-title">آماده‌ای شروع کنی؟</DialogTitle>
      <DialogContent><p className="mission-submit-copy">وقتی {selectedMission?.title} را انجام دادی، آن را کامل کن تا جایزهٔ نمایشی‌ات باز شود.</p></DialogContent>
      <DialogActions><Button onClick={() => setStartDialogOpen(false)}>بعداً</Button><Button variant="contained" onClick={completeMission} disabled={!canSubmit}>مأموریت را انجام دادم</Button></DialogActions>
    </Dialog>
    <Snackbar open={Boolean(notice)} autoHideDuration={4500} onClose={() => setNotice('')} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
      <Alert severity="success" onClose={() => setNotice('')} role="status">{notice}</Alert>
    </Snackbar>
  </Box>
}
