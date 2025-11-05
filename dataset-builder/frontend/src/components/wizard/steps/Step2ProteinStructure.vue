<template>
  <div class="step-content">
    <h2>Step 2: Protein and Structure Information</h2>
    <p>Provide protein identifiers and configure structure settings</p>

    <!-- Protein Identifiers Section -->
    <div class="section">
      <h3>Protein Identifiers</h3>
      <div class="form-group">
        <label for="uniprot-accession">UniProt Accession Number</label>
        <input
          id="uniprot-accession"
          v-model="proteinIdentifiers.uniprotAccession"
          type="text"
          placeholder="e.g., P10408"
        />
      </div>

      <div class="form-group">
        <label for="uniprot-entry">UniProt Entry Name</label>
        <input
          id="uniprot-entry"
          v-model="proteinIdentifiers.uniprotEntry"
          type="text"
          placeholder="e.g., SECA_ECOLI"
        />
      </div>

      <div class="form-group">
        <label for="protein-name">Protein Name</label>
        <input
          id="protein-name"
          v-model="proteinIdentifiers.proteinName"
          type="text"
          placeholder="e.g., Protein translocase subunit SecA"
        />
      </div>
    </div>

    <!-- Structure Configuration Section -->
    <div class="section">
      <h3>Structure Configuration</h3>

      <div v-if="store.structureFiles.length === 0" class="warning">
        <p>⚠️ No structure file uploaded. Please upload a structure file in Step 1.</p>
      </div>

      <template v-else>
        <div class="form-group">
          <label for="structure-file">Structure File</label>
          <select
            id="structure-file"
            v-model="selectedStructureFileId"
            @change="handleStructureFileChange"
          >
            <option value="">Select a structure file...</option>
            <option
              v-for="file in store.structureFiles"
              :key="file.id"
              :value="file.id"
            >
              {{ file.filename }}
            </option>
          </select>
        </div>

        <div v-if="selectedStructureFileId" class="form-group">
          <label for="structure-format">Format</label>
          <select id="structure-format" v-model="structureFormat">
            <option value="pdb">PDB</option>
            <option value="cif">mmCIF</option>
            <option value="bcif">BinaryCIF</option>
          </select>
          <small class="hint">Format auto-detected from file extension</small>
        </div>
      </template>
    </div>

    <div v-if="error" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useDatasetStore } from '@/stores/dataset'

const store = useDatasetStore()
const error = ref('')

// Protein identifiers
const proteinIdentifiers = ref({
  uniprotAccession: '',
  uniprotEntry: '',
  proteinName: ''
})

// Structure configuration
const selectedStructureFileId = ref('')
const structureFormat = ref<'pdb' | 'cif' | 'bcif'>('pdb')

const handleStructureFileChange = () => {
  if (!selectedStructureFileId.value) {
    structureFormat.value = 'pdb'
    return
  }

  // Auto-detect format from filename extension
  const file = store.structureFiles.find(f => f.id === selectedStructureFileId.value)
  if (file) {
    const ext = file.filename.split('.').pop()?.toLowerCase()
    if (ext === 'cif') {
      structureFormat.value = 'cif'
    } else if (ext === 'bcif') {
      structureFormat.value = 'bcif'
    } else {
      structureFormat.value = 'pdb'
    }
  }
}

// Watch protein identifiers and save to store
watch(proteinIdentifiers, () => {
  store.proteinIdentifiers = {
    uniprotAccessionNumber: proteinIdentifiers.value.uniprotAccession || undefined,
    uniprotEntryName: proteinIdentifiers.value.uniprotEntry || undefined,
    proteinName: proteinIdentifiers.value.proteinName || undefined
  }
}, { deep: true })

// Watch structure configuration and save to store
watch([selectedStructureFileId, structureFormat], () => {
  if (selectedStructureFileId.value) {
    // Merge with existing structure data (pdbId, alphafoldId, description from Step 1)
    const existingStructure = store.structure || {}
    store.structure = {
      ...existingStructure,
      fileId: selectedStructureFileId.value,
      format: structureFormat.value
    }
  }
})

// Watch for structure file changes (e.g., file removed in Step 1)
watch(() => store.structureFiles, (newFiles) => {
  // If selected file no longer exists, clear selection
  if (selectedStructureFileId.value && !newFiles.find(f => f.id === selectedStructureFileId.value)) {
    selectedStructureFileId.value = ''
    structureFormat.value = 'pdb'
  }

  // If only one file, auto-select it
  if (newFiles.length === 1 && !selectedStructureFileId.value) {
    selectedStructureFileId.value = newFiles[0].id
    handleStructureFileChange()
  }
}, { deep: true })

// Load existing data from store on mount
onMounted(() => {
  // Load protein identifiers
  if (store.proteinIdentifiers) {
    proteinIdentifiers.value = {
      uniprotAccession: store.proteinIdentifiers.uniprotAccessionNumber || '',
      uniprotEntry: store.proteinIdentifiers.uniprotEntryName || '',
      proteinName: store.proteinIdentifiers.proteinName || ''
    }
  }

  // Load structure configuration
  if (store.structure) {
    selectedStructureFileId.value = store.structure.fileId
    structureFormat.value = store.structure.format
  } else if (store.structureFiles.length === 1) {
    // Auto-select if only one file
    selectedStructureFileId.value = store.structureFiles[0].id
    handleStructureFileChange()
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

.section {
  margin: 30px 0;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.section h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #495057;
  font-size: 18px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #495057;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.hint {
  display: block;
  margin-top: 5px;
  color: #6c757d;
  font-size: 12px;
  font-style: italic;
}

.warning {
  padding: 15px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 4px;
  color: #856404;
}

.warning p {
  margin: 0;
}

.error {
  margin-top: 20px;
  padding: 15px;
  background: #f8d7da;
  border: 1px solid #dc3545;
  border-radius: 4px;
  color: #721c24;
}
</style>