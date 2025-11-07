/**
 * Mapping of data formats to their filter column names
 * Based on the filter_columns defined in hdxms_datasets/formats.py
 */
export const FORMAT_FILTER_COLUMNS: Record<string, string[]> = {
  DynamX_v3_state: ['Protein', 'State', 'Exposure'],
  DynamX_vx_state: ['Protein', 'State', 'Exposure'],
  DynamX_v3_cluster: ['Protein', 'State', 'Exposure'],
  HDExaminer_v3: ['Protein State', 'Deut Time'],
  OpenHDX: [],
  HXMS: ['TIME(Sec)']
}

/**
 * Get filter columns for a specific format
 */
export function getFilterColumns(format: string | null): string[] {
  if (!format) return []
  return FORMAT_FILTER_COLUMNS[format] || []
}

/**
 * Fetch filter options from the backend API
 * @param sessionId - Session identifier
 * @param fileId - File identifier
 * @param currentFilters - Already-applied filters to enable cascading behavior
 * @returns Dictionary mapping column names to available unique values
 */
export async function fetchFilterOptions(
  sessionId: string,
  fileId: string,
  currentFilters: Record<string, string[]>
): Promise<Record<string, string[]>> {
  try {
    const response = await fetch(`/api/data/dataframe/filter-options/${fileId}?session_id=${sessionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(currentFilters)
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Failed to fetch filter options: ${errorText}`)
    }

    const data = await response.json()
    return data.filter_options || {}
  } catch (error) {
    console.error('Error fetching filter options:', error)
    throw error
  }
}

/**
 * Generate mock filter options for a given filter column
 * Returns 15-20 mock values to simulate realistic dataset diversity
 */
export function getMockFilterOptions(columnName: string): string[] {
  // Mock data generators based on column type
  const generators: Record<string, () => string[]> = {
    Protein: () => [
      'Protein_A',
      'Protein_B',
      'Protein_C',
      'Protein_D',
      'Protein_E',
      'Protein_F',
      'Protein_G',
      'Protein_H'
    ],
    State: () => [
      'Apo',
      'Holo',
      'Bound_State1',
      'Bound_State2',
      'Bound_State3',
      'Intermediate',
      'Transition',
      'Control'
    ],
    'Protein State': () => [
      'WT_Apo',
      'WT_Holo',
      'Mutant_A_Apo',
      'Mutant_A_Holo',
      'Mutant_B_Apo',
      'Mutant_B_Holo',
      'Control_1',
      'Control_2',
      'Test_Condition_1',
      'Test_Condition_2'
    ],
    Exposure: () => [
      '0',
      '3',
      '10',
      '30',
      '60',
      '120',
      '300',
      '600',
      '900',
      '1200',
      '1800',
      '3600',
      '7200',
      '14400',
      '21600'
    ],
    'Deut Time': () => [
      '0s',
      '3s',
      '10s',
      '30s',
      '1min',
      '2min',
      '5min',
      '10min',
      '15min',
      '20min',
      '30min',
      '1h',
      '2h',
      '4h',
      '6h',
      '12h',
      '24h'
    ],
    'TIME(Sec)': () => [
      '0',
      '3',
      '10',
      '30',
      '60',
      '120',
      '300',
      '600',
      '900',
      '1200',
      '1800',
      '3600',
      '7200',
      '10800',
      '14400',
      '21600',
      '43200',
      '86400'
    ]
  }

  const generator = generators[columnName]
  if (generator) {
    return generator()
  }

  // Default mock data if column name not recognized
  return Array.from({ length: 15 }, (_, i) => `Value_${i + 1}`)
}

/**
 * Check if a format has any filter columns
 */
export function hasFilters(format: string | null): boolean {
  return getFilterColumns(format).length > 0
}
