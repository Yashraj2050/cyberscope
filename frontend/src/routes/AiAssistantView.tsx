export function AiAssistantView() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: '40px' }}>
      <div style={{ maxWidth: '600px', textAlign: 'center', backgroundColor: 'var(--bg-secondary)', padding: '48px', borderRadius: '8px', border: '1px solid var(--bg-tertiary)' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '16px' }}>LOCAL AI ANALYST</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>
          Evidence-grounded analysis assistant
        </p>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '8px 16px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '999px', fontSize: '14px', fontWeight: 600 }}>
          <div className="status-dot disabled" style={{ backgroundColor: '#64748b' }}></div>
          NOT CONFIGURED
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '32px', lineHeight: 1.6 }}>
          The Local AI Analyst is designed to explain attack paths and verify candidate plausibility exclusively using observed evidence. It does not generate new facts or connect to remote LLM services. A quantized local SLM must be downloaded and configured in settings.
        </p>
      </div>
    </div>
  );
}
