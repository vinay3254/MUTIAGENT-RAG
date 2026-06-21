export default function StatusBar({ steps, currentStep, isLoading }) {
  if (!isLoading && currentStep === null) return null;

  return (
    <div className="status-bar">
      <div className="status-bar-inner">
        {steps.map((step, i) => {
          const isDone = currentStep !== null && i < currentStep;
          const isActive = i === currentStep;
          return (
            <div key={step.key} className={`status-step ${isDone ? 'done' : ''} ${isActive ? 'active' : ''}`}>
              <div className="status-dot">
                {isDone ? '✓' : isActive ? <span className="pulse-dot" /> : i + 1}
              </div>
              <span className="status-label">{step.label}</span>
              {i < steps.length - 1 && <div className={`status-connector ${isDone ? 'done' : ''}`} />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
