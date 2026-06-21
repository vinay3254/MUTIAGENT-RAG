export default function FactBadge({ factCheck }) {
  if (!factCheck || factCheck.overall_confidence === undefined) return null;

  const confidence = factCheck.overall_confidence;
  const flagged = factCheck.flagged_claims?.length || 0;

  let level = 'high';
  let label = 'Verified';
  let emoji = '🟢';
  if (confidence < 0.4) { level = 'low'; label = 'Low confidence'; emoji = '🔴'; }
  else if (confidence < 0.7) { level = 'medium'; label = 'Partial'; emoji = '🟡'; }

  return (
    <div className={`fact-badge fact-badge--${level}`}>
      <span className="fact-emoji">{emoji}</span>
      <span className="fact-label">{label}</span>
      <span className="fact-score">{Math.round(confidence * 100)}%</span>
      {flagged > 0 && (
        <span className="fact-flagged" title={factCheck.flagged_claims?.join('\n')}>
          ⚠️ {flagged} flagged
        </span>
      )}
    </div>
  );
}
