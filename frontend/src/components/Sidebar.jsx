// src/components/Sidebar.jsx
import { useState, useEffect } from 'react';
import { getMemory, deleteMemory, clearMemory } from '../api';

const PROVIDERS = [
  {
    id: 'ollama',
    label: 'Ollama',
    icon: '🦙',
    badge: '● Local',
    badgeColor: '#4ade80',
    models: ['llama3', 'mistral', 'phi3', 'gemma3', 'llama3.2', 'deepseek-r1'],
    hint: 'Runs locally on your machine. Free & private.',
  },
  {
    id: 'openai',
    label: 'OpenAI',
    icon: '⚡',
    badge: '☁ Cloud',
    badgeColor: '#60a5fa',
    models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    hint: 'Set OPENAI_API_KEY in your .env file.',
  },
  {
    id: 'claude',
    label: 'Claude',
    icon: '✦',
    badge: '☁ Cloud',
    badgeColor: '#f59e0b',
    models: ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'],
    hint: 'Set ANTHROPIC_API_KEY in your .env file.',
  },
];

const MODEL_LABELS = {
  'gpt-4o': 'GPT-4o',
  'gpt-4o-mini': 'GPT-4o Mini',
  'gpt-4-turbo': 'GPT-4 Turbo',
  'gpt-3.5-turbo': 'GPT-3.5 Turbo',
  'claude-3-5-sonnet-20241022': 'Claude 3.5 Sonnet',
  'claude-3-5-haiku-20241022': 'Claude 3.5 Haiku',
  'claude-3-opus-20240229': 'Claude 3 Opus',
  'llama3': 'LLaMA 3',
  'llama3.2': 'LLaMA 3.2',
  'mistral': 'Mistral',
  'phi3': 'Phi-3',
  'gemma3': 'Gemma 3',
  'deepseek-r1': 'DeepSeek R1',
};

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

export default function Sidebar({ activeTab, onTabChange, llmConfig, setLlmConfig }) {
  const [apiKey, setApiKey] = useState(localStorage.getItem('imagemod_api_key') || '');
  const [showKey, setShowKey] = useState(false);
  const [memory, setMemory] = useState({});

  const activeProvider = PROVIDERS.find(p => p.id === llmConfig.provider) || PROVIDERS[0];

  useEffect(() => {
    localStorage.setItem('imagemod_api_key', apiKey);
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

  function setProvider(id) {
    const p = PROVIDERS.find(pr => pr.id === id);
    setLlmConfig({ provider: id, model: p.models[0] });
  }

  function setModel(model) {
    setLlmConfig(cfg => ({ ...cfg, model }));
  }

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">✦</div>
        <div>
          <h1>ImageMod</h1>
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

      {/* AI Provider */}
      <div className="sidebar-section">
        <div style={{display:'flex', alignItems:'center', justifyContent:'space-between'}}>
          <p className="sidebar-label">🤖 AI Provider</p>
          <span style={{
            fontSize:'10px', fontWeight:'600', padding:'2px 8px', borderRadius:'20px',
            background: `${activeProvider.badgeColor}20`,
            color: activeProvider.badgeColor,
            border: `1px solid ${activeProvider.badgeColor}40`,
          }}>{activeProvider.badge}</span>
        </div>

        {/* Provider cards */}
        <div style={{display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:'6px', marginTop:'4px'}}>
          {PROVIDERS.map(p => (
            <button
              key={p.id}
              id={`provider-${p.id}`}
              onClick={() => setProvider(p.id)}
              style={{
                display:'flex', flexDirection:'column', alignItems:'center', gap:'4px',
                padding:'10px 6px', borderRadius:'10px', border:'none', cursor:'pointer',
                background: llmConfig.provider === p.id
                  ? 'linear-gradient(135deg,rgba(99,102,241,.3),rgba(139,92,246,.2))'
                  : 'rgba(255,255,255,.04)',
                border: llmConfig.provider === p.id
                  ? '1px solid rgba(99,102,241,.5)'
                  : '1px solid var(--border)',
                color: llmConfig.provider === p.id ? 'var(--text-primary)' : 'var(--text-muted)',
                transition:'all .2s',
                boxShadow: llmConfig.provider === p.id ? '0 0 12px rgba(99,102,241,.2)' : 'none',
              }}
            >
              <span style={{fontSize:'18px'}}>{p.icon}</span>
              <span style={{fontSize:'11px', fontWeight:'600', fontFamily:'Space Grotesk,sans-serif'}}>{p.label}</span>
            </button>
          ))}
        </div>

        {/* Hint */}
        <p style={{fontSize:'11px', color:'var(--text-muted)', marginTop:'4px', padding:'0 2px'}}>
          {activeProvider.hint}
        </p>

        {/* Model selector */}
        <div className="field" style={{marginTop:'4px'}}>
          <label className="field-label">Model</label>
          <div style={{position:'relative'}}>
            <select
              id="llm-model-select"
              className="select"
              value={llmConfig.model}
              onChange={e => setModel(e.target.value)}
            >
              {activeProvider.models.map(m => (
                <option key={m} value={m}>{MODEL_LABELS[m] || m}</option>
              ))}
            </select>
            <span style={{
              position:'absolute', right:'12px', top:'50%', transform:'translateY(-50%)',
              color:'var(--text-muted)', pointerEvents:'none', fontSize:'12px',
            }}>▾</span>
          </div>
        </div>

        {/* Ollama-only: server status hint */}
        {llmConfig.provider === 'ollama' && (
          <div style={{
            display:'flex', alignItems:'center', gap:'6px',
            padding:'8px 10px', borderRadius:'8px',
            background:'rgba(74,222,128,.06)', border:'1px solid rgba(74,222,128,.15)',
            fontSize:'11px', color:'#86efac', marginTop:'4px',
          }}>
            <span>●</span>
            <span>Reads <code style={{background:'rgba(255,255,255,.08)',padding:'0 4px',borderRadius:'3px'}}>OLLAMA_URL</code> from .env</span>
          </div>
        )}

        {/* Cloud provider: key location hint */}
        {llmConfig.provider !== 'ollama' && (
          <div style={{
            display:'flex', alignItems:'center', gap:'6px',
            padding:'8px 10px', borderRadius:'8px',
            background:'rgba(96,165,250,.06)', border:'1px solid rgba(96,165,250,.15)',
            fontSize:'11px', color:'#93c5fd', marginTop:'4px',
          }}>
            <span>🔑</span>
            <span>Key stored in <code style={{background:'rgba(255,255,255,.08)',padding:'0 4px',borderRadius:'3px'}}>.env</code> on server</span>
          </div>
        )}
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
