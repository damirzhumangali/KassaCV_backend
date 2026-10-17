import type { JobAccepted, JobResponse, JobDone } from '../types/api'
import { MOCK_SCENARIOS } from '../data/mockData'

const STORAGE_KEYS = {
  BASE_URL: 'sana_api_base_url',
  API_KEY: 'sana_api_key',
  MOCK_MODE: 'sana_mock_mode',
}

export class ApiService {
  private static getStored(key: string, defaultValue: string): string {
    return localStorage.getItem(key) ?? defaultValue
  }

  static getBaseUrl(): string {
    return this.getStored(STORAGE_KEYS.BASE_URL, '') // empty string means relative path with Vite proxy (/api)
  }

  static setBaseUrl(url: string): void {
    localStorage.setItem(STORAGE_KEYS.BASE_URL, url.replace(/\/+$/, ''))
  }

  static getApiKey(): string {
    return this.getStored(STORAGE_KEYS.API_KEY, 'secret_test_key')
  }

  static setApiKey(key: string): void {
    localStorage.setItem(STORAGE_KEYS.API_KEY, key)
  }

  static isMockMode(): boolean {
    const val = localStorage.getItem(STORAGE_KEYS.MOCK_MODE)
    // Default to mock mode true if not configured yet, to guarantee immediate out-of-the-box working experience!
    return val === null ? true : val === 'true'
  }

  static setMockMode(enabled: boolean): void {
    localStorage.setItem(STORAGE_KEYS.MOCK_MODE, String(enabled))
  }

  static async checkHealth(): Promise<{ ok: boolean; message: string }> {
    if (this.isMockMode()) {
      return { ok: true, message: 'Демо-режим (эмуляция бэкенда активна)' }
    }
    const base = this.getBaseUrl()
    const target = base ? `${base}/health` : '/health'
    try {
      const res = await fetch(target, { method: 'GET', signal: AbortSignal.timeout(3000) })
      if (res.ok) {
        return { ok: true, message: 'FastAPI Backend подключен' }
      }
      return { ok: false, message: `Ошибка статуса: ${res.status}` }
    } catch {
      return { ok: false, message: 'Бэкенд недоступен на localhost:8000' }
    }
  }

  static async uploadVideo(file: File): Promise<JobAccepted> {
    if (this.isMockMode()) {
      // Return a simulated job ID based on timestamp
      await new Promise((res) => setTimeout(res, 800))
      return { job_id: `job_sim_${Date.now()}` }
    }

    const base = this.getBaseUrl()
    const url = base ? `${base}/api/v1/analyze` : '/api/v1/analyze'
    const formData = new FormData()
    formData.append('file', file)

    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'X-API-Key': this.getApiKey(),
      },
      body: formData,
    })

    if (!res.ok) {
      const errorText = await res.text()
      throw new Error(`Ошибка загрузки (${res.status}): ${errorText || res.statusText}`)
    }

    return (await res.json()) as JobAccepted
  }

  static async pollJob(jobId: string, elapsedSec: number): Promise<JobResponse> {
    if (this.isMockMode() || jobId.startsWith('job_mock_') || jobId.startsWith('job_sim_')) {
      // Simulate pipeline processing for ~6-8 seconds
      if (elapsedSec < 6) {
        return { job_id: jobId, status: 'processing' }
      }

      // If simulated, select a scenario based on jobId or default
      const scenario = MOCK_SCENARIOS.find((s) => s.data.job_id === jobId) || MOCK_SCENARIOS[0]
      const result: JobDone = {
        ...scenario.data,
        job_id: jobId,
      }
      return result
    }

    const base = this.getBaseUrl()
    const url = base ? `${base}/api/v1/jobs/${jobId}` : `/api/v1/jobs/${jobId}`

    const res = await fetch(url, {
      method: 'GET',
      headers: {
        'X-API-Key': this.getApiKey(),
      },
    })

    if (!res.ok) {
      if (res.status === 404) {
        throw new Error('Задача не найдена на сервере')
      }
      const errorText = await res.text()
      throw new Error(`Ошибка запроса (${res.status}): ${errorText || res.statusText}`)
    }

    return (await res.json()) as JobResponse
  }
}
