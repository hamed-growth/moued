import { useQuery, useQueryClient } from '@tanstack/react-query'
import { AuthContext } from './auth-context'
import { getSession, login, logout, sessionQueryKey } from '../api/session'

export function AuthProvider({ children }) {
  const queryClient = useQueryClient()
  const session = useQuery({
    queryKey: sessionQueryKey,
    queryFn: ({ signal }) => getSession({ signal }),
    retry: false,
    refetchOnWindowFocus: true,
  })

  async function signIn(credentials) {
    const result = await login(credentials)
    queryClient.setQueryData(sessionQueryKey, result.user)
    return result.user
  }

  async function signOut() {
    await logout()
    queryClient.clear()
    queryClient.setQueryData(sessionQueryKey, null)
  }

  const unauthenticated = session.error?.status === 401 || session.error?.status === 403
  const value = {
    user: session.data ?? null,
    status: session.isPending ? 'loading' : unauthenticated ? 'guest' : session.isError ? 'error' : session.data ? 'authenticated' : 'guest',
    error: session.error,
    refresh: session.refetch,
    signIn,
    signOut,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
