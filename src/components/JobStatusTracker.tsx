import React, { useEffect, useState } from 'react'
import { Loader2, CheckCircle2, Clock, Cpu } from 'lucide-react'
import { PIPELINE_STAGES } from '../data/rulesCatalog'

interface JobStatusTrackerProps {
  jobId: string
  fileName: string
  onCancel?: () => void
}

export const JobStatusTracker: React.FC<JobStatusTrackerProps> = ({
  jobId,
  fileName,
  onCancel,
}) => {
  const [elapsedSec, setElapsedSec] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSec((prev) => prev + 1)
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  // Approximate stage index based on elapsed time (or simulation)
  const currentStageIndex = Math.min(
    Math.floor(elapsedSec / 1.3),
    PIPELINE_STAGES.length - 1
  )

  return (
    <div className="glass-panel-glow animate-fade-in" style={{ padding: '2rem', marginBottom: '1.5rem' }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '1.5rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.9rem' }}>
          <div style={{
            width: '46px',
            height: '46px',
            borderRadius: '50%',
            background: 'rgba(6, 182, 212, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--accent-cyan)',
          }}>
            <Loader2 size={24} className="spin-slow" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>
                Нейросетевой анализ видеопотока
              </h3>
              <span className="badge badge-cyan font-mono">{jobId.slice(0, 16)}...</span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Обработка файла: <strong style={{ color: '#ffffff' }}>{fileName}</strong>
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            background: 'rgba(255, 255, 255, 0.05)',
            padding: '0.4rem 0.8rem',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.85rem',
          }}>
            <Clock size={16} color="var(--accent-cyan)" />
            <span className="font-mono">
              {String(Math.floor(elapsedSec / 60)).padStart(2, '0')}:
              {String(elapsedSec % 60).padStart(2, '0')}
            </span>
          </div>

          {onCancel && (
            <button onClick={onCancel} className="btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>
              Отмена
            </button>
          )}
        </div>
      </div>

      {/* Pipeline Steps Visualizer */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '0.75rem',
        marginTop: '1rem',
      }}>
        {PIPELINE_STAGES.map((stage, idx) => {
          const isDone = idx < currentStageIndex
          const isCurrent = idx === currentStageIndex

          return (
            <div
              key={stage.id}
              style={{
                background: isCurrent
                  ? 'rgba(6, 182, 212, 0.12)'
                  : isDone
                  ? 'rgba(16, 185, 129, 0.08)'
                  : 'rgba(255, 255, 255, 0.02)',
                border: `1px solid ${
                  isCurrent
                    ? 'var(--accent-cyan)'
                    : isDone
                    ? 'rgba(16, 185, 129, 0.3)'
                    : 'var(--border-subtle)'
                }`,
                borderRadius: 'var(--radius-md)',
                padding: '0.85rem 1rem',
                position: 'relative',
                transition: 'all 0.3s ease',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                <span style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  color: isCurrent ? 'var(--accent-cyan)' : isDone ? 'var(--accent-emerald)' : 'var(--text-dim)',
                }}>
                  {stage.label}
                </span>
                {isDone ? (
                  <CheckCircle2 size={16} color="var(--accent-emerald)" />
                ) : isCurrent ? (
                  <Cpu size={16} color="var(--accent-cyan)" className="pulse-indicator" />
                ) : (
                  <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--text-dim)' }} />
                )}
              </div>
              <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', lineHeight: 1.35 }}>
                {stage.description}
              </p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
