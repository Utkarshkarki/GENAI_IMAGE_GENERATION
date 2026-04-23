// src/pages/AgentPage.jsx
import { useState, useRef, useEffect } from 'react';
import { agentParse, agentAnswer, agentExecute } from '../api';
import UploadZone from '../components/UploadZone';
import Spinner from '../components/Spinner';

const PRESETS = [
  { label: '🛍️ Amazon Ready', text: 'Create a white-background packshot then add a natural shadow' },
  { label: '📱 Social Media Kit', text: 'Generate 4 lifestyle shots in different scene placements' },
  { label: '🎯 Ad Creative', text: 'Create a lifestyle shot with a coffee shop background' },
];

const SERVICE_LABELS = {
  generate_image: '🎨 Generate Image',
  lifestyle_shot_by_text: '🌄 Lifestyle Shot (text)',
  lifestyle_shot_by_image: '🌄 Lifestyle Shot (image)',
  add_shadow: '🌑 Add Shadow',
  create_packshot: '📦 Create Packshot',
  generative_fill: '🖌️ Generative Fill',
  erase_foreground: '🧹 Erase Foreground',
};

export default function AgentPage({ addToGallery, ollamaModel, ollamaUrl }) {
  const [file, setFile] = useState(null);
  const [input, setInput] = useState('');
  const [history, setHistory] = useState([]);
  const [pendingPlan, setPendingPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [showPlan, setShowPlan] = useState(true);
  const threadRef = useRef(null);

  useEffect(() => {
    if (threadRef.current) threadRef.current.scrollTop = threadRef.current.scrollHeight;
  }, [history]);

  function addMsg(role, content, images = []) {
    setHistory(h => [...h, { role, content, images }]);
  }

  async function handleSend(text) {
    const msg = text || input;
    if (!msg.trim()) return;
    setInput('');
    addMsg('user', msg);
    setLoading(true);
    try {
      const res = await agentParse({
        user_text: msg, image_provided: !!file,
        model: ollamaModel, ollama_url: ollamaUrl,
      });
      if (res.type === 'question' || !res.plan) {
        const ans = await agentAnswer({ user_text: msg, history, model: ollamaModel, ollama_url: ollamaUrl });
        addMsg('assistant', ans.answer);
      } else {
        const usedLlm = res.used_llm;
        addMsg('assistant',
          `🗺️ Planned **${res.plan.steps.length} step(s)** ${usedLlm ? '*(via Ollama LLM)*' : '*(keyword fallback)*'}. Review and confirm below.`);
        setPendingPlan(res.plan);
        setShowPlan(true);
      }
    } catch(e) { addMsg('assistant', `⚠️ Error: ${e.message}`); }
    finally { setLoading(false); }
  }

  async function handleExecute() {
    if (!pendingPlan) return;
    setExecuting(true);
    try {
      const res = await agentExecute(pendingPlan, file, { model: ollamaModel, ollama_url: ollamaUrl });
      const urls = res.result_urls || [];
      if (urls.length > 0) {
        addMsg('assistant', `✅ Done! Generated ${urls.length} image(s).`, urls);
        urls.forEach(u => addToGallery(u, 'AI Agent'));
      } else {
        addMsg('assistant', '⚠️ The agent ran but produced no results. Check your API key and try again.');
      }
    } catch(e) { addMsg('assistant', `⚠️ Execution error: ${e.message}`); }
    finally { setExecuting(false); setPendingPlan(null); }
  }

  return (
    <div className="form-col page-enter">
      <div className="section-header">
        <div><h2>🤖 AI Agent</h2>
          <p>Describe any image task in plain English — the agent plans and runs it automatically</p></div>
      </div>

      {/* Quick presets */}
      <div className="glass-elevated" style={{padding:'16px 20px'}}>
        <p className="field-label" style={{marginBottom:'10px'}}>⚡ Quick Presets</p>
        <div className="preset-grid">
          {PRESETS.map(p => (
            <button key={p.label} className="preset-btn" onClick={() => handleSend(p.text)}>{p.label}</button>
          ))}
        </div>
      </div>

      {/* Upload */}
      <div className="glass-elevated" style={{padding:'20px'}}>
        <p className="field-label" style={{marginBottom:'10px'}}>📸 Product Image (optional for text-only)</p>
        <UploadZone onFile={setFile} label="Upload your product image" />
      </div>

      {/* Chat thread */}
      <div className="glass-elevated" style={{padding:'20px',display:'flex',flexDirection:'column',gap:'16px'}}>
        <div className="chat-thread" ref={threadRef} style={{minHeight:'160px'}}>
          {history.length === 0 && (
            <div style={{textAlign:'center',padding:'32px',color:'var(--text-muted)',fontSize:'14px'}}>
              <div style={{fontSize:'32px',marginBottom:'8px'}}>🤖</div>
              Start by typing what you want or pick a quick preset above
            </div>
          )}
          {history.map((msg, i) => (
            <div key={i} className={`chat-bubble ${msg.role === 'user' ? 'user' : 'bot'}`}>
              <div className={`chat-avatar ${msg.role === 'user' ? 'user' : 'bot'}`}>
                {msg.role === 'user' ? '👤' : '🤖'}
              </div>
              <div style={{display:'flex',flexDirection:'column',gap:'8px',maxWidth:'100%'}}>
                <div className="chat-content">
                  {msg.content.split('\n').map((line, j) => <p key={j} style={{margin:0}}>{line}</p>)}
                </div>
                {msg.images && msg.images.length > 0 && (
                  <div className="chat-images">
                    {msg.images.map((url, j) => (
                      <img key={j} src={url} alt={`result ${j+1}`} />
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="chat-bubble bot">
              <div className="chat-avatar bot">🤖</div>
              <div className="chat-content">
                <div style={{display:'flex',gap:'4px'}}>
                  {[0,1,2].map(i=><span key={i} style={{width:'7px',height:'7px',borderRadius:'50%',background:'var(--accent)',animation:`pulse 1s ${i*0.15}s infinite`}} />)}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Pending plan */}
        {pendingPlan && !executing && (
          <div className="plan-preview">
            <div className="plan-header" onClick={() => setShowPlan(v => !v)}>
              📋 Planned {pendingPlan.steps.length} step(s) — click to {showPlan ? 'collapse' : 'expand'}
              <span style={{marginLeft:'auto'}}>{showPlan ? '▲' : '▼'}</span>
            </div>
            {showPlan && pendingPlan.steps.map((step, i) => (
              <div key={i} className="plan-step">
                <div className="plan-step-num">{i+1}</div>
                <div>
                  <div className="plan-step-name">{SERVICE_LABELS[step.service_name] || step.service_name}</div>
                  {step.use_previous_output && <div className="plan-step-params">↪ chains from previous step</div>}
                  {Object.keys(step.params).length > 0 && (
                    <div className="plan-step-params">{Object.entries(step.params).slice(0,4).map(([k,v])=>`${k}: ${v}`).join(' · ')}</div>
                  )}
                </div>
              </div>
            ))}
            <div className="plan-actions">
              <button id="agent-confirm-btn" className="btn btn-primary" onClick={handleExecute}>✅ Confirm &amp; Run</button>
              <button className="btn btn-ghost" onClick={() => { setPendingPlan(null); addMsg('assistant','Plan cancelled.'); }}>❌ Cancel</button>
            </div>
          </div>
        )}
        {executing && <Spinner text="Executing agent plan…" />}

        {/* Input */}
        <div style={{display:'flex',gap:'8px'}}>
          <input className="input" placeholder="Describe what you want…"
            value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key==='Enter' && !e.shiftKey && handleSend()}
            style={{flex:1}} />
          <button id="agent-send-btn" className="btn btn-primary" onClick={() => handleSend()} disabled={!input.trim() || loading}>Send</button>
        </div>
      </div>

      <style>{`@keyframes pulse{0%,100%{opacity:.3;transform:scale(.8)}50%{opacity:1;transform:scale(1)}}`}</style>
    </div>
  );
}
