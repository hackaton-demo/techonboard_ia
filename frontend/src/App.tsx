import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { LayoutDashboard, Bot, Plus, Zap } from 'lucide-react'
import clsx from 'clsx'
import { ManagerDashboard } from '@/pages/ManagerDashboard'
import { AgentCatalog } from '@/pages/AgentCatalog'
import { AgentBuilder } from '@/pages/AgentBuilder'
import { Interview } from '@/pages/Interview'
import { OnboardingPlan } from '@/pages/OnboardingPlan'

interface NavItem {
  to: string
  label: string
  icon: React.ReactNode
  exact?: boolean
}

const NAV_ITEMS: NavItem[] = [
  {
    to: '/',
    label: 'Dashboard',
    icon: <LayoutDashboard size={18} />,
    exact: true,
  },
  {
    to: '/agents',
    label: 'Agents',
    icon: <Bot size={18} />,
  },
  {
    to: '/agents/new',
    label: 'Create Agent',
    icon: <Plus size={18} />,
  },
]

function Sidebar() {
  return (
    <aside className="w-56 flex-shrink-0 bg-gray-950 border-r border-gray-800 flex flex-col">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-gray-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
            <Zap size={16} className="text-white" />
          </div>
          <span className="text-sm font-bold text-white tracking-tight">TechOnboard</span>
        </div>
        <p className="text-xs text-gray-600 mt-1 pl-[42px]">AI Onboarding Platform</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        <p className="text-xs text-gray-600 font-medium uppercase tracking-widest px-2 mb-2">
          Navigation
        </p>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.exact}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150',
                isActive
                  ? 'bg-indigo-600/15 text-indigo-300 font-medium'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800/60'
              )
            }
          >
            {item.icon}
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-gray-800">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs text-gray-600">TechEx 2026</span>
        </div>
      </div>
    </aside>
  )
}

function Header() {
  const location = useLocation()

  const getTitle = () => {
    if (location.pathname === '/') return 'Dashboard'
    if (location.pathname === '/agents') return 'Agent Catalog'
    if (location.pathname === '/agents/new') return 'Create Agent'
    if (location.pathname.startsWith('/interview/')) return 'Onboarding Interview'
    if (location.pathname.startsWith('/plan/')) return 'Onboarding Plan'
    return 'TechOnboard'
  }

  return (
    <header className="h-16 border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm flex items-center px-6 flex-shrink-0">
      <h1 className="text-base font-semibold text-white">{getTitle()}</h1>
      <div className="ml-auto flex items-center gap-3">
        <span className="text-xs text-gray-600 font-mono">
          hackathon-ai-onboarding
        </span>
        <div className="w-7 h-7 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-xs text-indigo-400 font-medium">
          M
        </div>
      </div>
    </header>
  )
}

function isFullScreenRoute(pathname: string): boolean {
  return pathname.startsWith('/interview/')
}

export default function App() {
  const location = useLocation()
  const fullScreen = isFullScreenRoute(location.pathname)

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 overflow-hidden">
      {!fullScreen && <Sidebar />}

      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Header />

        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<ManagerDashboard />} />
            <Route path="/agents" element={<AgentCatalog />} />
            <Route path="/agents/new" element={<AgentBuilder />} />
            <Route path="/interview/:sessionId" element={<Interview />} />
            <Route path="/plan/:sessionId" element={<OnboardingPlan />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
