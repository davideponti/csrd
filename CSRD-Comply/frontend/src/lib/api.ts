// ── API Client ──────────────────────────────────────────────────
// Uses HttpOnly cookies for JWT authentication (XSS-safe).
// All requests include credentials so the browser sends the cookie.

const API_BASE = '/api/v1'

/**
 * 🔒 SICUREZZA: L'autenticazione usa cookie HttpOnly (XSS-safe).
 * Il JWT non è accessibile via JavaScript. Il browser lo invia
 * automaticamente con ogni richiesta grazie a `credentials: 'include'`.
 */

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include',  // ← Invia cookie HttpOnly contenente il JWT
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
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    return fetch(`/api/v1${endpoint}`, { headers, credentials: 'include' }).then(async (res) => {
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || 'API Error');
      }
      return res.json() as Promise<T>;
    });
  },

  post: <T = any>(endpoint: string, body?: any) => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    return fetch(`/api/v1${endpoint}`, {
      method: 'POST',
      headers,
      credentials: 'include',
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
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    return fetch(`/api/v1${endpoint}`, {
      method: 'PUT',
      headers,
      credentials: 'include',
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
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    return fetch(`/api/v1${endpoint}`, {
      method: 'PATCH',
      headers,
      credentials: 'include',
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
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    return fetch(`/api/v1${endpoint}`, {
      method: 'DELETE',
      headers,
      credentials: 'include',
    }).then(async (res) => {
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || 'API Error');
      }
      return res.json() as Promise<T>;
    });
  },

  get_text: async (endpoint: string) => {
    const headers: Record<string, string> = {};
    const res = await fetch(`/api/v1${endpoint}`, { headers, credentials: 'include' });
    if (!res.ok) {
      throw new Error(`Failed to fetch text: ${res.statusText}`);
    }
    return res.text();
  },

  get_blob: async (endpoint: string) => {
    const headers: Record<string, string> = {};
    const res = await fetch(`/api/v1${endpoint}`, { headers, credentials: 'include' });
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

  saveQuestionnaireResponses: (id: string, responses: Record<string, string>) =>
    request<any>(`/assessment/${id}/context`, {
      method: 'PUT',
      body: JSON.stringify({ questionnaire_responses: responses }),
    }),

  getMatrix: (id: string) => request<any>(`/assessment/${id}/matrix`),
  getReport: (id: string) => request<any>(`/assessment/${id}/report`),
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

  parseBill: (text: string) =>
    request<any>('/emissions/parse-bill', {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),

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

  exportFormat: (id: string, format: string) =>
    `/api/v1/reports/${id}/export/${format}`,

  getFormats: () => request<any>('/reports/export/formats'),
  exportAll: (id: string) =>
    request<any>(`/reports/${id}/export-all`, {
      method: 'POST',
    }),
}
