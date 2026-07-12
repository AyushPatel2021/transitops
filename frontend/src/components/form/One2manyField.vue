<template>
  <div class="one2many-znova" :class="{ 'readonly': readonly }">
    <!-- Label (optional) -->
    <div v-if="showLabel && metadata.label" class="o2m-label">
      {{ metadata.label }}
    </div>
    
    <!-- Znova-style Table -->
    <div class="o2m-table-container">
      <table class="o2m-table">
        <thead>
          <tr>
            <th v-for="col in displayColumns" :key="col" class="o2m-th">
              {{ getColumnLabel(col) }}
              <span v-if="getColumnMetadata(col)?.required" class="required-star">*</span>
            </th>
            <th v-if="!readonly && metadata.delete" class="o2m-th-actions"></th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="(record, index) in localRecords" 
            :key="record._tempId || record.id || `row-${index}`"
            class="o2m-tr"
            :class="{ 'o2m-tr-editing': editingIndex === index }"
          >
            <td v-for="col in displayColumns" :key="col" class="o2m-td">
              <component
                class="o2m-cell-content"
                :is="getFieldComponent(col)"
                v-model="record[col]"
                :field-meta="getColumnMetadata(col)"
                :readonly="!metadata.editable || readonly"
                :invalid="!!cellErrors[`${index}-${col}`]"
                :relation-options="getRelationOptions(col)"
                :options="getColumnMetadata(col)?.options"
                :context="record"
                @update:modelValue="onFieldChange(index, col, $event)"
                @focus="editingIndex = index"
              />
            </td>
            <td v-if="!readonly && metadata.delete" class="o2m-td-actions">
              <button 
                @click="removeRecord(index)" 
                class="o2m-delete"
                type="button"
                title="Delete"
              >
                <Trash2 :size="16" />
              </button>
            </td>
          </tr>
          
          <!-- Add a line row (Znova style) -->
          <tr v-if="!readonly && metadata.create" class="o2m-tr-add">
            <td :colspan="displayColumns.length + (metadata.delete ? 1 : 0)" class="o2m-td-add">
              <a @click.prevent="addNewLine" class="o2m-add-link" href="#">
                Add a line
              </a>
            </td>
          </tr>
          
          <!-- Empty state (only when no records and can't add) -->
          <tr v-if="localRecords.length === 0 && (readonly || !metadata.create)">
            <td :colspan="displayColumns.length + (metadata.delete && !readonly ? 1 : 0)" class="o2m-empty">
              No records
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { Trash2 } from 'lucide-vue-next';
import O2MCharField from './one2many/O2MCharField.vue';
import O2MTextField from './one2many/O2MTextField.vue';
import O2MSelectionField from './one2many/O2MSelectionField.vue';
import O2MDateField from './one2many/O2MDateField.vue';
import O2MDateTimeField from './one2many/O2MDateTimeField.vue';
import O2MMany2OneField from './one2many/O2MMany2OneField.vue';
import O2MMany2ManyField from './one2many/O2MMany2ManyField.vue';
import O2MIntegerField from './one2many/O2MIntegerField.vue';
import O2MFloatField from './one2many/O2MFloatField.vue';
import O2MPriorityField from './one2many/O2MPriorityField.vue';
import O2MBooleanField from './one2many/O2MBooleanField.vue';
import O2MPasswordField from './one2many/O2MPasswordField.vue';
import O2MImageField from './one2many/O2MImageField.vue';
import api from '../../core/api';
import { DomainEngine } from '../../core/domain-engine';

interface One2manyMetadata {
  relation: string;
  inverse_name: string;
  columns: string[];
  editable: boolean;
  create: boolean;
  delete: boolean;
  limit?: number;
  label?: string;
  [key: string]: any;
}

const props = defineProps<{
  modelValue: any[];
  metadata: One2manyMetadata;
  readonly: boolean;
  invalid: boolean;
  showLabel?: boolean;
  context?: Record<string, any>;
}>();

// Default showLabel to metadata.show_label if not explicitly provided
const showLabel = computed(() => {
  if (props.showLabel !== undefined) return props.showLabel;
  return props.metadata.show_label !== false;
});

const emit = defineEmits(['update:modelValue', 'error']);

const localRecords = ref<any[]>([]);
const deletedRecordIds = ref<number[]>([]);
const relatedModelMetadata = ref<any>(null);
const relationOptions = ref<Record<string, any[]>>({});
const editingIndex = ref<number | null>(null);
const cellErrors = ref<Record<string, boolean>>({});
let tempIdCounter = 0;
let lastEmittedValue = '';

const displayColumns = computed(() => props.metadata.columns || []);

watch(() => props.modelValue, (newValue) => {
  // Prevent infinite loop by checking if the new value is the same as what we just emitted
  const newValueString = JSON.stringify(newValue);
  if (newValueString === lastEmittedValue) return;

  if (newValue && Array.isArray(newValue)) {
    const visibleRecords: any[] = [];
    const deletedIds: number[] = [];
    
    newValue.forEach(record => {
      // If BaseForm mutated this into an operations object or same-ref array, ignore if it matches last emission
      if (typeof record !== 'object' || record === null) return;

      if (record._deleted) {
        if (record.id) deletedIds.push(record.id);
      } else {
        visibleRecords.push({
          ...record,
          _tempId: record._tempId || (record.id ? null : `temp-${tempIdCounter++}`)
        });
        
        // Extract M2O options from record data to ensure they are available
        if (relatedModelMetadata.value?.fields) {
           Object.keys(relatedModelMetadata.value.fields).forEach(col => {
             const field = relatedModelMetadata.value.fields[col];
             if (field.type === 'many2one' && field.relation && record[col] && typeof record[col] === 'object') {
               const val = record[col];
               if (val.id && val.display_name) {
                 const model = field.relation;
                 if (!relationOptions.value[model]) relationOptions.value[model] = [];
                 if (!relationOptions.value[model].find((o: any) => o.id === val.id)) {
                   relationOptions.value[model].push({ id: val.id, display_name: val.display_name, name: val.display_name });
                 }
               }
             }
           });
        }
      }
    });
    
    localRecords.value = visibleRecords;
    deletedRecordIds.value = deletedIds;
    lastEmittedValue = JSON.stringify(newValue); // Sync our internal state
    
    // Reset editing state when data changes (e.g., on discard)
    editingIndex.value = null;
  } else if (!newValue || !Array.isArray(newValue)) {
    // If it's the operations object, ignore
  } else {
    localRecords.value = [];
    deletedRecordIds.value = [];
    lastEmittedValue = '';
    editingIndex.value = null;
  }
}, { immediate: true, deep: true });

const emitUpdate = () => {
  const allRecords = [...localRecords.value];
  deletedRecordIds.value.forEach(id => {
    allRecords.push({ id, _deleted: true });
  });
  
  const newValueString = JSON.stringify(allRecords);
  if (newValueString !== lastEmittedValue) {
    lastEmittedValue = newValueString;
    emit('update:modelValue', allRecords);
  }
};

watch(localRecords, emitUpdate, { deep: true });
watch(deletedRecordIds, emitUpdate, { deep: true });

const getColumnLabel = (columnName: string): string => {
  if (!relatedModelMetadata.value?.fields) return columnName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  const field = relatedModelMetadata.value.fields[columnName];
  return field?.label || columnName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

const getColumnType = (columnName: string): string => {
  if (!relatedModelMetadata.value?.fields) return 'string';
  const field = relatedModelMetadata.value.fields[columnName];
  return field?.type || 'string';
};

const getColumnMetadata = (columnName: string): any => {
  if (!relatedModelMetadata.value?.fields) return {};
  return relatedModelMetadata.value.fields[columnName] || {};
};

const getFieldComponent = (columnName: string): any => {
  const type = getColumnType(columnName);
  const meta = getColumnMetadata(columnName);
  
  // Check for priority widget first
  if (meta?.widget === 'priority') return O2MPriorityField;

  switch (type) {
    case 'char': return O2MCharField;
    case 'text': return O2MTextField;
    case 'integer': return O2MIntegerField;
    case 'float': return O2MFloatField;
    case 'boolean': return O2MBooleanField;
    case 'password': return O2MPasswordField;
    case 'image': return O2MImageField;
    case 'many2one': 
      return O2MMany2OneField;
    case 'many2many': return O2MMany2ManyField;
    case 'selection': 
      return O2MSelectionField;
    case 'date': return O2MDateField;
    case 'datetime': return O2MDateTimeField;
    default: 
      return O2MCharField;
  }
};

const getRelationOptions = (columnName: string): any[] => {
  const field = relatedModelMetadata.value?.fields?.[columnName];
  if (!field || field.type !== 'many2one' || !field.relation) return [];
  return relationOptions.value[field.relation] || [];
};

const addNewLine = () => {
  const newRecord: any = {
    _tempId: `temp-${tempIdCounter++}`,
    _isNew: true
  };
  
  displayColumns.value.forEach(col => {
    const field = relatedModelMetadata.value?.fields?.[col];
    newRecord[col] = field?.default !== undefined ? field.default : null;
  });
  
  if (props.metadata.inverse_name) {
    // Pass the parent ID to the new record if available in context
    newRecord[props.metadata.inverse_name] = props.context?.id || null;
  }
  
  localRecords.value.push(newRecord);
  editingIndex.value = localRecords.value.length - 1;
};

const removeRecord = (index: number) => {
  const record = localRecords.value[index];
  
  if (record._isNew || !record.id) {
    localRecords.value.splice(index, 1);
  } else {
    if (!deletedRecordIds.value.includes(record.id)) {
      deletedRecordIds.value.push(record.id);
    }
    localRecords.value.splice(index, 1);
  }
};

const onFieldChange = (index: number, columnName: string, value: any) => {
  const record = localRecords.value[index];
  if (record) {
    record[columnName] = value;
    if (record.id && !record._isNew) {
      record._modified = true;
    }
  }
};

const loadRelatedModelMetadata = async () => {
  if (!props.metadata.relation) return;
  
  try {
    const resp = await api.get(`/models/meta/${props.metadata.relation}`);
    relatedModelMetadata.value = resp.data;
    
    const many2oneColumns = displayColumns.value.filter(col => {
      const field = relatedModelMetadata.value?.fields?.[col];
      return field?.type === 'many2one';
    });
    
    for (const col of many2oneColumns) {
      await loadRelationOptions(col);
    }

    // Now scan local records for any M2O values that might be missing from relationOptions
    localRecords.value.forEach(record => {
      Object.keys(relatedModelMetadata.value.fields).forEach(col => {
         const field = relatedModelMetadata.value.fields[col];
         if (field.type === 'many2one' && field.relation && record[col] && typeof record[col] === 'object') {
           const val = record[col];
           if (val.id && val.display_name) {
             const model = field.relation;
             if (!relationOptions.value[model]) relationOptions.value[model] = [];
             if (!relationOptions.value[model].find(o => o.id === val.id)) {
               relationOptions.value[model].push({ id: val.id, display_name: val.display_name, name: val.display_name });
             }
           }
         }
      });
    });
  } catch (error) {
    emit('error', `Failed to load metadata for ${props.metadata.relation}`);
  }
};

const loadRelationOptions = async (columnName: string) => {
  const field = relatedModelMetadata.value?.fields?.[columnName];
  if (!field || field.type !== 'many2one' || !field.relation) return;
  
  const relationModel = field.relation;
  if (relationOptions.value[relationModel]) return;
  
  try {
    const params: any = {};
    
    // Support dynamic domains for O2M columns
    if (field.domain) {
      try {
        const domainEngine = new DomainEngine();
        // Use props.context (parent form) as standard context for O2M column fetches
        const domainFilters = domainEngine.resolveDomain(field.domain, props.context || {});
        if (domainFilters && domainFilters.length > 0) {
          params.domain = JSON.stringify(domainFilters);
        }
      } catch (e) {
        // Silently skip domain errors
      }
    }

    const resp = await api.get(`/models/${relationModel}`, { params });
    relationOptions.value[relationModel] = resp.data?.items || [];
  } catch (error) {
    relationOptions.value[relationModel] = [];
  }
};

onMounted(() => {
  loadRelatedModelMetadata();
});

const validate = () => {
  cellErrors.value = {};
  let isValid = true;
  
  // If metadata not loaded, we can't validate properly. 
  if (!relatedModelMetadata.value) {
     loadRelatedModelMetadata(); 
  }

  localRecords.value.forEach((record, index) => {
    if (record._deleted) return;
    
    displayColumns.value.forEach(col => {
      const meta = getColumnMetadata(col);
      const val = record[col];
      
      // Strict empty check
      const isEmpty = val === null || val === undefined || val === '' || 
                      (Array.isArray(val) && val.length === 0) ||
                      (typeof val === 'object' && val !== null && !val.id && Object.keys(val).length === 0);

      // Check required
      if (meta.required && isEmpty) {
        cellErrors.value[`${index}-${col}`] = true;
        isValid = false;
      }
    });
  });
  
  return isValid;
};

defineExpose({
  validate
});
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.one2many-znova {
  width: 100%;
  
  &.readonly {
    .o2m-table {
      background: v.$disabled-bg;
    }
  }
}

.o2m-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: v.$text-primary;
  margin-bottom: 8px;
  display: block;
}

.o2m-table-container {
  border: 1px solid v.$border-color;
  border-radius: 6px;
  overflow: hidden;
  background: v.$white;
  max-width: 100%;
  overflow-x: auto;
}

.o2m-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  
  thead {
    background: v.$table-header-bg;
    border-bottom: 1px solid v.$border-color;
  }
  
  .o2m-th {
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
    color: v.$gray-700;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.025em;
    white-space: nowrap;
    border-right: 1px solid v.$table-border;
    
    &:last-child {
      border-right: none;
    }
  }
  
  .o2m-th-actions {
    width: 44px;
    padding: 10px 8px;
    background: v.$table-header-bg;
  }
  
  .o2m-tr {
    border-bottom: 1px solid v.$table-border;
    transition: background 0.1s;
    
    &:hover {
      background: v.$table-hover;
    }
    
    &.o2m-tr-editing {
      background: v.$table-selected;
    }
  }
  
  .o2m-tr-add {
    background: transparent;
    height: 38px; // Match data row height
    
    &:hover {
      background: v.$table-hover;
    }
  }
  
  .o2m-td {
    padding: 0;
    border-right: 1px solid v.$table-border;
    vertical-align: middle;
    height: 38px;
    
    &:last-child {
      border-right: none;
    }
    
    /* Generic input styles removed in favor of component-specific styles */
    
    :deep(.o2m-field-readonly) {
      padding: 8px 12px;
      color: v.$gray-500;
    }
  }
  
  .o2m-td-add {
    padding: 0;
    border-right: none;
  }
  
  .o2m-td-actions {
    padding: 4px 8px;
    text-align: center;
    vertical-align: middle;
    border-right: none;
  }
  
  .o2m-delete {
    background: none;
    border: none;
    padding: 4px;
    cursor: pointer;
    color: v.$disabled-text;
    border-radius: 4px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
    
    &:hover {
      background: v.$light-red-bg;
      color: v.$red-500;
    }
  }
  
  .o2m-empty {
    padding: 40px 20px;
    text-align: center;
    color: v.$disabled-text;
    font-style: italic;
    font-size: 13px;
  }
}

.o2m-add-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 10px 12px;
  color: v.$primary-color;
  font-size: 13px; // Match table body text size
  font-weight: 600; // Match header weight for visibility
  text-decoration: none;
  cursor: pointer;
  transition: all 0.15s;
  width: 100%;
  height: 100%;
  
  &:hover {
    background: rgba(v.$primary-color, 0.05);
  }
}

.required-star {
  color: v.$danger-color;
  margin-left: 2px;
}

// Dark mode styles
[data-theme="dark"] {
  .one2many-znova {
    &.readonly {
      .o2m-table {
        background: #161b22;
      }
    }
  }
  
  .o2m-label {
    color: #e6edf3;
  }
  
  .o2m-table-container {
    background: #0d1117;
    border-color: #30363d;
  }
  
  .o2m-table {
    thead {
      background: #161b22;
      border-bottom-color: #30363d;
    }
    
    .o2m-th {
      color: #7d8590;
      border-right-color: #30363d;
    }
    
    .o2m-th-actions {
      background: #161b22;
    }
    
    .o2m-tr {
      border-bottom-color: #30363d;
      
      &:hover {
        background: #161b22;
      }
      
      &.o2m-tr-editing {
        background: rgba(37, 99, 235, 0.1);
      }
    }
    
    .o2m-tr-add {
      &:hover {
        background: #161b22;
      }
    }
    
    .o2m-td {
      border-right-color: #30363d;
      
      :deep(.o2m-field-readonly) {
        color: #7d8590;
      }
    }
    
    .o2m-delete {
      color: #7d8590;
      
      &:hover {
        background: rgba(248, 81, 73, 0.1);
        color: #f85149;
      }
    }
    
    .o2m-empty {
      color: #7d8590;
    }
  }
  
  .o2m-add-link {
    color: #58a6ff;
    
    &:hover {
      background: rgba(88, 166, 255, 0.1);
    }
  }
  
  .required-star {
    color: #f85149;
  }
}
</style>
