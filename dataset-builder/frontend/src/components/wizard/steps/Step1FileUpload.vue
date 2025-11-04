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
            <strong>{{ file.filename }}</strong>
            <span class="file-size">{{ formatFileSize(file.size) }}</span>
            <span v-if="file.detectedFormat" class="badge">{{ file.detectedFormat }}</span>
          </div>
          <button class="danger" @click="removeFile(file.id)">Remove</button>
        </div>
      </div>
    </div>

    <div class="upload-section">
      <h3>Structure File</h3>
      <div class="upload-area" @drop.prevent="handleDrop($event, 'structure')" @dragover.prevent>
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

      <div v-if="store.structureFiles.length > 0" class="file-list">
        <div v-for="file in store.structureFiles" :key="file.id" class="file-item">
          <div class="file-info">
            <strong>{{ file.filename }}</strong>
            <span class="file-size">{{ formatFileSize(file.size) }}</span>
          </div>
          <button class="danger" @click="removeFile(file.id)">Remove</button>
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
import { ref } from 'vue'
import { useDatasetStore } from '@/stores/dataset'
import { apiService } from '@/services/api'

const store = useDatasetStore()
const uploading = ref(false)
const error = ref('')

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
    for (const file of files) {
      const uploadedFile = await apiService.uploadFile(store.sessionId, file, fileType)
      store.addUploadedFile(uploadedFile)
    }
  } catch (e: any) {
    error.value = e.message || 'Upload failed'
  } finally {
    uploading.value = false
  }
}

const removeFile = async (fileId: string) => {
  try {
    await apiService.deleteFile(store.sessionId, fileId)
    store.removeUploadedFile(fileId)
  } catch (e: any) {
    error.value = e.message || 'Failed to remove file'
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
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
  gap: 15px;
  align-items: center;
}

.file-size {
  color: #666;
  font-size: 14px;
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
</style>
