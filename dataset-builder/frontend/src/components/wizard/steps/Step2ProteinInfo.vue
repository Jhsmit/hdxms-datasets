<template>
  <div class="step-content">
    <h2>Step 2: Protein Identifiers</h2>
    <p>Provide information about the protein (optional)</p>

    <div class="form-group">
      <label>UniProt Accession Number</label>
      <input
        v-model="store.proteinIdentifiers.uniprotAccessionNumber"
        type="text"
        placeholder="e.g., P10408"
      />
    </div>

    <div class="form-group">
      <label>UniProt Entry Name</label>
      <input
        v-model="store.proteinIdentifiers.uniprotEntryName"
        type="text"
        placeholder="e.g., SECA_ECOLI"
      />
    </div>

    <div class="form-group">
      <label>Protein Name</label>
      <input
        v-model="store.proteinIdentifiers.proteinName"
        type="text"
        placeholder="e.g., Protein translocase subunit SecA"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDatasetStore } from '@/stores/dataset'

const store = useDatasetStore()
</script>

<style scoped>
.step-content {
  padding: 20px;
}
</style>
