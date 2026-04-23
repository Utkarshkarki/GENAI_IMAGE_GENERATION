// src/pages/LifestylePage.jsx
import { useState } from 'react';
import { lifestyleByText, lifestyleByImage } from '../api';
import UploadZone from '../components/UploadZone';
import Spinner from '../components/Spinner';
import ResultGrid from '../components/ResultGrid';

const PLACEMENTS = ['original','automatic','manual_placement','manual_padding','custom_coordinates'];

export default function LifestylePage({ addToGallery }) {
  const [file, setFile] = useState(null);
  const [refFile, setRefFile] = useState(null);
  const [mode, setMode] = useState('text');
  const [scene, setScene] = useState('');
  const [placement, setPlacement] = useState('automatic');
  const [numResults, setNumResults] = useState(2);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');

  async function handleSubmit() {
    if (!file) return;
    setLoading(true); setError(''); setResults([]);
    try {
      let res;
      const params = { placement_type: placement, num_results: numResults, sync: true };
      if (mode === 'text') {
        res = await lifestyleByText(file, { ...params, scene_description: scene, fast: true });
      } else {
        if (!refFile) { setError('Please upload a reference image.'); setLoading(false); return; }
        res = await lifestyleByImage(file, refFile, params);
      }
      const urls = res.result_urls || [];
      setResults(urls);
      urls.forEach(u => addToGallery(u, 'Lifestyle'));
    } catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="form-col page-enter">
      <div className="section-header">
        <div><h2>🖼️ Lifestyle Shot</h2>
          <p>Place your product into AI-generated scenes</p></div>
      </div>

      <div className="glass-elevated" style={{padding:'24px',display:'flex',flexDirection:'column',gap:'16px'}}>
        <div className="field">
          <label className="field-label">Product Image</label>
          <UploadZone onFile={setFile} label="Drop your product image here" />
        </div>

        {/* Mode toggle */}
        <div className="tab-bar" style={{padding:'4px'}}>
          {['text','image'].map(m => (
            <button key={m} className={`tab-btn${mode===m?' active':''}`} onClick={() => setMode(m)}>
              {m === 'text' ? '📝 Text Prompt' : '🖼️ Reference Image'}
            </button>
          ))}
        </div>

        {mode === 'text' ? (
          <div className="field">
            <label className="field-label">Scene Description</label>
            <textarea className="textarea" placeholder="A luxury bathroom with marble tiles and soft warm lighting…"
              value={scene} onChange={e => setScene(e.target.value)} />
          </div>
        ) : (
          <div className="field">
            <label className="field-label">Reference Background Image</label>
            <UploadZone onFile={setRefFile} label="Drop reference image here" />
          </div>
        )}

        <div className="form-row">
          <div className="field">
            <label className="field-label">Placement Type</label>
            <select className="select" value={placement} onChange={e => setPlacement(e.target.value)}>
              {PLACEMENTS.map(p => <option key={p} value={p}>{p.replace(/_/g,' ')}</option>)}
            </select>
          </div>
          <div className="field">
            <label className="field-label">Results: {numResults}</label>
            <input type="range" className="slider" min={1} max={4} value={numResults}
              style={{'--val':`${((numResults-1)/3)*100}%`}}
              onChange={e => setNumResults(+e.target.value)} />
          </div>
        </div>

        {error && <div className="alert alert-error">⚠ {error}</div>}
        <button id="lifestyle-btn" className="btn btn-primary btn-full" onClick={handleSubmit}
          disabled={!file || loading || (mode==='text' && !scene)}>
          {loading ? '⏳ Generating…' : '🌄 Generate Lifestyle Shot'}
        </button>
      </div>

      {loading && <Spinner text="Building your lifestyle scene…" />}
      {results.length > 0 && (
        <><div className="section-header"><h2>Results</h2></div>
        <ResultGrid urls={results} onAdd={u => addToGallery(u,'Lifestyle')} /></>
      )}
    </div>
  );
}
