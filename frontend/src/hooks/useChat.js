import { useState } from 'react';
import { api } from '../api/client';

const PIPELINE_STEPS = [
  { key: 'retrieve', label: 'Retrieving chunks…' },
  { key: 'rank', label: 'Reranking results…' },
  { key: 'synthesize', label: 'Synthesizing answer…' },
  { key: 'fact_check', label: 'Fact-checking…' },
];

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(null);

  const sendMessage = async (query) => {
    // Append user message immediately
    setMessages((prev) => [...prev, { role: 'user', content: query }]);
    setIsLoading(true);
    setCurrentStep(0);

    // Simulate pipeline step advancement for visual feedback
    const stepInterval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev === null || prev >= PIPELINE_STEPS.length - 1) return prev;
        return prev + 1;
      });
    }, 1800);

    try {
      const res = await api.query(query);
      clearInterval(stepInterval);
      setCurrentStep(null);

      const { answer, citations, fact_check, pipeline_log, retry_count } = res.data;

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: answer,
          citations,
          factCheck: fact_check,
          pipelineLog: pipeline_log,
          retryCount: retry_count,
        },
      ]);
    } catch (err) {
      clearInterval(stepInterval);
      setCurrentStep(null);
      const msg = err.response?.data?.detail || err.message || 'An error occurred.';
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `⚠️ Error: ${msg}`, isError: true },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return { messages, isLoading, currentStep, pipelineSteps: PIPELINE_STEPS, sendMessage };
}
