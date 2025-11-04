<template>
  <div class="step-content">
    <h2>Step 5: Metadata</h2>
    <p>Provide information about authors, license, and publication</p>

    <h3>Authors *</h3>
    <button class="secondary" @click="store.addAuthor()">+ Add Author</button>

    <div v-if="store.metadata.authors.length === 0" class="warning">
      At least one author is required.
    </div>

    <div v-for="(author, index) in store.metadata.authors" :key="index" class="author-card card">
      <div class="author-header">
        <strong>Author {{ index + 1 }}</strong>
        <button class="danger" @click="store.removeAuthor(index)">Remove</button>
      </div>

      <div class="form-group">
        <label>Name *</label>
        <input v-model="author.name" type="text" placeholder="Full name" />
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>ORCID</label>
          <input v-model="author.orcid" type="text" placeholder="0000-0000-0000-0000" />
        </div>
        <div class="form-group">
          <label>Affiliation</label>
          <input v-model="author.affiliation" type="text" placeholder="Institution" />
        </div>
      </div>

      <div class="form-group">
        <label>Contact Email</label>
        <input v-model="author.contactEmail" type="email" placeholder="email@example.com" />
      </div>
    </div>

    <h3>License *</h3>
    <div class="form-group">
      <select v-model="store.metadata.license">
        <option value="CC0">CC0 (Public Domain)</option>
        <option value="CC BY 4.0">CC BY 4.0</option>
        <option value="CC BY-SA 4.0">CC BY-SA 4.0</option>
        <option value="MIT">MIT</option>
      </select>
    </div>

    <h3>Publication (Optional)</h3>
    <div class="form-group">
      <label>Title</label>
      <input v-model="publicationTitle" type="text" />
    </div>

    <div class="form-row">
      <div class="form-group">
        <label>DOI</label>
        <input v-model="publicationDoi" type="text" placeholder="10.1234/example" />
      </div>
      <div class="form-group">
        <label>PMID</label>
        <input v-model="publicationPmid" type="text" />
      </div>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label>Journal</label>
        <input v-model="publicationJournal" type="text" />
      </div>
      <div class="form-group">
        <label>Year</label>
        <input v-model.number="publicationYear" type="number" />
      </div>
    </div>

    <h3>Dataset Description (Optional)</h3>
    <div class="form-group">
      <textarea v-model="store.datasetDescription" rows="4" placeholder="Describe the dataset..." />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useDatasetStore } from '@/stores/dataset'

const store = useDatasetStore()

const publicationTitle = ref('')
const publicationDoi = ref('')
const publicationPmid = ref('')
const publicationJournal = ref('')
const publicationYear = ref<number>()

// Update publication object when fields change
watch([publicationTitle, publicationDoi, publicationPmid, publicationJournal, publicationYear], () => {
  if (publicationTitle.value || publicationDoi.value || publicationPmid.value) {
    store.metadata.publication = {
      title: publicationTitle.value || undefined,
      doi: publicationDoi.value || undefined,
      pmid: publicationPmid.value || undefined,
      journal: publicationJournal.value || undefined,
      year: publicationYear.value || undefined
    }
  }
})
</script>

<style scoped>
.step-content {
  padding: 20px;
}

.author-card {
  margin: 15px 0;
  padding: 15px;
}

.author-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

h3 {
  margin-top: 30px;
  margin-bottom: 15px;
  color: #007bff;
}
</style>
