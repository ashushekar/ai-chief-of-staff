'use client';
import { useState, useEffect, useRef } from 'react';
import Sidebar from '@/components/Sidebar';

export default function Chat() {
  const [messages, setMessages] = useState([
    { role: 'ai', text: "I'm your Chief of Staff, powered by Gemini. I know your priorities, team, and how you communicate. What do you need help with?" }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const bottomRef = useRef(null);

  const SUGGESTIONS = [
    "What should I focus on this afternoon?",
    "Help me prepare for a regulator meeting",
    "Draft a Slack message about a deployment delay",
    "Should I accept this speaking invite?",
    "What patterns do you see in my priorities?",
  ];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function send(text) {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: msg }]);
    setLoading(true);

    try {
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, history }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setMessages(prev => [...prev, { role: 'ai', text: data.response }]);
      setHistory(data.history);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'ai', text: `Error: ${e.message}` }]);
    }
    setLoading(false);
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content" style={{ display: 'flex', flexDirection: 'column', height: '100vh', padding: '32px 32px 24px' }}>
        <div className="page-header" style={{ marginBottom: 20, flexShrink: 0 }}>
          <h1 className="page-title">Chat</h1>
          <p className="page-subtitle">Ask your Chief of Staff anything — decisions, prep, drafts, priorities</p>
        </div>

        <div className="chat-container" style={{ flex: 1, minHeight: 0 }}>
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                <div className={`message-avatar ${msg.role}`}>
                  {msg.role === 'ai' ? '✦' : 'A'}
                </div>
                <div className="message-bubble">
                  {msg.text.split('\n').map((line, j) => (
                    <span key={j}>{line}{j < msg.text.split('\n').length - 1 && <br />}</span>
                  ))}
                </div>
              </div>
            ))}
            {loading && (
              <div className="message ai">
                <div className="message-avatar ai">✦</div>
                <div className="message-bubble" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                  <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>Thinking...</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {messages.length <= 1 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
              {SUGGESTIONS.map(s => (
                <button key={s} className="btn btn-secondary btn-sm" onClick={() => send(s)}
                  style={{ fontSize: 12, borderRadius: 20 }}>
                  {s}
                </button>
              ))}
            </div>
          )}

          <div className="chat-input-row">
            <textarea
              className="chat-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask anything... (Enter to send, Shift+Enter for new line)"
              rows={1}
              style={{ overflow: 'hidden' }}
              onInput={e => {
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px';
              }}
            />
            <button className="btn btn-primary" onClick={() => send()} disabled={loading || !input.trim()}
              style={{ height: 48, width: 48, padding: 0, justifyContent: 'center', flexShrink: 0 }}>
              ▲
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
