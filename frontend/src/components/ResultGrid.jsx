// src/components/ResultGrid.jsx
import { useState } from 'react';

export default function ResultGrid({ urls, onAdd }) {
  const [lightbox, setLightbox] = useState(null);

  if (!urls || urls.length === 0) return null;

  return (
    <>
      <div className="result-grid">
        {urls.map((url, i) => (
          <div key={i} className="result-card">
            <img src={url} alt={`Result ${i+1}`} onClick={() => setLightbox(url)} style={{cursor:'zoom-in'}} />
            <div className="result-card-actions">
              <a href={url} download={`imagemod_result_${i+1}.png`} target="_blank" rel="noreferrer"
                className="btn btn-ghost btn-xs btn-full">⬇ Download</a>
              {onAdd && <button className="btn btn-ghost btn-xs" onClick={() => onAdd(url)}>＋</button>}
            </div>
          </div>
        ))}
      </div>

      {lightbox && (
        <div className="lightbox" onClick={() => setLightbox(null)}>
          <img className="lightbox-img" src={lightbox} alt="Full size" onClick={e => e.stopPropagation()} />
          <button className="lightbox-close" onClick={() => setLightbox(null)}>✕</button>
        </div>
      )}
    </>
  );
}
