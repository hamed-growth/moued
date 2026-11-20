import { Box, Button } from '@mui/material'
import { AppIcon, ICONS } from '../../shared/ui/app-icon'
import { AnimatedNumber, TreasureChest } from './mission-elements'

const MISSION_ICONS = {
  gem: ICONS.gem, route: ICONS.route, flame: ICONS.flame,
  circleCheck: ICONS.circleCheck, bookOpen: ICONS.bookOpen, edit: ICONS.edit, heart: ICONS.heart,
}

const STATUS_COPY = {
  available: ['آماده انجام', 'available'],
  pending: ['در انتظار بررسی', 'pending'],
  approved: ['تکمیل‌شده', 'approved'],
  rejected: ['نیازمند تلاش دوباره', 'rejected'],
  missed: ['مهلت انجام گذشته', 'missed'],
  locked: ['در روز خودش فعال می‌شود', 'locked'],
  completed: ['تکمیل شد؛ جایزه آماده است', 'approved'],
}

function GreetingCard({ user, level }) {
  const name = user?.username || 'همراه موعود'
  return <section className="mission-greeting-card">
    <span className="mission-greeting-avatar"><AppIcon icon={ICONS.userRound} size={25} /></span>
    <div><h2>سلام، <bdi dir="auto">{name}</bdi>!</h2><p>سطح: <b>{level}</b></p></div>
    <span className="mission-greeting-spark"><AppIcon icon={ICONS.sparkles} size={18} /></span>
  </section>
}

function TodayOverview({ missions, statuses, onMissionSelect }) {
  return <section className="mission-side-card mission-today-overview">
    <div className="mission-card-heading"><div><span className="mission-eyebrow">یک قدم امروز</span><h3>خلاصهٔ امروز</h3></div><span className="mission-count-chip">{missions.length.toLocaleString('fa-IR')} مأموریت</span></div>
    <div className="mission-checklist">
      {missions.map((mission) => {
        const status = statuses[mission.id] || 'available'
        return <button className={`mission-check-row is-${status}`} key={mission.id} type="button" onClick={() => onMissionSelect(mission)}>
          <span className="mission-check-row__check">{status === 'approved' && <AppIcon icon={ICONS.circleCheck} size={17} />}</span>
          <span className="mission-check-row__title">{mission.title}</span>
          <small>{status === 'approved' ? 'انجام شد' : status === 'pending' ? 'در انتظار' : 'شروع'}</small>
        </button>
      })}
    </div>
  </section>
}

function MonthProgressCard({ activeDays, monthDays }) {
  const progress = Math.min(100, Math.round((activeDays / monthDays) * 100))
  return <section className="mission-side-card mission-month-card">
    <div className="mission-card-heading"><div><span className="mission-eyebrow">در مسیر رشد</span><h3>پیشرفت ماه</h3></div><AppIcon icon={ICONS.calendarDays} size={19} /></div>
    <div className="mission-month-card__numbers"><strong>{activeDays.toLocaleString('fa-IR')} از {monthDays.toLocaleString('fa-IR')} روز</strong><b>{progress.toLocaleString('fa-IR')}٪</b></div>
    <div className="mission-progress"><Box component="span" sx={{ width: `${progress}%` }} /></div>
    <p>هر قدم کوچک، تو را به هدف نزدیک‌تر می‌کند.</p>
  </section>
}

function NearestRewardCard({ activeDays }) {
  const daysLeft = 7 - (activeDays % 7 || 0)
  return <section className="mission-side-card mission-nearest-card">
    <div className="mission-nearest-card__chest"><TreasureChest state="closed" size={69} /></div>
    <div><span className="mission-eyebrow">جایزهٔ بعدی</span><h3>صندوق هفتگی</h3><p>با تکمیل {daysLeft.toLocaleString('fa-IR')} روز دیگر</p></div>
    <AppIcon icon={ICONS.chevronLeft} size={16} />
  </section>
}

function MissionDetailCard({ mission, status, canSubmit, dateLabel, isToday, onStart, onBack }) {
  const [label, tone] = STATUS_COPY[status] || STATUS_COPY.available
  return <section className="mission-detail-card" aria-labelledby="mission-detail-title">
    <header><span className="mission-detail-card__icon"><AppIcon icon={MISSION_ICONS[mission.icon] || ICONS.target} size={25} /></span><div><span className="mission-eyebrow">{isToday ? 'جزئیات مأموریت امروز' : `جزئیات مأموریت · ${dateLabel}`}</span><h3 id="mission-detail-title">{mission.title}</h3></div></header>
    <p className="mission-detail-card__description">{mission.id === 'daily-learning' ? '۱۵ دقیقه مطالعهٔ هدفمند در زمینهٔ فردی، معنوی یا مهارتی.' : mission.description}</p>
    <section className="mission-reward-box"><b>پاداش مأموریت</b><div><span className="mission-reward-chip is-points"><AppIcon icon={ICONS.star} size={17} />+{mission.points.toLocaleString('fa-IR')} امتیاز</span><span className="mission-reward-chip is-coins"><AppIcon icon={ICONS.coins} size={17} />+{mission.coins.toLocaleString('fa-IR')} سکه</span></div></section>
    <div className="mission-detail-status"><span>وضعیت:</span><b className={`mission-status-chip is-${tone}`}>{label}</b></div>
    <Button className="mission-start-button" variant="contained" disabled={!canSubmit} onClick={onStart} startIcon={<AppIcon icon={ICONS.route} size={18} />}>
      {canSubmit ? 'شروع مأموریت' : status === 'pending' ? 'در انتظار بررسی' : status === 'approved' ? 'مأموریت انجام شده' : 'فعلاً قابل شروع نیست'}
    </Button>
    <button className="mission-back-link" type="button" onClick={onBack}>بازگشت به خلاصهٔ امروز</button>
  </section>
}

function MonthReviewCard({ month }) {
  const days = month.dates.length
  return <section className="mission-review-card">
    <header><span className="mission-review-card__icon"><AppIcon icon={ICONS.calendarDays} size={21} /></span><div><span className="mission-eyebrow">مرور ماهانه</span><h3>{month.title}</h3></div><span className="mission-status-chip is-approved">تکمیل‌شده</span></header>
    <div className="mission-review-card__progress"><div><b>پیشرفت ماه</b><strong>{days.toLocaleString('fa-IR')} از {days.toLocaleString('fa-IR')} روز</strong></div><span className="mission-progress"><Box component="i" sx={{ width: '100%' }} /></span><small>۱۰۰٪</small></div>
    <h4>نتایج این ماه</h4>
    <div className="mission-review-stats"><span><AppIcon icon={ICONS.star} size={19} /><b>+۴۰۰</b><small>امتیاز</small></span><span><AppIcon icon={ICONS.coins} size={19} /><b>+۱۵۰</b><small>سکه</small></span><span><AppIcon icon={ICONS.flame} size={19} /><b>{days.toLocaleString('fa-IR')}</b><small>روز فعال</small></span></div>
  </section>
}

function CelebrationCard({ mission, activeDays, monthDays, onClaim, onBack }) {
  const rewardDays = Math.min(monthDays, activeDays + 1)
  const progress = Math.round((rewardDays / monthDays) * 100)
  return <section className="mission-celebration-card" aria-labelledby="mission-celebration-title">
    <div className="mission-celebration-card__chest"><TreasureChest state="open" size={104} /><span className="mission-confetti" aria-hidden="true"><i /><i /><i /><i /><i /><i /><i /></span></div>
    <span className="mission-eyebrow">آفرین، یک قدم دیگر!</span><h3 id="mission-celebration-title">مأموریت با موفقیت تکمیل شد!</h3>
    <p>{mission.title}</p>
    <div className="mission-celebration-rewards"><div><AppIcon icon={ICONS.star} size={22} /><strong>+<AnimatedNumber value={mission.points} animateFromZero /></strong><small>امتیاز</small></div><div><AppIcon icon={ICONS.coins} size={22} /><strong>+<AnimatedNumber value={mission.coins} animateFromZero /></strong><small>سکه</small></div></div>
    <div className="mission-celebration-progress"><span>پیشرفت ماه</span><strong>{progress.toLocaleString('fa-IR')}٪ · {rewardDays.toLocaleString('fa-IR')} از {monthDays.toLocaleString('fa-IR')} روز</strong><div className="mission-progress"><Box component="i" sx={{ width: `${progress}%` }} /></div></div>
    <div className="mission-weekly-banner"><TreasureChest state="ready" size={46} /><span><b>صندوق هفتگی باز شد!</b><small>یک روز دیگر به مسیرت اضافه شد</small></span><strong>+۱ روز</strong></div>
    <Button className="mission-claim-button" onClick={onClaim} variant="contained" startIcon={<AppIcon icon={ICONS.gift} size={18} />}>دریافت جایزه</Button>
    <button className="mission-back-link" type="button" onClick={onBack}>بعداً دریافت می‌کنم</button>
  </section>
}

export function MissionSidePanel({ view, user, level, todayMissions, todayStatuses, selectedMission, selectedStatus, canSubmit, month, activeDays, monthDays, dateLabel, isToday, onSelectMission, onStart, onClaim, onBack }) {
  return <div className="mission-side-panel">
    <GreetingCard user={user} level={level} />
    {view === 'overview' && <><TodayOverview missions={todayMissions} statuses={todayStatuses} onMissionSelect={onSelectMission} /><MonthProgressCard activeDays={activeDays} monthDays={monthDays} /><NearestRewardCard activeDays={activeDays} /></>}
    {view === 'detail' && selectedMission && <MissionDetailCard mission={selectedMission} status={selectedStatus} canSubmit={canSubmit} dateLabel={dateLabel} isToday={isToday} onStart={onStart} onBack={onBack} />}
    {view === 'archive' && <MonthReviewCard month={month} />}
    {view === 'reward' && selectedMission && <CelebrationCard mission={selectedMission} activeDays={activeDays} monthDays={monthDays} onClaim={onClaim} onBack={onBack} />}
  </div>
}
