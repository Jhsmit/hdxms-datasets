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



// Watch protein identifiers and save to store
watch(proteinIdentifiers, () => {
  store.proteinIdentifiers = {
    uniprotAccessionNumber: proteinIdentifiers.value.uniprotAccession || undefined,
    uniprotEntryName: proteinIdentifiers.value.uniprotEntry || undefined,
    proteinName: proteinIdentifiers.value.proteinName || undefined
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