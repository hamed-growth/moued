import { AdapterDateFnsJalali } from '@mui/x-date-pickers/AdapterDateFnsJalali'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { faIR } from '@mui/x-date-pickers/locales'

const localeText = faIR.components.MuiLocalizationProvider.defaultProps.localeText
const dateKeyFormatter = new Intl.DateTimeFormat('en-CA', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
})

export function MissionMonthPicker({ monthISO, todayISO, onSelect }) {
  return (
    <LocalizationProvider dateAdapter={AdapterDateFnsJalali} localeText={localeText}>
      <DatePicker
        label="انتخاب ماه"
        views={['year', 'month']}
        openTo="month"
        format="MMMM yyyy"
        value={new Date(`${monthISO}T12:00:00`)}
        maxDate={new Date(`${todayISO}T12:00:00`)}
        onAccept={(date, { validationError }) => {
          if (!date || validationError) return
          const parts = Object.fromEntries(dateKeyFormatter.formatToParts(date).map(({ type, value }) => [type, value]))
          onSelect(`${parts.year}-${parts.month}-${parts.day}`)
        }}
        slotProps={{
          textField: {
            dir: 'rtl',
            size: 'small',
            sx: { width: 'min(100%, 200px)', minWidth: 0, bgcolor: 'var(--mission-surface)' },
          },
          popper: { dir: 'rtl' },
          dialog: { dir: 'rtl', disableScrollLock: true },
        }}
      />
    </LocalizationProvider>
  )
}
