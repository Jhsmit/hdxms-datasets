<template>
  <div class="step-content">
    <h2>Step 1: Upload Files</h2>
    <p>Upload your HDX-MS data files and structure file</p>

    <div class="upload-section">
      <h3>Data Files</h3>
      <div class="upload-area" @drop.prevent="handleDrop($event, 'data')" @dragover.prevent>
        <input
          type="file"
          ref="dataFileInput"
          @change="handleFileSelect($event, 'data')"
          multiple
          accept=".csv,.txt"
          style="display: none"
        />
        <p>Drag and drop data files here or</p>
        <button class="primary" @click="$refs.dataFileInput.click()">
          Browse Files
        </button>
      </div>

      <div v-if="store.dataFiles.length > 0" class="file-list">
        <div v-for="file in store.dataFiles" :key="file.id" class="file-item">
          <div class="file-info">
            <div class="file-details">
              <strong>{{ file.filename }}</strong>
              <span class="file-size">{{ formatFileSize(file.size) }}</span>
              <span v-if="file.detectedFormat" class="badge">{{ file.detectedFormat }}</span>
            </div>
            <div class="dataframe-info">
              <span v-if="getDataframeInfo(file.id) === 'loading'" class="loading-text">
                Loading dataframe...
              </span>
              <span v-else-if="getDataframeInfo(file.id) === 'error'" class="error-text">
                Failed to load
              </span>
              <span v-else-if="getDataframeSizeText(file.id)" class="dataframe-size">
                {{ getDataframeSizeText(file.id) }}
              </span>
            </div>
          </div>
          <button class="danger" @click="removeFile(file.id)">Remove</button>
        </div>
      </div>
    </div>

    <div class="upload-section">
      <h3>Structure File</h3>
      <div
        v-if="store.structureFiles.length === 0"
        class="upload-area"
        @drop.prevent="handleDrop($event, 'structure')"
        @dragover.prevent
      >
        <input
          type="file"
          ref="structureFileInput"
          @change="handleFileSelect($event, 'structure')"
          accept=".pdb,.cif"
          style="display: none"
        />
        <p>Drag and drop structure file here or</p>
        <button class="primary" @click="$refs.structureFileInput.click()">
          Browse File
        </button>
      </div>
      <div v-else class="upload-area upload-area-disabled">
        <p>Structure file uploaded. Remove the existing file to upload a different one.</p>
      </div>

      <div v-if="store.structureFiles.length > 0" class="file-list">
        <div v-for="file in store.structureFiles" :key="file.id" class="file-item">
          <div class="file-info">
            <strong>{{ file.filename }}</strong>
            <span class="file-size">{{ formatFileSize(file.size) }}</span>
          </div>
          <button class="danger" @click="removeFile(file.id)">Remove</button>
        </div>
      </div>

      <div v-if="store.structureFiles.length > 0" class="structure-metadata-form">
        <h4>Structure Information (Optional)</h4>
        <div class="form-group">
          <label for="structure-description">Description</label>
          <textarea
            id="structure-description"
            v-model="structureDescription"
            placeholder="Brief description of the structure"
            rows="2"
          />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="pdb-id">PDB ID</label>
            <input
              id="pdb-id"
              v-model="pdbId"
              type="text"
              placeholder="e.g., 1ABC"
              maxlength="4"
            />
          </div>
          <div class="form-group">
            <label for="alphafold-id">AlphaFold ID</label>
            <input
              id="alphafold-id"
              v-model="alphafoldId"
              type="text"
              placeholder="e.g., AF-P12345-F1"
            />
          </div>
        </div>
      </div>
    </div>

    <div v-if="uploading" class="upload-progress">
      Uploading...
    </div>

    <div v-if="error" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useDatasetStore } from '@/stores/dataset'
import { apiService } from '@/services/api'
import type { DataframeInfo } from '@/types/dataset'

const store = useDatasetStore()
const uploading = ref(false)
const error = ref('')
const dataframeInfoMap = ref<Map<string, DataframeInfo | 'loading' | 'error'>>(new Map())

// Structure metadata refs
const structureDescription = ref('')
const pdbId = ref('')
const alphafoldId = ref('')

const handleFileSelect = async (event: Event, fileType: 'data' | 'structure') => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    await uploadFiles(Array.from(target.files), fileType)
  }
}

const handleDrop = async (event: DragEvent, fileType: 'data' | 'structure') => {
  if (event.dataTransfer?.files) {
    await uploadFiles(Array.from(event.dataTransfer.files), fileType)
  }
}

const uploadFiles = async (files: File[], fileType: 'data' | 'structure') => {
  uploading.value = true
  error.value = ''

  try {
    // Enforce structure file limit
    if (fileType === 'structure') {
      if (store.structureFiles.length > 0) {
        error.value = 'Only one structure file is allowed. Remove the existing file first.'
        return
      }
      if (files.length > 1) {
        error.value = 'Only one structure file can be uploaded at a time.'
        return
      }
    }

    for (const file of files) {
      const uploadedFile = await apiService.uploadFile(store.sessionId, file, fileType)
      store.addUploadedFile(uploadedFile)

      // Load dataframe info for data files
      if (fileType === 'data') {
        loadDataframeInfo(uploadedFile.id)
      }
    }
  } catch (e: any) {
    error.value = e.message || 'Upload failed'
  } finally {
    uploading.value = false
  }
}

const loadDataframeInfo = async (fileId: string) => {
  dataframeInfoMap.value.set(fileId, 'loading')

  try {
    const info = await apiService.getDataframeInfo(store.sessionId, fileId)
    dataframeInfoMap.value.set(fileId, info)
  } catch (e) {
    console.error(`Failed to load dataframe info for ${fileId}:`, e)
    dataframeInfoMap.value.set(fileId, 'error')
  }
}

const removeFile = async (fileId: string) => {
  try {
    await apiService.deleteFile(store.sessionId, fileId)
    store.removeUploadedFile(fileId)
    // Remove from dataframe info map
    dataframeInfoMap.value.delete(fileId)
  } catch (e: any) {
    error.value = e.message || 'Failed to remove file'
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const formatDataframeSize = (rows: number, cols: number): string => {
  return `${rows.toLocaleString()} rows × ${cols} columns`
}

const getDataframeInfo = (fileId: string): DataframeInfo | 'loading' | 'error' | null => {
  return dataframeInfoMap.value.get(fileId) || null
}

const getDataframeSizeText = (fileId: string): string => {
  const info = getDataframeInfo(fileId)
  if (!info || info === 'loading' || info === 'error') return ''
  return formatDataframeSize(info.shape.rows, info.shape.columns)
}

// Watch structure metadata changes and update store
watch([structureDescription, pdbId, alphafoldId], () => {
  if (store.structureFiles.length > 0) {
    const structureFile = store.structureFiles[0]
    const fileExtension = structureFile.filename.split('.').pop()?.toLowerCase()
    const format = fileExtension === 'cif' ? 'cif' : 'pdb'

    store.structure = {
      fileId: structureFile.id,
      format: format,
      description: structureDescription.value || undefined,
      pdbId: pdbId.value || undefined,
      alphafoldId: alphafoldId.value || undefined
    }
  }
})

// Watch for structure file changes and initialize metadata
watch(() => store.structureFiles, (newFiles) => {
  if (newFiles.length > 0 && !store.structure) {
    // Initialize structure in store when file is uploaded
    const structureFile = newFiles[0]
    const fileExtension = structureFile.filename.split('.').pop()?.toLowerCase()
    const format = fileExtension === 'cif' ? 'cif' : 'pdb'

    store.structure = {
      fileId: structureFile.id,
      format: format,
      description: structureDescription.value || undefined,
      pdbId: pdbId.value || undefined,
      alphafoldId: alphafoldId.value || undefined
    }
  } else if (newFiles.length === 0) {
    // Clear structure data when file is removed
    store.structure = null
    structureDescription.value = ''
    pdbId.value = ''
    alphafoldId.value = ''
  }
}, { deep: true })

// Load dataframe info for existing data files on mount
onMounted(() => {
  store.dataFiles.forEach(file => {
    if (!dataframeInfoMap.value.has(file.id)) {
      loadDataframeInfo(file.id)
    }
  })

  // Load existing structure metadata from store
  if (store.structure) {
    structureDescription.value = store.structure.description || ''
    pdbId.value = store.structure.pdbId || ''
    alphafoldId.value = store.structure.alphafoldId || ''
  }
})
</script>

<style scoped>
.step-content {
  padding: 20px;
}

h2 {
  margin-bottom: 10px;
}

.upload-section {
  margin: 30px 0;
}

.upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  transition: all 0.3s;
}

.upload-area:hover {
  border-color: #007bff;
  background: #f8f9fa;
}

.upload-area-disabled {
  border-color: #ccc;
  background: #f0f0f0;
  color: #666;
  cursor: not-allowed;
}

.upload-area-disabled:hover {
  border-color: #ccc;
  background: #f0f0f0;
}

.file-list {
  margin-top: 20px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 10px;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.file-details {
  display: flex;
  gap: 15px;
  align-items: center;
}

.file-size {
  color: #666;
  font-size: 14px;
}

.dataframe-info {
  font-size: 13px;
  padding-left: 2px;
}

.dataframe-size {
  color: #555;
  font-family: 'Courier New', monospace;
}

.loading-text {
  color: #007bff;
  font-style: italic;
}

.error-text {
  color: #dc3545;
  font-style: italic;
}

.badge {
  background: #007bff;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.upload-progress {
  text-align: center;
  padding: 20px;
  color: #007bff;
}

.structure-metadata-form {
  margin-top: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.structure-metadata-form h4 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #495057;
  font-size: 16px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #495057;
  font-size: 14px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.form-group textarea {
  resize: vertical;
  min-height: 50px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
