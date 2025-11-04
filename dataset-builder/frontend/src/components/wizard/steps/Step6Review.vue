<template>
  <div class="step-content">
    <h2>Step 6: Review & Generate</h2>
    <p>Review your dataset configuration and generate the final JSON file</p>

    <div class="review-section card">
      <h3>Files ({{ store.uploadedFiles.length }})</h3>
      <ul>
        <li v-for="file in store.uploadedFiles" :key="file.id">
          {{ file.filename }} ({{ file.fileType }})
        </li>
      </ul>
    </div>

    <div class="review-section card">
      <h3>Protein Identifiers</h3>
      <p v-if="store.proteinIdentifiers.uniprotAccessionNumber">
        UniProt: {{ store.proteinIdentifiers.uniprotAccessionNumber }}
      </p>
      <p v-else class="warning">No protein identifiers provided</p>
    </div>

    <div class="review-section card">
      <h3>Structure</h3>
      <p v-if="store.structure">
        {{ store.structure.format.toUpperCase() }} file
        <span v-if="store.structure.pdbId">(PDB: {{ store.structure.pdbId }})</span>
      </p>
      <p v-else class="error">No structure configured</p>
    </div>

    <div class="review-section card">
      <h3>States ({{ store.states.length }})</h3>
      <div v-for="state in store.states" :key="state.id" class="state-summary">
        <strong>{{ state.name }}</strong>
        <span>- {{ state.peptides.length }} peptide(s)</span>
      </div>
      <p v-if="store.states.length === 0" class="error">No states defined</p>
    </div>

    <div class="review-section card">
      <h3>Metadata</h3>
      <p>Authors: {{ store.metadata.authors.length }}</p>
      <p>License: {{ store.metadata.license }}</p>
      <p v-if="store.metadata.publication">Publication: {{ store.metadata.publication.title }}</p>
    </div>

    <div v-if="validationErrors.length > 0" class="error-box">
      <h4>Validation Errors:</h4>
      <ul>
        <li v-for="(error, index) in validationErrors" :key="index">{{ error }}</li>
      </ul>
    </div>

    <div class="actions">
      <button
        class="primary"
        @click="generateDataset"
        :disabled="!store.isComplete || generating"
      >
        {{ generating ? 'Generating...' : 'Generate Dataset JSON' }}
      </button>
    </div>

    <div v-if="generatedFile" class="success-box">
      Dataset generated successfully!
      <button class="primary" @click="downloadFile">Download JSON</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDatasetStore } from '@/stores/dataset'
import { apiService } from '@/services/api'

const store = useDatasetStore()
const generating = ref(false)
const generatedFile = ref<Blob | null>(null)
const validationErrors = ref<string[]>([])

const validateDataset = (): string[] => {
  const errors: string[] = []

  if (store.uploadedFiles.length === 0) {
    errors.push('No files uploaded')
  }

  if (!store.structure) {
    errors.push('No structure configured')
  }

  if (store.states.length === 0) {
    errors.push('No states defined')
  }

  store.states.forEach((state, index) => {
    if (!state.name) {
      errors.push(`State ${index + 1}: Name is required`)
    }
    if (!state.proteinState.sequence) {
      errors.push(`State ${index + 1}: Sequence is required`)
    }
    if (state.peptides.length === 0) {
      errors.push(`State ${index + 1}: At least one peptide required`)
    }
  })

  if (store.metadata.authors.length === 0) {
    errors.push('At least one author is required')
  }

  if (!store.metadata.license) {
    errors.push('License is required')
  }

  return errors
}

const generateDataset = async () => {
  validationErrors.value = validateDataset()

  if (validationErrors.value.length > 0) {
    return
  }

  generating.value = true

  try {
    // Build the dataset data object
    const datasetData = {
      session_id: store.sessionId,
      description: store.datasetDescription,
      protein_identifiers: {
        uniprot_accession_number: store.proteinIdentifiers.uniprotAccessionNumber,
        uniprot_entry_name: store.proteinIdentifiers.uniprotEntryName,
        protein_name: store.proteinIdentifiers.proteinName
      },
      structure: {
        file_id: store.structure!.fileId,
        format: store.structure!.format,
        description: store.structure!.description,
        pdb_id: store.structure!.pdbId,
        alphafold_id: store.structure!.alphafoldId
      },
      states: store.states.map(state => ({
        id: state.id,
        name: state.name,
        description: state.description,
        protein_state: {
          sequence: state.proteinState.sequence,
          n_term: state.proteinState.nTerm,
          c_term: state.proteinState.cTerm,
          oligomeric_state: state.proteinState.oligomericState
        },
        peptides: state.peptides.map(peptide => ({
          id: peptide.id,
          data_file_id: peptide.dataFileId,
          data_format: peptide.dataFormat,
          deuteration_type: peptide.deuterationType,
          filters: peptide.filters,
          pH: peptide.pH,
          temperature: peptide.temperature,
          d_percentage: peptide.dPercentage,
          chain: peptide.chain
        }))
      })),
      metadata: {
        authors: store.metadata.authors,
        license: store.metadata.license,
        publication: store.metadata.publication,
        repository: store.metadata.repository,
        conversion_notes: store.metadata.conversionNotes
      }
    }

    const blob = await apiService.generateJSON(datasetData)
    generatedFile.value = blob

  } catch (error: any) {
    validationErrors.value = [error.message || 'Failed to generate dataset']
  } finally {
    generating.value = false
  }
}

const downloadFile = () => {
  if (generatedFile.value) {
    const url = URL.createObjectURL(generatedFile.value)
    const a = document.createElement('a')
    a.href = url
    a.download = 'dataset.json'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
}
</script>

<style scoped>
.step-content {
  padding: 20px;
}

.review-section {
  margin: 20px 0;
  padding: 15px;
}

.review-section h3 {
  margin-bottom: 10px;
  color: #007bff;
}

.review-section ul {
  list-style: none;
  padding: 0;
}

.review-section li {
  padding: 5px 0;
}

.state-summary {
  padding: 5px 0;
}

.error-box {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
  padding: 15px;
  border-radius: 4px;
  margin: 20px 0;
}

.success-box {
  background: #d4edda;
  border: 1px solid #c3e6cb;
  color: #155724;
  padding: 15px;
  border-radius: 4px;
  margin: 20px 0;
  text-align: center;
}

.success-box button {
  margin-top: 10px;
}

.actions {
  text-align: center;
  margin: 30px 0;
}
</style>
