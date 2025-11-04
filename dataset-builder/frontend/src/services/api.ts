import axios from 'axios'
import type { UploadedFile, ValidationResponse, DataframeInfo } from '@/types/dataset'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000
})

export const apiService = {
  // Session
  async createSession(): Promise<string> {
    const response = await api.post<{ session_id: string }>('/files/session')
    return response.data.session_id
  },

  // File management
  async uploadFile(
    sessionId: string,
    file: File,
    fileType: 'data' | 'structure'
  ): Promise<UploadedFile> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('session_id', sessionId)
    formData.append('file_type', fileType)

    const response = await api.post<UploadedFile>('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    // Convert snake_case to camelCase
    return {
      id: response.data.id,
      filename: response.data.filename,
      size: response.data.size,
      detectedFormat: response.data.detected_format || null,
      fileType: fileType
    }
  },

  async deleteFile(sessionId: string, fileId: string): Promise<void> {
    await api.delete(`/files/${fileId}`, {
      params: { session_id: sessionId }
    })
  },

  async listFiles(sessionId: string): Promise<UploadedFile[]> {
    const response = await api.get<{ files: any[] }>('/files/list', {
      params: { session_id: sessionId }
    })
    return response.data.files.map(f => ({
      id: f.id,
      filename: f.filename,
      size: f.size,
      detectedFormat: f.detected_format || null,
      fileType: f.file_type
    }))
  },

  // Validation
  async validateState(stateData: any): Promise<ValidationResponse> {
    const response = await api.post<ValidationResponse>('/validate/state', stateData)
    return response.data
  },

  async validateProtein(proteinData: any): Promise<ValidationResponse> {
    const response = await api.post<ValidationResponse>('/validate/protein', proteinData)
    return response.data
  },

  async validateMetadata(metadataData: any): Promise<ValidationResponse> {
    const response = await api.post<ValidationResponse>('/validate/metadata', metadataData)
    return response.data
  },

  // Generation
  async generateJSON(datasetData: any): Promise<Blob> {
    const response = await api.post('/generate/json', datasetData, {
      responseType: 'blob'
    })
    return response.data
  },

  async generatePackage(datasetData: any): Promise<Blob> {
    const response = await api.post('/generate/package', datasetData, {
      responseType: 'blob'
    })
    return response.data
  },

  // Data
  async getDataframeInfo(sessionId: string, fileId: string): Promise<DataframeInfo> {
    const response = await api.get<DataframeInfo>(`/data/dataframe/${fileId}`, {
      params: { session_id: sessionId }
    })
    return {
      fileId: response.data.fileId,
      shape: response.data.shape,
      columns: response.data.columns
    }
  }
}

export default apiService
