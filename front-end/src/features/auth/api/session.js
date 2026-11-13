import { apiRequest } from '../../../shared/api'
import { authService } from '../../../entities/auth'

export const sessionQueryKey = ['session', 'me']

export const getSession = ({ signal } = {}) => apiRequest('me/', { signal })

export const login = (credentials) => authService.login(credentials)
export const logout = () => authService.logout()
