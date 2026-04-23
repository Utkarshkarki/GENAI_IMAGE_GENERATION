// src/pages/FillPage.jsx
import { useState } from 'react';
import { fill } from '../api';
import UploadZone from '../components/UploadZone';
import MaskCanvas from '../components/MaskCanvas';
import Spinner from '../components/Spinner';
import ResultGrid from '../components/ResultGrid';

export default function FillPage({ addToGallery }) {
  const [file, setFile] = useState(null);
  const [maskBlob, setMaskBlob] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [negPrompt, setNegPrompt] = useState('');
  const [numResults, setNumResults] = useState(1);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');
  const [maskReady, setMaskReady] = useState(false);

  function handleMask(blob) { setMaskBlob(blob); setMaskReady(true); }

  async function handleSubmit() {
    if (!file || !maskBlob || !prompt) return;
    setLoading(true); setError(''); setResults([]);
    try {
      const res = await fill(file, maskBlob, { prompt, negative_prompt: negPrompt || undefined, num_results: numResults, sync: true });
      const urls = res.result_urls || [];
      setResults(urls);
      urls.forEach(u => addToGallery(u, 'Gen Fill'));
    } catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="form-col page-enter">
      <div className="section-header">
        <div><h2>✏️ Generative Fill</h2>
          <p>Paint a mask and describe what to generate in that area</p></div>
      </div>

      <div className="glass-elevated" style={{padding:'24px',display:'flex',flexDirection:'column',gap:'16px'}}>
        {!file ? (
          <div className="field">
            <label className="field-label">Upload Image</label>
            <UploadZone onFile={f => { setFile(f); setMaskReady(false); setMaskBlob(null); }} label="Upload image to paint mask on" preview={false} />
          </div>
        ) : (
          <div className="field">
            <label className="field-label">🖌 Paint the area you want to replace</label>
            <MaskCanvas imageFile={file} onMaskReady={handleMask} />
            {maskReady && <div className="alert alert-success">✓ Mask captured — ready to generate</div>}
            <button className="btn btn-ghost btn-xs" style={{width:'fit-content'}} onClick={() => { setFile(null); setMaskBlob(null); setMaskReady(false); }}>
              ↩ Change image
            </button>
          </div>
        )}

        <div className="field">
          <label className="field-label">What to generate in the masked area</label>
          <textarea className="textarea" placeholder="A bunch of fresh red roses…"
            value={prompt} onChange={e => setPrompt(e.target.value)} />
        </div>
        <div className="field">
          <label className="field-label">Negative Prompt (optional)</label>
          <input className="input" placeholder="blurry, low quality…"
            value={negPrompt} onChange={e => setNegPrompt(e.target.value)} />
        </div>

        <div className="field">
          <label className="field-label">Variations: {numResults}</label>
          <input type="range" className="slider" min={1} max={4} value={numResults}
            style={{'--val':`${((numResults-1)/3)*100}%`}} onChange={e => setNumResults(+e.target.value)} />
        </div>

        {error && <div className="alert alert-error">⚠ {error}</div>}
        <button id="fill-btn" className="btn btn-primary btn-full" onClick={handleSubmit}
          disabled={!file || !maskBlob || !prompt || loading}>
          {loading ? '⏳ Generating…' : '🎨 Apply Generative Fill'}
        </button>
      </div>

      {loading && <Spinner text="Filling your selection…" />}
      {results.length > 0 && (
        <><div className="section-header"><h2>Results</h2></div>
        <ResultGrid urls={results} onAdd={u => addToGallery(u,'Gen Fill')} /></>
      )}
    </div>
  );
}
