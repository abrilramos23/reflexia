import { FaUser, FaUsers, FaBook, FaSignOutAlt, FaHome } from 'react-icons/fa'

export const sidebarConfig = [
  {
    label: 'Dashboard',
    path: '/dashboard',
    roles: ['therapist', 'patient', 'admin'],
    icon: FaHome,
  },
  {
    label: 'Pacients',
    path: '/patients',
    roles: ['therapist'],
    icon: FaUsers,
  },
  {
    label: 'Entrades',
    path: '/entries',
    roles: ['patient'],
    icon: FaBook,
  },
  {
    label: 'Perfil',
    path: '/profile',
    roles: ['therapist', 'patient', 'admin'],
    icon: FaUser,
  },
]