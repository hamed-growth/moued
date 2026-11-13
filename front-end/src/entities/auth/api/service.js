import { apiRequest } from '../../../shared/api'
import { authEndpoints } from './endpoints'

export const authService = {
  getCsrf: () => apiRequest(authEndpoints.csrf),
  async login(credentials) {
    await this.getCsrf()
    return apiRequest(authEndpoints.login, { method: 'POST', body: credentials })
  },
  async register(userData) {
    await this.getCsrf()
    return apiRequest(authEndpoints.register, { method: 'POST', body: userData })
  },
  async logout() {
    await this.getCsrf()
    return apiRequest(authEndpoints.logout, { method: 'POST' })
  },
}
