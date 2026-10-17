import { useState, useEffect } from 'react'
import { Header } from './components/Header'
import { UploadZone } from './components/UploadZone'
import { VideoPlayer } from './components/VideoPlayer'
import { ViolationsList } from './components/ViolationsList'
import { JobStatusTracker } from './components/JobStatusTracker'
import { EvidenceViewer } from './components/EvidenceViewer'
import { RulesDrawer } from './components/RulesDrawer'
import { SettingsModal } from './components/SettingsModal'
import { ReportModal } from './components/ReportModal'
import { HistoryList } from './components/HistoryList'
import { INITIAL_HISTORY } from './data/mockData'
import { ApiService } from './services/api'
import type { JobDone, JobHistoryItem, Violation, JobStatus } from './types/api'

const HISTORY_STORAGE_KEY = 'sana_cv_job_history'

export function App() {
  const [history, setHistory] = useState<JobHistoryItem[]>(() => {
    try {
      const stored = localStorage.getItem(HISTORY_STORAGE_KEY)
      return stored ? JSON.parse(stored) : INITIAL_HISTORY
    } catch {
      return INITIAL_HISTORY
    }
  })

  // Start with the first case loaded for instant visual delight!
  const [activeJobId, setActiveJobId] = useState<string>(INITIAL_HISTORY[0].jobId)
  const [currentJobData, setCurrentJobData] = useState<JobDone | null>(INITIAL_HISTORY[0].jobData || null)
  const [currentFileName, setCurrentFileName] = useState<string>(INITIAL_HISTORY[0].fileName)
  const [currentVideoUrl, setCurrentVideoUrl] = useState<string | undefined>(undefined)
  const [jobStatus, setJobStatus] = useState<JobStatus>('done')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Interactive focus state
  const [selectedTimecode, setSelectedTimecode] = useState<number | null>(null)
  const [inspectingViolation, setInspectingViolation] = useState<Violation | null>(null)

  // Modals state
  const [isRulesOpen, setIsRulesOpen] = useState(false)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [isReportOpen, setIsReportOpen] = useState(false)

  // Persist history
  useEffect(() => {
    try {
      localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history))
    } catch (e) {
      console.error('Failed to save history to localStorage', e)
    }
  }, [history])

  // Handle uploading real video or sending to backend
  const handleFileSelected = async (file: File) => {
    const videoUrl = URL.createObjectURL(file)
    setCurrentVideoUrl(videoUrl)
    setCurrentFileName(file.name)
    setErrorMessage(null)
    setJobStatus('uploading')

    try {
      const { job_id } = await ApiService.uploadVideo(file)
      setActiveJobId(job_id)
      setJobStatus('processing')

      // Poll until done or failed
      const startTime = Date.now()
      const pollTimer = setInterval(async () => {
        const elapsedSec = (Date.now() - startTime) / 1000
        try {
          const resp = await ApiService.pollJob(job_id, elapsedSec)

          if (resp.status === 'done') {
            clearInterval(pollTimer)
            setCurrentJobData(resp)
            setJobStatus('done')

            // Add to history
            const newHistoryItem: JobHistoryItem = {
              id: `hist_${Date.now()}`,
              jobId: resp.job_id,
              createdAt: Date.now(),
              fileName: file.name,
              fileSizeBytes: file.size,
              videoUrl,
              status: 'done',
              verdict: resp.verdict,
              violationsCount: resp.violations.length,
              jobData: resp,
            }
            setHistory((prev) => [newHistoryItem, ...prev])
          } else if (resp.status === 'failed') {
            clearInterval(pollTimer)
            setErrorMessage(resp.error || 'Ошибка обработки видео')
            setJobStatus('failed')
          }
        } catch (err: unknown) {
          clearInterval(pollTimer)
          const msg = err instanceof Error ? err.message : 'Ошибка опроса задачи'
          setErrorMessage(msg)
          setJobStatus('failed')
        }
      }, 1500)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Ошибка отправки файла на бэкенд'
      setErrorMessage(msg)
      setJobStatus('failed')
    }
  }

  // Handle selecting mock scenarios
  const handleSelectMockScenario = (scenarioData: JobDone, fileName: string) => {
    setCurrentFileName(fileName)
    setCurrentVideoUrl(undefined)
    setActiveJobId(scenarioData.job_id)
    setJobStatus('processing')
    setErrorMessage(null)

    // Simulate realistic 3-second pipeline execution
    setTimeout(() => {
      setCurrentJobData(scenarioData)
      setJobStatus('done')

      // Add to history if not existing
      const existing = history.find((h) => h.jobId === scenarioData.job_id)
      if (!existing) {
        const newHist: JobHistoryItem = {
          id: `hist_${Date.now()}`,
          jobId: scenarioData.job_id,
          createdAt: Date.now(),
          fileName,
          fileSizeBytes: 34 * 1024 * 1024,
          status: 'done',
          verdict: scenarioData.verdict,
          violationsCount: scenarioData.violations.length,
          jobData: scenarioData,
        }
        setHistory((prev) => [newHist, ...prev])
      }
    }, 2500)
  }

  // Switch to an existing history item
  const handleSelectHistoryItem = (item: JobHistoryItem) => {
    setActiveJobId(item.jobId)
    setCurrentFileName(item.fileName)
    setCurrentVideoUrl(item.videoUrl)
    if (item.jobData) {
      setCurrentJobData(item.jobData)
      setJobStatus('done')
    }
  }

  const handleClearHistory = () => {
    setHistory([])
    localStorage.removeItem(HISTORY_STORAGE_KEY)
  }

  return (
    <div className="app-container">
      {/* Top Header */}
      <Header
        onOpenRules={() => setIsRulesOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenReport={() => setIsReportOpen(true)}
        history={history}
      />

      {/* Error Banner */}
      {errorMessage && (
        <div style={{
          background: 'rgba(244, 63, 94, 0.15)',
          border: '1px solid rgba(244, 63, 94, 0.4)',
          borderRadius: 'var(--radius-md)',
          padding: '1rem 1.25rem',
          color: '#fda4af',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div>
            <strong>Ошибка пайплайна: </strong> {errorMessage}
          </div>
          <button onClick={() => setErrorMessage(null)} className="btn-secondary" style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}>
            Закрыть
          </button>
        </div>
      )}

      {/* Active Processing Tracker */}
      {jobStatus === 'processing' && (
        <JobStatusTracker
          jobId={activeJobId}
          fileName={currentFileName}
          onCancel={() => setJobStatus('idle')}
        />
      )}

      {/* Main Studio Workspace */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(0, 1.15fr) minmax(0, 0.85fr)',
        gap: '1.5rem',
        alignItems: 'start',
      }}>
        {/* Left Column: Video Studio & Uploader */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <VideoPlayer
            videoUrl={currentVideoUrl}
            violations={currentJobData?.violations || []}
            selectedTimecode={selectedTimecode}
            onSeekViolation={(tc) => setSelectedTimecode(tc)}
            onInspectEvidence={(v) => setInspectingViolation(v)}
          />

          <UploadZone
            onFileSelected={handleFileSelected}
            onSelectMockScenario={handleSelectMockScenario}
            isUploading={jobStatus === 'uploading' || jobStatus === 'processing'}
          />
        </div>

        {/* Right Column: Violations & Compliance Verdict */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {currentJobData ? (
            <ViolationsList
              verdict={currentJobData.verdict}
              violations={currentJobData.violations}
              onSelectTimecode={(tc) => setSelectedTimecode(tc)}
              onInspectEvidence={(v) => setInspectingViolation(v)}
            />
          ) : (
            <div className="glass-panel" style={{ padding: '3rem 2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              Выберите сценарий или загрузите видеофайл для отображения вердикта и инцидентов.
            </div>
          )}
        </div>
      </div>

      {/* History Strip */}
      <HistoryList
        history={history}
        activeJobId={activeJobId}
        onSelectJob={handleSelectHistoryItem}
        onClearHistory={handleClearHistory}
      />

      {/* Evidence Lightbox Modal */}
      <EvidenceViewer
        violation={inspectingViolation}
        onClose={() => setInspectingViolation(null)}
      />

      {/* Rules & Legal Norms Drawer */}
      <RulesDrawer
        isOpen={isRulesOpen}
        onClose={() => setIsRulesOpen(false)}
      />

      {/* Connection & Mode Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSettingsSaved={() => {}}
      />

      {/* Official Audit Report Modal */}
      <ReportModal
        jobData={currentJobData}
        fileName={currentFileName}
        isOpen={isReportOpen}
        onClose={() => setIsReportOpen(false)}
      />
    </div>
  )
}
export default App
