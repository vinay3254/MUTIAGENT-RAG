import { useState } from 'react';
import { api } from '../api/client';

export function useUpload() {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  const uploadFile = async (file) => {
    setIsUploading(true);

    const entry = { name: file.name, status: 'uploading', progress: 0, chunks: null, error: null };
    setUploadedFiles((prev) => [...prev, entry]);

    try {
      const res = await api.ingest(file);
      setUploadedFiles((prev) =>
        prev.map((f) =>
          f.name === file.name
            ? { ...f, status: 'done', progress: 100, chunks: res.data.chunks_added }
            : f
        )
      );
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Upload failed';
      setUploadedFiles((prev) =>
        prev.map((f) =>
          f.name === file.name ? { ...f, status: 'error', error: msg } : f
        )
      );
    } finally {
      setIsUploading(false);
    }
  };

  const uploadMultiple = async (files) => {
    for (const file of files) {
      await uploadFile(file);
    }
  };

  return { uploadedFiles, isUploading, uploadMultiple };
}
