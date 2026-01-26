// utils/dateFormatter.js
export const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp);

  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();

  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');

  return `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;
};

// Format number with thousand separator as dot and decimal as comma
// Example: 1234567.89 -> "1.234.567,89"
export const formatPrice = (value) => {
  if (value === null || value === undefined || value === '') return '';

  const number = Number(value);
  if (Number.isNaN(number)) return '';

  // de-DE locale uses "." as thousands separator and "," as decimal separator
  return number.toLocaleString('de-DE');
};
