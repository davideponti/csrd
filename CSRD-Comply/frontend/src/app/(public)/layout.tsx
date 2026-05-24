'use client'

import Link from 'next/link'
import { Leaf, Menu, X } from 'lucide-react'
import { Button } from '@/components/ui'
import { useState } from 'react'
import { useLanguage } from '@/i18n/LanguageContext'
import { LanguageSwitcher } from '@/components/LanguageSwitcher'

export default function PublicLayout({ children }: { children: React.ReactNode }) {
  const { t } = useLanguage()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navLinks = [
    { href: '/how-it-works', label: t('nav.how-it-works') },
    { href: '/pricing', label: t('nav.pricing') },
    { href: '/faq', label: t('nav.faq') },
  ]

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header / Navigation */}
      <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2">
              <Leaf className="h-6 w-6 text-emerald-600" />
              <span className="text-lg font-bold text-gray-900">CSRD Comply</span>
            </Link>

            {/* Desktop nav */}
            <nav className="hidden md:flex items-center gap-8">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-sm font-medium text-gray-600 hover:text-emerald-600 transition-colors"
                >
                  {link.label}
                </Link>
              ))}
            </nav>

            {/* Desktop actions */}
            <div className="hidden md:flex items-center gap-2">
              <LanguageSwitcher />
              <Link href="/auth/login">
                <Button variant="ghost" size="sm">{t('nav.login')}</Button>
              </Link>
              <Link href="/auth/register">
                <Button size="sm">{t('nav.register')}</Button>
              </Link>
            </div>

            {/* Mobile hamburger */}
            <button
              className="md:hidden p-2 rounded-lg hover:bg-gray-100"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-100 bg-white">
            <div className="px-4 py-4 space-y-3">
              <div className="flex justify-end">
                <LanguageSwitcher />
              </div>
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="block text-sm font-medium text-gray-600 hover:text-emerald-600 py-2"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {link.label}
                </Link>
              ))}
              <div className="pt-3 border-t border-gray-100 flex flex-col gap-2">
                <Link href="/auth/login" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="outline" className="w-full">{t('nav.login')}</Button>
                </Link>
                <Link href="/auth/register" onClick={() => setMobileMenuOpen(false)}>
                  <Button className="w-full">{t('nav.register')}</Button>
                </Link>
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Main content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="md:col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <Leaf className="h-6 w-6 text-emerald-400" />
                <span className="text-lg font-bold text-white">CSRD Comply</span>
              </div>
              <p className="text-sm text-gray-400 max-w-md">
                {t('features.subtitle')}
              </p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white mb-4">{t('footer.product')}</h3>
              <ul className="space-y-2">
                <li><Link href="/how-it-works" className="text-sm hover:text-emerald-400 transition-colors">{t('nav.how-it-works')}</Link></li>
                <li><Link href="/pricing" className="text-sm hover:text-emerald-400 transition-colors">{t('nav.pricing')}</Link></li>
                <li><Link href="/faq" className="text-sm hover:text-emerald-400 transition-colors">{t('nav.faq')}</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white mb-4">{t('footer.legal')}</h3>
              <ul className="space-y-2 flex flex-col items-end">
                <li><span className="text-sm text-gray-400">{t('footer.privacy')}</span></li>
                <li><span className="text-sm text-gray-400">{t('footer.terms')}</span></li>
              </ul>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-gray-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-gray-500">
            <div className="flex items-center gap-2">
              <LanguageSwitcher />
            </div>
            <div>
              &copy; {new Date().getFullYear()} CSRD Comply. {t('footer.rights')}
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
