<template>
  <div class="filter-selector">
    <div class="filter-header">
      <label>{{ label }}</label>
      <div class="filter-actions">
        <button type="button" class="text-button" @click="selectAll">Select All</button>
        <span class="separator">|</span>
        <button type="button" class="text-button" @click="selectNone">Select None</button>
      </div>
    </div>

    <div class="dropdown-wrapper">
      <div class="selected-display" @click="toggleDropdown">
        <span v-if="selectedCount === 0" class="placeholder">Select {{ label.toLowerCase() }}...</span>
        <span v-else-if="selectedCount === options.length" class="selection-text">All ({{ selectedCount }})</span>
        <span v-else class="selection-text">{{ selectedCount }} selected</span>
        <span class="dropdown-arrow">{{ isOpen ? '▲' : '▼' }}</span>
      </div>

      <div v-if="isOpen" class="dropdown-menu">
        <div v-if="options.length === 0" class="empty-state">
          No options available
        </div>
        <div v-else class="options-list">
          <label
            v-for="option in options"
            :key="option"
            class="option-item"
          >
            <input
              type="checkbox"
              :checked="modelValue.includes(option)"
              @change="toggleOption(option)"
            />
            <span>{{ option }}</span>
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface Props {
  label: string
  options: string[]
  modelValue: string[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const isOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

const selectedCount = computed(() => props.modelValue.length)

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const toggleOption = (option: string) => {
  const newValue = props.modelValue.includes(option)
    ? props.modelValue.filter((v) => v !== option)
    : [...props.modelValue, option]
  emit('update:modelValue', newValue)
}

const selectAll = () => {
  emit('update:modelValue', [...props.options])
}

const selectNone = () => {
  emit('update:modelValue', [])
}

// Close dropdown when clicking outside
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.filter-selector')) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.filter-selector {
  margin-bottom: 15px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

label {
  font-weight: 500;
  color: #333;
}

.filter-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.text-button {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  font-size: 12px;
  padding: 2px 4px;
  transition: color 0.2s;
}

.text-button:hover {
  color: #0056b3;
  text-decoration: underline;
}

.separator {
  color: #ccc;
  font-size: 12px;
}

.dropdown-wrapper {
  position: relative;
}

.selected-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  transition: border-color 0.2s;
  min-height: 38px;
}

.selected-display:hover {
  border-color: #007bff;
}

.placeholder {
  color: #999;
}

.selection-text {
  color: #333;
}

.dropdown-arrow {
  color: #666;
  font-size: 12px;
  margin-left: 8px;
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  max-height: 300px;
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  overflow-y: auto;
}

.empty-state {
  padding: 12px;
  text-align: center;
  color: #999;
  font-style: italic;
}

.options-list {
  padding: 4px 0;
}

.option-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.15s;
  user-select: none;
  gap: 8px;
}

.option-item:hover {
  background-color: #f0f0f0;
}

.option-item input[type='checkbox'] {
  margin: 0;
  cursor: pointer;
  flex-shrink: 0;
  width: 16px;
  height: 16px;
}

.option-item span {
  color: #333;
  text-align: left;
}

/* Scrollbar styling */
.dropdown-menu::-webkit-scrollbar {
  width: 8px;
}

.dropdown-menu::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.dropdown-menu::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.dropdown-menu::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
