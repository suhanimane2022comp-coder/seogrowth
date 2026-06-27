'use client'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { LayoutDashboard, PlusCircle, FileText, TrendingUp, LogOut, User, Sparkles, Share2, BarChart3, Building2, Bell } from 'lucide-react'
import clsx from 'clsx'
import { getNotifications, getUnreadCount, markAllNotificationsRead } from '@/lib/api'

const nav = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/analyze', label: 'New Analysis', icon: PlusCircle },
  { href: '/reports', label: 'Reports', icon: FileText },
  { href: '/prompts', label: 'Prompt Agent', icon: Sparkles },
  { href: '/social', label: 'Social Media', icon: Share2 },
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/profile/setup', label: 'Business Profile', icon: Building2 },
]

export default function Sidebar() {
  const pathname = usePathname()
  const { user, logout } = useAuth()
  const [unread, setUnread] = useState(0)
  const [notifs, setNotifs] = useState<any[]>([])
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const load = () => getUnreadCount().then((r) => setUnread(r.data.count)).catch(() => {})
    load()
    const timer = setInterval(load, 15000)
    return () => clearInterval(timer)
  }, [])

  const openPanel = async () => {
    setOpen((o) => !o)
    if (!open) {
      try {
        const { data } = await getNotifications()
        setNotifs(data)
      } catch {}
    }
  }

  const clearAll = async () => {
    await markAllNotificationsRead()
    setUnread(0)
  }

  return (
    <aside className="w-64 min-h-screen bg-brand-900 text-white flex flex-col">
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-indigo-300" />
            <span className="font-bold text-lg">SEO Growth AI</span>
          </div>
          <div className="relative">
            <button onClick={openPanel} className="relative p-1.5 rounded-lg hover:bg-white/10">
              <Bell className="w-5 h-5 text-indigo-200" />
              {unread > 0 && <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center">{unread}</span>}
            </button>
            {open && (
              <div className="absolute right-0 mt-2 w-72 bg-white text-slate-700 rounded-xl shadow-xl z-50 max-h-80 overflow-y-auto">
                <div className="flex items-center justify-between p-3 border-b border-slate-100">
                  <span className="font-semibold text-sm">Notifications</span>
                  <button onClick={clearAll} className="text-xs text-brand-600 hover:underline">Mark all read</button>
                </div>
                {notifs.length === 0 ? (
                  <p className="text-xs text-slate-400 p-4">No notifications yet.</p>
                ) : notifs.map((n) => (
                  <div key={n.id} className="p-3 border-b border-slate-50 text-xs">
                    <p className={clsx(!n.is_read && 'font-semibold')}>{n.message}</p>
                    <p className="text-slate-400 mt-1">{new Date(n.created_at).toLocaleString()}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={clsx(
              'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition',
              pathname === href || pathname.startsWith(href + '/')
                ? 'bg-white/15 text-white'
                : 'text-indigo-200 hover:bg-white/10 hover:text-white'
            )}
          >
            <Icon className="w-5 h-5" />
            {label}
          </Link>
        ))}
      </nav>

      <div className="p-4 border-t border-white/10">
        <div className="flex items-center gap-3 px-4 py-2 mb-2">
          <div className="bg-indigo-400 rounded-full p-1.5"><User className="w-4 h-4 text-white" /></div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.name}</p>
            <p className="text-xs text-indigo-300 truncate">{user?.email}</p>
          </div>
        </div>
        <button onClick={logout} className="flex items-center gap-2 px-4 py-2 text-indigo-300 hover:text-white text-sm transition w-full">
          <LogOut className="w-4 h-4" /> Sign out
        </button>
      </div>
    </aside>
  )
}
