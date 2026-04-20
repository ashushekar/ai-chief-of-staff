'use client';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';

export default function Reply() {
  const [emailContent, setEmailContent] = useState('');
  const [intent, setIntent] = useState('');
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const ctx = localStorage.getItem('cos_reply_context');
    if (ctx) { setEmailContent(ctx); localStorage.removeItem('cos_reply_context'); }
  }, []);

  async function generateDraft() {
    if (!emailContent.trim()) return;
    setLoading(true); setError(''); setDraft('');
    try {
      const res = await fetch('http://localhost:8000/api/reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_content: emailContent, intent }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setDraft(data.draft);
    } catch (e) { setError(e.message); }
    setLoading(false);
  }

  function copyDraft() {
    navigator.clipboard.writeText(draft);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const EXAMPLES = [
    "Accept the meeting but suggest a different time",
    "Decline politely, leave door open for next quarter",
    "Request more information before committing",
    "Confirm attendance and ask for agenda",
  ];

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <h1 className="page-title">Email Reply Drafter</h1>
          <p className="page-subtitle">Paste any email and get a draft in your voice — friendly, professional, under 150 words</p>
        </div>

        <div className="grid-2" style={{ alignItems: 'start', gap: 20 }}>
          {/* Input panel */}
          <div className="stack">
            <div className="card">
              <p className="section-title" style={{ marginBottom: 10 }}>Paste Email</p>
              <textarea
                className="textarea"
                value={emailContent}
                onChange={e => setEmailContent(e.target.value)}
                placeholder="Paste the email you want to reply to here..."
                style={{ minHeight: 200 }}
              />
            </div>

            <div className="card">
              <p className="section-title" style={{ marginBottom: 10 }}>Your Intent <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span></p>
              <input
                className="input"
                value={intent}
                onChange={e => setIntent(e.target.value)}
                placeholder="e.g. Accept but push back on timeline"
              />
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
                {EXAMPLES.map(ex => (
                  <button key={ex} className="btn btn-ghost btn-sm" onClick={() => setIntent(ex)}
                    style={{ fontSize: 11, borderRadius: 20, border: '1px solid var(--border)' }}>
                    {ex}
                  </button>
                ))}
              </div>
            </div>

            <button className="btn btn-primary" onClick={generateDraft} disabled={loading || !emailContent.trim()}
              style={{ width: '100%', justifyContent: 'center', padding: '13px' }}>
              {loading ? <><span className="spinner" /> Drafting...</> : '◻ Generate Draft'}
            </button>
          </div>

          {/* Output panel */}
          <div className="stack">
            {error && (
              <div style={{ background: 'var(--red-dim)', border: '1px solid rgba(255,71,87,0.3)', borderRadius: 'var(--radius-md)', padding: '14px 18px', color: 'var(--red)', fontSize: 13 }}>
                {error}
              </div>
            )}

            {!draft && !loading && (
              <div className="empty-state card" style={{ padding: '48px 24px' }}>
                <div className="empty-state-icon">◻</div>
                <div className="empty-state-title">Draft will appear here</div>
                <div className="empty-state-text">Paste an email and click Generate Draft. Gemini 2.5 Pro will write a reply in your voice.</div>
              </div>
            )}

            {loading && (
              <div className="card" style={{ padding: '48px 24px', textAlign: 'center' }}>
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 12 }}>
                  <div className="spinner" style={{ width: 28, height: 28, borderWidth: 3 }} />
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Gemini 2.5 Pro is drafting...</div>
              </div>
            )}

            {draft && (
              <div className="card card-accent">
                <div className="row-between" style={{ marginBottom: 16 }}>
                  <span className="section-title" style={{ margin: 0 }}>Draft Reply</span>
                  <div className="row" style={{ gap: 8 }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => setDraft('')}>Clear</button>
                    <button className="btn btn-secondary btn-sm" onClick={copyDraft}>
                      {copied ? '✓ Copied' : 'Copy'}
                    </button>
                  </div>
                </div>
                <div style={{ whiteSpace: 'pre-wrap', fontSize: 14, lineHeight: 1.8, color: 'var(--text-secondary)' }}>
                  {draft}
                </div>
                <div className="divider" />
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  Want a different tone? Update your intent above and regenerate.
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
