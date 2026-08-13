const BASE_URL = '/api';

function getTokens() {
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  };
}

function setTokens(access: string, refresh: string) {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

export function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

async function tryRefresh(): Promise<boolean> {
  const { refresh } = getTokens();
  if (!refresh) return false;
  const resp = await fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!resp.ok) return false;
  const data = await resp.json();
  setTokens(data.access_token, data.refresh_token);
  return true;
}

export class ApiError extends Error {
  status: number;
  code?: string;
  constructor(status: number, message: string, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export async function apiFetch<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const { access } = getTokens();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (access) headers['Authorization'] = `Bearer ${access}`;

  const resp = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (resp.status === 401 && retry) {
    const refreshed = await tryRefresh();
    if (refreshed) return apiFetch<T>(path, options, false);
    clearTokens();
    window.location.href = '/login';
    throw new ApiError(401, 'Sesión expirada');
  }

  if (!resp.ok) {
    let message = `Error ${resp.status}`;
    let code: string | undefined;
    try {
      const body = await resp.json();
      message = body?.detail?.error?.message || body?.detail?.[0]?.msg || message;
      code = body?.detail?.error?.code;
    } catch {
      /* respuesta sin cuerpo JSON */
    }
    throw new ApiError(resp.status, message, code);
  }

  if (resp.status === 204) return undefined as T;
  return resp.json();
}

export async function login(email: string, password: string) {
  const resp = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => null);
    throw new ApiError(resp.status, body?.detail?.error?.message || 'Credenciales inválidas');
  }
  const data = await resp.json();
  setTokens(data.access_token, data.refresh_token);
  return data;
}

export function getAccessToken() {
  return getTokens().access;
}
