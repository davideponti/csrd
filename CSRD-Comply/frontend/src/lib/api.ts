// ── API Client ──────────────────────────────────────────────────
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1'

function getAuthHeader(): Record<string, string> {
  if (typeof window === 'undefined') return {}
  const token = localStorage.getItem('access_token')
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
    ...options.headers,
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || 'API Error')
  }

  return res.json()
}

// ── Generic API Client ──────────────────────────────────────────

export const api = {
  get: <T = any>(endpoint: string) => {
    return fetch(`${API_BASE}${endpoint}`, {
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
    }).then(async (res) => {
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || 'API Error');
      }
      return res.json() as Promise<T>;
    });
  },

  post: <T = any>(endpoint: string, body?: any) => {
    return fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: body ? JSON.stringify(body) : undefined,
    }).then(async (res) => {
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || 'API Error');
      }
      return res.json() as Promise<T>;
    });
  },

  put: <T = any>(endpoint: string, body?: any) => {
    return fetch(`${API_BASE}${endpoint}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: body ? JSON.stringify(body) : undefined,
    }).then(async (res) => {
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || 'API Error');
      }
      return res.json() as Promise<T>;
    });
  },

  patch: <T = any>(endpoint: string, body?: any) => {
    return fetch(`${API_BASE}${endpoint}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: body ? JSON.stringify(body) : undefined,
    }).then(async (res) => {
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || 'API Error');
      }
      return res.json() as Promise<T>;
    });
  },

  del: <T = any>(endpoint: string) => {
    return fetch(`${API_BASE}${endpoint}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
    }).then(async (res) => {
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || 'API Error');
      }
      return res.json() as Promise<T>;
    });
  },

  get_text: async (endpoint: string) => {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) throw new Error(`Failed to fetch text: ${res.statusText}`);
    return res.text();
  },

  get_blob: async (endpoint: string) => {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) throw new Error(`Failed to fetch blob: ${res.statusText}`);
    return res.blob();
  },
};

// ── Auth ───────────────────────────────────────────────────────
export const auth = {
  register: async (data: { email: string; password: string; company_name: string }) => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(error.detail || 'API Error')
    }
    const json = await res.json()
    if (json.access_token) localStorage.setItem('access_token', json.access_token)
    return json
  },

  login: async (data: { email: string; password: string }) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(error.detail || 'API Error')
    }
    const json = await res.json()
    if (json.access_token) localStorage.setItem('access_token', json.access_token)
    return json
  },
}

// ── Companies ──────────────────────────────────────────────────
export const companies = {
  getMe: () => request<any>('/companies/me'),
  updateMe: (data: any) =>
    request<any>('/companies/me', {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
}

// ── Assessment (Steps 8-11) ────────────────────────────────────
export const assessments = {
  list: () => request<any[]>('/assessment/'),
  create: (data?: { methodology_version?: string }) =>
    request<any>('/assessment/', {
      method: 'POST',
      body: JSON.stringify(data || {}),
    }),
  get: (id: string) => request<any>(`/assessment/${id}`),
  getContext: (id: string) => request<any>(`/assessment/${id}/context`),
  updateContext: (id: string, data: any) =>
    request<any>(`/assessment/${id}/context`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  getQuestionnaire: (id: string) => request<any>(`/assessment/${id}/questionnaire`),
  getIros: (id: string) => request<any>(`/assessment/${id}/iros`),
  generateIros: (id: string, data?: { use_ai?: boolean; context_override?: any }) =>
    request<any>(`/assessment/${id}/iros/generate`, {
      method: 'POST',
      body: JSON.stringify(data || { use_ai: false }),
    }),
  listScores: (id: string) => request<any>(`/assessment/${id}/scores`),
  updateScore: (id: string, scoreId: string, data: any) =>
    request<any>(`/assessment/${id}/scores/${scoreId}`, {
      method: 'PATCH',
      body: JSON.stringify({ score_id: scoreId, ...data }),
    }),
  getAiFollowup: (id: string, scoreId: string) =>
    request<any>(`/assessment/${id}/scores/${scoreId}/ai-followup`, { method: 'POST' }),
  generateScores: (id: string) =>
    request<any>(`/assessment/${id}/scores/generate`, { method: 'POST' }),
  calculateScores: (id: string) =>
    request<any>(`/assessment/${id}/scores/calculate`, { method: 'POST' }),
  saveQuestionnaireResponses: (id: string, responses: Record<string, string>) =>
    request<any>(`/assessment/${id}/context`, {
      method: 'PUT',
      body: JSON.stringify({ questionnaire_responses: responses }),
    }),
  getMatrix: (id: string) => request<any>(`/assessment/${id}/matrix`),
  getReport: (id: string) => request<any>(`/assessment/${id}/report`),
  getGapAnalysis: (id: string) => request<any>(`/assessment/${id}/gap-analysis`),
}

// ── Emissions ─────────────────────────────────────────────────
export const emissions = {
  list: (params?: { scope?: string; year?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.scope) searchParams.set('scope', params.scope)
    if (params?.year) searchParams.set('year', String(params.year))
    const query = searchParams.toString()
    return request<any[]>(`/emissions/${query ? `?${query}` : ''}`)
  },
  create: (data: any) => request<any>('/emissions/', { method: 'POST', body: JSON.stringify(data) }),
  getFactors: () => request<any>('/emissions/factors'),
  calculateScope1: (data: any) => request<any>('/emissions/calculate/scope1', { method: 'POST', body: JSON.stringify(data) }),
  calculateScope1Process: (data: any) => request<any>('/emissions/calculate/scope1/process', { method: 'POST', body: JSON.stringify(data) }),
  calculateScope2: (data: any) => request<any>('/emissions/calculate/scope2', { method: 'POST', body: JSON.stringify(data) }),
  calculateScope3: (data: any) => request<any>('/emissions/calculate/scope3', { method: 'POST', body: JSON.stringify(data) }),
  saveCalculated: (data: any) => request<any>('/emissions/save-calculated', { method: 'POST', body: JSON.stringify(data) }),
  validate: (data: any) => request<any>('/emissions/validate', { method: 'POST', body: JSON.stringify(data) }),
  parseBill: (text: string) => request<any>('/emissions/parse-bill', { method: 'POST', body: JSON.stringify({ text }) }),
  getSummary: (year?: number) => request<any>(`/emissions/summary${year ? `?year=${year}` : ''}`),
}

// ── AI ────────────────────────────────────────────────────────
export const ai = {
  mapDatapoint: (data: any) => request<any>('/ai/esrs-mapper', { method: 'POST', body: JSON.stringify(data) }),
  batchMap: (datapoints: any[]) => request<any>('/ai/esrs-mapper/batch', { method: 'POST', body: JSON.stringify({ datapoints }) }),
  getMapperStatus: () => request<any>('/ai/esrs-mapper/status'),
  clearCache: () => request<any>('/ai/esrs-mapper/clear-cache', { method: 'POST' }),
}

// ── Reports ───────────────────────────────────────────────────
export const reports = {
  list: () => request<any[]>('/reports/'),
  create: (data: { reporting_year: number; title: string }) =>
    request<any>('/reports/', { method: 'POST', body: JSON.stringify(data) }),
  get: (id: string) => request<any>(`/reports/${id}`),
  exportFormat: (id: string, format: string) => `${API_BASE}/reports/${id}/export/${format}`,
  getFormats: () => request<any>('/reports/export/formats'),
  exportAll: (id: string) => request<any>(`/reports/${id}/export-all`, { method: 'POST' }),
}
