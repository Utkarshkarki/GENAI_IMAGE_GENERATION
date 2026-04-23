// src/pages/ShadowPage.jsx
import { useState } from 'react';
import { shadow } from '../api';
import UploadZone from '../components/UploadZone';
import Spinner from '../components/Spinner';
import ResultGrid from '../components/ResultGrid';

export default function ShadowPage({ addToGallery }) {
  const [file, setFile] = useState(null);
  const [shadowType, setShadowType] = useState('natural');
  const [intensity, setIntensity] = useState(60);
  const [blur, setBlur] = useState(15);
  const [offsetX, setOffsetX] = useState(0);
  const [offsetY, setOffsetY] = useState(15);
  const [shadowColor, setShadowColor] = useState('#000000');
  const [bgColor, setBgColor] = useState('');
  const [useBg, setUseBg] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');

  async function handleSubmit() {
    if (!file) return;
    setLoading(true); setError(''); setResults([]);
    try {
      const res = await shadow(file, {
        shadow_type: shadowType, shadow_color: shadowColor,
        shadow_intensity: intensity, shadow_blur: blur,
        offset_x: offsetX, offset_y: offsetY,
        background_color: useBg ? bgColor : undefined,
      });
      const urls = res.result_urls || [];
      setResults(urls);
      urls.forEach(u => addToGallery(u, 'Shadow'));
    } catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }

  const TYPES = [
    { id:'natural', label:'🌿 Natural', desc:'Realistic ground shadow' },
    { id:'drop',    label:'💧 Drop',    desc:'Classic drop shadow' },
  ];

  return (
    <div className="form-col page-enter">
      <div className="section-header">
        <div><h2>🌑 Add Shadow</h2>
          <p>Add professional shadows to make your product images pop</p></div>
      </div>

      <div className="glass-elevated" style={{padding:'24px',display:'flex',flexDirection:'column',gap:'16px'}}>
        <div className="field">
          <label className="field-label">Product Image</label>
          <UploadZone onFile={setFile} label="Upload product image" />
        </div>

        {/* Shadow type cards */}
        <div className="field">
          <label className="field-label">Shadow Type</label>
          <div style={{display:'flex',gap:'10px'}}>
            {TYPES.map(t => (
              <button key={t.id} onClick={() => setShadowType(t.id)} style={{
                flex:1, padding:'14px', borderRadius:'12px', cursor:'pointer', border:'none',
                background: shadowType===t.id ? 'linear-gradient(135deg,rgba(99,102,241,.3),rgba(139,92,246,.2))' : 'rgba(255,255,255,.04)',
                borderWidth:'1px', borderStyle:'solid',
                borderColor: shadowType===t.id ? 'rgba(99,102,241,.5)' : 'var(--border)',
                color: shadowType===t.id ? 'var(--text-primary)' : 'var(--text-muted)',
                textAlign:'center', transition:'.2s', fontFamily:'inherit',
              }}>
                <div style={{fontSize:'18px',marginBottom:'4px'}}>{t.label}</div>
                <div style={{fontSize:'11px'}}>{t.desc}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="form-row">
          <div className="field">
            <label className="field-label">Intensity: {intensity}%</label>
            <input type="range" className="slider" min={0} max={100} value={intensity}
              style={{'--val':`${intensity}%`}} onChange={e => setIntensity(+e.target.value)} />
          </div>
          <div className="field">
            <label className="field-label">Blur: {blur}px</label>
            <input type="range" className="slider" min={0} max={50} value={blur}
              style={{'--val':`${(blur/50)*100}%`}} onChange={e => setBlur(+e.target.value)} />
          </div>
        </div>

        <div className="form-row">
          <div className="field">
            <label className="field-label">X Offset: {offsetX}px</label>
            <input type="range" className="slider" min={-50} max={50} value={offsetX}
              style={{'--val':`${((offsetX+50)/100)*100}%`}} onChange={e => setOffsetX(+e.target.value)} />
          </div>
          <div className="field">
            <label className="field-label">Y Offset: {offsetY}px</label>
            <input type="range" className="slider" min={-50} max={50} value={offsetY}
              style={{'--val':`${((offsetY+50)/100)*100}%`}} onChange={e => setOffsetY(+e.target.value)} />
          </div>
        </div>

        <div className="form-row">
          <div className="field">
            <label className="field-label">Shadow Color</label>
            <div className="color-swatch" onClick={() => document.getElementById('shadow-color').click()}>
              <div className="color-dot" style={{background:shadowColor}} />
              <span className="color-hex">{shadowColor}</span>
              <input id="shadow-color" type="color" value={shadowColor} onChange={e => setShadowColor(e.target.value)} style={{opacity:0,position:'absolute'}} />
            </div>
          </div>
          <div className="field">
            <label className="toggle" style={{marginTop:'22px'}}>
              <input type="checkbox" checked={useBg} onChange={e => setUseBg(e.target.checked)} />
              <span className="toggle-track"><span className="toggle-thumb"/></span>
              <span className="toggle-label">Custom background</span>
            </label>
            {useBg && (
              <div className="color-swatch" style={{marginTop:'8px'}} onClick={() => document.getElementById('bg-color').click()}>
                <div className="color-dot" style={{background:bgColor||'#fff'}} />
                <span className="color-hex">{bgColor||'#FFFFFF'}</span>
                <input id="bg-color" type="color" value={bgColor||'#FFFFFF'} onChange={e => setBgColor(e.target.value)} style={{opacity:0,position:'absolute'}} />
              </div>
            )}
          </div>
        </div>

        {error && <div className="alert alert-error">⚠ {error}</div>}
        <button id="shadow-btn" className="btn btn-primary btn-full" onClick={handleSubmit} disabled={!file || loading}>
          {loading ? '⏳ Rendering…' : '🌑 Add Shadow'}
        </button>
      </div>

      {loading && <Spinner text="Rendering shadow effect…" />}
      {results.length > 0 && (
        <><div className="section-header"><h2>Results</h2></div>
        <ResultGrid urls={results} onAdd={u => addToGallery(u,'Shadow')} /></>
      )}
    </div>
  );
}
