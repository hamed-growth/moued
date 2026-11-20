import { addDays } from './calendar.js'
import { DEMO_ARCHIVE_REWARDS, DEMO_MISSIONS, getDemoMissionStatus } from './demo-data.js'

export function buildDemoMonthStats(month, isCurrentMonth, todayISO, submissions) {
  const byDate = {}
  for (const iso of month.dates) {
    const noData = !isCurrentMonth && iso < todayISO
    const statuses = Object.fromEntries(DEMO_MISSIONS.map((mission) => {
      if (iso > todayISO) return [mission.id, 'locked']
      if (noData) return [mission.id, 'no-data']
      const submitted = submissions[`${iso}|${mission.id}`]
      const status = submitted?.status || submitted || getDemoMissionStatus(iso, mission.id, todayISO, true)
      return [mission.id, iso < todayISO && status === 'available' ? 'missed' : status]
    }))
    const values = Object.values(statuses)
    byDate[iso] = {
      statuses,
      approved: values.filter((status) => status === 'approved').length,
      pending: values.filter((status) => status === 'pending').length,
      noData: values.every((status) => status === 'no-data'),
    }
  }

  const history = Object.entries(byDate).filter(([iso, day]) => iso <= todayISO && !day.noData)
  const approved = history.reduce((sum, [, day]) => sum + day.approved, 0)
  const pending = history.reduce((sum, [, day]) => sum + day.pending, 0)
  const evaluated = Math.max(history.length * DEMO_MISSIONS.length, 1)
  let streak = 0
  for (let iso = todayISO; byDate[iso]; iso = addDays(iso, -1)) {
    const day = byDate[iso]
    if (!day || (!day.approved && !day.pending)) break
    streak += 1
  }

  const approvedRewards = (key) => history.reduce((sum, [, day]) => sum + DEMO_MISSIONS.reduce(
    (daySum, mission) => daySum + (day.statuses[mission.id] === 'approved' ? mission[key] : 0), 0,
  ), 0)

  return {
    byDate,
    approved,
    pending,
    points: approvedRewards('points'),
    coins: approvedRewards('coins'),
    monthPercent: Math.round((approved / evaluated) * 100),
    streak,
    todayApproved: byDate[todayISO]?.approved || 0,
    todayTotal: DEMO_MISSIONS.length,
  }
}

export function buildDemoArchiveStats(month) {
  const byDate = Object.fromEntries(month.dates.map((iso) => [iso, {
    statuses: Object.fromEntries(DEMO_MISSIONS.map(({ id }) => [id, 'approved'])),
    approved: DEMO_MISSIONS.length,
    pending: 0,
    noData: false,
  }]))
  return {
    byDate,
    approved: month.dates.length * DEMO_MISSIONS.length,
    pending: 0,
    points: DEMO_ARCHIVE_REWARDS.points,
    coins: DEMO_ARCHIVE_REWARDS.coins,
    monthPercent: 100,
    activeDays: month.dates.length,
    streak: month.dates.length,
    todayApproved: 0,
    todayTotal: DEMO_MISSIONS.length,
  }
}
