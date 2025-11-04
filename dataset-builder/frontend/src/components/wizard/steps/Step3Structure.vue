<template>
  <div class="step-content">
    <h2>Step 3: Structure Information</h2>
    <p>Configure the structure file settings</p>

    <div v-if="store.structureFiles.length === 0" class="warning">
      No structure file uploaded yet. Please go back to Step 1.
    </div>

    <div v-else class="form-group">
      <label>Structure File</label>
      <select v-model="selectedFileId" @change="updateStructure">
        <option value="">Select a structure file...</option>
        <option v-for="file in store.structureFiles" :key="file.id" :value="file.id">
          {{ file.filename }}
        </option>
      </select>
    </div>

    <div v-if="selectedFileId">
      <div class="form-group">
        <label>Format</label>
        <select v-model="format">
          <option value="pdb">PDB</option>
          <option value="cif">mmCIF</option>
          <option value="bcif">BinaryCIF</option>
        </select>
      </div>

      <div class="form-group">
        <label>PDB ID (optional)</label>
        <input v-model="pdbId" type="text" placeholder="e.g., 2VDA" />
      </div>

      <div class="form-group">
        <label>AlphaFold ID (optional)</label>
        <input v-model="alphafoldId" type="text" />
      </div>

      <div class="form-group">
        <label>Description (optional)</label>
        <textarea v-model="description" rows="3" />
      </div>

      <button class="primary" @click="saveStructure">Save Structure Info</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useDatasetStore } from '@/stores/dataset'

const store = useDatasetStore()

const selectedFileId = ref('')
const format = ref('pdb')
const pdbId = ref('')
const alphafoldId = ref('')
const description = ref('')

onMounted(() => {
  if (store.structure) {
    selectedFileId.value = store.structure.fileId
    format.value = store.structure.format
    pdbId.value = store.structure.pdbId || ''
    alphafoldId.value = store.structure.alphafoldId || ''
    description.value = store.structure.description || ''
  }
})

const updateStructure = () => {
  // Auto-detect format from filename
  const file = store.structureFiles.find(f => f.id === selectedFileId.value)
  if (file) {
    if (file.filename.endsWith('.pdb')) format.value = 'pdb'
    else if (file.filename.endsWith('.cif')) format.value = 'cif'
  }
}

const saveStructure = () => {
  store.structure = {
    fileId: selectedFileId.value,
    format: format.value,
    pdbId: pdbId.value || undefined,
    alphafoldId: alphafoldId.value || undefined,
    description: description.value || undefined
  }
}
</script>

<style scoped>
.step-content {
  padding: 20px;
}
</style>
