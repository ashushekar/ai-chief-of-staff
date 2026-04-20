'use client';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';

export default function Dashboard() {
  const [status, setStatus] = useState(null);
  const [greeting, setGreeting] = useState('');
  const [time, setTime] = useState('');

  useEffect(() => {
    const hour = new Date().getHours();
    setGreeting(hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening');
    setTime(new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' }));
    fetch('http://localhost:8000/api/health').then(r => r.json()).then(setStatus).catch(() => {});
  }, []);

  const QUICK_ACTIONS = [
    { href: '/triage', icon: '⬡', label: 'Run Triage', desc: 'Prioritise your inbox + calendar', color: 'var(--cyan)' },
    { href: '/reply',  icon: '◻', label: 'Draft Reply', desc: 'Write an email in your voice',  color: 'var(--purple)' },
    { href: '/chat',   icon: '◇', label: 'Ask CoS',     desc: 'Get help with a decision',      color: 'var(--gold)' },
    { href: '/logs',   icon: '▤', label: 'Review Logs', desc: 'See patterns in your week',     color: 'var(--green)' },
  ];

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        {/* Header */}
        <div className="page-header">
          <div className="row-between">
            <div>
              <h1 className="page-title">
                {greeting}, <span className="gradient-text">Ashwin</span>
              </h1>
              <p className="page-subtitle">{time}</p>
            </div>
            <a href="/triage" className="btn btn-primary">
              <span>⬡</span> Run Morning Triage
            </a>
          </div>
        </div>

        {/* Status cards */}
        {status && (
          <div className="grid-3" style={{ marginBottom: 28 }}>
            <div className="stat-card">
              <div className="stat-value" style={{ color: status.gemini_configured ? 'var(--cyan)' : 'var(--red)' }}>
                {status.gemini_configured ? '✓' : '✗'}
              </div>
              <div className="stat-label">Gemini API</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: status.gmail_connected ? 'var(--green)' : 'var(--gold)' }}>
                {status.gmail_connected ? '✓' : '~'}
              </div>
              <div className="stat-label">Gmail {status.gmail_connected ? 'Live' : 'Demo mode'}</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: status.gcal_connected ? 'var(--green)' : 'var(--gold)' }}>
                {status.gcal_connected ? '✓' : '~'}
              </div>
              <div className="stat-label">Calendar {status.gcal_connected ? 'Live' : 'Demo mode'}</div>
            </div>
          </div>
        )}

        {/* Quick actions */}
        <p className="section-title">Quick Actions</p>
        <div className="grid-2" style={{ marginBottom: 32 }}>
          {QUICK_ACTIONS.map(({ href, icon, label, desc, color }) => (
            <a key={href} href={href} style={{ textDecoration: 'none' }}>
              <div className="card" style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 12,
                  background: `color-mix(in srgb, ${color} 15%, transparent)`,
                  border: `1px solid color-mix(in srgb, ${color} 30%, transparent)`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 20, flexShrink: 0, color,
                }}>
                  {icon}
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 2 }}>{label}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{desc}</div>
                </div>
              </div>
            </a>
          ))}
        </div>

        {/* How it works */}
        <p className="section-title">How It Works</p>
        <div className="card card-accent">
          <div style={{ display: 'flex', gap: 0, flexWrap: 'wrap' }}>
            {[
              { step: '01', title: 'Context', desc: 'Reads your priorities, team, and communication style' },
              { step: '02', title: 'Triage', desc: 'Fetches Gmail + Calendar and ranks by what actually matters' },
              { step: '03', title: 'Brief', desc: 'Returns P0 / P1 / P2 breakdown with calendar annotations' },
              { step: '04', title: 'Act', desc: 'Draft replies, prep for meetings, and ask follow-up questions' },
            ].map(({ step, title, desc }, i) => (
              <div key={step} style={{
                flex: '1 1 200px', padding: '16px 20px',
                borderRight: i < 3 ? '1px solid var(--border)' : 'none',
              }}>
                <div style={{ fontSize: 11, color: 'var(--cyan)', fontWeight: 700, letterSpacing: '0.1em', marginBottom: 8 }}>
                  STEP {step}
                </div>
                <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{title}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6 }}>{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
