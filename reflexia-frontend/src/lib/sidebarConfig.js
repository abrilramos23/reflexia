import { FaUser, FaUsers, FaBook, FaSignOutAlt, FaHome, FaBriefcase, FaBuilding, FaQuestionCircle } from 'react-icons/fa'

export const sidebarConfig = [
  {
    label: 'Dashboard',
    path: '/dashboard',
    roles: ['therapist', 'patient', 'platform_admin'],
    icon: FaHome,
    section: 'General',
  },
  {
    label: 'Clínica',
    path: '/clinic',
    roles: ['therapist'], 
    icon: FaBuilding,
    section: 'Organització',
  },
  {
    label: 'Organitzacions',
    path: '/admin/organisations',
    roles: ['platform_admin'],
    icon: FaBriefcase,
    section: 'Administració',
  },
  {
    label: 'Admins de Clínica',
    path: '/admin/clinic-admins',
    roles: ['platform_admin'],
    icon: FaBuilding,
    section: 'Administració',
  },
  {
    label: 'Terapeutes',
    path: '/admin/therapists',
    roles: ['platform_admin', 'therapist'], // We will filter visibility for therapists in the SideBar component based on isAdmin flag
    icon: FaUsers,
    section: 'Organització',
  },
  {
    label: 'Entrades',
    path: '/entries',
    roles: ['patient'],
    icon: FaBook,
    section: 'General',
  },
  {
    label: 'Pacients',
    path: '/patients',
    roles: ['therapist'],
    icon: FaUsers,
    section: 'Compte',
  },
  {
    label: 'Preguntes',
    path: '/questions',
    roles: ['therapist'],
    icon: FaQuestionCircle,
    section: 'Compte',
  },
  {
    label: 'Suport',
    path: '/support',
    roles: ['therapist'],
    icon: FaUsers,
    section: 'Compte',
  },
  {
    label: 'Contactes',
    path: '/contacts',
    roles: ['patient'],
    icon: FaUsers,
    section: 'Compte',
  },
  {
    label: 'Perfil',
    path: '/profile',
    roles: ['therapist', 'patient', 'platform_admin'],
    icon: FaUser,
    section: 'Compte',
  },
]
