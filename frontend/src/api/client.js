import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // 2 minutes — LLM calls can be slow
});

export const api = {
  health: () => client.get('/health'),

  ingest: (file) => {
    const form = new FormData();
    form.append('file', file);
    return client.post('/ingest', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  query: (query) => client.post('/query', { query }),
};

export default client;
