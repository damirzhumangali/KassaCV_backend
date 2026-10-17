import React, { useRef, useState } from 'react'
import { UploadCloud, Film, PlayCircle, AlertCircle } from 'lucide-react'
import { MOCK_SCENARIOS } from '../data/mockData'
import type { JobDone } from '../types/api'

interface UploadZoneProps {
  onFileSelected: (file: File) => void
  onSelectMockScenario: (scenarioData: JobDone, fileName: string) => void
  isUploading: boolean
}

export const UploadZone: React.FC<UploadZoneProps> = ({
  onFileSelected,
  onSelectMockScenario,
  isUploading,
}) => {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const validateAndProcessFile = (file: File) => {
    setError(null)
    const validExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    const hasValidExt = validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext))

    if (!file.type.startsWith('video/') && !hasValidExt) {
      setError('Поддерживаются только видеофайлы: MP4, AVI, MOV, MKV, WebM')
      return
    }

    if (file.size > 500 * 1024 * 1024) {
      setError('Размер файла превышает лимит 500 МБ')
      return
    }

    onFileSelected(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndProcessFile(e.dataTransfer.files[0])
    }
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndProcessFile(e.target.files[0])
    }
  }

  return (
    <div className="glass-panel" style={{ padding: '1.75rem', position: 'relative' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
        <div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff' }}>
            Загрузка видеозаписи кассовой зоны
          </h2>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>
            Файл будет обработан пайплайном детекции, трекинга и мультимодального анализа нарушений
          </p>
        </div>
        <span className="badge badge-cyan">
          <Film size={12} />
          MP4 / MOV / AVI до 500 MB
        </span>
      </div>

      {error && (
        <div style={{
          background: 'rgba(244, 63, 94, 0.15)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          padding: '0.75rem 1rem',
          borderRadius: 'var(--radius-md)',
          color: '#fda4af',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.85rem',
          marginBottom: '1rem',
        }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${isDragging ? 'var(--accent-cyan)' : 'rgba(255, 255, 255, 0.15)'}`,
          borderRadius: 'var(--radius-lg)',
          padding: '2.5rem 1.5rem',
          textAlign: 'center',
          background: isDragging ? 'rgba(6, 182, 212, 0.06)' : 'rgba(12, 19, 34, 0.4)',
          cursor: isUploading ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease',
          marginBottom: '1.5rem',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="video/mp4,video/quicktime,video/x-msvideo,video/mkv,video/webm"
          style={{ display: 'none' }}
          onChange={handleFileInputChange}
          disabled={isUploading}
        />

        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          background: 'rgba(6, 182, 212, 0.1)',
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '1rem',
          color: 'var(--accent-cyan)',
        }}>
          <UploadCloud size={32} />
        </div>

        <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '0.35rem' }}>
          Перетащите видеофайл сюда или нажмите для выбора
        </h3>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          Анализатор автоматически разделит видео на кадры, распознает кассира, клиента и лоток ККМ
        </p>
      </div>

      {/* Preset Test Scenarios */}
      <div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          marginBottom: '0.75rem',
          fontSize: '0.85rem',
          fontWeight: 600,
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
        }}>
          <PlayCircle size={15} color="var(--accent-cyan)" />
          Или выберите готовый тестовый сценарий (Instant Demo):
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '0.75rem',
        }}>
          {MOCK_SCENARIOS.map((scen, idx) => (
            <button
              key={scen.id}
              onClick={() => onSelectMockScenario(scen.data, `sample_test_case_${idx + 1}.mp4`)}
              className="glass-panel"
              style={{
                padding: '0.9rem 1rem',
                textAlign: 'left',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(17, 26, 46, 0.6)',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-bright)'
                e.currentTarget.style.transform = 'translateY(-2px)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-subtle)'
                e.currentTarget.style.transform = 'translateY(0)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#ffffff' }}>
                  {scen.title}
                </span>
                <span className={`badge ${scen.data.verdict === 'violation' ? 'badge-rose' : 'badge-emerald'}`}>
                  {scen.data.verdict === 'violation' ? 'Инцидент' : 'Чисто'}
                </span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                {scen.description}
              </p>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
