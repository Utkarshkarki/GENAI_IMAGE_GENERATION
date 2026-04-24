// src/api/index.js — All API call wrappers
const BASE = '/api';

function getKey() {
  return localStorage.getItem('imagemod_api_key') || '';
}

function headers() {
  return { 'x-api-key': getKey() };
}

function json(method, path, body) {
  return fetch(BASE + path, {
    method,
    headers: { ...headers(), 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  }).then(async r => {
    if (!r.ok) { const e = await r.json().catch(()=>({detail:r.statusText})); throw new Error(e.detail||'Request failed'); }
    return r.json();
  });
}

function form(path, formData) {
  return fetch(BASE + path, {
    method: 'POST',
    headers: headers(),
    body: formData,
  }).then(async r => {
    if (!r.ok) { const e = await r.json().catch(()=>({detail:r.statusText})); throw new Error(e.detail||'Request failed'); }
    return r.json();
  });
}

// ── Generate ──────────────────────────────────────────────
export const generate = (body) => json('POST', '/generate', body);
export const enhancePrompt = (prompt) => json('POST', '/enhance-prompt', { prompt });

// ── Lifestyle ─────────────────────────────────────────────
export function lifestyleByText(file, params) {
  const fd = new FormData();
  fd.append('file', file);
  Object.entries(params).forEach(([k,v]) => v !== undefined && v !== null && fd.append(k, v));
  return form('/lifestyle/text', fd);
}
export function lifestyleByImage(file, refFile, params) {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('reference_image', refFile);
  Object.entries(params).forEach(([k,v]) => v !== undefined && v !== null && fd.append(k, v));
  return form('/lifestyle/image', fd);
}

// ── Packshot ──────────────────────────────────────────────
export function packshot(file, params) {
  const fd = new FormData();
  fd.append('file', file);
  Object.entries(params).forEach(([k,v]) => v !== undefined && v !== null && fd.append(k, v));
  return form('/packshot', fd);
}

// ── Shadow ────────────────────────────────────────────────
export function shadow(file, params) {
  const fd = new FormData();
  fd.append('file', file);
  Object.entries(params).forEach(([k,v]) => v !== undefined && v !== null && fd.append(k, v));
  return form('/shadow', fd);
}

// ── Fill ──────────────────────────────────────────────────
export function fill(file, maskBlob, params) {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('mask', maskBlob, 'mask.png');
  Object.entries(params).forEach(([k,v]) => v !== undefined && v !== null && fd.append(k, v));
  return form('/fill', fd);
}

// ── Erase ─────────────────────────────────────────────────
export function erase(file, params = {}) {
  const fd = new FormData();
  fd.append('file', file);
  Object.entries(params).forEach(([k,v]) => v !== undefined && v !== null && fd.append(k, v));
  return form('/erase', fd);
}

// ── Agent ─────────────────────────────────────────────────
export const agentParse = (body) => json('POST', '/agent/parse', body);
export const agentAnswer = (body) => json('POST', '/agent/answer', body);

export function agentExecute(planJson, file, params = {}) {
  const fd = new FormData();
  fd.append('plan_json', JSON.stringify(planJson));
  Object.entries(params).forEach(([k,v]) => fd.append(k, v));
  if (file) fd.append('file', file);
  return form('/agent/execute', fd);
}

export const getMemory = () => fetch(BASE + '/agent/memory', { headers: headers() }).then(r => r.json());
export const deleteMemory = (key) => fetch(BASE + `/agent/memory/${key}`, { method:'DELETE', headers: headers() }).then(r => r.json());
export const clearMemory = () => fetch(BASE + '/agent/memory', { method:'DELETE', headers: headers() }).then(r => r.json());
