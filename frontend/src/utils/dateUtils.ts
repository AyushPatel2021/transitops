/**
 * Date and time formatting utilities
 * All functions use lowercase am/pm for consistency with PrimeVue components
 */

/**
 * Format a date to "Jan 15, 2026 11:54 am" format
 */
export function formatDateTime(date: Date | string | null | undefined): string {
  if (!date) return '';
  
  try {
    const d = typeof date === 'string' ? new Date(date) : date;
    
    if (isNaN(d.getTime())) {
      return '';
    }
    
    const months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    
    const month = months[d.getMonth()];
    const day = d.getDate();
    const year = d.getFullYear();
    
    let hours = d.getHours();
    const minutes = d.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'pm' : 'am';
    
    hours = hours % 12;
    hours = hours ? hours : 12; // 0 should be 12
    
    return `${month} ${day}, ${year} ${hours}:${minutes} ${ampm}`;
  } catch {
    return '';
  }
}

/**
 * Format a date to "Jan 15, 2026" format (date only)
 */
export function formatDate(date: Date | string | null | undefined): string {
  if (!date) return '';
  
  try {
    const d = typeof date === 'string' ? new Date(date) : date;
    
    if (isNaN(d.getTime())) {
      return '';
    }
    
    const months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    
    const month = months[d.getMonth()];
    const day = d.getDate();
    const year = d.getFullYear();
    
    return `${month} ${day}, ${year}`;
  } catch {
    return '';
  }
}

/**
 * Format time to "11:54 am" format (time only)
 */
export function formatTime(date: Date | string | null | undefined): string {
  if (!date) return '';
  
  try {
    const d = typeof date === 'string' ? new Date(date) : date;
    
    if (isNaN(d.getTime())) {
      return '';
    }
    
    let hours = d.getHours();
    const minutes = d.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'pm' : 'am';
    
    hours = hours % 12;
    hours = hours ? hours : 12; // 0 should be 12
    
    return `${hours}:${minutes} ${ampm}`;
  } catch {
    return '';
  }
}

/**
 * Check if a value is a valid date
 */
export function isValidDate(date: any): boolean {
  if (!date) return false;
  
  try {
    const d = typeof date === 'string' ? new Date(date) : date;
    return d instanceof Date && !isNaN(d.getTime());
  } catch {
    return false;
  }
}