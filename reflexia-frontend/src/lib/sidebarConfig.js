import { FaUser, FaUsers, FaBook, FaHome, FaBuilding, FaQuestionCircle, FaBell } from 'react-icons/fa'

export const sidebarConfig = [
  {
    label: 'Dashboard',
    path: '/dashboard',
    roles: ['therapist', 'patient'],
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
    label: 'Terapeutes',
    path: '/admin/therapists',
    roles: ['therapist'],
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
    label: 'Alertes',
    path: '/alerts',
    roles: ['therapist'],
    icon: FaBell,
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
    roles: ['therapist', 'patient'],
    icon: FaUser,
    section: 'Compte',
  },
]
