import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CacheProvider } from '@emotion/react'
import createCache from '@emotion/cache'
import { CssBaseline, ThemeProvider } from '@mui/material'
import { prefixer } from 'stylis'
import rtlPlugin from '@mui/stylis-plugin-rtl'
import { AuthProvider } from '../../features/auth'
import { theme } from '../theme'

const queryClient = new QueryClient()
const rtlCache = createCache({ key: 'muirtl', stylisPlugins: [prefixer, rtlPlugin] })

export function AppProviders({ children }) {
  return (
    <CacheProvider value={rtlCache}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <QueryClientProvider client={queryClient}>
          <AuthProvider>{children}</AuthProvider>
        </QueryClientProvider>
      </ThemeProvider>
    </CacheProvider>
  )
}
