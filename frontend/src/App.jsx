// src/App.jsx
import { useState, useEffect } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import Sidebar from './components/Sidebar';
import GeneratePage  from './pages/GeneratePage';
import LifestylePage from './pages/LifestylePage';
import PackshotPage  from './pages/PackshotPage';
import ShadowPage    from './pages/ShadowPage';
import FillPage      from './pages/FillPage';
import ErasePage     from './pages/ErasePage';
import AgentPage     from './pages/AgentPage';
import GalleryPage   from './pages/GalleryPage';

function loadGallery() {
  try { return JSON.parse(localStorage.getItem('imagemod_gallery') || '[]'); } catch { return []; }
}

export default function App() {
  const [activeTab, setActiveTab] = useState('generate');
  const [gallery, setGallery] = useState(loadGallery);
  const [ollamaModel, setOllamaModel] = useState('llama3');
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem('imagemod_gallery', JSON.stringify(gallery));
  }, [gallery]);

  function addToGallery(url, label) {
    setGallery(g => {
      if (g.some(i => i.url === url)) return g;
      const next = [...g, { url, label, index: g.length + 1 }];
      toast.success(`Saved to gallery!`, { duration: 2000, position: 'bottom-right' });
      return next;
    });
  }

  function clearGallery() {
    setGallery([]);
    localStorage.removeItem('imagemod_gallery');
    toast('Gallery cleared', { icon: '🗑️', duration: 2000 });
  }

  const PAGE_PROPS = { addToGallery, ollamaModel, ollamaUrl };

  const PAGES = {
    generate:  <GeneratePage  {...PAGE_PROPS} />,
    lifestyle: <LifestylePage {...PAGE_PROPS} />,
    packshot:  <PackshotPage  {...PAGE_PROPS} />,
    shadow:    <ShadowPage    {...PAGE_PROPS} />,
    fill:      <FillPage      {...PAGE_PROPS} />,
    erase:     <ErasePage     {...PAGE_PROPS} />,
    agent:     <AgentPage     {...PAGE_PROPS} />,
    gallery:   <GalleryPage gallery={gallery} clearGallery={clearGallery} />,
  };

  return (
    <>
      <Toaster toastOptions={{
        style: {
          background:'var(--bg-elevated)', color:'var(--text-primary)',
          border:'1px solid var(--border)', borderRadius:'10px',
          fontFamily:'Inter,sans-serif', fontSize:'13px',
        },
      }} />

      <div className="app-shell">
        {/* Mobile overlay */}
        {sidebarOpen && (
          <div onClick={() => setSidebarOpen(false)} style={{
            position:'fixed',inset:0,background:'rgba(0,0,0,.5)',zIndex:99,
          }} />
        )}

        <Sidebar
          activeTab={activeTab}
          onTabChange={t => { setActiveTab(t); setSidebarOpen(false); }}
          ollamaModel={ollamaModel} setOllamaModel={setOllamaModel}
          ollamaUrl={ollamaUrl} setOllamaUrl={setOllamaUrl}
        />

        <main className="main-content">
          {/* Mobile header */}
          <div style={{display:'none'}} id="mobile-header">
            <button onClick={() => setSidebarOpen(v => !v)} style={{
              background:'none',border:'none',color:'var(--text-primary)',fontSize:'22px',cursor:'pointer',
            }}>☰</button>
          </div>

          {/* Gallery badge in top right */}
          <div style={{display:'flex',justifyContent:'flex-end',marginBottom:'-8px'}}>
            <button className="btn btn-ghost btn-sm" onClick={() => setActiveTab('gallery')}
              style={{display:'flex',alignItems:'center',gap:'6px'}}>
              🖼️ Gallery
              {gallery.length > 0 && (
                <span style={{
                  background:'var(--accent)',color:'#fff',
                  borderRadius:'10px',padding:'1px 7px',fontSize:'11px',fontWeight:'700',
                }}>{gallery.length}</span>
              )}
            </button>
          </div>

          {/* Page content */}
          <div key={activeTab}>
            {PAGES[activeTab]}
          </div>
        </main>
      </div>
    </>
  );
}
