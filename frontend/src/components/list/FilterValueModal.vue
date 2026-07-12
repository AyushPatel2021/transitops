<template>
  <div class="filter-modal-overlay" @click="handleOverlayClick">
    <div class="filter-modal">
      <div class="modal-header">
        <h3>Add Filter: {{ field?.label }}</h3>
        <button @click="$emit('cancel')" class="close-button">
          <X class="icon-sm" />
        </button>
      </div>
      
      <div class="modal-body">
        <!-- Operator Selection -->
        <div class="form-group">
          <label>Condition</label>
          <select v-model="selectedOperator" class="form-select">
            <option v-for="op in availableOperators" :key="op.value" :value="op.value">
              {{ op.label }}
            </option>
          </select>
        </div>
        
        <!-- Value Input -->
        <div class="form-group" v-if="needsValue">
          <label>Value</label>
          
          <!-- Text Input -->
          <input 
            v-if="['char', 'text'].includes(fieldType)"
            v-model="filterValue"
            type="text"
            class="form-input"
            :placeholder="getValuePlaceholder()"
          />
          
          <!-- Number Input -->
          <input 
            v-else-if="['integer', 'float'].includes(fieldType)"
            v-model.number="filterValue"
            type="number"
            class="form-input"
            :step="fieldType === 'float' ? '0.01' : '1'"
          />
          
          <!-- Date Input -->
          <input 
            v-else-if="fieldType === 'date'"
            v-model="filterValue"
            type="date"
            class="form-input"
          />
          
          <!-- DateTime Input -->
          <input 
            v-else-if="fieldType === 'datetime'"
            v-model="filterValue"
            type="datetime-local"
            class="form-input"
          />
          
          <!-- Boolean Select -->
          <select 
            v-else-if="fieldType === 'boolean'"
            v-model="filterValue"
            class="form-select"
          >
            <option value="">Select...</option>
            <option :value="true">Yes</option>
            <option :value="false">No</option>
          </select>
          
          <!-- Selection Field -->
          <select 
            v-else-if="fieldType === 'selection'"
            v-model="filterValue"
            class="form-select"
          >
            <option value="">Select...</option>
            <option 
              v-for="(option, key) in getSelectionOptions()" 
              :key="key" 
              :value="key"
            >
              {{ typeof option === 'object' ? option.label : option }}
            </option>
          </select>
          
          <!-- Many2One Field -->
          <div v-else-if="fieldType === 'many2one'" class="many2one-input">
            <input 
              v-model="many2oneSearch"
              type="text"
              class="form-input"
              :placeholder="`Search ${field?.label}...`"
              @input="searchMany2One"
              @focus="showMany2OneDropdown = true"
            />
            
            <div v-if="showMany2OneDropdown && many2oneOptions.length > 0" class="many2one-dropdown">
              <div 
                v-for="option in many2oneOptions" 
                :key="option.id"
                class="many2one-option"
                @click="selectMany2One(option)"
              >
                {{ option.display_name || option.name || `#${option.id}` }}
              </div>
            </div>
          </div>
          
          <!-- Multiple Values (for 'in' operator) -->
          <div v-else-if="selectedOperator === 'in'" class="multiple-values">
            <div class="value-tags">
              <span 
                v-for="(val, index) in multipleValues" 
                :key="index"
                class="value-tag"
              >
                {{ val }}
                <button @click="removeMultipleValue(index)" class="tag-remove">
                  <X class="icon-xs" />
                </button>
              </span>
            </div>
            <input 
              v-model="newMultipleValue"
              type="text"
              class="form-input"
              placeholder="Add value and press Enter"
              @keydown.enter="addMultipleValue"
            />
          </div>
          
          <!-- Default Text Input -->
          <input 
            v-else
            v-model="filterValue"
            type="text"
            class="form-input"
            :placeholder="getValuePlaceholder()"
          />
        </div>
        
        <!-- Preview -->
        <div class="filter-preview" v-if="isValidFilter">
          <strong>Preview:</strong> 
          {{ field?.label }} {{ getOperatorLabel(selectedOperator) }} {{ getPreviewValue() }}
        </div>
      </div>
      
      <div class="modal-footer">
        <button @click="$emit('cancel')" class="btn btn-secondary">
          Cancel
        </button>
        <button @click="applyFilter" class="btn btn-primary" :disabled="!isValidFilter">
          Apply Filter
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { X } from 'lucide-vue-next';
import api from '../../core/api';

interface Field {
  key: string;
  label: string;
  type: string;
  options?: Record<string, any>;
  relation?: string;
}

interface Operator {
  value: string;
  label: string;
  needsValue: boolean;
}

const props = defineProps<{
  field: Field | null;
  metadata: any;
}>();

const emit = defineEmits(['apply', 'cancel']);

// Refs
const selectedOperator = ref('=');
const filterValue = ref<any>('');
const many2oneSearch = ref('');
const showMany2OneDropdown = ref(false);
const many2oneOptions = ref<any[]>([]);
const multipleValues = ref<string[]>([]);
const newMultipleValue = ref('');

// Computed
const fieldType = computed(() => props.field?.type || '');

const availableOperators = computed<Operator[]>(() => {
  if (!props.field) return [];
  
  const baseOperators: Operator[] = [
    { value: '=', label: 'is equal to', needsValue: true },
    { value: '!=', label: 'is not equal to', needsValue: true }
  ];
  
  if (['char', 'text'].includes(props.field.type)) {
    return [
      ...baseOperators,
      { value: 'ilike', label: 'contains', needsValue: true },
      { value: 'not ilike', label: 'does not contain', needsValue: true },
      { value: 'in', label: 'is in', needsValue: true },
      { value: 'not in', label: 'is not in', needsValue: true }
    ];
  }
  
  if (['integer', 'float', 'date', 'datetime'].includes(props.field.type)) {
    return [
      ...baseOperators,
      { value: '>', label: 'is greater than', needsValue: true },
      { value: '>=', label: 'is greater than or equal to', needsValue: true },
      { value: '<', label: 'is less than', needsValue: true },
      { value: '<=', label: 'is less than or equal to', needsValue: true },
      { value: 'in', label: 'is in', needsValue: true }
    ];
  }
  
  if (props.field.type === 'boolean') {
    return [
      { value: '=', label: 'is', needsValue: true }
    ];
  }
  
  if (['selection', 'many2one'].includes(props.field.type)) {
    return [
      ...baseOperators,
      { value: 'in', label: 'is in', needsValue: true },
      { value: 'not in', label: 'is not in', needsValue: true }
    ];
  }
  
  return baseOperators;
});

const needsValue = computed(() => {
  const operator = availableOperators.value.find(op => op.value === selectedOperator.value);
  return operator?.needsValue ?? true;
});

const isValidFilter = computed(() => {
  if (!needsValue.value) return true;
  
  if (selectedOperator.value === 'in' || selectedOperator.value === 'not in') {
    return multipleValues.value.length > 0;
  }
  
  if (props.field?.type === 'many2one') {
    return filterValue.value && typeof filterValue.value === 'object';
  }
  
  return filterValue.value !== '' && filterValue.value !== null && filterValue.value !== undefined;
});

// Methods
const getSelectionOptions = () => {
  if (!props.field || props.field.type !== 'selection') return {};
  return props.metadata?.fields?.[props.field.key]?.options || {};
};

const getValuePlaceholder = () => {
  if (!props.field) return '';
  
  const placeholders: Record<string, string> = {
    'char': 'Enter text...',
    'text': 'Enter text...',
    'integer': 'Enter number...',
    'float': 'Enter decimal number...',
    'date': 'Select date...',
    'datetime': 'Select date and time...'
  };
  
  return placeholders[props.field.type] || 'Enter value...';
};

const getOperatorLabel = (operator: string) => {
  const op = availableOperators.value.find(o => o.value === operator);
  return op?.label || operator;
};

const getPreviewValue = () => {
  if (selectedOperator.value === 'in' || selectedOperator.value === 'not in') {
    return `[${multipleValues.value.join(', ')}]`;
  }
  
  if (props.field?.type === 'selection') {
    const options = getSelectionOptions();
    const option = options[filterValue.value];
    return typeof option === 'object' ? option.label : option || filterValue.value;
  }
  
  if (props.field?.type === 'many2one' && typeof filterValue.value === 'object') {
    return filterValue.value.display_name || filterValue.value.name || `#${filterValue.value.id}`;
  }
  
  if (props.field?.type === 'boolean') {
    return filterValue.value ? 'Yes' : 'No';
  }
  
  return String(filterValue.value);
};

const searchMany2One = async () => {
  if (!props.field?.relation || many2oneSearch.value.length < 2) {
    many2oneOptions.value = [];
    return;
  }
  
  try {
    const response = await api.get(`/models/${props.field.relation}`, {
      params: {
        search: many2oneSearch.value,
        limit: 10
      }
    });
    
    many2oneOptions.value = response.data.items || response.data || [];
  } catch (error) {
    // Failed to search many2one options - handle silently
    many2oneOptions.value = [];
  }
};

const selectMany2One = (option: any) => {
  filterValue.value = option;
  many2oneSearch.value = option.display_name || option.name || `#${option.id}`;
  showMany2OneDropdown.value = false;
};

const addMultipleValue = () => {
  if (newMultipleValue.value.trim() && !multipleValues.value.includes(newMultipleValue.value.trim())) {
    multipleValues.value.push(newMultipleValue.value.trim());
    newMultipleValue.value = '';
  }
};

const removeMultipleValue = (index: number) => {
  multipleValues.value.splice(index, 1);
};

const applyFilter = () => {
  if (!isValidFilter.value || !props.field) return;
  
  let value = filterValue.value;
  let displayValue = '';
  
  if (selectedOperator.value === 'in' || selectedOperator.value === 'not in') {
    value = multipleValues.value;
    displayValue = `[${multipleValues.value.join(', ')}]`;
  } else if (props.field.type === 'selection') {
    const options = getSelectionOptions();
    const option = options[value];
    displayValue = typeof option === 'object' ? option.label : option || value;
  } else if (props.field.type === 'many2one' && typeof value === 'object') {
    displayValue = value.display_name || value.name || `#${value.id}`;
    value = value.id; // Store just the ID for the filter
  } else if (props.field.type === 'boolean') {
    displayValue = value ? 'Yes' : 'No';
  } else {
    displayValue = String(value);
  }
  
  emit('apply', {
    operator: selectedOperator.value,
    value,
    displayValue
  });
};

const handleOverlayClick = (e: MouseEvent) => {
  if (e.target === e.currentTarget) {
    emit('cancel');
  }
};

// Watch for field changes to reset form
watch(() => props.field, (newField) => {
  if (newField) {
    selectedOperator.value = '=';
    filterValue.value = '';
    many2oneSearch.value = '';
    multipleValues.value = [];
    newMultipleValue.value = '';
    showMany2OneDropdown.value = false;
    many2oneOptions.value = [];
  }
}, { immediate: true });

// Watch for operator changes
watch(selectedOperator, (newOperator) => {
  if (newOperator === 'in' || newOperator === 'not in') {
    if (filterValue.value && !multipleValues.value.includes(String(filterValue.value))) {
      multipleValues.value = [String(filterValue.value)];
    }
  } else {
    multipleValues.value = [];
  }
});

onMounted(() => {
  // Focus on the first input when modal opens
  const firstInput = document.querySelector('.filter-modal input, .filter-modal select') as HTMLElement;
  if (firstInput) {
    firstInput.focus();
  }
});
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.filter-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: v.$overlay-modal;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(2px);
}

.filter-modal {
  background: v.$white;
  border-radius: 12px;
  box-shadow: 0 20px 60px v.$shadow-darker;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid v.$border-color;
  
  h3 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: v.$text-primary;
  }
  
  .close-button {
    background: none;
    border: none;
    color: v.$text-secondary;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    
    &:hover {
      background: v.$border-light;
      color: v.$text-primary;
    }
  }
}

.modal-body {
  padding: 24px;
  flex: 1;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 20px;
  
  label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: v.$text-primary;
    font-size: 0.875rem;
  }
}

.form-input, .form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid v.$border-color;
  border-radius: 6px;
  font-size: 0.875rem;
  color: v.$text-primary;
  background: v.$white;
  transition: border-color 0.2s;
  
  &:focus {
    outline: none;
    border-color: v.$primary-color;
    box-shadow: 0 0 0 2px rgba(v.$primary-color, 0.1);
  }
  
  &::placeholder {
    color: v.$text-placeholder;
  }
}

.many2one-input {
  position: relative;
}

.many2one-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: v.$radius-btn;
  box-shadow: 0 4px 6px -1px v.$shadow-light;
  z-index: 1000;
  max-height: 200px;
  overflow-y: auto;
  margin-top: 4px;
  min-height: 40px;
}

.many2one-option {
  padding: 10px 12px;
  cursor: pointer;
  font-size: 0.875rem;
  color: v.$text-primary;
  transition: background 0.15s;
  
  &:hover {
    background: v.$border-light;
  }
}

.multiple-values {
  .value-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 8px;
  }
  
  .value-tag {
    display: flex;
    align-items: center;
    background: v.$primary-color;
    color: v.$white;
    border-radius: 16px;
    padding: 4px 8px 4px 12px;
    font-size: 0.75rem;
    font-weight: 500;
    gap: 4px;
    
    .tag-remove {
      background: none;
      border: none;
      color: v.$white;
      cursor: pointer;
      padding: 2px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0.8;
      
      &:hover {
        opacity: 1;
        background: v.$white-transparent-20;
      }
    }
  }
}

.filter-preview {
  background: v.$border-light;
  border: 1px solid v.$border-color;
  border-radius: 6px;
  padding: 12px;
  font-size: 0.875rem;
  color: v.$text-secondary;
  margin-top: 16px;
  
  strong {
    color: v.$text-primary;
  }
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid v.$border-color;
  background: v.$bg-main;
}

.btn {
  padding: 10px 20px;
  border-radius: v.$radius-btn;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  &.btn-secondary {
    background: v.$border-color;
    color: v.$text-primary;
    
    &:hover:not(:disabled) {
      background: v.$text-secondary;
    }
  }
  
  &.btn-primary {
    background: v.$primary-color;
    color: v.$white;
    
    &:hover:not(:disabled) {
      background: v.$primary-hover;
    }
  }
}

.icon-xs {
  width: 12px;
  height: 12px;
}

.icon-sm {
  width: 16px;
  height: 16px;
}

// Mobile responsiveness
@media (max-width: 768px) {
  .filter-modal {
    width: 95%;
    margin: 20px;
  }
  
  .modal-header, .modal-body, .modal-footer {
    padding: 16px 20px;
  }
}
</style>
