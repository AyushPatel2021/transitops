
<template>
  <div class="notification-container">
    <TransitionGroup name="list" tag="div">
        <NotificationItem 
          v-for="notification in notifications" 
          :key="notification.id" 
          :notification="notification"
          @close="remove(notification.id)"
        />
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { useNotificationsStore } from '../../composables/useNotificationsStore';
import NotificationItem from './NotificationItem.vue';

const { notifications, removeLocalNotification: remove } = useNotificationsStore();
</script>

<style lang="scss" scoped>
.notification-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 99999; /* Highest priority */
    display: flex;
    flex-direction: column;
    pointer-events: none; /* Let clicks pass through empty space */
}

/* Animations */
.list-enter-active,
.list-leave-active {
  transition: all 0.4s ease;
}
.list-enter-from {
  opacity: 0;
  transform: translateX(30px);
}
.list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
