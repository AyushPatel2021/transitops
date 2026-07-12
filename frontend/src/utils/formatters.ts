/**
 * Global formatting utilities - simplified without timezone support
 */

/**
 * Format value based on field type
 */
export function formatValue(
  value: any, 
  fieldType: string, 
  options?: any
): string {
  if (value === null || value === undefined || value === '') {
    return '';
  }

  switch (fieldType) {
    case 'datetime':
      try {
        const date = new Date(value);
        if (!isNaN(date.getTime())) {
          return date.toLocaleString();
        }
      } catch {
        // Ignore date parsing errors
      }
      return String(value);
      
    case 'date':
      try {
        const date = new Date(value);
        if (!isNaN(date.getTime())) {
          return date.toLocaleDateString();
        }
      } catch {
        // Ignore date parsing errors
      }
      return String(value);
      
    case 'time':
      try {
        const date = new Date(value);
        if (!isNaN(date.getTime())) {
          return date.toLocaleTimeString();
        }
      } catch {
        // Ignore date parsing errors
      }
      return String(value);
      
    case 'boolean':
      return value ? 'Yes' : 'No';
      
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: options?.currency || 'USD'
      }).format(value);
      
    case 'number':
      return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: options?.decimals || 0,
        maximumFractionDigits: options?.decimals || 2
      }).format(value);
      
    case 'percentage':
      return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: options?.decimals || 0,
        maximumFractionDigits: options?.decimals || 2
      }).format(value / 100);
      
    case 'many2one':
      if (typeof value === 'object' && value !== null) {
        return value.name || value.display_name || value.title || `ID: ${value.id}`;
      }
      return String(value);
      
    case 'one2many':
    case 'many2many':
      if (Array.isArray(value)) {
        return `${value.length} item${value.length !== 1 ? 's' : ''}`;
      }
      return String(value);
      
    case 'image':
      return value ? 'Image uploaded' : 'No image';
      
    case 'text':
      // Truncate long text for display
      const text = String(value);
      const maxLength = options?.maxLength || 100;
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
      
    default:
      return String(value);
  }
}

/**
 * Format datetime specifically for list views
 */
export function formatDateTimeForList(
  value: string | null | undefined
): string {
  if (!value) return '';
  try {
    const date = new Date(value);
    if (!isNaN(date.getTime())) {
      return date.toLocaleDateString();
    }
  } catch {
    // Ignore date parsing errors
  }
  return String(value);
}

/**
 * Format datetime for form displays
 */
export function formatDateTimeForForm(
  value: string | null | undefined
): string {
  if (!value) return '';
  try {
    const date = new Date(value);
    if (!isNaN(date.getTime())) {
      return date.toLocaleString();
    }
  } catch {
    // Ignore date parsing errors
  }
  return String(value);
}

/**
 * Format datetime for detailed views
 */
export function formatDateTimeDetailed(
  value: string | null | undefined
): string {
  if (!value) return '';
  try {
    const date = new Date(value);
    if (!isNaN(date.getTime())) {
      return date.toLocaleString();
    }
  } catch {
    // Ignore date parsing errors
  }
  return String(value);
}