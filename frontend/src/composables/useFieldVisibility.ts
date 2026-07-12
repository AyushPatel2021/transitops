import { ref, computed, watch, reactive, unref, nextTick } from 'vue';
import { DomainEngine } from '../core/domain-engine';

export interface FieldVisibilityState {
  isVisible: boolean;
  isReadonly: boolean;
  isRequired: boolean;
}

export interface FieldMetadata {
  invisible?: string;
  readonly?: string;
  required?: string | boolean;
  [key: string]: any;
}

export interface ModelMetadata {
  fields: Record<string, FieldMetadata>;
  views?: any;
  domain_fields?: {
    invisible: string[];
    readonly: string[];
  };
}

/**
 * Composable for managing field visibility and readonly states based on domain expressions.
 * 
 * This composable evaluates domain expressions from model metadata against form data
 * to determine which fields should be visible or readonly. It provides reactive updates
 * when form data changes.
 */
export function useFieldVisibility(metadata: any, formData: any) {
  const domainEngine = new DomainEngine();
  
  // Track field visibility and readonly states
  const fieldStates = reactive<Record<string, FieldVisibilityState>>({});
  
  // Track if we should use local evaluation (when form data has been modified)
  const useLocalEvaluation = ref(false);
  
  // Initialize field states
  const initializeFieldStates = () => {
    const metadataValue = unref(metadata);
    
    if (!metadataValue?.fields) {
      return;
    }
    
    // Clear existing field states
    Object.keys(fieldStates).forEach(key => delete fieldStates[key]);
    
    for (const fieldName in metadataValue.fields) {
      fieldStates[fieldName] = {
        isVisible: true,
        isReadonly: false,
        isRequired: false
      };
    }
  };
  
  // Evaluate all domain expressions for current form data
  const evaluateAllFields = () => {
    const metadataValue = unref(metadata);
    const formDataValue = unref(formData);
    
    if (!metadataValue?.fields || !formDataValue || Object.keys(formDataValue).length === 0) {
      return;
    }

    // Always use local evaluation if form has been modified, or if no pre-evaluated states exist
    const shouldUseLocalEvaluation = useLocalEvaluation.value || !formDataValue._domain_states;
    
    if (!shouldUseLocalEvaluation && formDataValue._domain_states) {
      // Use pre-evaluated states from backend only for initial load
      for (const fieldName in metadataValue.fields) {
        // Ensure field state exists
        if (!fieldStates[fieldName]) {
          fieldStates[fieldName] = {
            isVisible: true,
            isReadonly: false,
            isRequired: false
          };
        }
        
        // Use pre-evaluated states if available
        const domainState = formDataValue._domain_states[fieldName];
        if (domainState) {
          fieldStates[fieldName].isVisible = domainState.is_visible;
          fieldStates[fieldName].isReadonly = domainState.is_readonly;
          fieldStates[fieldName].isRequired = domainState.is_required;
        }
      }
      return;
    }
    
    // Perform local evaluation for real-time updates
    
    // Create evaluation context from form data
    const context = createEvaluationContext(formDataValue);
    
    for (const fieldName in metadataValue.fields) {
      const fieldMeta = metadataValue.fields[fieldName];
      
      // Ensure field state exists before trying to set properties
      if (!fieldStates[fieldName]) {
        fieldStates[fieldName] = {
          isVisible: true,
          isReadonly: false,
          isRequired: false
        };
      }
      
      // Evaluate visibility (invisible domain)
      if (fieldMeta.invisible !== undefined) {
        if (typeof fieldMeta.invisible === 'boolean') {
          // Direct boolean value
          fieldStates[fieldName].isVisible = !fieldMeta.invisible;
        } else if (typeof fieldMeta.invisible === 'string') {
          // Domain expression
          try {
            const isInvisible = domainEngine.evaluate(fieldMeta.invisible, context);
            fieldStates[fieldName].isVisible = !isInvisible;
          } catch (error) {
            fieldStates[fieldName].isVisible = true; // Default to visible on error
          }
        } else {
          fieldStates[fieldName].isVisible = true;
        }
      } else {
        fieldStates[fieldName].isVisible = true;
      }
      
      // Evaluate readonly state
      if (fieldMeta.readonly !== undefined) {
        if (typeof fieldMeta.readonly === 'boolean') {
          // Direct boolean value
          fieldStates[fieldName].isReadonly = fieldMeta.readonly;
        } else if (typeof fieldMeta.readonly === 'string') {
          // Domain expression
          try {
            fieldStates[fieldName].isReadonly = domainEngine.evaluate(fieldMeta.readonly, context);
          } catch (error) {
            fieldStates[fieldName].isReadonly = false; // Default to editable on error
          }
        } else {
          fieldStates[fieldName].isReadonly = false;
        }
      } else {
        fieldStates[fieldName].isReadonly = false;
      }

      // Evaluate required state
      if (fieldMeta.required !== undefined) {
        if (typeof fieldMeta.required === 'boolean') {
          // Direct boolean value
          fieldStates[fieldName].isRequired = fieldMeta.required;
        } else if (typeof fieldMeta.required === 'string') {
          // Domain expression
          try {
            const isRequired = domainEngine.evaluateWithDefault(fieldMeta.required, context, false);
            fieldStates[fieldName].isRequired = isRequired;
          } catch (error) {
            fieldStates[fieldName].isRequired = false; // Default to not required on error
          }
        } else {
          fieldStates[fieldName].isRequired = false;
        }
      } else {
        fieldStates[fieldName].isRequired = false;
      }
    }
  };
  
  // Create evaluation context from form data
  const createEvaluationContext = (data: any): Record<string, any> => {
    const context: Record<string, any> = {};
    
    if (!data) return context;
    
    // Copy all form data to context
    for (const key in data) {
      const value = data[key];
      
      // Handle different field types for domain evaluation
      if (value === null || value === undefined) {
        context[key] = null;
      } else if (typeof value === 'object' && value.id !== undefined) {
        // Many2one field - provide both the object and just the ID
        context[key] = value;
      } else {
        context[key] = value;
      }
    }

    // Explicitly add 'status' to context as an alias for the metadata status_field
    // to support domain expressions written as ('status', '=', ...) regardless of actual field name
    const metadataValue = unref(metadata);
    if (metadataValue?.status_field && metadataValue.status_field !== 'status') {
      context['status'] = data[metadataValue.status_field];
    }
    
    return context;
  };
  
  // Check if a specific field is visible
  const isFieldVisible = (fieldName: string): boolean => {
    return fieldStates[fieldName]?.isVisible ?? true;
  };
  
  // Check if a specific field is readonly
  const isFieldReadonly = (fieldName: string): boolean => {
    return fieldStates[fieldName]?.isReadonly ?? false;
  };

  // Check if a specific field is required
  const isFieldRequired = (fieldName: string): boolean => {
    return fieldStates[fieldName]?.isRequired ?? false;
  };
  
  // Get all visible fields from a list
  const getVisibleFields = (fieldNames: string[]): string[] => {
    // Guard against undefined/null fieldNames
    if (!fieldNames || !Array.isArray(fieldNames)) {
      return [];
    }
    
    const metadataValue = unref(metadata);
    const formDataValue = unref(formData);
    
    // Force evaluation if fieldStates is empty but we have metadata
    if (Object.keys(fieldStates).length === 0 && metadataValue?.fields) {
      initializeFieldStates();
      if (formDataValue && Object.keys(formDataValue).length > 0) {
        evaluateAllFields();
      }
    }
    
    return fieldNames.filter(fieldName => isFieldVisible(fieldName));
  };
  
  // Get all editable fields from a list
  const getEditableFields = (fieldNames: string[]): string[] => {
    return fieldNames.filter(fieldName => !isFieldReadonly(fieldName));
  };
  
  // Get fields that have domain expressions
  const getFieldsWithDomains = () => {
    const fieldsWithDomains = {
      invisible: [] as string[],
      readonly: [] as string[],
      required: [] as string[]
    };
    
    const metadataValue = unref(metadata);
    if (!metadataValue?.fields) return fieldsWithDomains;
    
    for (const fieldName in metadataValue.fields) {
      const fieldMeta = metadataValue.fields[fieldName];
      if (fieldMeta.invisible) {
        fieldsWithDomains.invisible.push(fieldName);
      }
      if (fieldMeta.readonly) {
        fieldsWithDomains.readonly.push(fieldName);
      }
      if (fieldMeta.required) {
        fieldsWithDomains.required.push(fieldName);
      }
    }
    
    return fieldsWithDomains;
  };
  
  // Computed property for fields that should trigger re-evaluation
  const dependentFields = computed(() => {
    const deps = new Set<string>();
    
    const metadataValue = unref(metadata);
    if (!metadataValue?.fields) return Array.from(deps);
    
    for (const fieldName in metadataValue.fields) {
      const fieldMeta = metadataValue.fields[fieldName];
      
      // Extract field references from domain expressions
      if (fieldMeta.invisible) {
        const refs = extractFieldReferences(fieldMeta.invisible);
        refs.forEach(ref => deps.add(ref));
      }
      
      if (fieldMeta.readonly) {
        const refs = extractFieldReferences(fieldMeta.readonly);
        refs.forEach(ref => deps.add(ref));
      }

      if (fieldMeta.required) {
        const refs = extractFieldReferences(fieldMeta.required);
        refs.forEach(ref => deps.add(ref));
      }
    }
    
    return Array.from(deps);
  });
  
  // Extract field references from domain expression
  const extractFieldReferences = (expression: string): string[] => {
    const refs: string[] = [];
    
    try {
      // Simple regex to extract field names from domain expressions
      // Matches patterns like ('field_name', '=', value)
      const fieldPattern = /\(\s*['"]([^'"]+)['"]/g;
      let match;
      
      while ((match = fieldPattern.exec(expression)) !== null) {
        const fieldName = match[1];
        if (fieldName && !refs.includes(fieldName)) {
          refs.push(fieldName);
        }
      }
    } catch (error) {
      // Silently handle expression parsing errors
    }
    
    return refs;
  };
  
  // Watch for metadata changes
  watch(
    () => unref(metadata),
    (newMetadata) => {
      if (newMetadata?.fields) {
        initializeFieldStates();
        const formDataValue = unref(formData);
        if (formDataValue && Object.keys(formDataValue).length > 0) {
          evaluateAllFields();
        }
      }
    },
    { deep: true, immediate: true }
  );
  
  // Watch for formData changes - Enhanced for real-time reactivity
  watch(
    () => unref(formData),
    (newFormData, oldFormData) => {
      if (newFormData && Object.keys(newFormData).length > 0) {
        const metadataValue = unref(metadata);
        if (metadataValue?.fields) {
          // Ensure field states are initialized before evaluation
          if (Object.keys(fieldStates).length === 0) {
            initializeFieldStates();
          }
          
          // Check if any dependent fields have changed
          const deps = dependentFields.value;
          let shouldRevaluate = false;
          
          if (!oldFormData) {
            shouldRevaluate = true;
          } else {
            // Check if any dependent field values have changed
            for (const fieldName of deps) {
              if (newFormData[fieldName] !== oldFormData[fieldName]) {
                shouldRevaluate = true;
                break;
              }
            }
          }
          
          if (shouldRevaluate) {
            useLocalEvaluation.value = true;
            evaluateAllFields();
          }
        }
      }
    },
    { deep: true, immediate: true }
  );

  // Additional watcher for specific field changes that affect domains
  watch(
    () => {
      const formDataValue = unref(formData);
      const deps = dependentFields.value;
      return deps.map(field => formDataValue?.[field]);
    },
    () => {
      const metadataValue = unref(metadata);
      const formDataValue = unref(formData);
      
      if (metadataValue?.fields && formDataValue && Object.keys(formDataValue).length > 0) {
        if (Object.keys(fieldStates).length === 0) {
          initializeFieldStates();
        }
        useLocalEvaluation.value = true;
        evaluateAllFields();
      }
    },
    { immediate: true }
  );
  
  // Create a computed that tracks specific fields that affect domains
  const domainTriggerFields = computed(() => {
    const formDataValue = unref(formData);
    const metadataValue = unref(metadata);
    if (!formDataValue) return {};
    
    // Dynamic status field from metadata
    const statusField = metadataValue?.status_field || 'status';

    // Track fields that commonly affect domain conditions
    return {
      [statusField]: formDataValue[statusField],
      status: formDataValue.status,
      state: formDataValue.state,
      stage: formDataValue.stage,
      type: formDataValue.type,
      category_id: formDataValue.category_id,
      // Add other fields that commonly appear in domain conditions
      timestamp: Date.now() // Force reactivity
    };
  });
  
  // Watch the domain trigger fields
  watch(domainTriggerFields, (newValues: any, oldValues: any) => {
    if (oldValues && newValues) {
      const changedFields = Object.keys(newValues).filter(key => 
        key !== 'timestamp' && newValues[key] !== oldValues[key]
      );
      
      if (changedFields.length > 0) {
        useLocalEvaluation.value = true;
        nextTick(() => {
          evaluateAllFields();
        });
      }
    }
  }, { deep: true });
  
  // Method to force local evaluation (called when form data changes)
  const forceLocalEvaluation = () => {
    useLocalEvaluation.value = true;
    evaluateAllFields();
  };
  
  // Method to evaluate an arbitrary domain expression
  const evaluateDomain = (expression: string, defaultValue: boolean = true): boolean => {
    if (!expression || typeof expression !== 'string') return defaultValue;
    
    const formDataValue = unref(formData);
    const context = createEvaluationContext(formDataValue);
    
    try {
      return domainEngine.evaluateWithDefault(expression, context, defaultValue);
    } catch (error) {
      return defaultValue;
    }
  };
  
  // Reset to use backend states (called when form is saved/loaded)
  const resetToBackendEvaluation = () => {
    useLocalEvaluation.value = false;
  };
  
  // Initialize on setup
  const metadataValue = unref(metadata);
  const formDataValue = unref(formData);
  
  if (metadataValue?.fields) {
    initializeFieldStates();
    if (formDataValue && Object.keys(formDataValue).length > 0) {
      evaluateAllFields();
    }
  }
  
  return {
    fieldStates: readonly(fieldStates),
    isFieldVisible,
    isFieldReadonly,
    isFieldRequired,
    getVisibleFields,
    getEditableFields,
    getFieldsWithDomains,
    dependentFields,
    evaluateAllFields,
    evaluateDomain,
    forceLocalEvaluation,
    resetToBackendEvaluation
  };
}

/**
 * Helper function to create a readonly reactive reference
 */
function readonly<T>(obj: T): T {
  return obj; // Vue 3's reactive objects are already protected in templates
}