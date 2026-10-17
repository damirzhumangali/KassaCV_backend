import React, { useState } from 'react'
import { X, Sliders, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react'
import { ApiService } from '../services/api'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
  onSettingsSaved: () => void
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  onSettingsSaved,
}) => {
  const [baseUrl, setBaseUrl] = useState(ApiService.getBaseUrl())
  const [apiKey, setApiKey] = useState(ApiService.getApiKey())
  const [isMockMode, setIsMockMode] = useState(ApiService.isMockMode())
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null)
  const [testing, setTesting] = useState(false)

  if (!isOpen) return null

  const handleTestConnection = async () => {
    setTesting(true)
    setTestResult(null)
    ApiService.setBaseUrl(baseUrl)
    ApiService.setApiKey(apiKey)
    ApiService.setMockMode(isMockMode)
    const result = await ApiService.checkHealth()
    setTestResult(result)
    setTesting(false)
  }

  const handleSave = () => {
    ApiService.setBaseUrl(baseUrl)
    ApiService.setApiKey(apiKey)
    ApiService.setMockMode(isMockMode)
    onSettingsSaved()
    onClose()
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(7, 11, 20, 0.8)',
        backdropFilter: 'blur(10px)',
        zIndex: 1200,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '520px',
          border: '1px solid var(--border-bright)',
          boxShadow: 'var(--shadow-glow-cyan)',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <Sliders size={20} color="var(--accent-cyan)" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>
              Параметры подключения к API
            </h3>
          </div>
          <button onClick={onClose} className="btn-secondary" style={{ padding: '0.35rem 0.6rem' }}>
            <X size={16} />
          </button>
        </div>

        {/* Form Body */}
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Mock Mode Toggle */}
          <div style={{
            background: 'rgba(6, 182, 212, 0.08)',
            border: '1px solid rgba(6, 182, 212, 0.25)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ffffff' }}>
                Демо-режим / Эмуляция пайплайна
              </span>
              <input
                type="checkbox"
                checked={isMockMode}
                onChange={(e) => setIsMockMode(e.target.checked)}
                style={{
                  width: '18px',
                  height: '18px',
                  accentColor: 'var(--accent-cyan)',
                  cursor: 'pointer',
                }}
              />
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
              Позволяет запускать полноценный анализ видео, исследовать таймлайны и кадры доказательств без запущенного локального Python/FastAPI сервера.
            </p>
          </div>

          {/* Base URL */}
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
              URL Бэкенда (FastAPI):
            </label>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="http://localhost:8000 (оставьте пустым для локального прокси)"
              disabled={isMockMode}
              style={{
                width: '100%',
                padding: '0.65rem 0.9rem',
                borderRadius: 'var(--radius-sm)',
                background: isMockMode ? 'rgba(255,255,255,0.02)' : 'rgba(12, 19, 34, 0.8)',
                border: '1px solid var(--border-subtle)',
                color: isMockMode ? 'var(--text-dim)' : '#ffffff',
                fontSize: '0.88rem',
              }}
            />
          </div>

          {/* API Key */}
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
              Заголовок X-API-Key:
            </label>
            <input
              type="text"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="secret_test_key"
              disabled={isMockMode}
              style={{
                width: '100%',
                padding: '0.65rem 0.9rem',
                borderRadius: 'var(--radius-sm)',
                background: isMockMode ? 'rgba(255,255,255,0.02)' : 'rgba(12, 19, 34, 0.8)',
                border: '1px solid var(--border-subtle)',
                color: isMockMode ? 'var(--text-dim)' : '#ffffff',
                fontSize: '0.88rem',
                fontFamily: 'var(--font-mono)',
              }}
            />
          </div>

          {/* Test Status feedback */}
          {testResult && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.65rem 0.9rem',
              borderRadius: 'var(--radius-sm)',
              background: testResult.ok ? 'rgba(16, 185, 129, 0.12)' : 'rgba(244, 63, 94, 0.12)',
              border: `1px solid ${testResult.ok ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
              color: testResult.ok ? 'var(--accent-emerald)' : 'var(--accent-rose)',
              fontSize: '0.82rem',
            }}>
              {testResult.ok ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
              <span>{testResult.message}</span>
            </div>
          )}

          {/* Action buttons */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.5rem' }}>
            <button
              onClick={handleTestConnection}
              className="btn-secondary"
              disabled={testing}
              style={{ padding: '0.55rem 0.95rem', fontSize: '0.82rem' }}
            >
              <RefreshCw size={14} className={testing ? 'spin-slow' : ''} />
              Проверить связь
            </button>

            <button
              onClick={handleSave}
              className="btn-primary"
              style={{ padding: '0.55rem 1.4rem', fontSize: '0.88rem' }}
            >
              Сохранить
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
