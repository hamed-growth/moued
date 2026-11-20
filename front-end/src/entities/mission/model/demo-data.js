export const DEMO_PROFILE = Object.freeze({ hearts: 5, points: 1340, coins: 480, streak: 12, activeDays: 18, monthDays: 30, level: 'همراه' })
export const DEMO_ARCHIVE_REWARDS = Object.freeze({ points: 400, coins: 150 })

export const TODAY_MISSION_IDS = Object.freeze(['daily-learning', 'movement', 'kindness'])

export const DEMO_MISSIONS = Object.freeze([
  { id: 'morning-prayer', title: 'نماز اول وقت', description: 'نماز صبح را در زمان خودش به‌جا بیاور.', category: 'عبادت', points: 20, coins: 4, time: ['05:00', '07:00'], icon: 'gem' },
  { id: 'daily-learning', title: 'مطالعهٔ ۱۵ دقیقه‌ای', description: '۱۵ دقیقه مطالعهٔ هدفمند در زمینهٔ فردی، معنوی یا مهارتی.', category: 'رشد فردی', points: 20, coins: 5, time: null, icon: 'bookOpen' },
  { id: 'movement', title: 'تمرین خوشنویسی', description: 'چند دقیقه با حوصله تمرین کن و از مسیر لذت ببر.', category: 'مهارت', points: 20, coins: 5, time: null, icon: 'edit' },
  { id: 'quran-reading', title: 'همراهی با قرآن', description: 'چند آیه بخوان و لحظه‌ای تأمل کن.', category: 'عبادت', points: 20, coins: 4, time: ['06:00', '23:00'], icon: 'gem' },
  { id: 'kindness', title: 'یادداشت شکرگزاری', description: 'سه اتفاق خوب امروز را بنویس و برایشان قدردان باش.', category: 'رشد فردی', points: 15, coins: 3, time: null, icon: 'heart' },
])

const TODAY_FIXTURE = Object.freeze({
  'morning-prayer': 'missed',
  'daily-learning': 'available',
  movement: 'pending',
  'quran-reading': 'missed',
  kindness: 'approved',
})

export function getDemoMissionStatus(iso, missionId, todayISO, hasHistory) {
  if (iso > todayISO) return 'locked'
  if (iso === todayISO) return TODAY_FIXTURE[missionId] || 'available'
  if (!hasHistory) return 'no-data'

  // Stable, clearly labeled demo history so path states remain reproducible.
  const day = Number(iso.slice(-2))
  const missionIndex = DEMO_MISSIONS.findIndex(({ id }) => id === missionId)
  const seed = (day * 7 + missionIndex * 11) % 13
  if (seed < 5) return 'approved'
  if (seed === 5) return 'pending'
  if (seed === 6) return 'rejected'
  if (seed < 9) return 'missed'
  return 'available'
}

export function isMissionInTime(mission, time) {
  return !mission.time || (time >= mission.time[0] && time <= mission.time[1])
}
