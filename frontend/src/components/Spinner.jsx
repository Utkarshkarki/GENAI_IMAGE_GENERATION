// src/components/Spinner.jsx
export default function Spinner({ text = 'Processing…' }) {
  return (
    <div className="spinner-wrap">
      <div style={{position:'relative',width:'60px',height:'60px'}}>
        <div className="spinner" />
        <div style={{
          position:'absolute',inset:0,display:'flex',alignItems:'center',justifyContent:'center',
          fontSize:'20px'
        }}>✦</div>
      </div>
      <p className="spinner-text">{text}</p>
      <p style={{fontSize:'12px',color:'var(--text-muted)'}}>This may take a few seconds…</p>
    </div>
  );
}
