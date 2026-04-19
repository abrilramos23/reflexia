import { FaUser, FaUsers, FaBook, FaSignOutAlt, FaHome, FaBriefcase, FaBuilding } from 'react-icons/fa'

export const sidebarConfig = [
  {
    label: 'Dashboard',
    path: '/dashboard',
    roles: ['therapist', 'patient', 'platform_admin', 'clinic_admin'],
    icon: FaHome,
  },
  {
    label: 'Pacients',
    path: '/patients',
    roles: ['therapist'],
    icon: FaUsers,
  },
  {
    label: 'Clínica',
    path: '/clinic',
    roles: [], // Removed clinic_admin from here
    icon: FaBuilding,
  },
  {
    label: 'Organitzacions',
    path: '/admin/organisations',
    roles: ['platform_admin'],
    icon: FaBriefcase,
  },
  {
    label: 'Admins de Clínica',
    path: '/admin/clinic-admins',
    roles: ['platform_admin'],
    icon: FaBuilding,
  },
  {
    label: 'Terapeutes',
    path: '/admin/therapists',
    roles: ['platform_admin', 'clinic_admin'],
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
    roles: ['therapist', 'patient', 'platform_admin', 'clinic_admin'],
    icon: FaUser,
  },
]