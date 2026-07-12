export type Language = 'pl' | 'en';

function normalizeLanguage(value: string | null | undefined): Language | null {
  const normalized = value?.trim().toLowerCase();
  if (normalized === 'pl' || normalized === 'en') {
    return normalized;
  }
  return null;
}

export function detectLanguage(): Language {
  const fromQuery = normalizeLanguage(new URLSearchParams(window.location.search).get('lang'));
  if (fromQuery) {
    return fromQuery;
  }

  const envValue = (import.meta as ImportMeta & { env?: { VITE_APP_LANG?: string } }).env?.VITE_APP_LANG;
  const fromEnv = normalizeLanguage(envValue);
  if (fromEnv) {
    return fromEnv;
  }

  return 'pl';
}

export function localeForLanguage(lang: Language): string {
  return lang === 'en' ? 'en-US' : 'pl-PL';
}
