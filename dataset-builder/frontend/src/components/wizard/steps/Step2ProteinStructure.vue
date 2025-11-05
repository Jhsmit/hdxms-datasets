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

    <!-- Structure Mappings Section -->
    <div class="section">
      <div class="section-header">
        <div>
          <h3>Structure Mappings (Optional)</h3>
          <p class="hint">
            Define structure mappings to map peptides to specific chains or entities in the structure.
            Only needed if you have peptides that map to different regions or chains.
          </p>
        </div>
        <button class="primary" @click="store.addStructureMapping()">+ Add Mapping</button>
      </div>

      <div v-if="store.structureMappings.length === 0" class="warning">
        <p>No structure mappings defined. This is optional - add mappings only if needed.</p>
      </div>

      <div
        v-for="(mapping, index) in store.structureMappings"
        :key="mapping.id"
        class="mapping-card card"
      >
        <div class="mapping-header">
          <h4>Mapping {{ index + 1 }}{{ mapping.name ? `: ${mapping.name}` : '' }}</h4>
          <button class="danger" @click="store.removeStructureMapping(mapping.id)">Remove</button>
        </div>

        <div class="form-group">
          <label>Mapping Name</label>
          <input
            v-model="mapping.name"
            type="text"
            placeholder="e.g., Chain A mapping"
            @input="updateMapping(mapping.id)"
          />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Entity ID</label>
            <input
              v-model="mapping.entityId"
              type="text"
              placeholder="Optional"
              @input="updateMapping(mapping.id)"
            />
          </div>

          <div class="form-group">
            <label>Chains (comma-separated)</label>
            <input
              v-model="chainInputs[mapping.id]"
              type="text"
              placeholder="e.g., A, B, C"
              @input="(e) => updateChains(mapping.id, (e.target as HTMLInputElement).value)"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Residue Offset</label>
            <input
              v-model.number="mapping.residueOffset"
              type="number"
              @input="updateMapping(mapping.id)"
            />
            <span class="hint">Offset to apply to residue numbers (default: 0)</span>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group checkbox-group">
            <label>
              <input
                v-model="mapping.authResidueNumbers"
                type="checkbox"
                @change="updateMapping(mapping.id)"
              />
              Use Author Residue Numbers
            </label>
          </div>

          <div class="form-group checkbox-group">
            <label>
              <input
                v-model="mapping.authChainLabels"
                type="checkbox"
                @change="updateMapping(mapping.id)"
              />
              Use Author Chain Labels
            </label>
          </div>
        </div>
      </div>
    </div>

    <div v-if="error" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, reactive } from 'vue'
import { useDatasetStore } from '@/stores/dataset'

const store = useDatasetStore()
const error = ref('')

// Protein identifiers
const proteinIdentifiers = ref({
  uniprotAccession: '',
  uniprotEntry: '',
  proteinName: ''
})

// Local chain input values (not controlled by store directly)
const chainInputs = reactive<Record<string, string>>({})

// Watch protein identifiers and save to store
watch(proteinIdentifiers, () => {
  store.proteinIdentifiers = {
    uniprotAccessionNumber: proteinIdentifiers.value.uniprotAccession || undefined,
    uniprotEntryName: proteinIdentifiers.value.uniprotEntry || undefined,
    proteinName: proteinIdentifiers.value.proteinName || undefined
  }
}, { deep: true })

// Structure mapping helper functions
function updateMapping(mappingId: string) {
  const mapping = store.structureMappings.find(m => m.id === mappingId)
  if (mapping) {
    store.updateStructureMapping(mappingId, mapping)
  }
}

function updateChains(mappingId: string, value: string) {
  chainInputs[mappingId] = value
  const chains = value.split(',').map(c => c.trim()).filter(c => c.length > 0)
  store.updateStructureMapping(mappingId, { chain: chains.length > 0 ? chains : undefined })
}

function getChainInput(mappingId: string): string {
  if (chainInputs[mappingId] !== undefined) {
    return chainInputs[mappingId]
  }
  const mapping = store.structureMappings.find(m => m.id === mappingId)
  const value = mapping?.chain?.join(', ') || ''
  chainInputs[mappingId] = value
  return value
}

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

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0 0 5px 0;
}

.section-header p.hint {
  margin: 0;
  font-style: normal;
  font-size: 13px;
}

.mapping-card {
  margin: 15px 0;
  padding: 15px;
  background: white;
  border-radius: 6px;
  border: 1px solid #dee2e6;
}

.mapping-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e9ecef;
}

.mapping-header h4 {
  margin: 0;
  color: #495057;
  font-size: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  margin-bottom: 15px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-group input[type="checkbox"] {
  width: auto;
  cursor: pointer;
}

button.primary {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

button.primary:hover {
  background: #0056b3;
}

button.danger {
  background: #dc3545;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
}

button.danger:hover {
  background: #c82333;
}
</style>