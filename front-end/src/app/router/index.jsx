import { createBrowserRouter, Navigate } from 'react-router'
import { RouterProvider } from 'react-router/dom'
import { AuthGuard, EntryRoute, GuestGuard } from '../../features/auth'
import { HomePage } from '../../pages/home'
import { LoginPage } from '../../pages/login'
import { RegisterPage } from '../../pages/register'
import { MissionsPage } from '../../pages/missions'

const router = createBrowserRouter([
  {
    Component: GuestGuard,
    children: [
      { path: '/', Component: EntryRoute },
      { path: '/login', Component: LoginPage },
      { path: '/register', Component: RegisterPage },
      { path: '/home', Component: HomePage },
    ],
  },
  {
    Component: AuthGuard,
    children: [{ path: '/missions', Component: MissionsPage }, { path: '/account', Component: MissionsPage }],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
