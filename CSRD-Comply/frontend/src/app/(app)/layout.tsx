'use client'

import { useEffect } from 'react'
import { LayoutDashboard, ClipboardCheck, Leaf, FileText, Settings, Bell, User, LogOut, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { OnboardingWizard, useOnboarding } from '@/components/OnboardingWizard'
import { ThemeProvider, ThemeSwitcher } from '@/components/ThemeProvider'

const navItems = [
  { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/assessment', icon: ClipboardCheck, label: 'Assessment' },
  { href: '/emissions', icon: Leaf, label: 'Emissioni' },
  { href: '/reports', icon: FileText, label: 'Reports' },
  { href: '/settings', icon: Settings, label: 'Settings' },
]

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { logout, isAuthenticated, loading } = useAuth()
  const { showOnboarding, setShowOnboarding } = useOnboarding()

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace('/auth/login')
    }
  }, [loading, isAuthenticated, router])

  const handleLogout = async () => {
    await logout()
    router.push('/auth/login')
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <ThemeProvider>
    <ErrorBoundary>
    <div className="flex h-screen">
      {/* Onboarding Wizard — shown for new users */}
      {showOnboarding && (
        <OnboardingWizard
          isNewUser={true}
          onComplete={() => setShowOnboarding(false)}
        />
      )}

      {/* Sidebar */}
      <aside className="w-64 bg-background border-r border-border p-4 flex flex-col">

        <Link href="/" className="text-xl font-bold text-primary mb-8 px-3">
          CSRD Comply
        </Link>
        <nav className="flex flex-col gap-1 flex-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors text-sm font-medium"
            >
              <item.icon className="h-4 w-4" />
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        {/* Logout button at bottom of sidebar */}
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors text-sm font-medium mt-auto"
        >
          <LogOut className="h-4 w-4" />
          <span>Logout</span>
        </button>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto bg-background">
        <header className="bg-background border-b border-border px-6 py-4 flex items-center justify-between">

          <h1 className="text-xl font-semibold text-foreground">
            CSRD Comply
          </h1>
          <div className="flex items-center gap-4">
            <ThemeSwitcher />
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

        {/* Footer */}
        <footer className="bg-background border-t border-border px-6 py-4">

          <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-muted-foreground">
            <div>
              &copy; {new Date().getFullYear()} CSRD Comply. Tutti i diritti riservati.
            </div>
            <div className="flex items-center gap-4">
              <Link href="/privacy" className="hover:text-emerald-600 transition-colors">
                Privacy Policy
              </Link>
              <Link href="/terms" className="hover:text-emerald-600 transition-colors">
                Termini di Servizio
              </Link>
            </div>
          </div>
        </footer>
      </main>
    </div>
    </ErrorBoundary>
    </ThemeProvider>
  )
}
