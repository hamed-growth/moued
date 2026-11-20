import { AppIcon, ICONS } from '../../shared/ui/app-icon'
import { Box } from '@mui/material'
import { getPersianParts } from '../../entities/mission'
import { PathScenery, TreasureChest } from './mission-elements'

const PATH_ROW_HEIGHT = 96

function makePath(count, amplitude) {
  const sway = [50, 50 + amplitude, 50, 50 - amplitude, 50, 50 + amplitude, 50, 50 - amplitude]
  return Array.from({ length: Math.max(count - 1, 0) }, (_, index) => {
    const y = index * PATH_ROW_HEIGHT + 38
    const nextY = y + PATH_ROW_HEIGHT
    const x = sway[index % sway.length]
    const nextX = sway[(index + 1) % sway.length]
    const segment = `C ${x} ${y + 36}, ${nextX} ${nextY - 36}, ${nextX} ${nextY}`
    return index === 0 ? `M ${x} ${y} ${segment}` : segment
  }).join(' ')
}

function getDateLabel(iso) {
  return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
    timeZone: 'Asia/Tehran', day: 'numeric', month: 'long',
  }).format(new Date(`${iso}T12:00:00Z`))
}

export function MissionJourney({ month, todayISO, selectedISO, isCurrentMonth, isArchive, onSelect, onSelectChest, scrollRef, isMobile, days = [] }) {
  const pathHeight = Math.max(PATH_ROW_HEIGHT, month.dates.length * PATH_ROW_HEIGHT)
  const currentDay = days.filter((day) => day.missions.length && day.missions.every((mission) => mission.status === 'approved')).length + 1
  const amplitude = isMobile ? 5.55 : 7.25
  const path = makePath(month.dates.length, amplitude)

  return <section className="mission-journey" aria-label="مسیر مأموریت‌های ماه">
    <div className="mission-journey__scroll" ref={scrollRef}>
      <Box component="div" className="mission-day-path" key={month.firstISO} sx={{ height: pathHeight }}>
        <svg className="mission-day-path__line" viewBox={`0 0 100 ${pathHeight}`} preserveAspectRatio="none" aria-hidden="true">
          <path className="mission-day-path__track" d={path} />
          <Box component="path" className="mission-day-path__progress" d={path} pathLength="1" sx={{ '--mission-progress-offset': 1 - ((currentDay - 1) / Math.max(month.dates.length - 1, 1)) }} />
        </svg>
        {month.dates.map((iso, index) => {
          const date = getPersianParts(iso).day
          const today = isCurrentMonth && iso === todayISO
          const missions = days.find((day) => day.date === iso)?.missions || []
          const completed = missions.length > 0 && missions.every((mission) => mission.status === 'approved')
          const state = completed ? 'completed' : today ? 'current' : iso < todayISO ? 'missed' : 'locked'
          const rewardDay = false
          const chestState = isArchive || (isCurrentMonth && date < currentDay) ? 'open' : rewardDay && date === 28 ? 'ready' : 'closed'
          const weekday = new Intl.DateTimeFormat('fa-IR', { timeZone: 'Asia/Tehran', weekday: 'long' }).format(new Date(`${iso}T12:00:00Z`))
          const position = 50 + (index % 8 === 1 ? amplitude : index % 8 === 3 || index % 8 === 7 ? -amplitude : 0)
          const label = `روز ${getDateLabel(iso)}، ${today ? 'امروز' : state === 'completed' ? 'تکمیل‌شده' : 'قفل‌شده'}`

          return <Box component="div" className={`mission-node-wrap${today ? ' is-today' : ''}${rewardDay ? ' has-chest' : ''}`} key={iso} sx={{ top: index * PATH_ROW_HEIGHT + 4, left: `${position}%`, animationDelay: `${Math.min(index * 40, 900)}ms` }}>
            <button
              className={`mission-day-node is-${state}${rewardDay ? ' is-chest-day' : ''}${selectedISO === iso ? ' is-selected' : ''}`}
              type="button" onClick={() => rewardDay ? onSelectChest(iso, chestState) : onSelect(iso)} aria-current={selectedISO === iso ? 'date' : undefined}
              data-day-index={index}
              onKeyDown={(event) => {
                const nodes = scrollRef.current?.querySelectorAll('[data-day-index]')
                const direction = event.key === 'ArrowDown' || event.key === 'ArrowLeft' ? 1 : event.key === 'ArrowUp' || event.key === 'ArrowRight' ? -1 : 0
                if (direction) {
                  event.preventDefault()
                  nodes?.[Math.max(0, Math.min(month.dates.length - 1, index + direction))]?.focus()
                } else if (event.key === 'Home') {
                  event.preventDefault(); nodes?.[0]?.focus()
                } else if (event.key === 'End') {
                  event.preventDefault(); nodes?.[month.dates.length - 1]?.focus()
                }
              }}
              aria-label={`${label}${rewardDay ? `، صندوق ${chestState === 'ready' ? 'جایزهٔ آماده' : chestState === 'open' ? 'دریافت‌شده' : 'قفل‌شده'}` : ''}`}
              data-today={today || undefined}
            >
              {rewardDay ? <TreasureChest state={chestState} size={58} /> : <span className="mission-day-node__circle">
                {state === 'completed' ? <AppIcon icon={ICONS.circleCheck} size={27} /> : state === 'locked' ? <AppIcon icon={ICONS.lockKeyhole} size={20} /> : <AppIcon icon={ICONS.star} size={31} />}
              </span>}
              <span className="mission-day-node__label"><b>{new Intl.NumberFormat('fa-IR').format(date)}</b><small>{weekday}</small></span>
              {today && <span className="mission-start-bubble">شروع</span>}
            </button>
          </Box>
        })}
        <PathScenery />
      </Box>
    </div>
  </section>
}
