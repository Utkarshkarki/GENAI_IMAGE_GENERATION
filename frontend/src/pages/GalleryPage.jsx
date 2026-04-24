// src/pages/GalleryPage.jsx
import { useState } from 'react';

export default function GalleryPage({ gallery, clearGallery }) {
  const [lightbox, setLightbox] = useState(null);
  const [filter, setFilter] = useState('All');

  const LABELS = ['All', 'Generate', 'Lifestyle', 'Packshot', 'Shadow', 'Gen Fill', 'Erase', 'AI Agent'];
  const filtered = filter === 'All' ? gallery : gallery.filter(i => i.label === filter);

  return (
    <div className="form-col page-enter">
      <div style={{display:'flex',alignItems:'flex-start',justifyContent:'space-between',flexWrap:'wrap',gap:'12px'}}>
        <div className="section-header" style={{margin:0}}>
          <div>
            <h2>🖼️ Session Gallery</h2>
            <p>{gallery.length} image{gallery.length !== 1 ? 's' : ''} generated this session</p>
          </div>
        </div>
        {gallery.length > 0 && (
          <button className="btn btn-ghost btn-sm" onClick={clearGallery}>🗑️ Clear all</button>
        )}
      </div>

      {/* Filter chips */}
      {gallery.length > 0 && (
        <div style={{display:'flex',gap:'6px',flexWrap:'wrap'}}>
          {LABELS.map(l => (
            <button key={l} onClick={() => setFilter(l)} style={{
              padding:'5px 14px',borderRadius:'20px',border:'1px solid',cursor:'pointer',fontSize:'12px',fontWeight:'500',
              borderColor: filter===l ? 'var(--accent)' : 'var(--border)',
              background: filter===l ? 'rgba(99,102,241,.2)' : 'rgba(255,255,255,.04)',
              color: filter===l ? 'var(--text-primary)' : 'var(--text-muted)',
              transition:'.15s', fontFamily:'inherit',
            }}>{l}</button>
          ))}
        </div>
      )}

      {filtered.length === 0 ? (
        <div className="glass" style={{padding:'60px',textAlign:'center'}}>
          <div style={{fontSize:'48px',marginBottom:'12px'}}>🖼️</div>
          <p style={{color:'var(--text-secondary)',fontSize:'16px',fontWeight:'500'}}>No images yet</p>
          <p style={{color:'var(--text-muted)',fontSize:'13px',marginTop:'6px'}}>Generate images across any tab — they'll all appear here</p>
        </div>
      ) : (
        <div className="gallery-grid">
          {filtered.map((item, i) => (
            <div key={i} className="gallery-item" onClick={() => setLightbox(item)}>
              <img src={item.url} alt={item.label} />
              <div className="gallery-item-overlay">
                <span className="badge badge-accent" style={{width:'fit-content',fontSize:'10px'}}>{item.label}</span>
                <div style={{display:'flex',gap:'6px'}}>
                  <a href={item.url} download={`imagemod_${i+1}.png`} target="_blank" rel="noreferrer"
                    className="btn btn-ghost btn-xs btn-full" onClick={e => e.stopPropagation()}>⬇ Download</a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {lightbox && (
        <div className="lightbox" onClick={() => setLightbox(null)}>
          <img className="lightbox-img" src={lightbox.url} alt={lightbox.label} onClick={e => e.stopPropagation()} />
          <button className="lightbox-close" onClick={() => setLightbox(null)}>✕</button>
          <div style={{position:'absolute',bottom:'24px',left:'50%',transform:'translateX(-50%)',display:'flex',gap:'10px'}}>
            <span className="badge badge-accent">{lightbox.label}</span>
            <a href={lightbox.url} download="imagemod_image.png" target="_blank" rel="noreferrer"
              className="btn btn-primary btn-sm" onClick={e => e.stopPropagation()}>⬇ Download</a>
          </div>
        </div>
      )}
    </div>
  );
}
