<template>
  <div class="priority-stars" :class="{ readonly }">
    <div 
      v-for="star in 3" 
      :key="star"
      class="star-item"
      :class="{ 
        'active': star <= currentStars,
        'urgent': currentStars === 3
      }"
      @click="handleStarClick(star)"
    >
      <Star 
        class="star-icon" 
        :fill="star <= currentStars ? (currentStars === 3 ? '#EF4444' : '#EAB308') : 'none'"
        :stroke="star <= currentStars ? (currentStars === 3 ? '#EF4444' : '#EAB308') : '#CBD5E1'"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Star } from 'lucide-vue-next';

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: '0'
  },
  readonly: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:modelValue']);

const currentStars = computed(() => {
  const val = parseInt(props.modelValue?.toString() || '0');
  return Math.min(Math.max(val, 0), 3);
});

const handleStarClick = (star: number) => {
  if (props.readonly) return;
  
  // If clicking the current star level, toggle off (set to 0) or handle logic
  // Requirement: 0 = no stars, 1 = 1 star, 2 = 2 stars, 3 = 3 stars
  let newValue = star;
  if (currentStars.value === star) {
    newValue = star - 1; // Decrease level if clicking active star
  }
  
  emit('update:modelValue', newValue.toString());
};
</script>

<style lang="scss" scoped>
.priority-stars {
  display: flex;
  gap: 2px;
  align-items: center;
  
  &.readonly {
    cursor: default;
    opacity: 0.8;
  }
  
  &:not(.readonly) {
    cursor: pointer;
    
    .star-item:hover {
      transform: scale(1.1);
    }
  }
}

.star-item {
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  
  .star-icon {
    width: 20px;
    height: 20px;
  }
}
</style>
