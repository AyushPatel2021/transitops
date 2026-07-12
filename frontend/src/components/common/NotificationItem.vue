
<template>
  <div 
    class="notification-item" 
    :class="['type-' + notification.type, { sticky: notification.sticky }]"
    @mouseenter="onMouseEnter"
    @mouseleave="onMouseLeave"
  >
    <div class="notification-content">
        <div class="icon-area">
            <i :class="iconClass"></i>
        </div>
        <div class="text-area">
            <strong class="title">{{ notification.title }}</strong>
            <p class="message">{{ notification.message }}</p>
        </div>
        <button class="close-btn" @click="$emit('close')">
            <i class="icofont-close"></i>
        </button>
    </div>
    
    <!-- Progress Bar for non-sticky -->
    <div v-if="!notification.sticky" class="progress-bar-container">
        <div 
            class="progress-bar" 
            :style="{ width: progress + '%' }"
        ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, PropType } from 'vue';
import { Notification } from '../../stores/notificationStore';

const props = defineProps({
  notification: {
    type: Object as PropType<Notification>,
    required: true
  }
});

const emit = defineEmits(['close']);

const iconClass = computed(() => {
    switch (props.notification.type) {
        case 'success': return 'icofont-check-circled';
        case 'warning': return 'icofont-warning';
        case 'danger': return 'icofont-error';
        default: return 'icofont-info-circle';
    }
});

// Timer logic
const progress = ref(0);
const duration = props.notification.duration || 4000;
let remaining = duration;
let startTime = 0;
let timerId: any = null;
let animationFrameId: any = null;
let isPaused = false;

const startTimer = () => {
    if (props.notification.sticky) return;
    
    startTime = Date.now();
    const tick = () => {
        if (isPaused) return; // Don't update if paused
        
        const elapsedInLoop = Date.now() - startTime;
        const currentRemaining = remaining - elapsedInLoop;
        
        if (currentRemaining <= 0) {
            progress.value = 100;
            emit('close');
        } else {
            const totalElapsed = duration - currentRemaining;
            progress.value = (totalElapsed / duration) * 100;
            animationFrameId = requestAnimationFrame(tick);
        }
    };
    animationFrameId = requestAnimationFrame(tick);
};

const onMouseEnter = () => {
    if (props.notification.sticky) return;
    isPaused = true;
    // Calculate remaining time precisely when paused
    if (startTime) {
        remaining -= (Date.now() - startTime);
    }
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
};

const onMouseLeave = () => {
    if (props.notification.sticky) return;
    isPaused = false;
    startTime = Date.now(); // Reset start time to now, but remaining is already reduced
    startTimer();
};

onMounted(() => {
    startTimer();
});

onUnmounted(() => {
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
    if (timerId) clearTimeout(timerId);
});

</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.notification-item {
    background: v.$white; // Or dark theme
    color: #333;
    width: 350px;
    border-radius: 4px;
    box-shadow: 0 4px 12px v.$shadow-medium;
    margin-bottom: 0.75rem;
    overflow: hidden;
    position: relative;
    pointer-events: auto;
    transition: all 0.3s ease;
    border-left: 4px solid #ccc;
    
    &.type-success { border-left-color: v.$success-color; .icon-area { color: v.$success-color; } }
    &.type-warning { border-left-color: v.$warning-color; .icon-area { color: v.$warning-color; } }
    &.type-danger { border-left-color: v.$danger-color; .icon-area { color: v.$danger-color; } }
    &.type-info { border-left-color: v.$primary-color; .icon-area { color: v.$primary-color; } }
    
    .notification-content {
        display: flex;
        padding: 1rem;
        align-items: flex-start;
    }
    
    .icon-area {
        font-size: 1.5rem;
        margin-right: 0.75rem;
        display: flex;
        align-items: center;
    }
    
    .text-area {
        flex: 1;
        .title {
            display: block;
            font-size: 0.95rem;
            margin-bottom: 0.25rem;
        }
        .message {
            font-size: 0.85rem;
            color: #666;
            margin: 0;
            line-height: 1.4;
        }
    }
    
    .close-btn {
        background: none;
        border: none;
        cursor: pointer;
        opacity: 0.5;
        padding: 0;
        margin-left: 0.5rem;
        font-size: 1.2rem;
        transition: opacity 0.2s;
        
        &:hover { opacity: 1; }
    }
    
    .progress-bar-container {
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: v.$black-transparent-05;
        
        .progress-bar {
            height: 100%;
            background: v.$black-transparent-20; // Semi-transparent v.$black works on any color
            /* transition: width linear; NO TRANSITION for JS driven animation to be smooth, or uses linear */
        }
    }

    // Sticky specific
    &.sticky {
        // Sticky typically doesn't have the timer bar
        .progress-bar-container { display: none; }
    }
}

// Dark mode notification
[data-theme="dark"] .notification-item {
    background: #161b22;
    color: #e6edf3;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    border-left-color: #30363d;
    
    &.type-success { 
        border-left-color: #3fb950; 
        .icon-area { color: #3fb950; } 
    }
    &.type-warning { 
        border-left-color: #d29922; 
        .icon-area { color: #d29922; } 
    }
    &.type-danger { 
        border-left-color: #f85149; 
        .icon-area { color: #f85149; } 
    }
    &.type-info { 
        border-left-color: #58a6ff; 
        .icon-area { color: #58a6ff; } 
    }
    
    .text-area {
        .title {
            color: #e6edf3;
        }
        .message {
            color: #7d8590;
        }
    }
    
    .close-btn {
        color: #7d8590;
        
        &:hover { 
            color: #e6edf3;
        }
    }
    
    .progress-bar-container {
        background: rgba(255, 255, 255, 0.05);
        
        .progress-bar {
            background: rgba(255, 255, 255, 0.2);
        }
    }
}
</style>
