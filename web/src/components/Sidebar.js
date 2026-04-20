'use client';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

const NAV = [
  { href: '/',          icon: '◈',  label: 'Dashboard'  },
  { href: '/triage',    icon: '⬡',  label: 'Triage'     },
  { href: '/reply',     icon: '◻',  label: 'Reply'      },
  { href: '/chat',      icon: '◇',  label: 'Chat'       },
  { href: '/logs',      icon: '▤',  label: 'Logs'       },
  { href: '/settings',  icon: '◎',  label: 'Settings'   },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [status, setStatus] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/health')
      .then(r => r.json())
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div style={{ fontSize: 22, marginBottom: 2 }}>✦</div>
        <span className="sidebar-logo-text">Chief of Staff</span>
        <span className="sidebar-logo-sub">Powered by Gemini</span>
      </div>

      <nav className="sidebar-nav">
        {NAV.map(({ href, icon, label }) => (
          <div
            key={href}
            className={`nav-item ${pathname === href ? 'active' : ''}`}
            onClick={() => router.push(href)}
          >
            <span className="nav-icon">{icon}</span>
            <span>{label}</span>
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        {status ? (
          <>
            <div className="status-row">
              <span className={`status-dot ${status.gemini_configured ? 'green' : 'red'}`} />
              Gemini {status.gemini_configured ? 'connected' : 'not configured'}
            </div>
            <div className="status-row">
              <span className={`status-dot ${status.gmail_connected ? 'green' : 'amber'}`} />
              Gmail {status.gmail_connected ? 'connected' : 'demo mode'}
            </div>
            <div className="status-row">
              <span className={`status-dot ${status.gcal_connected ? 'green' : 'amber'}`} />
              Calendar {status.gcal_connected ? 'connected' : 'demo mode'}
            </div>
          </>
        ) : (
          <div className="status-row">
            <span className="status-dot amber" />
            <span className="pulse">Connecting to API...</span>
          </div>
        )}
      </div>
    </aside>
  );
}
