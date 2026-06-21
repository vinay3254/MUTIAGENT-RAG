import { useEffect, useRef, useState } from 'react';
import MessageBubble from './MessageBubble';
import StatusBar from './StatusBar';
import { useChat } from '../hooks/useChat';

export default function ChatWindow() {
  const { messages, isLoading, currentStep, pipelineSteps, sendMessage } = useChat();
  const [input, setInput] = useState('');
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const q = input.trim();
    if (!q || isLoading) return;
    setInput('');
    sendMessage(q);
  };

  return (
    <section className="chat-window">
      <div className="chat-header">
        <div className="chat-header-left">
          <span className="chat-header-icon">🧠</span>
          <div>
            <h1 className="chat-title">Multi-Agent RAG</h1>
            <p className="chat-subtitle">Retriever · Ranker · Synthesizer · FactChecker</p>
          </div>
        </div>
        <div className="chat-header-right">
          <span className="model-chip">claude-sonnet-4-6</span>
          <span className="model-chip">ChromaDB</span>
        </div>
      </div>

      <div className="message-list">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">💬</div>
            <h3>Ask a question about your documents</h3>
            <p>Upload PDFs or text files on the left, then ask anything.</p>
            <div className="example-queries">
              {[
                'What are the main findings of this paper?',
                'Summarize the methodology section.',
                'What conclusions does the author draw?',
              ].map((q) => (
                <button key={q} className="example-chip" onClick={() => { setInput(q); }}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {isLoading && (
          <div className="thinking-indicator">
            <StatusBar steps={pipelineSteps} currentStep={currentStep} isLoading={isLoading} />
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <div className="chat-input-wrapper">
          <input
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your documents…"
            disabled={isLoading}
          />
          <button className="chat-send-btn" type="submit" disabled={isLoading || !input.trim()}>
            {isLoading ? (
              <span className="sending-spinner" />
            ) : (
              <span>➤</span>
            )}
          </button>
        </div>
        <p className="chat-disclaimer">Answers are grounded in uploaded documents only.</p>
      </form>
    </section>
  );
}
