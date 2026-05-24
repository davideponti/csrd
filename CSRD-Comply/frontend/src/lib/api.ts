// ── API Client ──────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
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
// Used by pages that need low-level GET/POST/PUT/DELETE access
// with support for text responses and blob downloads.

export const api = {
  get: <T = any>(endpoint: string) => {
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    return fetch(`${base}${endpoint}`, { headers }).then(async (res) => {
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || 'API Error');
      }
      return res.json() as Promise<T>;
    });
  },

  post: <T = any>(endpoint: string, body?: any) => {
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    return fetch(`${base}${endpoint}`, {
      method: 'POST',
      headers,
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
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    return fetch(`${base}${endpoint}`, {
      method: 'PUT',
      headers,
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
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    return fetch(`${base}${endpoint}`, {
      method: 'PATCH',
      headers,
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
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    return fetch(`${base}${endpoint}`, {
      method: 'DELETE',
      headers,
    }).then(async (res) => {
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || 'API Error');
      }
      return res.json() as Promise<T>;
    });
  },

  get_text: async (endpoint: string) => {
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    const headers: Record<string, string> = {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    const res = await fetch(`${base}${endpoint}`, { headers });
    if (!res.ok) {
      throw new Error(`Failed to fetch text: ${res.statusText}`);
    }
    return res.text();
  },

  get_blob: async (endpoint: string) => {
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    const headers: Record<string, string> = {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    const res = await fetch(`${base}${endpoint}`, { headers });
    if (!res.ok) {
      throw new Error(`Failed to fetch blob: ${res.statusText}`);
    }
    return res.blob();
  },
};

// ── Auth ───────────────────────────────────────────────────────
export const auth = {
  register: (data: { email: string; password: string; company_name: string }) =>
    request<{ access_token: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  login: (data: { email: string; password: string }) =>
    request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
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

  // Context Questionnaire
  getContext: (id: string) => request<any>(`/assessment/${id}/context`),
  updateContext: (id: string, data: any) =>
    request<any>(`/assessment/${id}/context`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  getQuestionnaire: (id: string) => request<any>(`/assessment/${id}/questionnaire`),

  // IRO Generator
  getIros: (id: string) => request<any>(`/assessment/${id}/iros`),
  generateIros: (id: string, data?: { use_ai?: boolean; context_override?: any }) =>
    request<any>(`/assessment/${id}/iros/generate`, {
      method: 'POST',
      body: JSON.stringify(data || { use_ai: false }),
    }),

  // Scoring Engine (Step 10)
  listScores: (id: string) => request<any>(`/assessment/${id}/scores`),
  updateScore: (id: string, scoreId: string, data: {
    impact_scale?: number;
    impact_scope?: number;
    impact_irremediability?: number;
    impact_likelihood?: number;
    financial_magnitude?: number;
    financial_likelihood?: number;
    rationale?: string;
  }) =>
    request<any>(`/assessment/${id}/scores/${scoreId}`, {
      method: 'PATCH',
      body: JSON.stringify({ score_id: scoreId, ...data }),
    }),
  getAiFollowup: (id: string, scoreId: string) =>
    request<any>(`/assessment/${id}/scores/${scoreId}/ai-followup`, {
      method: 'POST',
    }),

  generateScores: (id: string) =>
    request<any>(`/assessment/${id}/scores/generate`, {
      method: 'POST',
    }),
  calculateScores: (id: string) =>
    request<any>(`/assessment/${id}/scores/calculate`, {
      method: 'POST',
    }),

  // Context Questionnaire
  saveQuestionnaireResponses: (id: string, responses: Record<string, string>) =>
    request<any>(`/assessment/${id}/context`, {
      method: 'PUT',
      body: JSON.stringify({ questionnaire_responses: responses }),
    }),

  // Materiality Matrix (Step 10-11)
  getMatrix: (id: string) => request<any>(`/assessment/${id}/matrix`),

  // Materiality Report (Step 11)
  getReport: (id: string) => request<any>(`/assessment/${id}/report`),

  // Gap Analysis
  getGapAnalysis: (id: string) => request<any>(`/assessment/${id}/gap-analysis`),
}

// ── Emissions & Carbon Calculator (Steps 12-16) ────────────────
export const emissions = {
  list: (params?: { scope?: string; year?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.scope) searchParams.set('scope', params.scope)
    if (params?.year) searchParams.set('year', String(params.year))
    const query = searchParams.toString()
    return request<any[]>(`/emissions/${query ? `?${query}` : ''}`)
  },
  create: (data: any) =>
    request<any>('/emissions/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Carbon Calculator
  getFactors: () => request<any>('/emissions/factors'),
  calculateScope1: (data: any) =>
    request<any>('/emissions/calculate/scope1', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  calculateScope1Process: (data: any) =>
    request<any>('/emissions/calculate/scope1/process', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  calculateScope2: (data: any) =>
    request<any>('/emissions/calculate/scope2', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  calculateScope3: (data: any) =>
    request<any>('/emissions/calculate/scope3', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Save & Validate
  saveCalculated: (data: any) =>
    request<any>('/emissions/save-calculated', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  validate: (data: any) =>
    request<any>('/emissions/validate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Utility Bill OCR
  parseBill: (text: string) =>
    request<any>('/emissions/parse-bill', {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),

  // Summary
  getSummary: (year?: number) =>
    request<any>(`/emissions/summary${year ? `?year=${year}` : ''}`),
}

// ── AI / ESRS Mapper (Steps 6-7) ──────────────────────────────
export const ai = {
  mapDatapoint: (data: {
    disclosure_text: string
    sector: string
    activities: string[]
    countries: string[]
    employee_count: number
    turnover?: number
  }) =>
    request<any>('/ai/esrs-mapper', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  batchMap: (datapoints: any[]) =>
    request<any>('/ai/esrs-mapper/batch', {
      method: 'POST',
      body: JSON.stringify({ datapoints }),
    }),

  getMapperStatus: () => request<any>('/ai/esrs-mapper/status'),

  clearCache: () =>
    request<any>('/ai/esrs-mapper/clear-cache', {
      method: 'POST',
    }),
}

// ── Reports (Steps 18-22) ──────────────────────────────────────
export const reports = {
  list: () => request<any[]>('/reports/'),
  create: (data: { reporting_year: number; title: string }) =>
    request<any>('/reports/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  get: (id: string) => request<any>(`/reports/${id}`),

  // Export Multi-Formato (Step 22)
  exportFormat: (id: string, format: string) =>
    `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/reports/${id}/export/${format}`,

  getFormats: () => request<any>('/reports/export/formats'),

  exportAll: (id: string) =>
    request<any>(`/reports/${id}/export-all`, {
      method: 'POST',
    }),
}
