// src/components/UploadZone.jsx
import { useRef, useState } from 'react';

export default function UploadZone({ onFile, accept = 'image/*', label = 'Drop an image or click to upload', preview = true }) {
  const inputRef = useRef();
  const [drag, setDrag] = useState(false);
  const [img, setImg] = useState(null);

  function handle(file) {
    if (!file || !file.type.startsWith('image/')) return;
    if (preview) setImg(URL.createObjectURL(file));
    onFile(file);
  }

  return (
    <div
      className={`upload-zone${drag ? ' drag-over' : ''}`}
      onClick={() => inputRef.current.click()}
      onDragOver={e => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={e => { e.preventDefault(); setDrag(false); handle(e.dataTransfer.files[0]); }}
    >
      <input ref={inputRef} type="file" accept={accept} style={{display:'none'}}
        onChange={e => handle(e.target.files[0])} />
      {img ? (
        <img src={img} alt="preview" style={{maxHeight:'200px',borderRadius:'8px',objectFit:'contain'}} />
      ) : (
        <>
          <div className="upload-icon">📁</div>
          <p className="upload-text">{label}</p>
          <p className="upload-subtext">PNG, JPG, JPEG supported</p>
        </>
      )}
    </div>
  );
}
