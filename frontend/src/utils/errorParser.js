/**
 * Safely parses any API error response into a clean, human-readable string.
 * Prevents React crash: 'Objects are not valid as a React child' under all error shapes.
 */
export const parseApiError = (err, fallback = 'An unexpected error occurred') => {
  if (!err) return fallback;
  
  // Direct string message
  if (typeof err === 'string') return err;

  // If err has response.data
  const data = err.response?.data;

  // If data itself is a string
  if (typeof data === 'string') return data;

  const detail = data?.detail ?? data?.message ?? data?.error ?? err.message;

  if (typeof detail === 'string') return detail;

  // FastAPI / Pydantic 422 validation error array: [{ loc, msg, type, ... }]
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => {
      if (typeof item === 'string') return item;
      if (item && typeof item === 'object') {
        const field = Array.isArray(item.loc) ? item.loc.filter(l => l !== 'body').join('.') : '';
        const msg = item.msg || item.message || (typeof item === 'object' ? JSON.stringify(item) : String(item));
        return field ? `${field}: ${msg}` : String(msg);
      }
      return String(item);
    });
    return messages.filter(Boolean).join('; ') || fallback;
  }

  // Single object error with msg, message, or detail
  if (detail && typeof detail === 'object') {
    if (typeof detail.msg === 'string') return detail.msg;
    if (typeof detail.message === 'string') return detail.message;
    if (typeof detail.detail === 'string') return detail.detail;
    try {
      return JSON.stringify(detail);
    } catch {
      return fallback;
    }
  }

  // If err has a standard message property
  if (err.message && typeof err.message === 'string') {
    return err.message;
  }

  try {
    return String(err);
  } catch {
    return fallback;
  }
};
