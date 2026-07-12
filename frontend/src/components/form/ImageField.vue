<template>
  <div class="image-field-container" :class="{ 'is-invalid': invalid, 'is-disabled': disabled || readonly, 'is-readonly': readonly }">
    <!-- Image Preview when image exists -->
    <div v-if="hasImage" class="image-preview" :style="previewStyle">
      <img 
        :src="imageDataUrl" 
        :alt="label || 'Image'" 
        class="preview-image"
        @load="onImageLoad"
        @error="onImageError"
      />
      <div class="image-overlay" v-if="!readonly">
        <button 
          @click="selectFile" 
          class="overlay-btn change-btn"
          :style="{ minHeight: touchTargetSize.minHeight, minWidth: touchTargetSize.minWidth }"
          title="Change image"
        >
          <Edit class="icon-sm" />
        </button>
        <button 
          @click="removeImage" 
          class="overlay-btn remove-btn"
          :style="{ minHeight: touchTargetSize.minHeight, minWidth: touchTargetSize.minWidth }"
          title="Remove image"
        >
          <X class="icon-sm" />
        </button>
      </div>
    </div>
    
    <!-- Placeholder when no image -->
    <div 
      v-else 
      class="image-placeholder" 
      :style="placeholderStyle"
      @click="selectFile"
      :class="{ 'clickable': !readonly && !disabled }"
    >
      <ImageIcon class="placeholder-icon" />
      <span class="placeholder-text">{{ readonly ? 'No image' : 'Click to upload image' }}</span>
    </div>
    
    <!-- Hidden file input -->
    <input 
      ref="fileInput" 
      type="file" 
      :accept="acceptedFormats" 
      @change="handleFileSelect" 
      style="display: none"
      :disabled="disabled || readonly"
    />
    
    <!-- Upload progress -->
    <div v-if="uploading" class="upload-progress">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
      </div>
      <span class="progress-text">Uploading... {{ uploadProgress }}%</span>
    </div>
    
    <!-- Error message -->
    <div v-if="errorMessage" class="error-message">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { ImageIcon, Edit, X } from 'lucide-vue-next';
import { useResponsive } from '../../composables/useResponsive';

interface ImageFieldMetadata {
  label?: string;
  type: "image";
  max_size?: number;        // Maximum file size in bytes (default: 5MB)
  allowed_formats?: string[]; // Default: ["jpeg", "jpg", "png", "gif", "webp"]
  display_width?: number;   // Display width in pixels (default: 120)
  display_height?: number;  // Display height in pixels (default: 120)
  required?: boolean;
}

const props = defineProps<{
  modelValue: string | null; // Base64 encoded image data
  label?: string;
  metadata?: ImageFieldMetadata;
  disabled?: boolean;
  invalid?: boolean;
  readonly?: boolean;
}>();

const emit = defineEmits(['update:modelValue', 'change', 'error']);

// Initialize responsive composable
const { isTouchDevice, touchTargetSize } = useResponsive();

// Refs
const fileInput = ref<HTMLInputElement | null>(null);
const uploading = ref(false);
const uploadProgress = ref(0);
const errorMessage = ref('');

// Default configuration
const defaultConfig = {
  max_size: 5 * 1024 * 1024, // 5MB
  allowed_formats: ['jpeg', 'jpg', 'png', 'gif', 'webp'],
  display_width: 120,
  display_height: 120
};

// Computed properties
const config = computed(() => ({
  ...defaultConfig,
  ...props.metadata
}));

const hasImage = computed(() => {
  return props.modelValue && props.modelValue.trim() !== '';
});

const imageDataUrl = computed(() => {
  if (!hasImage.value) return '';
  
  // If already a data URL, return as is
  if (props.modelValue?.startsWith('data:')) {
    return props.modelValue;
  }
  
  // If base64 without data URL prefix, add it
  return `data:image/jpeg;base64,${props.modelValue}`;
});

const acceptedFormats = computed(() => {
  return config.value.allowed_formats.map(format => {
    // Handle both 'jpg' and 'jpeg' formats
    if (format === 'jpg') return '.jpg,.jpeg';
    return `.${format}`;
  }).join(',');
});

const previewStyle = computed(() => ({
  width: `${config.value.display_width}px`,
  height: `${config.value.display_height}px`
}));

const placeholderStyle = computed(() => ({
  width: `${config.value.display_width}px`,
  height: `${config.value.display_height}px`
}));

// Methods
const selectFile = () => {
  if (props.disabled || props.readonly) return;
  
  errorMessage.value = '';
  fileInput.value?.click();
};

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  
  if (!file) return;
  
  // Validate file type
  const fileExtension = file.name.split('.').pop()?.toLowerCase();
  if (!fileExtension || !config.value.allowed_formats.includes(fileExtension)) {
    errorMessage.value = `Invalid file format. Allowed formats: ${config.value.allowed_formats.join(', ')}`;
    emit('error', errorMessage.value);
    return;
  }
  
  // Validate file size
  if (file.size > config.value.max_size) {
    const maxSizeMB = (config.value.max_size / (1024 * 1024)).toFixed(1);
    errorMessage.value = `File size exceeds ${maxSizeMB}MB limit`;
    emit('error', errorMessage.value);
    return;
  }
  
  // Convert to base64 and emit
  convertToBase64(file);
  
  // Clear the input so the same file can be selected again
  target.value = '';
};

const convertToBase64 = (file: File) => {
  uploading.value = true;
  uploadProgress.value = 0;
  errorMessage.value = '';
  
  const reader = new FileReader();
  
  reader.onload = () => {
    const result = reader.result as string;
    uploading.value = false;
    uploadProgress.value = 100;
    
    // Emit the full data URL
    emit('update:modelValue', result);
    emit('change', result);
    
    // Clear progress after a short delay
    setTimeout(() => {
      uploadProgress.value = 0;
    }, 500);
  };
  
  reader.onerror = () => {
    uploading.value = false;
    uploadProgress.value = 0;
    errorMessage.value = 'Failed to read file';
    emit('error', errorMessage.value);
  };
  
  reader.onprogress = (event) => {
    if (event.lengthComputable) {
      uploadProgress.value = Math.round((event.loaded / event.total) * 100);
    }
  };
  
  reader.readAsDataURL(file);
};

const removeImage = () => {
  if (props.disabled || props.readonly) return;
  
  errorMessage.value = '';
  emit('update:modelValue', null);
  emit('change', null);
};

const onImageLoad = () => {
  errorMessage.value = '';
};

const onImageError = () => {
  errorMessage.value = 'Failed to load image';
  emit('error', errorMessage.value);
};

// Clear error when modelValue changes
watch(() => props.modelValue, () => {
  errorMessage.value = '';
});
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.image-field-container {
  position: relative;
  width: 100%;
  font-family: inherit;

  &.is-disabled {
    pointer-events: none;
    opacity: 0.7;
  }

  &.is-readonly {
    .image-placeholder {
      cursor: not-allowed;
      
      .placeholder-text {
        color: v.$text-secondary !important;
      }
    }
  }

  &.is-invalid {
    .image-preview,
    .image-placeholder {
      border-color: v.$danger-color !important;
    }
  }
}

.image-preview {
  position: relative;
  border: 2px solid v.$border-color;
  border-radius: 8px;
  overflow: hidden;
  background: v.$bg-main;
  transition: all 0.2s ease;
  
  &:hover {
    border-color: v.$primary-color;
    
    .image-overlay {
      opacity: 1;
    }
  }
  
  .preview-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }
  
  .image-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: v.$shadow-darkest;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    opacity: 0;
    transition: opacity 0.2s ease;
  }
  
  .overlay-btn {
    background: v.$white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
    box-shadow: 0 2px 4px v.$shadow-light;
    
    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 8px v.$shadow-medium;
    }
    
    &.change-btn {
      color: v.$primary-color;
      
      &:hover {
        background: v.$primary-color;
        color: v.$white;
      }
    }
    
    &.remove-btn {
      color: v.$danger-color;
      
      &:hover {
        background: v.$danger-color;
        color: v.$white;
      }
    }
  }
}

.image-placeholder {
  border: 2px dashed v.$border-color;
  border-radius: 8px;
  background: v.$bg-main;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  transition: all 0.2s ease;
  
  &.clickable {
    cursor: pointer;
    
    &:hover {
      border-color: v.$primary-color;
      background: rgba(v.$primary-color, 0.05);
      
      .placeholder-icon {
        color: v.$primary-color;
      }
      
      .placeholder-text {
        color: v.$primary-color;
      }
    }
  }
  
  .placeholder-icon {
    width: 32px;
    height: 32px;
    color: v.$text-secondary;
    transition: color 0.2s ease;
  }
  
  .placeholder-text {
    font-size: 0.875rem;
    color: v.$text-secondary;
    font-weight: 500;
    text-align: center;
    transition: color 0.2s ease;
  }
}

.upload-progress {
  margin-top: 0.75rem;
  
  .progress-bar {
    width: 100%;
    height: 4px;
    background: v.$border-light;
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 0.5rem;
    
    .progress-fill {
      height: 100%;
      background: v.$primary-color;
      transition: width 0.3s ease;
      border-radius: 2px;
    }
  }
  
  .progress-text {
    font-size: 0.75rem;
    color: v.$text-secondary;
    font-weight: 500;
  }
}

.error-message {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 6px;
  color: v.$danger-color;
  font-size: 0.875rem;
  font-weight: 500;
}

[data-theme="dark"] .error-message {
  background: rgba(248, 81, 73, 0.1);
  border-color: rgba(248, 81, 73, 0.3);
  color: #f85149;
}

.icon-sm {
  width: 16px;
  height: 16px;
}
</style>