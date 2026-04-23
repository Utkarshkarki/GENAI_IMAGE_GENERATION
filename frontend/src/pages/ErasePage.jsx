// src/pages/ErasePage.jsx
import { useState } from 'react';
import { erase } from '../api';
import UploadZone from '../components/UploadZone';
import MaskCanvas from '../components/MaskCanvas';
import Spinner from '../components/Spinner';
import ResultGrid from '../components/ResultGrid';

export default function ErasePage({ addToGallery }) {
  const [file, setFile] = useState(null);
  const [maskBlob, setMaskBlob] = useState(null);
  const [maskReady, setMaskReady] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');

  async function handleSubmit() {
    if (!file) return;
    setLoading(true); setError(''); setResults([]);
    try {
      const res = await erase(file, { content_moderation: false });
      const urls = res.result_urls || [];
      setResults(urls);
      urls.forEach(u => addToGallery(u, 'Erase'));
    } catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="form-col page-enter">
      <div className="section-header">
        <div><h2>🧹 Erase Elements</h2>
          <p>Remove unwanted objects from your image with AI inpainting</p></div>
      </div>

      <div className="glass-elevated" style={{padding:'24px',display:'flex',flexDirection:'column',gap:'16px'}}>
        {!file ? (
          <div className="field">
            <label className="field-label">Upload Image</label>
            <UploadZone onFile={f => { setFile(f); setMaskReady(false); setMaskBlob(null); }}
              label="Upload the image to erase from" preview={false} />
          </div>
        ) : (
          <div className="field">
            <label className="field-label">🖌 Paint over the areas you want to erase</label>
            <MaskCanvas imageFile={file} onMaskReady={blob => { setMaskBlob(blob); setMaskReady(true); }} />
            {maskReady && <div className="alert alert-success">✓ Mask captured</div>}
            <button className="btn btn-ghost btn-xs" style={{width:'fit-content'}} onClick={() => { setFile(null); setMaskBlob(null); setMaskReady(false); }}>
              ↩ Change image
            </button>
          </div>
        )}

        {error && <div className="alert alert-error">⚠ {error}</div>}

        <button id="erase-btn" className="btn btn-primary btn-full" onClick={handleSubmit} disabled={!file || loading}>
          {loading ? '⏳ Erasing…' : '🧹 Erase Selection'}
        </button>
      </div>

      {loading && <Spinner text="Erasing and healing image…" />}
      {results.length > 0 && (
        <><div className="section-header"><h2>Results</h2></div>
        <ResultGrid urls={results} onAdd={u => addToGallery(u,'Erase')} /></>
      )}
    </div>
  );
}
