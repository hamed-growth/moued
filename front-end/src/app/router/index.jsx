import { createBrowserRouter, Navigate } from 'react-router'
import { RouterProvider } from 'react-router/dom'
import { AuthGuard, GuestGuard } from '../../features/auth'
import { HomePage } from '../../pages/home'
import { LoginPage } from '../../pages/login'
import { AccountPage } from '../../pages/account'

const router = createBrowserRouter([
  {
    Component: GuestGuard,
    children: [
      { path: '/', Component: LoginPage },
      { path: '/login', element: <Navigate to="/" replace /> },
      { path: '/home', Component: HomePage },
    ],
  },
  {
    Component: AuthGuard,
    children: [{ path: '/account', Component: AccountPage }],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
