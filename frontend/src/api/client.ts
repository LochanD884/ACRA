export const apiBase = import.meta.env.VITE_API_BASE || "http://localhost:8000/api/v1";
const apiKey = import.meta.env.VITE_API_KEY as string | undefined;

export const getApiKey = () => apiKey;

export const apiHeaders = () => {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (apiKey) headers.Authorization = `Bearer ${apiKey}`;
  return headers;
};
