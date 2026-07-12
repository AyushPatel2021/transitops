/**
 * useDashboardTheme — lightweight composable that tracks theme toggles
 * and exposes a `themeVersion` counter.  Increment themeVersion to force
 * AppChart to re-render with fresh CSS-variable values.
 */
import { ref, onMounted, onUnmounted } from 'vue'

export function useDashboardTheme() {
  const themeVersion = ref(0)
  let observer: MutationObserver | null = null

  onMounted(() => {
    observer = new MutationObserver(() => { themeVersion.value++ })
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    })
  })

  onUnmounted(() => observer?.disconnect())

  return { themeVersion }
}
