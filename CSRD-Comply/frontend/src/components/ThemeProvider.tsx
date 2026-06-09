"use client"

import { createContext, useContext, useEffect, useState, useRef } from "react"

type Theme = 'light' | 'dark' | 'system'

const ThemeContext = createContext<{
  theme: Theme
  setTheme: (t: Theme) => void
  resolvedTheme: 'light' | 'dark'
}>({
  theme: 'system',
  setTheme: () => {},
  resolvedTheme: 'light',
})

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('system')
  const [resolved, setResolved] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    const saved = localStorage.getItem('csrd-theme') as Theme | null
    if (saved) setThemeState(saved)
  }, [])

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const updateResolved = () => {
      let r: 'light' | 'dark'
      if (theme === 'system') {
        r = mediaQuery.matches ? 'dark' : 'light'
      } else {
        r = theme
      }
      setResolved(r)
      document.documentElement.classList.toggle('dark', r === 'dark')
    }
    updateResolved()
    mediaQuery.addEventListener('change', updateResolved)
    return () => mediaQuery.removeEventListener('change', updateResolved)
  }, [theme])

  const setTheme = (t: Theme) => {
    setThemeState(t)
    localStorage.setItem('csrd-theme', t)
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme: resolved }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  return useContext(ThemeContext)
}

export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const options: { value: Theme; label: string; icon: string }[] = [
    { value: 'light', label: 'Chiaro', icon: '☀️' },
    { value: 'dark', label: 'Scuro', icon: '🌙' },
    { value: 'system', label: 'Sistema', icon: '💻' },
  ]

  const currentIcon = options.find(o => o.value === theme)?.icon || '💻'

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="p-2 rounded-full hover:bg-accent text-muted-foreground"
        title="Cambia tema"
      >
        <span className="text-base">{currentIcon}</span>
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-40 bg-background border border-border rounded-lg shadow-lg z-50">
          {options.map(opt => (
            <button
              key={opt.value}
              onClick={() => { setTheme(opt.value); setOpen(false) }}
              className={`w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent transition-colors ${
                theme === opt.value ? 'text-primary font-medium' : 'text-muted-foreground'
              }`}
            >
              <span>{opt.icon}</span>
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
