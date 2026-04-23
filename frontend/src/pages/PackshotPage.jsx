// src/pages/PackshotPage.jsx
import { useState } from 'react';
import { packshot } from '../api';
import UploadZone from '../components/UploadZone';
import Spinner from '../components/Spinner';
import ResultGrid from '../components/ResultGrid';

export default function PackshotPage({ addToGallery }) {
  const [file, setFile] = useState(null);
  const [bgColor, setBgColor] = useState('#FFFFFF');
  const [forceRmbg, setForceRmbg] = useState(false);
  const [contentMod, setContentMod] = useState(false);
  const [sku, setSku] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');

  async function handleSubmit() {
    if (!file) return;
    setLoading(true); setError(''); setResults([]);
    try {
      const res = await packshot(file, { background_color: bgColor, force_rmbg: forceRmbg, content_moderation: contentMod, sku: sku || undefined });
      const urls = res.result_urls || [];
      setResults(urls);
      urls.forEach(u => addToGallery(u, 'Packshot'));
    } catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }

  const presets = [
    { label: '⬜ White', color: '#FFFFFF' },
    { label: '⬛ Black', color: '#000000' },
    { label: '🩶 Gray', color: '#F5F5F5' },
    { label: '🔵 Navy', color: '#1E3A5F' },
  ];

  return (
    <div className="form-col page-enter">
      <div className="section-header">
        <div><h2>📦 Create Packshot</h2>
          <p>Professional studio-quality product shots with clean backgrounds</p></div>
      </div>

      <div className="glass-elevated" style={{padding:'24px',display:'flex',flexDirection:'column',gap:'16px'}}>
        <div className="field">
          <label className="field-label">Product Image</label>
          <UploadZone onFile={setFile} label="Upload your product image" />
        </div>

        <div className="field">
          <label className="field-label">Background Color</label>
          <div style={{display:'flex',gap:'8px',flexWrap:'wrap',alignItems:'center'}}>
            {presets.map(p => (
              <button key={p.color} className="btn btn-ghost btn-xs" style={{
                borderColor: bgColor===p.color ? 'var(--accent)' : undefined,
                background: bgColor===p.color ? 'rgba(99,102,241,.15)' : undefined,
              }} onClick={() => setBgColor(p.color)}>{p.label}</button>
            ))}
            <div className="color-swatch" onClick={() => document.getElementById('bg-color-picker').click()}>
              <div className="color-dot" style={{background:bgColor}} />
              <span className="color-hex">{bgColor}</span>
              <input id="bg-color-picker" type="color" value={bgColor} onChange={e => setBgColor(e.target.value)} style={{opacity:0,position:'absolute'}} />
            </div>
          </div>
        </div>

        <div className="form-row">
          <div className="field">
            <label className="field-label">SKU (optional)</label>
            <input className="input" placeholder="e.g. SKU-12345" value={sku} onChange={e => setSku(e.target.value)} />
          </div>
        </div>

        <div style={{display:'flex',gap:'20px',flexWrap:'wrap'}}>
          <label className="toggle">
            <input type="checkbox" checked={forceRmbg} onChange={e => setForceRmbg(e.target.checked)} />
            <span className="toggle-track"><span className="toggle-thumb"/></span>
            <span className="toggle-label">Force background removal</span>
          </label>
          <label className="toggle">
            <input type="checkbox" checked={contentMod} onChange={e => setContentMod(e.target.checked)} />
            <span className="toggle-track"><span className="toggle-thumb"/></span>
            <span className="toggle-label">Content moderation</span>
          </label>
        </div>

        {error && <div className="alert alert-error">⚠ {error}</div>}
        <button id="packshot-btn" className="btn btn-primary btn-full" onClick={handleSubmit} disabled={!file || loading}>
          {loading ? '⏳ Processing…' : '📦 Create Packshot'}
        </button>
      </div>

      {loading && <Spinner text="Creating professional packshot…" />}
      {results.length > 0 && (
        <><div className="section-header"><h2>Results</h2></div>
        <ResultGrid urls={results} onAdd={u => addToGallery(u,'Packshot')} /></>
      )}
    </div>
  );
}
