<template>
  <transition name="wizard-fade">
    <div v-if="show" class="wizard-dialog-overlay" @mousedown.self="emit('close')">
    <div class="wizard-dialog">
      <!-- Header -->
      <div class="wizard-header">
        <div class="wizard-title">
          <h3>{{ computedTitle }}</h3>
          <p v-if="metadata?.description && metadata.description !== computedTitle" class="wizard-subtitle">{{ metadata.description }}</p>
        </div>
        <button class="close-button" @click="handleCancel">
          <X class="icon-sm" />
        </button>
      </div>

      <!-- Content -->
      <div class="wizard-content">
        <template v-if="loading">
          <div class="loading-state">
            <span class="spinner"></span>
            <p>Loading wizard...</p>
          </div>
        </template>
        
        <template v-else-if="metadata && recordData">
          <div v-if="error" class="error-banner">
            <AlertTriangle class="icon-sm" />
            <span>{{ error }}</span>
          </div>
          
          <div class="form-grid">
            <template v-if="metadata.views?.form?.groups">
              <!-- Render Groups -->
              <template v-for="(group, gIndex) in metadata.views.form.groups" :key="gIndex">
                <div class="form-group">
                  <h4 v-if="group.title" class="group-title">{{ group.title }}</h4>
                  <div class="fields-container">
                    <template v-for="fieldName in group.fields" :key="fieldName">
                      <div v-if="metadata.fields[fieldName] && isFieldVisible(fieldName)" class="field-item">
                        <label :class="{ 
                          'required-label': isFieldRequired(fieldName)
                        }">
                          {{ metadata.fields[fieldName].label }}
                        </label>
                        
                        <div class="field-wrapper">
                          <!-- Show as display value when readonly for simple fields -->
                          <div v-if="isFieldReadonly(fieldName) && !['one2many', 'many2many'].includes(metadata.fields[fieldName]?.type)" class="view-value">
                            {{ formatValue(getFieldValue(fieldName), metadata.fields[fieldName]?.type, metadata.fields[fieldName]) }}
                          </div>
                          
                          <!-- Editable fields -->
                          <template v-else>
                            <!-- One2many Field -->
                            <One2manyField 
                                v-if="metadata.fields[fieldName]?.type === 'one2many'"
                                :modelValue="getFieldValue(fieldName) || []"
                                :metadata="metadata.fields[fieldName]"
                                :invalid="showValidationErrors && isFieldRequired(fieldName) && (!getFieldValue(fieldName) || getFieldValue(fieldName).length === 0)"
                                :readonly="isFieldReadonly(fieldName)"
                                :context="recordData"
                                @update:modelValue="(val: any) => updateField(fieldName, val)"
                            />
                            
                            <!-- Many2many Field -->
                            <Many2manyField 
                                v-else-if="metadata.fields[fieldName]?.type === 'many2many'"
                                :modelValue="getFieldValue(fieldName) || []"
                                :metadata="metadata.fields[fieldName]"
                                :invalid="showValidationErrors && isFieldRequired(fieldName) && (!getFieldValue(fieldName) || getFieldValue(fieldName).length === 0)"
                                :readonly="isFieldReadonly(fieldName)"
                                :context="recordData"
                                @update:modelValue="(val: any) => updateField(fieldName, val)"
                            />
                            
                            <!-- Many2one Field -->
                            <Many2oneField 
                                v-else-if="metadata.fields[fieldName]?.type === 'many2one'"
                                :modelValue="getFieldValue(fieldName) && typeof getFieldValue(fieldName) === 'object' ? getFieldValue(fieldName).id : getFieldValue(fieldName)" 
                                :options="getOptions(metadata.fields[fieldName], fieldName)"
                                :invalid="showValidationErrors && isFieldRequired(fieldName) && isFieldEmpty(getFieldValue(fieldName))"
                                :readonly="isFieldReadonly(fieldName)"
                                @update:modelValue="(val: any) => updateField(fieldName, val)"
                                @focus="handleRelationFocus(metadata.fields[fieldName].relation, fieldName)"
                            />
                            
                            <!-- Selection Field -->
                            <SelectionField 
                                v-else-if="metadata.fields[fieldName]?.type === 'selection'"
                                :modelValue="getFieldValue(fieldName)" 
                                :options="getOptions(metadata.fields[fieldName])"
                                :invalid="showValidationErrors && isFieldRequired(fieldName) && !getFieldValue(fieldName)"
                                :readonly="isFieldReadonly(fieldName)"
                                @update:modelValue="(val: any) => updateField(fieldName, val)"
                            />
                            
                            <!-- Date Field -->
                            <DateField 
                                v-else-if="metadata.fields[fieldName]?.type === 'date'"
                                :modelValue="getFieldValue(fieldName)"
                                :invalid="showValidationErrors && isFieldRequired(fieldName) && !getFieldValue(fieldName)"
                                :readonly="isFieldReadonly(fieldName)"
                                @update:modelValue="(val: any) => updateField(fieldName, val)"
                            />
                            
                            <!-- DateTime Field -->
                            <DateTimeField 
                                v-else-if="metadata.fields[fieldName]?.type === 'datetime'"
                                :modelValue="getFieldValue(fieldName)"
                                :invalid="showValidationErrors && isFieldRequired(fieldName) && !getFieldValue(fieldName)"
                                :readonly="isFieldReadonly(fieldName)"
                                @update:modelValue="(val: any) => updateField(fieldName, val)"
                            />
                            
                            <!-- Boolean Field -->
                            <BooleanField 
                                v-else-if="metadata.fields[fieldName]?.type === 'boolean'"
                                :modelValue="getFieldValue(fieldName)"
                                :invalid="showValidationErrors && isFieldRequired(fieldName) && !getFieldValue(fieldName)"
                                :readonly="isFieldReadonly(fieldName)"
                                @update:modelValue="(val: any) => updateField(fieldName, val)"
                            />
                            
                            <!-- Password Field -->
                            <PasswordField 
                                v-else-if="metadata.fields[fieldName]?.type === 'password'"
                                :modelValue="getFieldValue(fieldName)"
                                :invalid="showValidationErrors && isFieldRequired(fieldName) && !getFieldValue(fieldName)"
                                :readonly="isFieldReadonly(fieldName)"
                                :showRequirements="true"
                                :placeholder="metadata.fields[fieldName]?.label"
                                @update:modelValue="(val: any) => updateField(fieldName, val)"
                            />
                            
                            <!-- Image Field -->
                            <ImageField 
                                v-else-if="metadata.fields[fieldName]?.type === 'image'"
                                :modelValue="getFieldValue(fieldName)"
                                :label="metadata.fields[fieldName]?.label"
                                :metadata="metadata.fields[fieldName]"
                                :invalid="showValidationErrors && isFieldRequired(fieldName) && !getFieldValue(fieldName)"
                                :readonly="isFieldReadonly(fieldName)"
                                @update:modelValue="(val: any) => updateField(fieldName, val)"
                            />
                            
                            <!-- Text Area -->
                            <textarea
                              v-else-if="metadata.fields[fieldName]?.type === 'text'"
                              :id="fieldName"
                              class="form-control"
                              :value="getFieldValue(fieldName)"
                              @input="(e: any) => updateField(fieldName, (e.target as HTMLTextAreaElement).value)"
                              :readonly="isFieldReadonly(fieldName)"
                              :placeholder="metadata.fields[fieldName].label"
                              :class="{ 'field-invalid': showValidationErrors && isFieldRequired(fieldName) && !getFieldValue(fieldName) }"
                              rows="4"
                            ></textarea>
                            
                            <!-- Default Input -->
                            <input
                              v-else
                              :id="fieldName"
                              :type="metadata.fields[fieldName]?.type === 'integer' || metadata.fields[fieldName]?.type === 'float' ? 'number' : 'text'"
                              :step="metadata.fields[fieldName]?.type === 'float' ? '0.01' : metadata.fields[fieldName]?.type === 'integer' ? '1' : undefined"
                              class="form-control"
                              :value="getFieldValue(fieldName)"
                              @input="(e: any) => updateField(fieldName, (e.target as HTMLInputElement).value)"
                              :readonly="isFieldReadonly(fieldName)"
                              :placeholder="metadata.fields[fieldName].label"
                              :class="{ 'field-invalid': showValidationErrors && isFieldRequired(fieldName) && !getFieldValue(fieldName) }"
                            />
                          </template>
                        </div>
                      </div>
                    </template>
                  </div>
                </div>
              </template>
            </template>
            
            <template v-else>
              <!-- Fallback: Render all fields flat -->
              <div class="fields-container">
                <template v-for="(field, name) in metadata.fields" :key="name">
                  <div v-if="isFieldVisible(name.toString())" class="field-item">
                    <label :class="{ 
                      'required-label': isFieldRequired(name.toString())
                    }">
                      {{ field.label }}
                    </label>
                    
                    <div class="field-wrapper">
                      <!-- Same field rendering logic as above -->
                      <div v-if="isFieldReadonly(name.toString()) && !['one2many', 'many2many'].includes(field?.type)" class="view-value">
                        {{ formatValue(getFieldValue(name.toString()), field?.type, field) }}
                      </div>
                      
                      <template v-else>
                        <One2manyField 
                            v-if="field?.type === 'one2many'"
                            :modelValue="getFieldValue(name.toString()) || []"
                            :metadata="field"
                            :invalid="showValidationErrors && isFieldRequired(name.toString()) && (!getFieldValue(name.toString()) || getFieldValue(name.toString()).length === 0)"
                            :readonly="isFieldReadonly(name.toString())"
                            :context="recordData"
                            @update:modelValue="(val: any) => updateField(name.toString(), val)"
                        />
                        <Many2manyField 
                            v-else-if="field?.type === 'many2many'"
                            :modelValue="getFieldValue(name.toString()) || []"
                            :metadata="field"
                            :invalid="showValidationErrors && isFieldRequired(name.toString()) && (!getFieldValue(name.toString()) || getFieldValue(name.toString()).length === 0)"
                            :readonly="isFieldReadonly(name.toString())"
                            :context="recordData"
                            @update:modelValue="(val: any) => updateField(name.toString(), val)"
                        />
                        <Many2oneField 
                            v-else-if="field?.type === 'many2one'"
                            :modelValue="getFieldValue(name.toString()) && typeof getFieldValue(name.toString()) === 'object' ? getFieldValue(name.toString()).id : getFieldValue(name.toString())" 
                            :options="getOptions(field, name.toString())"
                            :invalid="showValidationErrors && isFieldRequired(name.toString()) && isFieldEmpty(getFieldValue(name.toString()))"
                            :readonly="isFieldReadonly(name.toString())"
                            @update:modelValue="(val: any) => updateField(name.toString(), val)"
                            @focus="handleRelationFocus(field.relation, name.toString())"
                        />
                        <SelectionField 
                            v-else-if="field?.type === 'selection'"
                            :modelValue="getFieldValue(name.toString())" 
                            :options="getOptions(field)"
                            :invalid="showValidationErrors && isFieldRequired(name.toString()) && !getFieldValue(name.toString())"
                            :readonly="isFieldReadonly(name.toString())"
                            @update:modelValue="(val: any) => updateField(name.toString(), val)"
                        />
                        <DateField 
                            v-else-if="field?.type === 'date'"
                            :modelValue="getFieldValue(name.toString())"
                            :invalid="showValidationErrors && isFieldRequired(name.toString()) && !getFieldValue(name.toString())"
                            :readonly="isFieldReadonly(name.toString())"
                            @update:modelValue="(val: any) => updateField(name.toString(), val)"
                        />
                        <DateTimeField 
                            v-else-if="field?.type === 'datetime'"
                            :modelValue="getFieldValue(name.toString())"
                            :invalid="showValidationErrors && isFieldRequired(name.toString()) && !getFieldValue(name.toString())"
                            :readonly="isFieldReadonly(name.toString())"
                            @update:modelValue="(val: any) => updateField(name.toString(), val)"
                        />
                        <BooleanField 
                            v-else-if="field?.type === 'boolean'"
                            :modelValue="getFieldValue(name.toString())"
                            :invalid="showValidationErrors && isFieldRequired(name.toString()) && !getFieldValue(name.toString())"
                            :readonly="isFieldReadonly(name.toString())"
                            @update:modelValue="(val: any) => updateField(name.toString(), val)"
                        />
                        <PasswordField 
                            v-else-if="field?.type === 'password'"
                            :modelValue="getFieldValue(name.toString())"
                            :invalid="showValidationErrors && isFieldRequired(name.toString()) && !getFieldValue(name.toString())"
                            :readonly="isFieldReadonly(name.toString())"
                            :showRequirements="true"
                            :placeholder="field?.label"
                            @update:modelValue="(val: any) => updateField(name.toString(), val)"
                        />
                        <ImageField 
                            v-else-if="field?.type === 'image'"
                            :modelValue="getFieldValue(name.toString())"
                            :label="field?.label"
                            :metadata="field"
                            :invalid="showValidationErrors && isFieldRequired(name.toString()) && !getFieldValue(name.toString())"
                            :readonly="isFieldReadonly(name.toString())"
                            @update:modelValue="(val: any) => updateField(name.toString(), val)"
                        />
                        <textarea
                          v-else-if="field?.type === 'text'"
                          :id="name.toString()"
                          class="form-control"
                          :value="getFieldValue(name.toString())"
                          @input="(e: any) => updateField(name.toString(), (e.target as HTMLTextAreaElement).value)"
                          :readonly="isFieldReadonly(name.toString())"
                          :placeholder="field.label"
                          :class="{ 'field-invalid': showValidationErrors && isFieldRequired(name.toString()) && !getFieldValue(name.toString()) }"
                          rows="4"
                        ></textarea>
                        <input
                          v-else
                          :id="name.toString()"
                          :type="field?.type === 'integer' || field?.type === 'float' ? 'number' : 'text'"
                          class="form-control"
                          :value="getFieldValue(name.toString())"
                          @input="(e: any) => updateField(name.toString(), (e.target as HTMLInputElement).value)"
                          :readonly="isFieldReadonly(name.toString())"
                          :placeholder="field.label"
                          :class="{ 'field-invalid': showValidationErrors && isFieldRequired(name.toString()) && !getFieldValue(name.toString()) }"
                        />
                      </template>
                    </div>
                  </div>
                </template>
              </div>
            </template>
          </div>
        </template>
      </div>

      <!-- Footer Actions -->
      <div class="wizard-footer">
        <button class="btn btn-secondary" @click="handleCancel" :disabled="executing">
          Cancel
        </button>
        
        <template v-if="wizardButtons.length > 0">
           <button 
            v-for="btn in wizardButtons" 
            :key="btn.name"
            class="btn"
            :class="[
              btn.type === 'primary' ? 'btn-primary' : 'btn-secondary',
              { 'btn-disabled': executing }
            ]"
            @click="handleWizardAction(btn)"
            :disabled="executing"
            :title="btn.label"
          >
            <span v-if="executing && currentAction === btn.name" class="mini-spinner"></span>
            {{ btn.label }}
          </button>
        </template>
        <template v-else>
          <!-- Default Confirm Button -->
            <button 
              class="btn btn-primary" 
              @click="handleDefaultConfirm"
              :disabled="executing || loading"
              title="Confirm and submit"
            >
              <span v-if="executing" class="mini-spinner"></span>
              <span v-else>Confirm</span>
            </button>
        </template>
      </div>
    </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, ref, watch, reactive, nextTick, onMounted, onUnmounted } from 'vue';
import { X, AlertTriangle } from 'lucide-vue-next';
import api from '../../core/api';
import { useNotifications } from '../../composables/useNotifications';
import { useFieldVisibility } from '../../composables/useFieldVisibility';
import { DomainEngine } from '../../core/domain-engine';
import { formatDateTime, formatDate } from '../../utils/dateUtils';

// Import all field components
import BooleanField from '../form/BooleanField.vue';
import DateField from '../form/DateField.vue';
import DateTimeField from '../form/DateTimeField.vue';
import SelectionField from '../form/SelectionField.vue';
import Many2oneField from '../form/Many2OneField.vue';
import One2manyField from '../form/One2manyField.vue';
import Many2manyField from '../form/Many2manyField.vue';
import PasswordField from '../form/PasswordField.vue';
import ImageField from '../form/ImageField.vue';

const props = defineProps({
  show: Boolean,
  loading: Boolean,
  modelName: String,
  wizardId: Number,
  metadata: Object,
  initialData: Object
});

const emit = defineEmits(['close', 'action-complete']);
const { add } = useNotifications();

const executing = ref(false);
const recordData = ref<any>({});
const error = ref<string | null>(null);
const currentAction = ref<string | null>(null);
const relations = reactive<any>({});
const showValidationErrors = ref(false);

// Initialize reactive copies for field visibility
const reactiveRecordData = reactive<any>({});
const reactiveMetadata = reactive<any>({});

// Sync reactive copies with props
watch([() => props.show, () => props.initialData], ([show, data]) => {
  if (show && data) {
    recordData.value = { ...data };
    Object.assign(reactiveRecordData, data);
    error.value = null;
    showValidationErrors.value = false;
  } else if (!show) {
    // Clear validation state when wizard is closed
    showValidationErrors.value = false;
    error.value = null;
  }
}, { immediate: true });

watch(() => props.metadata, (newMeta) => {
  if (newMeta) {
    Object.assign(reactiveMetadata, newMeta);
  }
}, { deep: true, immediate: true });

// Initialize field visibility composable
const { 
  isFieldVisible, 
  isFieldReadonly, 
  isFieldRequired,
  evaluateDomain,
  forceLocalEvaluation
} = useFieldVisibility(
  computed(() => reactiveMetadata),
  computed(() => reactiveRecordData)
);

const computedTitle = computed(() => {
  return props.metadata?.description || 'Wizard';
});

const wizardButtons = computed(() => {
  return props.metadata?.views?.form?.wizard_buttons || [];
});

// Format value for display
const formatValue = (value: any, type: string, field: any) => {
    if (value === null || value === undefined) return '';
    if (type === 'boolean') return value ? 'Yes' : 'No';
    
    if (type === 'date' || type === 'datetime') {
        if (value && typeof value === 'string') {
            try {
                if (type === 'date') {
                    return formatDate(value);
                } else {
                    return formatDateTime(value);
                }
            } catch {
                // Ignore date parsing errors
            }
        }
        return value || '';
    }
    
    if (type === 'many2one' && typeof value === 'object') {
        return value.display_name || value.name || value.full_name || value.id;
    }

    if (type === 'selection') {
        if (Array.isArray(field.selection)) {
            const option = field.selection.find(([val]: any) => val === value);
            return option ? option[1] : value;
        }
        if (field.options && typeof field.options === 'object') {
            const opt = field.options[value];
            return typeof opt === 'object' ? opt.label : opt;
        }
        return value;
    }
    
    if (type === 'many2one' && relations[field.relation]) {
        const rel = relations[field.relation].find((r: any) => r.id === value);
        return rel ? (rel.display_name || rel.name || rel.full_name || rel.subject) : `#${value}`;
    }
    
    if (type === 'many2many') {
        if (!Array.isArray(value)) return '';
        const names = value.map((item: any) => {
            if (typeof item === 'object') {
                return item.display_name || item.name || item.full_name || item.subject || `#${item.id}`;
            }
            return item;
        });
        return names.join(', ');
    }
    
    if (type === 'one2many') {
        if (!Array.isArray(value)) return '';
        const count = value.filter((item: any) => !item._deleted).length;
        return `${count} record${count !== 1 ? 's' : ''}`;
    }
    
    if (type === 'image') {
        return value ? 'Image uploaded' : 'No image';
    }
    
    if (type === 'password') {
        return value ? '••••••••' : '';
    }
    
    return value;
};

const getOptions = (field: any, fieldName?: string) => {
    if (!field) return [];
    if (field.type === 'selection') {
        if (field.selection && Array.isArray(field.selection)) {
            return field.selection.map(([val, label]: any) => ({ val, label }));
        }
        if (field.options && typeof field.options === 'object') {
            return Object.entries(field.options).map(([val, opt]: any) => ({ val, label: opt.label || opt }));
        }
        return [];
    }
    if (field.type === 'many2one') {
        if (fieldName && relations[fieldName]) {
             return (relations[fieldName] || []).map((r: any) => ({ 
                val: r.id, 
                label: r.display_name || r.name || r.full_name || r.subject || `#${r.id}` 
            }));
        }
        return (relations[field.relation] || []).map((r: any) => ({ 
            val: r.id, 
            label: r.display_name || r.name || r.full_name || r.subject || `#${r.id}` 
        }));
    }
    return [];
};

const handleRelationFocus = async (modelName: string, fieldName?: string) => {
    let relationKey = modelName;
    let params: any = {};
    let isDynamic = false;
    
    if (fieldName) {
         const field = props.metadata?.fields[fieldName];
         if (field && field.domain) {
              try {
                  const engine = new DomainEngine();
                  const domain = engine.resolveDomain(field.domain, recordData.value);
                  if (domain.length) {
                      params.domain = JSON.stringify(domain);
                      relationKey = fieldName;
                      isDynamic = true;
                  }
              } catch(e) { 
                  // Silently handle domain resolution errors
              }
         }
    }

    if (isDynamic || !relations[relationKey]) {
        try {
            const resp = await api.get(`/models/${modelName}`, { params });
            relations[relationKey] = resp.data?.items || (Array.isArray(resp.data) ? resp.data : []);
        } catch (e) {
            // Relational fetch error - silently fail
        }
    }
};

const getFieldValue = (fieldName: string) => {
  return recordData.value?.[fieldName];
};

const isFieldEmpty = (value: any): boolean => {
  // Handle null, undefined, empty string
  if (value === null || value === undefined || value === '') return true;
  
  // Handle many2one fields (can be object or ID)
  if (typeof value === 'object' && value !== null) {
    // If it's an object with an id property, check if id is empty
    if ('id' in value) {
      return value.id === null || value.id === undefined || value.id === '';
    }
    // For other objects, consider them not empty
    return false;
  }
  
  // Handle arrays (one2many, many2many)
  if (Array.isArray(value)) {
    // Filter out deleted records
    const activeRecords = value.filter((item: any) => !item._deleted);
    return activeRecords.length === 0;
  }
  
  // Handle boolean false (false is a valid value, not empty)
  if (typeof value === 'boolean') {
    return false;
  }
  
  // Handle number 0 (0 is a valid value, not empty)
  if (typeof value === 'number') {
    return false;
  }
  
  return false;
};

const updateField = (fieldName: string, value: any) => {
  if (!recordData.value) recordData.value = {};
  
  // Parse integer and float values
  const field = (props.metadata as any)?.fields?.[fieldName];
  if (field) {
    if (field.type === 'integer') {
      // Parse as integer
      if (value === '' || value === null || value === undefined) {
        value = null;
      } else {
        const parsed = parseInt(value, 10);
        value = isNaN(parsed) ? null : parsed;
      }
    } else if (field.type === 'float') {
      // Parse as float
      if (value === '' || value === null || value === undefined) {
        value = null;
      } else {
        const parsed = parseFloat(value);
        value = isNaN(parsed) ? null : parsed;
      }
    }
  }
  
  recordData.value[fieldName] = value;
  reactiveRecordData[fieldName] = value;
  
  // Force local domain evaluation immediately when form data changes
  nextTick(() => {
    forceLocalEvaluation();
  });
};

// Actions
const handleCancel = () => {
  emit('close');
};

const handleWizardAction = async (btn: any) => {
  if (!props.modelName || !props.wizardId) {
    console.error('Cannot execute wizard action: modelName or wizardId is missing', { 
      modelName: props.modelName, 
      wizardId: props.wizardId 
    });
    return;
  }

  if (executing.value) return;
  
  // CRITICAL: Validate form BEFORE submission (like BaseForm save button)
  if (!validateForm()) {
    // Validation failed - do not proceed with submission
    return;
  }
  
  executing.value = true;
  currentAction.value = btn.name;
  error.value = null;
  
  try {
    // 1. Execute the wizard method
    const response = await api.post(
      `/models/${props.modelName}/${props.wizardId}/wizard_execute/${btn.method}`,
      recordData.value // Send current form data
    );
    
    // 2. Handle result
    const result = response.data;
    
    // If result is an action (e.g. close_wizard), emit it
    if (result && result.type) {
      emit('action-complete', result);
    } else {
      emit('close');
    }
    
  } catch (err: any) {
    console.error('Wizard execution error:', err);
    error.value = err.response?.data?.detail || err.message || 'An error occurred';
    
    add({
      type: 'danger',
      message: error.value || 'An error occurred',
      title: 'Execution Error',
      sticky: false
    });
  } finally {
    executing.value = false;
    currentAction.value = null;
  }
};

const handleDefaultConfirm = () => {
  // If no buttons defined, look for action_confirm
  handleWizardAction({ name: 'confirm', method: 'action_confirm' });
};

const validateForm = () => {
  let isValid = true;
  const missingFields: string[] = [];
  
  // Validate all fields in metadata
  for (const [fieldName, field] of Object.entries(props.metadata?.fields || {})) {
    const f: any = field;
    
    // Skip validation for invisible or readonly fields
    if (!isFieldVisible(fieldName) || isFieldReadonly(fieldName)) {
      continue;
    }
    
    // Check if field is required
    if (isFieldRequired(fieldName)) {
      const val = recordData.value[fieldName];
      
      // Check if field is empty
      if (isFieldEmpty(val)) {
        const fieldLabel = f.label || fieldName;
        missingFields.push(fieldLabel);
        isValid = false;
      }
    }
  }
  
  if (!isValid) {
    showValidationErrors.value = true;
    
    const message = `Please fill in the following required fields: ${missingFields.join(', ')}`;
    
    add({
      title: 'Validation Error',
      message: message,
      type: 'danger',
      duration: 5000,
      sticky: false
    });
  } else {
    // Clear validation errors if form is valid
    showValidationErrors.value = false;
  }
  
  return isValid;
};

// Watch for reactive form data changes to trigger domain re-evaluation
watch(reactiveRecordData, (newData, oldData) => {
  if (newData && oldData) {
    const changedFields = Object.keys(newData).filter(key => 
      newData[key] !== oldData[key]
    );
    
    if (changedFields.length > 0) {
      nextTick(() => {
        forceLocalEvaluation();
      });
    }
  }
}, { deep: true });

// Handle Escape key to close wizard
const handleEscape = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && props.show && !executing.value) {
    handleCancel();
  }
};

onMounted(() => {
  window.addEventListener('keydown', handleEscape);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleEscape);
});
</script>

<style lang="scss" scoped>
@use "sass:color";
@use "../../styles/variables" as v;

.wizard-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: v.$black-transparent-40;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(2px);
  animation: fadeIn 0.15s ease-out;
}

.wizard-dialog {
  background: v.$white;
  border-radius: v.$radius-lg;
  box-shadow: v.$shadow-lg;
  width: 700px;
  max-width: 95vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  animation: scaleIn 0.15s ease-out;
}

.wizard-header {
  padding: 1.5rem;
  border-bottom: 1px solid v.$border-color;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  
  .wizard-title {
    h3 {
      margin: 0;
      font-size: 1.25rem;
      font-weight: 600;
      color: v.$text-primary;
    }
    .wizard-subtitle {
      margin: 4px 0 0;
      font-size: 0.875rem;
      color: v.$text-secondary;
    }
  }
  
  .close-button {
    background: none;
    border: none;
    color: v.$text-secondary;
    cursor: pointer;
    padding: 6px;
    border-radius: v.$radius-btn;
    
    &:hover {
      background: v.$bg-main;
      color: v.$text-primary;
    }
  }
}

.wizard-content {
  padding: 1.5rem;
  flex: 1;
  overflow-y: auto;
  
  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    color: v.$text-secondary;
    gap: 1rem;
  }
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.group-title {
  margin: 0 0 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  color: v.$text-secondary;
  letter-spacing: 0.05em;
  border-bottom: 1px solid v.$border-color;
  padding-bottom: 0.5rem;
}

.fields-container {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.25rem;
}

.wizard-footer {
  padding: 1.25rem 1.5rem;
  border-top: 1px solid v.$border-color;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  background: v.$bg-main;
  border-radius: 0 0 v.$radius-lg v.$radius-lg;
  
  .btn {
    padding: 0.625rem 1.25rem;
    border-radius: v.$radius-btn;
    font-weight: 500;
    font-size: 0.875rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: all 0.2s;
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    
    &.btn-disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    
    &.btn-primary {
      background: v.$primary-color;
      color: v.$white;
      border: 1px solid transparent;
      &:hover:not(:disabled) { 
        background: v.$primary-hover;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      }
      &:active:not(:disabled) {
        transform: translateY(0);
      }
    }
    
    &.btn-secondary {
      background: v.$white;
      color: v.$text-primary;
      border: 1px solid v.$border-color;
      &:hover:not(:disabled) { 
        background: v.$bg-main;
        border-color: v.$text-disabled;
      }
    }
  }
}

.error-banner {
  background: v.$danger-bg;
  border: 1px solid v.$danger-border;
  color: v.$danger-color;
  padding: 0.75rem;
  border-radius: v.$radius-md;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.875rem;
}

.mini-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid v.$white-transparent-30;
  border-top: 2px solid v.$white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid v.$border-color;
  border-top: 3px solid v.$primary-color;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes scaleIn { 
  from { opacity: 0; transform: scale(0.95); } 
  to { opacity: 1; transform: scale(1); } 
}

.icon-sm { width: 18px; height: 18px; }

.wizard-fade-enter-active, .wizard-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
  
  .wizard-dialog {
    transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
}

.wizard-fade-enter-from, .wizard-fade-leave-to {
  opacity: 0;
  
  .wizard-dialog {
    transform: scale(0.95) translateY(10px);
  }
}

.field-item {
  display: grid;
  grid-template-columns: 140px 1fr;
  align-items: center;
  min-height: 40px;
  gap: 1rem;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 0.25rem;
    align-items: flex-start;
  }
}

label {
  font-size: 0.875rem;
  font-weight: 500;
  color: v.$text-secondary;
  transition: color 0.2s;
  
  &.required-label::after {
    content: "*";
    color: v.$danger-color;
    margin-left: 2px;
  }
}

.field-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  width: 100%;
}

.view-value {
  font-size: 1rem;
  color: v.$text-primary;
  font-weight: 500;
}

.form-control {
  width: 100%;
  border: none;
  background: transparent;
  outline: none;
  font-size: 1rem;
  color: v.$text-primary;
  font-weight: 500;
  border-bottom: 1px solid transparent;
  transition: all 0.2s;
  border-radius: 0;
  font-family: inherit;
  min-height: 32px;
  padding: 4px 0;
  
  &:hover {
    border-bottom-color: v.$border-color;
  }
  
  &:focus {
    border-bottom-color: v.$primary-color !important;
    border-bottom-width: 2px;
    margin-bottom: -1px;
  }
  
  &[type="number"] {
    appearance: textfield;
    -moz-appearance: textfield;
    
    &::-webkit-outer-spin-button,
    &::-webkit-inner-spin-button {
      -webkit-appearance: none;
      margin: 0;
    }
  }
}

textarea.form-control {
  min-height: 80px;
  resize: vertical;
  padding: 8px 0;
  line-height: 1.5;
}

.field-invalid {
  border-bottom-color: v.$danger-color !important;
  
  &:hover {
    border-bottom-color: v.$danger-color !important;
  }
  
  &:focus {
    border-bottom-color: v.$danger-color !important;
  }
}

// Dark Mode Styles
[data-theme="dark"] {
  .wizard-dialog-overlay {
    background: rgba(0, 0, 0, 0.7);
  }

  .wizard-dialog {
    background: #161b22;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.4);
  }

  .wizard-header {
    border-bottom: 1px solid #30363d;
    
    .wizard-title h3 {
      color: #e6edf3;
    }
    
    .wizard-subtitle {
      color: #7d8590;
    }
    
    .close-button {
      color: #7d8590;
      
      &:hover {
        background: #0d1117;
        color: #e6edf3;
      }
    }
  }

  .loading-state {
    color: #7d8590;
  }

  .group-title {
    color: #7d8590;
    border-bottom: 1px solid #30363d;
  }

  .wizard-footer {
    border-top: 1px solid #30363d;
    background: #0d1117;
    
    .btn-primary {
      background: #2563eb;
      
      &:hover:not(:disabled) {
        background: #1d4ed8;
      }
    }
    
    .btn-secondary {
      background: #161b22;
      color: #e6edf3;
      border: 1px solid #30363d;
      
      &:hover:not(:disabled) {
        background: #0d1117;
        border-color: #7d8590;
      }
    }
  }

  .error-banner {
    background: rgba(248, 81, 73, 0.1);
    border: 1px solid rgba(248, 81, 73, 0.3);
    color: #ff7b72;
  }

  .spinner {
    border: 3px solid #30363d;
    border-top: 3px solid #58a6ff;
  }

  label {
    color: #7d8590;
    
    &.required-label::after {
      color: #f85149;
    }
  }

  .view-value {
    color: #e6edf3;
  }

  .form-control {
    color: #e6edf3;
    
    &::placeholder {
      color: #7d8590;
    }
    
    &:hover {
      border-bottom-color: #30363d;
    }
    
    &:focus {
      border-bottom-color: #58a6ff !important;
    }
  }

  .field-invalid {
    border-bottom-color: #f85149 !important;
    
    &:hover {
      border-bottom-color: #f85149 !important;
    }
    
    &:focus {
      border-bottom-color: #f85149 !important;
    }
  }
}
</style>
