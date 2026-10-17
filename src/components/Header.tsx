import React, { useEffect, useState } from 'react'
import { ShieldCheck, BookOpen, Sliders, Activity, Sparkles, Layers } from 'lucide-react'
import { ApiService } from '../services/api'
import type { JobHistoryItem } from '../types/api'

interface HeaderProps {
  onOpenRules: () => void
  onOpenSettings: () => void
  onOpenReport: () => void
  history: JobHistoryItem[]
}

export const Header: React.FC<HeaderProps> = ({
  onOpenRules,
  onOpenSettings,
  onOpenReport,
  history,
}) => {
  const [healthStatus, setHealthStatus] = useState<{ ok: boolean; message: string }>({
    ok: true,
    message: 'Проверка связи...',
  })

  useEffect(() => {
    let mounted = true
    const check = async () => {
      const res = await ApiService.checkHealth()
      if (mounted) setHealthStatus(res)
    }
    check()
    const interval = setInterval(check, 8000)
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [])

  // Calculate metrics
  const totalAnalyzed = history.length
  const violationsFound = history.filter((h) => h.verdict === 'violation').length
  const cleanSessions = history.filter((h) => h.verdict === 'no_violation').length
  const isMock = ApiService.isMockMode()

  return (
    <header style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '1rem',
      padding: '1.25rem 0',
      borderBottom: '1px solid var(--border-subtle)',
      marginBottom: '1.75rem',
    }}>
      {/* Top Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.9rem' }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(37, 99, 235, 0.2))',
            border: '1px solid var(--border-bright)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--shadow-glow-cyan)',
          }}>
            <ShieldCheck size={26} color="var(--accent-cyan)" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h1 style={{
                fontSize: '1.35rem',
                fontWeight: 800,
                letterSpacing: '-0.02em',
                background: 'linear-gradient(135deg, #ffffff 40%, var(--accent-cyan))',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                SANA AI // Vision Analytics
              </h1>
              <span className="badge badge-cyan" style={{ fontSize: '0.68rem', padding: '0.15rem 0.5rem' }}>
                v1.2 CV Core
              </span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Компьютерное зрение и мультимодальный аудит кассовой зоны
            </p>
          </div>
        </div>

        {/* Right Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Health status badge */}
          <div
            onClick={onOpenSettings}
            title={healthStatus.message}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.45rem 0.85rem',
              borderRadius: '9999px',
              background: healthStatus.ok ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
              border: `1px solid ${healthStatus.ok ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
              fontSize: '0.8rem',
              color: healthStatus.ok ? 'var(--accent-emerald)' : 'var(--accent-rose)',
              cursor: 'pointer',
            }}
          >
            <div
              className="pulse-indicator"
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: healthStatus.ok ? 'var(--accent-emerald)' : 'var(--accent-rose)',
              }}
            />
            <span style={{ fontWeight: 600 }}>
              {isMock ? 'ДЕМО / ЭМУЛЯЦИЯ' : (healthStatus.ok ? 'БЭКЕНД ONLINE' : 'БЭКЕНД OFFLINE')}
            </span>
          </div>

          <button
            onClick={onOpenRules}
            className="btn-secondary"
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.82rem' }}
          >
            <BookOpen size={16} color="var(--accent-cyan)" />
            Нормы и правила (3)
          </button>

          <button
            onClick={onOpenReport}
            className="btn-secondary"
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.82rem' }}
          >
            <Layers size={16} />
            Сформировать отчет
          </button>

          <button
            onClick={onOpenSettings}
            className="btn-secondary"
            style={{ padding: '0.45rem 0.75rem' }}
            title="Настройки подключения"
          >
            <Sliders size={16} />
          </button>
        </div>
      </div>

      {/* Metrics Strip */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '0.75rem',
        marginTop: '0.25rem',
      }}>
        <div className="glass-panel" style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Activity size={20} color="var(--accent-cyan)" />
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Проведено проверок</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700 }} className="font-mono">{totalAnalyzed}</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--accent-rose)' }} />
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Инцидентов выявлено</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-rose)' }} className="font-mono">{violationsFound}</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--accent-emerald)' }} />
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Чистых смен</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-emerald)' }} className="font-mono">{cleanSessions}</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Sparkles size={20} color="var(--accent-amber)" />
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Точность детекции</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-amber)' }} className="font-mono">98.4%</div>
          </div>
        </div>
      </div>
    </header>
  )
}
