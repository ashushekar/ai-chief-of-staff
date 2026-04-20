'use client';
import { useState, useRef, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';

function parseTriage(text) {
  if (!text) return { p0: [], p1: [], p2: [], archived: [], calendar: [], note: '' };
  const sections = { p0: [], p1: [], p2: [], archived: [], calendar: [], note: '' };
  const lines = text.split('\n');
  let section = null;
  for (const raw of lines) {
    const line = raw.trim();
    if (/P0.*Act Now/i.test(line)) { section = 'p0'; continue; }
    if (/P1.*Act Today/i.test(line)) { section = 'p1'; continue; }
    if (/P2.*Radar/i.test(line)) { section = 'p2'; continue; }
    if (/Archived/i.test(line)) { section = 'archived'; continue; }
    if (/Calendar/i.test(line)) { section = 'calendar'; continue; }
    if (/Chief of Staff Note/i.test(line)) { section = 'note'; continue; }
    if (line.startsWith('•') || line.startsWith('-') || line.startsWith('*')) {
      const content = line.replace(/^[•\-\*]\s*/, '');
      if (section === 'note') sections.note = content;
      else if (section && sections[section]) sections[section].push(content);
    } else if (section === 'calendar' && line.match(/^\d{1,2}:/)) {
      sections.calendar.push(line);
    }
  }
  return sections;
}

function PriorityCard({ item, level, onReply }) {
  const parts = item.split('|').map(s => s.trim());
  const sender = parts[0] || '';
  const subject = parts[1] || '';
  const summary = parts[2] || item;
  const action = parts[3] || '';

  return (
    <div className={`priority-card ${level}`}>
      <div className="row-between" style={{ marginBottom: 8 }}>
        <span className={`priority-badge ${level}`}>{level.toUpperCase()}</span>
        {onReply && (
          <button className="btn btn-ghost btn-sm" onClick={() => onReply(item)}>
            Draft reply →
          </button>
        )}
      </div>
      {sender && <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)', marginBottom: 4 }}>{sender}</div>}
      {subject && <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 6 }}>{subject}</div>}
      <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6 }}>{summary}</div>
      {action && (
        <div style={{ marginTop: 10, fontSize: 11, color: 'var(--cyan)', fontWeight: 600 }}>
          → {action.replace(/^Suggested action:\s*/i, '')}
        </div>
      )}
    </div>
  );
}

export default function Triage() {
  const [loading, setLoading] = useState(false);
  const [demo, setDemo] = useState(false);
  const [result, setResult] = useState(null);
  const [raw, setRaw] = useState('');
  const [view, setView] = useState('cards');
  const [error, setError] = useState('');

  async function runTriage() {
    setLoading(true); setError(''); setResult(null); setRaw('');
    try {
      const res = await fetch('http://localhost:8000/api/triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ demo }),
      });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail); }
      const data = await res.json();
      setRaw(data.brief);
      setResult(parseTriage(data.brief));
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }

  function goToReply(context) {
    localStorage.setItem('cos_reply_context', context);
    window.location.href = '/reply';
  }

  const parsed = result;

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <div className="row-between">
            <div>
              <h1 className="page-title">Morning Triage</h1>
              <p className="page-subtitle">Prioritised inbox + calendar brief, powered by Gemini 2.5 Flash</p>
            </div>
            <div className="row" style={{ gap: 10 }}>
              <label className="row" style={{ gap: 8, cursor: 'pointer', fontSize: 13, color: 'var(--text-secondary)' }}>
                <input type="checkbox" checked={demo} onChange={e => setDemo(e.target.checked)}
                  style={{ accentColor: 'var(--cyan)' }} />
                Demo mode
              </label>
              <button className="btn btn-primary" onClick={runTriage} disabled={loading}>
                {loading ? <><span className="spinner" /> Analysing...</> : <><span>⬡</span> Run Triage</>}
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div style={{ background: 'var(--red-dim)', border: '1px solid rgba(255,71,87,0.3)', borderRadius: 'var(--radius-md)', padding: '14px 18px', marginBottom: 20, color: 'var(--red)', fontSize: 13 }}>
            {error}
          </div>
        )}

        {!result && !loading && (
          <div className="empty-state">
            <div className="empty-state-icon">⬡</div>
            <div className="empty-state-title">Ready to triage</div>
            <div className="empty-state-text">Click Run Triage to analyse your Gmail and Calendar with Gemini. Use demo mode to test without Gmail access.</div>
            <button className="btn btn-primary" onClick={runTriage}>Run Triage</button>
          </div>
        )}

        {loading && (
          <div className="card card-accent" style={{ textAlign: 'center', padding: '48px 24px' }}>
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
              <div className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
            </div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>Gemini is reading your inbox...</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Fetching emails, calendar, loading context files</div>
          </div>
        )}

        {parsed && (
          <>
            <div className="row-between" style={{ marginBottom: 20 }}>
              <div className="tabs">
                <button className={`tab ${view === 'cards' ? 'active' : ''}`} onClick={() => setView('cards')}>Cards</button>
                <button className={`tab ${view === 'raw' ? 'active' : ''}`} onClick={() => setView('raw')}>Raw</button>
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                {parsed.p0.length} P0 · {parsed.p1.length} P1 · {parsed.p2.length} P2 · {parsed.archived.length} archived
              </div>
            </div>

            {view === 'cards' ? (
              <div className="stack">
                {parsed.p0.length > 0 && (
                  <div>
                    <p className="section-title" style={{ color: 'var(--p0-color)' }}>P0 — Act Now</p>
                    <div className="stack">
                      {parsed.p0.map((item, i) => <PriorityCard key={i} item={item} level="p0" onReply={goToReply} />)}
                    </div>
                  </div>
                )}
                {parsed.p1.length > 0 && (
                  <div>
                    <p className="section-title" style={{ color: 'var(--p1-color)', marginTop: 16 }}>P1 — Act Today</p>
                    <div className="stack">
                      {parsed.p1.map((item, i) => <PriorityCard key={i} item={item} level="p1" onReply={goToReply} />)}
                    </div>
                  </div>
                )}
                {parsed.p2.length > 0 && (
                  <div>
                    <p className="section-title" style={{ color: 'var(--p2-color)', marginTop: 16 }}>P2 — On My Radar</p>
                    <div className="stack">
                      {parsed.p2.map((item, i) => <PriorityCard key={i} item={item} level="p2" />)}
                    </div>
                  </div>
                )}
                {parsed.calendar.length > 0 && (
                  <div>
                    <p className="section-title" style={{ marginTop: 16 }}>Today's Calendar</p>
                    <div className="cal-strip">
                      {parsed.calendar.map((ev, i) => {
                        const match = ev.match(/^(\d{1,2}:\d{2}(?:\s*[AP]M)?)\s+(.+?)(?:\s*—\s*(.+))?$/i);
                        return (
                          <div key={i} className="cal-event">
                            <div className="cal-time">{match?.[1] || '—'}</div>
                            <div>
                              <div className="cal-title">{match?.[2] || ev}</div>
                              {match?.[3] && <div className="cal-note">{match[3]}</div>}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
                {parsed.archived.length > 0 && (
                  <div>
                    <p className="section-title" style={{ marginTop: 16 }}>Archived</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                      {parsed.archived.map((item, i) => <span key={i} className="chip">{item}</span>)}
                    </div>
                  </div>
                )}
                {parsed.note && (
                  <div className="card" style={{ borderColor: 'var(--border-accent)', marginTop: 8 }}>
                    <span style={{ fontSize: 11, color: 'var(--cyan)', fontWeight: 700, letterSpacing: '0.08em' }}>CoS NOTE</span>
                    <p style={{ marginTop: 6, fontSize: 13, color: 'var(--text-secondary)' }}>{parsed.note}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="code-block mono" style={{ maxHeight: '70vh', overflow: 'auto' }}>{raw}</div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
