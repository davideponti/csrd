'use client'

import { LayoutDashboard, ClipboardCheck, Leaf, FileText, Settings, Bell, User } from 'lucide-react'
import Link from 'next/link'

const navItems = [
  { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/assessment', icon: ClipboardCheck, label: 'Assessment' },
  { href: '/emissions', icon: Leaf, label: 'Emissioni' },
  { href: '/reports', icon: FileText, label: 'Reports' },
  { href: '/settings', icon: Settings, label: 'Settings' },
]

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-border p-4 flex flex-col">
        <Link href="/" className="text-xl font-bold text-primary mb-8 px-3">
          CSRD Comply
        </Link>
        <nav className="flex flex-col gap-1 flex-1">
          {navItems.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors text-sm font-medium"
            >
              <item.icon className="h-4 w-4" />
              <span>{item.label}</span>
            </a>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto bg-background">
        <header className="bg-white border-b border-border px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-foreground">
            CSRD Comply
          </h1>
          <div className="flex items-center gap-4">
            <button className="p-2 rounded-full hover:bg-accent text-muted-foreground">
              <Bell className="h-5 w-5" />
            </button>
            <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-medium">
              <User className="h-4 w-4" />
            </div>
          </div>
        </header>
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  )
}
