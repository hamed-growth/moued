import { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { AppIcon, ICONS } from '../../shared/ui/app-icon'

export function AnimatedNumber({ value, animateFromZero = false }) {
  const [display, setDisplay] = useState(animateFromZero ? 0 : value)
  useEffect(() => {
    const start = display
    if (start === value) return undefined
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      const frame = window.requestAnimationFrame(() => setDisplay(value))
      return () => window.cancelAnimationFrame(frame)
    }
    let frame
    let startedAt
    const tick = (time) => {
      if (startedAt === undefined) startedAt = time
      const progress = Math.min((time - startedAt) / 600, 1)
      const eased = 1 - ((1 - progress) ** 3)
      setDisplay(Math.round(start + ((value - start) * eased)))
      if (progress < 1) frame = window.requestAnimationFrame(tick)
    }
    frame = window.requestAnimationFrame(tick)
    return () => window.cancelAnimationFrame(frame)
  // The previous displayed number is intentionally used as the animation start.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])

  return <span>{display.toLocaleString('fa-IR')}</span>
}

export function StatsBar({ hearts, points, coins, streak }) {
  const values = [
    { label: 'جان', value: hearts, icon: ICONS.heart, tone: 'heart' },
    { label: 'امتیاز', value: points, icon: ICONS.star, tone: 'points' },
    { label: 'سکه', value: coins, icon: ICONS.coins, tone: 'coins' },
    { label: 'روز متوالی', value: streak, icon: ICONS.flame, tone: 'streak' },
  ]
  return <section className="mission-statsbar" aria-label="وضعیت حساب">
    {values.map((item) => <div className={`mission-statsbar__item is-${item.tone}`} key={item.tone} role="group" aria-label={`${item.value.toLocaleString('fa-IR')} ${item.label}`}>
      <AppIcon icon={item.icon} size={19} />
      <strong><AnimatedNumber value={item.value} /></strong>
    </div>)}
  </section>
}

export function TreasureChest({ state = 'closed', size = 58 }) {
  return <Box component="span" className={`mission-chest is-${state}`} sx={{ '--chest-size': `${size}px` }} aria-hidden="true">
    <svg viewBox="0 0 72 64" role="presentation">
      {state !== 'closed' && <g className="mission-chest__rays" stroke="currentColor" strokeLinecap="round" strokeWidth="2">
        <path d="M36 4v-4M13 14l-4-4M59 14l4-4M6 32H1M66 32h5M18 6l-2-4M54 6l2-4" />
      </g>}
      <path className="mission-chest__lid" d={state === 'open' ? 'M12 25 21 9q2-4 7-4h19q5 0 7 4l7 16z' : 'M12 25V18q0-7 7-7h34q7 0 7 7v7z'} />
      <path className="mission-chest__body" d="M9 25h54v28q0 4-4 4H13q-4 0-4-4z" />
      <path className="mission-chest__edge" d="M8 25h56v9H8zM16 34v23M56 34v23" />
      <path className="mission-chest__lock" d="M30 36h12v14H30zM33 36v-4q0-4 3-4t3 4v4" />
      {state === 'open' && <path className="mission-chest__shine" d="m30 22 6-7 6 7-6 5z" />}
    </svg>
  </Box>
}

export function PathScenery() {
  return <svg className="mission-scenery" viewBox="0 0 520 112" preserveAspectRatio="none" aria-hidden="true" focusable="false">
    <path className="mission-scenery__hill" d="M0 89Q42 55 89 82t85 7q43-39 96-8t91 8q57-41 103-5t56 7v21H0z" />
    <path className="mission-scenery__hill is-back" d="M0 99q54-31 101-8t97 0q54-41 109-5t98 2q55-34 115 0v24H0z" />
    <g className="mission-scenery__plant" stroke="currentColor" strokeLinecap="round" strokeWidth="2" fill="none">
      <path d="M56 104V72m0 20q-22-2-23-17 19 0 23 17Zm0-8q18-3 19-19-16 1-19 19ZM463 105V77m0 18q-18 0-20-14 15 0 20 14Zm0-8q17-2 18-16-14 0-18 16Z" />
      <path d="M109 105q8-14 17 0m265 0q8-14 17 0" />
    </g>
  </svg>
}

export function MissionBrandMark() {
  return <span className="mission-brand__mark" aria-hidden="true">
    <svg viewBox="0 0 42 42"><path d="M21 4 34 13H8z" /><path d="M9 15h24v4H9zm3 6h18v13H12z" /><path d="M18 34V24h6v10" /><path d="M5 36h32" /></svg>
  </span>
}
