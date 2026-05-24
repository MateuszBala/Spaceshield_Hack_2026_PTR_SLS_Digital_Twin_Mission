// HTTP client for dt_api.
// Vite dev proxy rewrites: /api/* → http://localhost:8000/*
//   /api/simulate      → POST http://localhost:8000/simulate
//   /api/capabilities  → GET  http://localhost:8000/capabilities
// API has CORS allow_origins=["*"], so direct fetch also works as fallback.

import type { SimRequest, SimResult, CapabilitiesResponse } from '../types/contracts';

const SIMULATE_TIMEOUT_MS  = 60_000;
const CAPS_TIMEOUT_MS      = 5_000;

async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeout: number,
): Promise<Response> {
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
    SIMULATE_TIMEOUT_MS,
  );
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
  return response.json() as Promise<SimResult>;
}

export async function fetchCapabilities(): Promise<CapabilitiesResponse> {
  const response = await fetchWithTimeout('/api/capabilities', {}, CAPS_TIMEOUT_MS);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<CapabilitiesResponse>;
}
