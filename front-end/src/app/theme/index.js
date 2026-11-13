import { createTheme } from '@mui/material/styles'
import { faIR } from '@mui/material/locale'

export const theme = createTheme(
  {
    direction: 'rtl',
    palette: {
      primary: { main: '#206f59' },
      background: { default: '#f7f8f4', paper: '#ffffff' },
      text: { primary: '#182421', secondary: '#53635e' },
    },
    typography: { fontFamily: 'Vazir, Tahoma, sans-serif' },
  },
  faIR,
)
