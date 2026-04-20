'use client';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';

const FILES = [
  { key: 'my-priorities', label: 'My Priorities', icon: '◈', desc: 'Q2 goals, deadlines, what you\'re NOT doing' },
  { key: 'my-team', label: 'My Team', icon: '◇', desc: 'Stakeholders, SLAs, who to never miss' },
  { key: 'communication-style', label: 'Communication Style', icon: '◻', desc: 'Voice, banned phrases, sign-offs' },
];

export default function Settings() {
  const [selected, setSelected] = useState('my-priorities');
  const [content, setContent] = useState({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/context').then(r => r.json()).then(setContent).catch(() => {});
    fetch('http://localhost:8000/api/health').then(r => r.json()).then(setStatus).catch(() => {});
  }, []);

  async function save() {
    setSaving(true); setSaved(false);
    try {
      await fetch('http://localhost:8000/api/context', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file: selected, content: content[`${selected}.md`] || '' }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch {}
    setSaving(false);
  }

  const currentContent = content[`${selected}.md`] || '';

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Edit your context files — these power every triage, draft, and chat response</p>
        </div>

        {/* Connection status */}
        {status && (
          <div className="card" style={{ marginBottom: 28 }}>
            <p className="section-title" style={{ marginBottom: 16 }}>System Status</p>
            <div className="grid-3">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span className={`status-dot ${status.gemini_configured ? 'green' : 'red'}`} style={{ width: 8, height: 8 }} />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>Gemini API</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{status.gemini_configured ? 'Connected' : 'Not configured'}</div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span className={`status-dot ${status.gmail_connected ? 'green' : 'amber'}`} style={{ width: 8, height: 8 }} />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>Gmail</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{status.gmail_connected ? 'Live — OAuth active' : 'Demo mode — run setup_oauth.py'}</div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span className={`status-dot ${status.gcal_connected ? 'green' : 'amber'}`} style={{ width: 8, height: 8 }} />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>Calendar</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{status.gcal_connected ? 'Live — OAuth active' : 'Demo mode — run setup_oauth.py'}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Context editor */}
        <p className="section-title" style={{ marginBottom: 12 }}>Context Files</p>
        <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr', gap: 16, alignItems: 'start' }}>
          {/* File selector */}
          <div className="stack" style={{ gap: 6 }}>
            {FILES.map(({ key, label, icon, desc }) => (
              <div
                key={key}
                onClick={() => setSelected(key)}
                className={`card ${selected === key ? 'card-accent' : ''}`}
                style={{ cursor: 'pointer', padding: '14px 16px', transition: 'all 0.2s' }}
              >
                <div className="row" style={{ gap: 10, marginBottom: 4 }}>
                  <span style={{ color: selected === key ? 'var(--cyan)' : 'var(--text-muted)' }}>{icon}</span>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{label}</span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5, paddingLeft: 24 }}>{desc}</div>
              </div>
            ))}
          </div>

          {/* Editor */}
          <div className="stack">
            <div className="card card-accent">
              <div className="row-between" style={{ marginBottom: 12 }}>
                <div style={{ fontWeight: 600, fontSize: 14 }}>
                  {FILES.find(f => f.key === selected)?.label}
                  <span className="chip mono" style={{ marginLeft: 10, fontSize: 11 }}>{selected}.md</span>
                </div>
                <button className="btn btn-primary btn-sm" onClick={save} disabled={saving}>
                  {saving ? <><span className="spinner" style={{ width: 12, height: 12, borderWidth: 2 }} /> Saving...</>
                           : saved ? '✓ Saved' : 'Save'}
                </button>
              </div>
              <textarea
                className="textarea mono"
                value={currentContent}
                onChange={e => setContent(prev => ({ ...prev, [`${selected}.md`]: e.target.value }))}
                style={{ minHeight: 420, fontSize: 13, lineHeight: 1.7 }}
              />
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6 }}>
              Changes take effect immediately on the next triage, reply, or chat request.
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
