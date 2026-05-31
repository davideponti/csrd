'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { Button } from '@/components/ui'
import { Input } from '@/components/ui'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui'
import { Save, User, Building, Palette, Loader2, Eye, EyeOff } from 'lucide-react'
import { companies } from '@/lib/api'

export default function SettingsPage() {
  const [companyName, setCompanyName] = useState('')
  const [vatId, setVatId] = useState('')
  const [country, setCountry] = useState('')
  const [naceCode, setNaceCode] = useState('')
  const [employees, setEmployees] = useState('')
  const [turnover, setTurnover] = useState('')
  const [legalForm, setLegalForm] = useState('')
  const [fiscalYear, setFiscalYear] = useState('')
  const [website, setWebsite] = useState('')
  const [address, setAddress] = useState('')
  const [city, setCity] = useState('')
  const [province, setProvince] = useState('')
  const [zipCode, setZipCode] = useState('')
  const [phone, setPhone] = useState('')
  const [pec, setPec] = useState('')
  const [sdiCode, setSdiCode] = useState('')
  const [certifiedEmail, setCertifiedEmail] = useState(false)
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
        if (data.legal_form) setLegalForm(data.legal_form)
        if (data.fiscal_year) setFiscalYear(String(data.fiscal_year))
        if (data.website) setWebsite(data.website)
        if (data.address) setAddress(data.address)
        if (data.city) setCity(data.city)
        if (data.province) setProvince(data.province)
        if (data.zip_code) setZipCode(data.zip_code)
        if (data.phone) setPhone(data.phone)
        if (data.pec) setPec(data.pec)
        if (data.sdi_code) setSdiCode(data.sdi_code)
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
      if (legalForm) payload.legal_form = legalForm
      if (fiscalYear) payload.fiscal_year = Number(fiscalYear)
      if (website) payload.website = website
      if (address) payload.address = address
      if (city) payload.city = city
      if (province) payload.province = province
      if (zipCode) payload.zip_code = zipCode
      if (phone) payload.phone = phone
      if (pec) payload.pec = pec
      if (sdiCode) payload.sdi_code = sdiCode

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
              <p className="text-sm text-muted-foreground">
                I campi contrassegnati con <span className="text-red-500 font-medium">*</span> sono obbligatori. Quelli con <span className="text-muted-foreground italic">(optional)</span> possono essere lasciati vuoti.
              </p>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Anagrafica */}
              <div>
                <h3 className="text-sm font-semibold text-foreground mb-3 border-b pb-1">Anagrafica</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Ragione Sociale <span className="text-red-500">*</span></label>
                    <Input placeholder="Nome azienda" value={companyName} onChange={(e) => setCompanyName(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Partita IVA <span className="text-red-500">*</span></label>
                    <Input placeholder="IT00000000000" value={vatId} onChange={(e) => setVatId(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Forma Giuridica <span className="text-red-500">*</span></label>
                    <Input placeholder="S.r.l., S.p.A., S.n.c., Ditta Individuale" value={legalForm} onChange={(e) => setLegalForm(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Codice NACE / ATECO <span className="text-red-500">*</span></label>
                    <Input placeholder="Es. C10, M69, 62.09" value={naceCode} onChange={(e) => setNaceCode(e.target.value)} />
                  </div>
                </div>
              </div>

              {/* Sede */}
              <div>
                <h3 className="text-sm font-semibold text-foreground mb-3 border-b pb-1">Sede</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2 md:col-span-2">
                    <label className="text-sm font-medium">Indirizzo <span className="text-muted-foreground italic">(optional)</span></label>
                    <Input placeholder="Via Roma, 123" value={address} onChange={(e) => setAddress(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Città <span className="text-muted-foreground italic">(optional)</span></label>
                    <Input placeholder="Milano" value={city} onChange={(e) => setCity(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Provincia</label>
                    <Input placeholder="MI" value={province} onChange={(e) => setProvince(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">CAP</label>
                    <Input placeholder="20100" value={zipCode} onChange={(e) => setZipCode(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Paese <span className="text-red-500">*</span></label>
                    <Input placeholder="Italia" value={country} onChange={(e) => setCountry(e.target.value)} />
                  </div>
                </div>
              </div>

              {/* Dimensioni */}
              <div>
                <h3 className="text-sm font-semibold text-foreground mb-3 border-b pb-1">Dimensioni Azienda</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Dipendenti <span className="text-red-500">*</span></label>
                    <Input type="number" placeholder="50" value={employees} onChange={(e) => setEmployees(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Fatturato (€) <span className="text-red-500">*</span></label>
                    <Input type="number" placeholder="1000000" value={turnover} onChange={(e) => setTurnover(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Anno Fiscale di Riferimento <span className="text-red-500">*</span></label>
                    <Input type="number" placeholder="2025" value={fiscalYear} onChange={(e) => setFiscalYear(e.target.value)} />
                  </div>
                </div>
              </div>

              {/* Contatti */}
              <div>
                <h3 className="text-sm font-semibold text-foreground mb-3 border-b pb-1">Contatti e Fatturazione</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Sito Web <span className="text-muted-foreground italic">(optional)</span></label>
                    <Input placeholder="https://www.azienda.it" value={website} onChange={(e) => setWebsite(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Telefono <span className="text-muted-foreground italic">(optional)</span></label>
                    <Input placeholder="+39 02 12345678" value={phone} onChange={(e) => setPhone(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">PEC <span className="text-muted-foreground italic">(optional)</span></label>
                    <Input placeholder="azienda@pec.it" value={pec} onChange={(e) => setPec(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Codice SDI <span className="text-muted-foreground italic">(optional)</span></label>
                    <Input placeholder="ABC1234" value={sdiCode} onChange={(e) => setSdiCode(e.target.value)} />
                  </div>
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
