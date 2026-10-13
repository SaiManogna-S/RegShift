import { NavLink, Outlet } from 'react-router-dom'
import { useState } from 'react'
import {
  LayoutDashboard, FileText, Zap, Ticket, ScrollText,
  Shield, Menu, X
} from 'lucide-react'
import clsx from 'clsx'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { loadDemo } from '../api/client'
import { useQueryClient } from '@tanstack/react-query'

const navItems = [
  { path: '/overview', label: 'Overview', icon: LayoutDashboard },
  { path: '/documents', label: 'Regulatory Documents', icon: FileText },
  { path: '/impact', label: 'Impact Analysis', icon: Zap },
  { path: '/tickets', label: 'Change Tickets', icon: Ticket },
  { path: '/audit', label: 'Audit Trail', icon: ScrollText },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [demoLoading, setDemoLoading] = useState(false)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const handleLoadDemo = async () => {
    setDemoLoading(true)
    try {
      const result = await loadDemo()
      queryClient.invalidateQueries()
      toast.success(`Demo loaded: ${result.requirements_count} requirements, ${result.impact_results_count} impacts`)
      navigate('/documents')
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to load demo')
    } finally {
      setDemoLoading(false)
    }
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed lg:static inset-y-0 left-0 z-30 w-60 flex-shrink-0',
          'bg-navy-950 flex flex-col transition-transform duration-300',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        )}
        style={{ boxShadow: '2px 0 20px rgba(0,0,0,0.3)' }}
      >
        {/* Logo */}
        <div className="px-5 pt-6 pb-5 border-b border-white/8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center flex-shrink-0">
              <Shield size={16} className="text-white" />
            </div>
            <div>
              <span className="text-white font-bold text-lg tracking-tight">RegShift</span>
              <div className="text-white/40 text-xs">Regulatory Intelligence</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {navItems.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
                  isActive
                    ? 'bg-white/12 text-white'
                    : 'text-white/55 hover:text-white hover:bg-white/8'
                )
              }
            >
              <Icon size={16} className="flex-shrink-0" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Demo action */}
        <div className="px-3 py-4 border-t border-white/8">
          <button
            id="load-demo-btn"
            onClick={handleLoadDemo}
            disabled={demoLoading}
            className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium
                       text-violet-300 hover:text-white hover:bg-violet-500/20 transition-all duration-150
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Zap size={15} className="flex-shrink-0" />
            {demoLoading ? 'Loading…' : 'Load Demo Scenario'}
          </button>
          <div className="mt-3 px-3">
            <div className="text-white/25 text-xs leading-relaxed">
              Synthetic demo data only.
              Not real regulations.
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar */}
        <header className="h-14 flex-shrink-0 bg-white border-b border-slate-200 flex items-center px-4 lg:px-6 gap-4">
          <button
            className="lg:hidden p-1.5 text-slate-600 hover:text-slate-900 rounded-lg hover:bg-slate-100"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>

          <div className="flex-1" />

          <a
            href="/documents"
            className="btn-primary text-xs px-4 py-2"
            id="cta-analyze"
            onClick={(e) => { e.preventDefault(); navigate('/documents') }}
          >
            <Zap size={14} />
            Analyze Regulatory Update
          </a>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-4 lg:px-6 py-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
