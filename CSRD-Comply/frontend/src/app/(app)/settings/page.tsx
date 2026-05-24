'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { Button } from '@/components/ui'
import { Input } from '@/components/ui'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui'
import { Save, User, Building, Palette, Loader2 } from 'lucide-react'
import { companies } from '@/lib/api'

export default function SettingsPage() {
  const [companyName, setCompanyName] = useState('')
  const [vatId, setVatId] = useState('')
  const [country, setCountry] = useState('')
  const [naceCode, setNaceCode] = useState('')
  const [employees, setEmployees] = useState('')
  const [turnover, setTurnover] = useState('')
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    const loadCompany = async () => {
      try {
        const data = await companies.getMe()
        if (data.company_name) setCompanyName(data.company_name)
        if (data.vat_number) setVatId(data.vat_number)
        if (data.country) setCountry(data.country)
        if (data.sector) setNaceCode(data.sector)
        if (data.employee_count) setEmployees(String(data.employee_count))
        if (data.turnover) setTurnover(String(data.turnover))
      } catch (err: any) {
        console.error('[SettingsPage] Load error:', err)
      } finally {
        setLoading(false)
      }
    }
    loadCompany()
  }, [])

  const handleSave = async () => {
    setSaving(true)
    setMessage(null)

    try {
      const payload: Record<string, any> = {}
      if (companyName) payload.company_name = companyName
      if (vatId) payload.vat_number = vatId
      if (country) payload.country = country
      if (naceCode) payload.sector = naceCode
      if (employees) payload.employee_count = Number(employees)
      if (turnover) payload.turnover = Number(turnover)

      await companies.updateMe(payload)
      setMessage({ type: 'success', text: 'Dati salvati con successo!' })
    } catch (err: any) {
      console.error('[SettingsPage] Save error:', err)
      setMessage({ type: 'error', text: err.message || 'Errore durante il salvataggio' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-foreground mb-6">Impostazioni</h2>
      
      <Tabs defaultValue="company" className="space-y-4">
        <TabsList>
          <TabsTrigger value="company">
            <Building className="h-4 w-4 mr-2" />
            Azienda
          </TabsTrigger>
          <TabsTrigger value="profile">
            <User className="h-4 w-4 mr-2" />
            Profilo
          </TabsTrigger>
          <TabsTrigger value="theme">
            <Palette className="h-4 w-4 mr-2" />
            Aspetto
          </TabsTrigger>
        </TabsList>

        <TabsContent value="company">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Dati Aziendali</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Ragione Sociale</label>
                  <Input placeholder="Nome azienda" value={companyName} onChange={(e) => setCompanyName(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Partita IVA</label>
                  <Input placeholder="IT00000000000" value={vatId} onChange={(e) => setVatId(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Paese</label>
                  <Input placeholder="Italia" value={country} onChange={(e) => setCountry(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Codice NACE</label>
                  <Input placeholder="Es. C10, M69" value={naceCode} onChange={(e) => setNaceCode(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Dipendenti</label>
                  <Input type="number" placeholder="50" value={employees} onChange={(e) => setEmployees(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Fatturato (€)</label>
                  <Input type="number" placeholder="1000000" value={turnover} onChange={(e) => setTurnover(e.target.value)} />
                </div>
              </div>

              {message && (
                <div
                  className={`text-sm px-3 py-2 rounded-md ${
                    message.type === 'success'
                      ? 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-400'
                      : 'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-400'
                  }`}
                >
                  {message.text}
                </div>
              )}

              <Button onClick={handleSave} disabled={saving}>
                {saving ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                {saving ? 'Salvataggio...' : 'Salva Modifiche'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="profile">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Profilo Utente</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Email</label>
                  <Input type="email" placeholder="user@azienda.it" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Ruolo</label>
                  <Input value="Admin" disabled />
                </div>
              </div>
              <Button variant="outline">Cambia Password</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="theme">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Tema</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                Il tema chiaro/scuro può essere configurato dalle preferenze di sistema.
              </p>
              <div className="flex gap-2">
                <Button variant="outline">Tema Chiaro</Button>
                <Button variant="outline">Tema Scuro</Button>
                <Button variant="outline">Sistema</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
