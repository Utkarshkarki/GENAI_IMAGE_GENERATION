// src/pages/GeneratePage.jsx
import { useState } from 'react';
import { generate, enhancePrompt } from '../api';
import Spinner from '../components/Spinner';
import ResultGrid from '../components/ResultGrid';

const STYLES = ['Realistic','Artistic','Cartoon','Sketch','Watercolor','Oil Painting','Digital Art'];
const RATIOS = ['1:1','16:9','9:16','4:3','3:4'];

export default function GeneratePage({ addToGallery }) {
  const [prompt, setPrompt] = useState('');
  const [enhanced, setEnhanced] = useState('');
  const [style, setStyle] = useState('Realistic');
  const [ratio, setRatio] = useState('1:1');
  const [numResults, setNumResults] = useState(1);
  const [enhance, setEnhance] = useState(true);
  const [loading, setLoading] = useState(false);
  const [enhancing, setEnhancing] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');

  async function handleEnhance() {
    if (!prompt) return;
    setEnhancing(true); setError('');
    try {
      const res = await enhancePrompt(prompt);
      setEnhanced(res.enhanced_prompt || prompt);
    } catch(e) { setError(e.message); }
    finally { setEnhancing(false); }
  }

  async function handleGenerate() {
    if (!prompt && !enhanced) return;
    setLoading(true); setError(''); setResults([]);
    try {
      const res = await generate({
        prompt: enhanced || prompt, style, aspect_ratio: ratio,
        num_results: numResults, enhance_image: enhance,
      });
      const urls = res.result_urls || [];
      setResults(urls);
      urls.forEach(u => addToGallery(u, 'Generate'));
    } catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="form-col page-enter">
      <div className="section-header">
        <div>
          <h2>🎨 Generate Image</h2>
          <p>Create stunning images from a text prompt using Bria AI</p>
        </div>
      </div>

      <div className="glass-elevated" style={{padding:'24px',display:'flex',flexDirection:'column',gap:'16px'}}>
        {/* Prompt */}
        <div className="field">
          <label className="field-label">Prompt</label>
          <textarea className="textarea" placeholder="A sleek red sneaker on a marble surface with dramatic lighting…"
            value={prompt} onChange={e => { setPrompt(e.target.value); setEnhanced(''); }} />
        </div>

        {enhanced && (
          <div className="alert alert-info">
            <span>✨</span>
            <div><strong>Enhanced:</strong> {enhanced}</div>
          </div>
        )}

        {/* Options row */}
        <div className="form-row">
          <div className="field">
            <label className="field-label">Style</label>
            <select className="select" value={style} onChange={e => setStyle(e.target.value)}>
              {STYLES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="field">
            <label className="field-label">Aspect Ratio</label>
            <select className="select" value={ratio} onChange={e => setRatio(e.target.value)}>
              {RATIOS.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div className="field">
            <label className="field-label">Images: {numResults}</label>
            <input type="range" className="slider" min={1} max={4} value={numResults}
              style={{'--val':`${((numResults-1)/3)*100}%`}}
              onChange={e => setNumResults(+e.target.value)} />
          </div>
        </div>

        <label className="toggle">
          <input type="checkbox" checked={enhance} onChange={e => setEnhance(e.target.checked)} />
          <span className="toggle-track"><span className="toggle-thumb"/></span>
          <span className="toggle-label">Enhance image quality</span>
        </label>

        {error && <div className="alert alert-error">⚠ {error}</div>}

        <div className="form-row" style={{gap:'10px'}}>
          <button id="enhance-prompt-btn" className="btn btn-ghost" onClick={handleEnhance} disabled={!prompt || enhancing}>
            {enhancing ? '…' : '✨'} Enhance Prompt
          </button>
          <button id="generate-btn" className="btn btn-primary btn-full" onClick={handleGenerate} disabled={(!prompt && !enhanced) || loading}>
            {loading ? '⏳ Generating…' : '🎨 Generate Images'}
          </button>
        </div>
      </div>

      {loading && <Spinner text="Generating your masterpiece…" />}
      {results.length > 0 && (
        <div className="form-col">
          <div className="section-header"><h2>Results</h2></div>
          <ResultGrid urls={results} onAdd={u => addToGallery(u,'Generate')} />
        </div>
      )}
    </div>
  );
}
