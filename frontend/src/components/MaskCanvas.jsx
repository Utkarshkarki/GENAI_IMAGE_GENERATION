// src/components/MaskCanvas.jsx
import { useEffect, useRef, useState } from 'react';

export default function MaskCanvas({ imageFile, onMaskReady }) {
  const canvasRef = useRef(null);
  const bgCanvasRef = useRef(null);
  const [brushSize, setBrushSize] = useState(24);
  const [drawing, setDrawing] = useState(false);
  const [imgDims, setImgDims] = useState({ w: 0, h: 0 });
  const lastPos = useRef(null);

  useEffect(() => {
    if (!imageFile) return;
    const url = URL.createObjectURL(imageFile);
    const img = new Image();
    img.onload = () => {
      const maxW = 700;
      const scale = Math.min(1, maxW / img.naturalWidth);
      const w = Math.round(img.naturalWidth * scale);
      const h = Math.round(img.naturalHeight * scale);
      setImgDims({ w, h });

      // Draw background image
      const bgCanvas = bgCanvasRef.current;
      bgCanvas.width = w; bgCanvas.height = h;
      bgCanvas.getContext('2d').drawImage(img, 0, 0, w, h);

      // Clear mask canvas
      const canvas = canvasRef.current;
      canvas.width = w; canvas.height = h;
      canvas.getContext('2d').clearRect(0, 0, w, h);

      URL.revokeObjectURL(url);
    };
    img.src = url;
  }, [imageFile]);

  function getPos(e) {
    const rect = canvasRef.current.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    const scaleX = canvasRef.current.width / rect.width;
    const scaleY = canvasRef.current.height / rect.height;
    return { x: (clientX - rect.left) * scaleX, y: (clientY - rect.top) * scaleY };
  }

  function startDraw(e) {
    e.preventDefault();
    setDrawing(true);
    const pos = getPos(e);
    lastPos.current = pos;
    drawAt(pos);
  }

  function drawAt(pos) {
    const ctx = canvasRef.current.getContext('2d');
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = 'rgba(255,255,255,1)';
    ctx.beginPath();
    if (lastPos.current) {
      ctx.moveTo(lastPos.current.x, lastPos.current.y);
      ctx.lineTo(pos.x, pos.y);
      ctx.strokeStyle = 'rgba(255,255,255,1)';
      ctx.lineWidth = brushSize;
      ctx.lineCap = 'round';
      ctx.stroke();
    }
    ctx.arc(pos.x, pos.y, brushSize / 2, 0, Math.PI * 2);
    ctx.fill();
  }

  function onMove(e) {
    if (!drawing) return;
    e.preventDefault();
    const pos = getPos(e);
    drawAt(pos);
    lastPos.current = pos;
  }

  function stopDraw() {
    setDrawing(false);
    lastPos.current = null;
  }

  function clearMask() {
    const ctx = canvasRef.current.getContext('2d');
    ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
  }

  function exportMask() {
    canvasRef.current.toBlob(blob => {
      if (onMaskReady) onMaskReady(blob);
    }, 'image/png');
  }

  return (
    <div className="form-col">
      <div className="canvas-toolbar">
        <div className="field" style={{flexDirection:'row',alignItems:'center',gap:'8px',flex:'none'}}>
          <label className="field-label" style={{whiteSpace:'nowrap'}}>Brush {brushSize}px</label>
          <input type="range" className="slider" min={4} max={80} value={brushSize}
            style={{'--val':`${((brushSize-4)/76)*100}%`}}
            onChange={e => setBrushSize(+e.target.value)} />
        </div>
        <button className="btn btn-ghost btn-xs" onClick={clearMask}>🗑 Clear</button>
        <button className="btn btn-primary btn-xs" onClick={exportMask}>✓ Use Mask</button>
      </div>
      <div className="canvas-wrap" style={{position:'relative', cursor:'crosshair'}}>
        {/* Background image */}
        <canvas ref={bgCanvasRef} style={{
          display:'block', width:'100%', height:'auto',
          position:'absolute', top:0, left:0, pointerEvents:'none',
        }} />
        {/* Mask draw layer */}
        <canvas
          ref={canvasRef}
          width={imgDims.w || 600} height={imgDims.h || 400}
          style={{
            display:'block', width:'100%', height:'auto',
            opacity:.55, mixBlendMode:'screen', position:'relative', zIndex:2,
          }}
          onMouseDown={startDraw} onMouseMove={onMove}
          onMouseUp={stopDraw} onMouseLeave={stopDraw}
          onTouchStart={startDraw} onTouchMove={onMove} onTouchEnd={stopDraw}
        />
      </div>
      {imgDims.w === 0 && (
        <div style={{textAlign:'center',padding:'40px',color:'var(--text-muted)',fontSize:'14px'}}>
          Upload an image to start painting your mask
        </div>
      )}
    </div>
  );
}
