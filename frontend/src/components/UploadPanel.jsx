import { useDropzone } from 'react-dropzone';
import { useUpload } from '../hooks/useUpload';

const ACCEPTED = { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'], 'text/markdown': ['.md'] };

export default function UploadPanel() {
  const { uploadedFiles, isUploading, uploadMultiple } = useUpload();

  const onDrop = (accepted) => {
    if (accepted.length) uploadMultiple(accepted);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    multiple: true,
  });

  return (
    <aside className="upload-panel">
      <div className="panel-header">
        <span className="panel-icon">📂</span>
        <h2>Document Library</h2>
      </div>

      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'dropzone--active' : ''} ${isUploading ? 'dropzone--uploading' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="dropzone-inner">
          <div className="dropzone-icon">{isDragActive ? '⬇️' : '☁️'}</div>
          <p className="dropzone-title">
            {isDragActive ? 'Drop files here' : 'Drag & drop files'}
          </p>
          <p className="dropzone-sub">PDF, TXT, MD supported</p>
          <button className="btn-upload" disabled={isUploading}>
            {isUploading ? 'Uploading…' : 'Browse Files'}
          </button>
        </div>
      </div>

      {uploadedFiles.length > 0 && (
        <ul className="file-list">
          {uploadedFiles.map((f, i) => (
            <li key={i} className={`file-item file-item--${f.status}`}>
              <div className="file-info">
                <span className="file-icon">
                  {f.status === 'done' ? '✅' : f.status === 'error' ? '❌' : '⏳'}
                </span>
                <span className="file-name" title={f.name}>{f.name}</span>
              </div>
              {f.status === 'done' && (
                <span className="file-chunks">{f.chunks} chunks</span>
              )}
              {f.status === 'error' && (
                <span className="file-error" title={f.error}>Error</span>
              )}
              {f.status === 'uploading' && (
                <div className="file-progress-bar">
                  <div className="file-progress-fill" />
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
