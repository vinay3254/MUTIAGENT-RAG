import { useState } from 'react';

export default function CitationCard({ citations }) {
  const [open, setOpen] = useState(false);
  if (!citations || citations.length === 0) return null;

  return (
    <div className="citation-card">
      <button className="citation-toggle" onClick={() => setOpen((p) => !p)}>
        <span>📎 {citations.length} Source{citations.length !== 1 ? 's' : ''}</span>
        <span className="citation-chevron">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="citation-list">
          {citations.map((c, i) => (
            <div key={i} className="citation-item">
              <div className="citation-meta">
                <span className="citation-index">[{i + 1}]</span>
                <span className="citation-source">{c.source}</span>
                {c.page && <span className="citation-page">p.{c.page}</span>}
                {c.rerank_score !== undefined && (
                  <span className="citation-score">
                    score: {c.rerank_score.toFixed(3)}
                  </span>
                )}
              </div>
              <p className="citation-preview">{c.text_preview}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
