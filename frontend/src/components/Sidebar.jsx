// src/components/Sidebar.jsx
import { useState, useEffect } from 'react';
import { getMemory, deleteMemory, clearMemory } from '../api';

export default function Sidebar({ activeTab, onTabChange, ollamaModel, setOllamaModel, ollamaUrl, setOllamaUrl }) {
  const [apiKey, setApiKey] = useState(localStorage.getItem('adsnap_api_key') || '');
  const [showKey, setShowKey] = useState(false);
  const [memory, setMemory] = useState({});

  const TABS = [
    { id: 'generate',  label: 'Generate',   icon: '🎨' },
    { id: 'lifestyle', label: 'Lifestyle',   icon: '🖼️' },
    { id: 'packshot',  label: 'Packshot',    icon: '📦' },
    { id: 'shadow',    label: 'Shadow',      icon: '🌑' },
    { id: 'fill',      label: 'Gen Fill',    icon: '✏️' },
    { id: 'erase',     label: 'Erase',       icon: '🧹' },
    { id: 'agent',     label: 'AI Agent',    icon: '🤖' },
    { id: 'gallery',   label: 'Gallery',     icon: '🖼️' },
  ];

  useEffect(() => {
    localStorage.setItem('adsnap_api_key', apiKey);
  }, [apiKey]);

  useEffect(() => {
    loadMemory();
  }, [activeTab]);

  async function loadMemory() {
    try { const m = await getMemory(); setMemory(m || {}); } catch {}
  }

  async function handleDeleteMemory(k) {
    await deleteMemory(k);
    loadMemory();
  }

  async function handleClearMemory() {
    await clearMemory();
    setMemory({});
  }

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">✦</div>
        <div>
          <h1>AdSnap</h1>
          <span>Studio</span>
        </div>
      </div>

      {/* API Key */}
      <div className="sidebar-section">
        <p className="sidebar-label">Bria API Key</p>
        <div className="apikey-field">
          <input
            id="api-key-input"
            className="input"
            type={showKey ? 'text' : 'password'}
            placeholder="Paste your API key…"
            value={apiKey}
            onChange={e => setApiKey(e.target.value)}
          />
          <button className="apikey-eye" onClick={() => setShowKey(v => !v)}>{showKey ? '🙈' : '👁️'}</button>
        </div>
        {apiKey && <span className="badge badge-green" style={{width:'fit-content'}}>✓ Key saved</span>}
      </div>

      {/* Navigation */}
      <div className="sidebar-section">
        <p className="sidebar-label">Navigation</p>
        <nav style={{display:'flex', flexDirection:'column', gap:'4px'}}>
          {TABS.map(t => (
            <button
              key={t.id}
              id={`nav-${t.id}`}
              onClick={() => onTabChange(t.id)}
              style={{
                display:'flex', alignItems:'center', gap:'10px',
                padding:'10px 12px', borderRadius:'10px', border:'none', cursor:'pointer',
                background: activeTab === t.id ? 'linear-gradient(135deg,rgba(99,102,241,.25),rgba(139,92,246,.2))' : 'none',
                borderLeft: activeTab === t.id ? '3px solid var(--accent)' : '3px solid transparent',
                color: activeTab === t.id ? 'var(--text-primary)' : 'var(--text-muted)',
                fontFamily:'Space Grotesk,sans-serif', fontSize:'14px', fontWeight:'500',
                transition:'all .2s', textAlign:'left',
              }}
            >
              <span style={{fontSize:'16px'}}>{t.icon}</span>
              {t.label}
              {activeTab === t.id && (
                <span style={{marginLeft:'auto',width:'6px',height:'6px',borderRadius:'50%',background:'var(--accent)'}} />
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Ollama */}
      <div className="sidebar-section">
        <p className="sidebar-label">🤖 Ollama (AI Agent)</p>
        <div className="field">
          <label className="field-label">Model</label>
          <select id="ollama-model" className="select" value={ollamaModel} onChange={e => setOllamaModel(e.target.value)}>
            {['llama3','mistral','phi3','gemma3'].map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
        <div className="field">
          <label className="field-label">Ollama URL</label>
          <input id="ollama-url" className="input" value={ollamaUrl} onChange={e => setOllamaUrl(e.target.value)} />
        </div>
      </div>

      {/* Agent Memory */}
      {Object.keys(memory).length > 0 && (
        <div className="sidebar-section">
          <div style={{display:'flex',alignItems:'center',justifyContent:'space-between'}}>
            <p className="sidebar-label">🧠 Agent Memory</p>
            <button className="btn btn-xs btn-ghost" onClick={handleClearMemory}>Clear all</button>
          </div>
          <div style={{display:'flex',flexDirection:'column',gap:'6px'}}>
            {Object.entries(memory).map(([k,v]) => (
              <div key={k} className="memory-tag">
                <span className="memory-tag-key">{k}:</span>
                <span className="memory-tag-val">{String(v)}</span>
                <button className="memory-tag-del" onClick={() => handleDeleteMemory(k)}>✕</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div style={{marginTop:'auto',paddingTop:'16px',borderTop:'1px solid var(--border)'}}>
        <p style={{fontSize:'11px',color:'var(--text-muted)',textAlign:'center'}}>
          Powered by <a href="https://bria.ai" target="_blank" rel="noreferrer" style={{color:'var(--accent)',textDecoration:'none'}}>Bria AI</a>
        </p>
      </div>
    </aside>
  );
}
