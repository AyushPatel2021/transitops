/**
 * useChartTheme — resolves CSS custom property values at runtime so charts
 * automatically inherit the active light/dark theme without any hardcoded hex.
 *
 * Usage:
 *   const { getColor, chartDefaults } = useChartTheme()
 *   const color = getColor('primary')   // returns current --primary-color value
 */

const COLOR_MAP: Record<string, string> = {
  primary:  '--primary-color',
  success:  '--success-color',
  danger:   '--danger-color',
  warning:  '--warning-color',
  info:     '--info-color',
  muted:    '--text-tertiary',
  text:     '--text-primary',
  textSec:  '--text-secondary',
  border:   '--border-color',
  bg:       '--bg-secondary',
  bgMain:   '--bg-main',
}

function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

export function useChartTheme() {
  /**
   * Resolve a semantic color name to its current CSS-variable value.
   * Falls back to a neutral grey if the key is unknown.
   */
  function getColor(key: string): string {
    const varName = COLOR_MAP[key]
    if (!varName) return '#888'
    return cssVar(varName) || '#888'
  }

  /**
   * Resolve an array of semantic color names → hex/rgb strings.
   */
  function getColors(keys: string[]): string[] {
    return keys.map(getColor)
  }

  /**
   * Return Chart.js global defaults that use theme variables.
   * Call this every time you (re)build a chart config, especially when the
   * theme toggles, so colors are always current.
   */
  function chartDefaults() {
    return {
      color: getColor('text'),
      borderColor: getColor('border'),
      backgroundColor: getColor('bg'),
      plugins: {
        legend: {
          labels: {
            color: getColor('text'),
            font: { family: 'inherit', size: 12 },
          },
        },
        tooltip: {
          backgroundColor: getColor('bg'),
          titleColor: getColor('text'),
          bodyColor: getColor('textSec'),
          borderColor: getColor('border'),
          borderWidth: 1,
        },
      },
      scales: {
        x: {
          ticks: { color: getColor('textSec') },
          grid:  { color: getColor('border') },
        },
        y: {
          ticks: { color: getColor('textSec') },
          grid:  { color: getColor('border') },
        },
      },
    }
  }

  return { getColor, getColors, chartDefaults }
}
