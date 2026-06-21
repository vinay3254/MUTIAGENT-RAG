import FactBadge from './FactBadge';
import CitationCard from './CitationCard';

function renderAnswer(text) {
  // Highlight inline citations like [Source: doc.pdf, p.4]
  const parts = text.split(/(\[Source:[^\]]+\])/g);
  return parts.map((part, i) =>
    part.startsWith('[Source:') ? (
      <span key={i} className="inline-citation">{part}</span>
    ) : (
      <span key={i}>{part}</span>
    )
  );
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`bubble-wrapper ${isUser ? 'bubble-wrapper--user' : 'bubble-wrapper--assistant'}`}>
      <div className={`avatar ${isUser ? 'avatar--user' : 'avatar--bot'}`}>
        {isUser ? '👤' : '🤖'}
      </div>

      <div className={`bubble ${isUser ? 'bubble--user' : 'bubble--assistant'} ${message.isError ? 'bubble--error' : ''}`}>
        <div className="bubble-content">
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <p className="answer-text">{renderAnswer(message.content)}</p>
          )}
        </div>

        {!isUser && message.factCheck && (
          <FactBadge factCheck={message.factCheck} />
        )}

        {!isUser && message.citations && message.citations.length > 0 && (
          <CitationCard citations={message.citations} />
        )}

        {!isUser && message.retryCount > 0 && (
          <div className="retry-badge">🔄 Re-retrieved {message.retryCount}×</div>
        )}
      </div>
    </div>
  );
}
