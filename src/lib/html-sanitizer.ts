/**
 * HTML Sanitizer Utility
 * Centralized escaping for user-generated content to prevent XSS
 */

/**
 * Escapes HTML special characters to prevent XSS
 * @param str - Input string to escape
 * @returns HTML-escaped string safe for innerHTML insertion
 */
export function escapeHtml(str: string): string {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Sets element content safely using textContent (preferred over innerHTML)
 * @param el - Target HTMLElement
 * @param text - Text content to set
 */
export function safeTextContent(el: HTMLElement, text: string): void {
  el.textContent = text;
}

/**
 * Sets element HTML safely by escaping user content first
 * Only use when HTML structure is needed (e.g., template with interpolated user data)
 * @param el - Target HTMLElement
 * @param html - HTML string with user data already escaped
 */
export function safeInnerHTML(el: HTMLElement, html: string): void {
  el.innerHTML = html;
}