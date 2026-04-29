import { FaUser, FaUsers, FaBook, FaSignOutAlt, FaHome, FaBriefcase, FaBuilding } from 'react-icons/fa'

export const sidebarConfig = [
  {
    label: 'Dashboard',
    path: '/dashboard',
    roles: ['therapist', 'patient', 'platform_admin'],
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
    roles: [], 
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
    roles: ['platform_admin', 'therapist'], // We will filter visibility for therapists in the SideBar component based on isAdmin flag
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
    roles: ['therapist', 'patient', 'platform_admin'],
    icon: FaUser,
  },
]