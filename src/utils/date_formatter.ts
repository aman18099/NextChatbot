import { toZonedTime, format } from 'date-fns-tz';

export function formatDate(date: Date) {
  const now = new Date();
  const today = now.toDateString();
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);

  if (date.toDateString() === today) return "Today";
  if (date.toDateString() === yesterday.toDateString()) return "Yesterday";
  return date.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}


export function formatToIST(date: Date): string {
  const utc = date.getTime() + date.getTimezoneOffset() * 60000;
  // IST is UTC + 5:30 hours
  const istOffset = 5.5 * 60 * 60000; // 5.5 hours in milliseconds
  const istDate = new Date(utc + istOffset);

  // Format time in hh:mm AM/PM format in English India locale
  return istDate.toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
}

export function formatDateTime(utcString: string): string {
    // const trimmedUtcString = utcString.replace(/(\.\d{3})\d+/, '$1');
const utcDate = new Date(utcString + "Z"); // Adding 'Z' enforces UTC parsing

// Convert to IST by adding 5.5 hours manually:
// const istOffsetMs = 5.5 * 60 * 60 * 1000;
const istDate = new Date(utcDate.getTime());
return istDate.toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
    
})}