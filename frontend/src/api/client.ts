// HTTP client for dt_api.
// Uses Vite dev proxy: /api/* → http://localhost:8000/*
// Falls back to synthetic data when the API is unreachable.

import type { SimRequest, SimResult, Capabilities } from '../types/contracts';

const TIMEOUT_MS = 30_000;
const CAPS_TIMEOUT_MS = 4_000;

async function fetchWithTimeout(url: string, options: RequestInit, timeout: number): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(id);
  }
}

export async function fetchSimulate(request: SimRequest): Promise<SimResult> {
  const response = await fetchWithTimeout(
    '/api/simulate',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    },
    TIMEOUT_MS,
  );
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
  return response.json() as Promise<SimResult>;
}

export async function fetchCapabilities(): Promise<Capabilities> {
  const response = await fetchWithTimeout('/api/capabilities', {}, CAPS_TIMEOUT_MS);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<Capabilities>;
}
