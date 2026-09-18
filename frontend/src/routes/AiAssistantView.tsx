import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { getLlmStatus, explainInvestigation, type LlmStatus, type StructuredLLMResponse, runAnalysis, type FullPipelineResult } from '../services/api';

interface ConversationTurn {
  role: 'user' | 'assistant';
  text?: string;
  response?: StructuredLLMResponse;
}

export function AiAssistantView() {
  const { caseId } = useParams();
  const [status, setStatus] = useState<LlmStatus | null>(null);
  const [pipelineResult, setPipelineResult] = useState<FullPipelineResult | null>(null);
  const [conversation, setConversation] = useState<ConversationTurn[]>([]);
  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scenarioId = (caseId && caseId.includes('.json')) ? caseId : 'scenario_001.json';

  useEffect(() => {
    // 1. Fetch LLM status
    getLlmStatus().then(st => setStatus(st)).catch(err => console.error("LLM Status Error", err));
    
    // 2. Fetch ground-truth pipeline result to show deterministic baseline
    runAnalysis(scenarioId)
      .then(res => {
        if (res && res.length > 0) {
          setPipelineResult(res[0]);
        }
      })
      .catch(err => console.error("Pipeline Error", err));

  }, [scenarioId]);

  useEffect(() => {
    // 3. Automatically request initial explanation if available
    if (status?.available && conversation.length === 0 && !loading && !error) {
      handleAsk("Explain the investigation outcome based solely on the provided context.");
    }
  }, [status, scenarioId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation, loading]);

  const handleAsk = async (question: string) => {
    if (!question.trim()) return;
    
    const isInitial = question === "Explain the investigation outcome based solely on the provided context.";
    if (!isInitial) {
      setConversation(prev => [...prev, { role: 'user', text: question }]);
      setInput('');
    }
    
    setLoading(true);
    setError(null);
    try {
      const result = await explainInvestigation(scenarioId, question);
      setConversation(prev => [...prev, { role: 'assistant', response: result }]);
    } catch (err: any) {
      setError(err.message || 'Failed to generate explanation.');
      if (!isInitial) {
        setConversation(prev => prev.slice(0, -1)); // remove user question on fail
      }
    } finally {
      setLoading(false);
    }
  };

  const isUnavailable = status && (!status.enabled || !status.available);
  const isMock = status?.provider === 'mock';

  return (
    <div style={{ padding: '24px', display: 'flex', gap: '24px', height: 'calc(100vh - 48px)', boxSizing: 'border-box' }}>
      
      {/* Left Column: Context & Status */}
      <div style={{ flex: '1', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
        
        {/* Status Panel */}
        <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '20px', borderRadius: '8px', border: '1px solid var(--bg-tertiary)' }}>
          <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Local AI Analyst</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', padding: '4px 8px', borderRadius: '4px', backgroundColor: isUnavailable ? 'rgba(255,59,48,0.1)' : 'rgba(52,199,89,0.1)', color: isUnavailable ? 'var(--status-fail)' : 'var(--status-pass)' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'currentColor' }}></span>
              {isUnavailable ? 'NOT CONFIGURED' : 'ONLINE'}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Provider:</span>
              <span style={{ fontWeight: isMock ? 700 : 400, color: isMock ? 'var(--status-gap)' : 'var(--text-primary)' }}>
                {status?.provider || 'None'} {isMock && '(MOCK / DEV ONLY)'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Model:</span>
              <span style={{ color: 'var(--text-primary)' }}>{status?.model_version || 'N/A'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Context Window:</span>
              <span style={{ color: 'var(--text-primary)' }}>{status?.context_size ? `${status.context_size} tokens` : 'N/A'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Network:</span>
              <span style={{ color: 'var(--text-primary)' }}>{status?.offline ? 'Offline Only (Safe)' : 'Unknown'}</span>
            </div>
          </div>
        </div>

        {/* Deterministic Boundary Notice */}
        <div style={{ backgroundColor: 'rgba(100, 210, 255, 0.05)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(100, 210, 255, 0.2)' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '8px', textTransform: 'uppercase' }}>
            Trust Boundary Notice
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            AI Analyst explains verified investigation data. It cannot create evidence or change the final classification. The deterministic verification result remains the final trust boundary.
          </div>
        </div>

        {/* Final Engine Decision */}
        {pipelineResult && (
          <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '20px', borderRadius: '8px', border: '1px solid var(--bg-tertiary)' }}>
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase' }}>
              Final Engine Decision
            </div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: pipelineResult.result.status === 'UNKNOWN' ? 'var(--status-gap)' : pipelineResult.result.status === 'INFERRED' ? 'var(--status-pass)' : 'var(--accent-cyan)' }}>
              {pipelineResult.result.status}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Deterministic Engine • Candidate: {pipelineResult.result.technique_id}
            </div>
          </div>
        )}
      </div>

      {/* Right Column: Chat Interface */}
      <div style={{ flex: '2', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--bg-tertiary)', overflow: 'hidden' }}>
        
        {/* Chat History */}
        <div style={{ flex: '1', padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {isUnavailable ? (
            <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.2 }}>🤖</div>
              <div style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px', color: 'var(--text-primary)' }}>Local model not configured</div>
              <div style={{ fontSize: '13px' }}>Configure a local GGUF model to enable AI analysis.</div>
            </div>
          ) : (
            conversation.map((turn, i) => (
              <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: turn.role === 'user' ? 'flex-end' : 'flex-start' }}>
                {turn.role === 'user' ? (
                  <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '12px 16px', borderRadius: '16px 16px 0 16px', maxWidth: '80%', fontSize: '14px', color: 'var(--text-primary)' }}>
                    {turn.text}
                  </div>
                ) : (
                  <div style={{ backgroundColor: 'var(--bg-primary)', border: '1px solid var(--bg-tertiary)', padding: '20px', borderRadius: '16px 16px 16px 0', maxWidth: '90%', width: '100%' }}>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '12px', display: 'flex', justifyContent: 'space-between' }}>
                      <span>AI Analyst</span>
                      <span style={{ color: 'var(--text-muted)' }}>{turn.response?.provider}</span>
                    </div>
                    
                    <div style={{ fontSize: '14px', color: 'var(--text-primary)', lineHeight: 1.6, marginBottom: '16px' }}>
                      {turn.response?.summary}
                    </div>
                    
                    <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '16px', borderRadius: '8px', marginBottom: '16px' }}>
                      <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>Assessment</div>
                      <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                        {turn.response?.assessment}
                      </div>
                    </div>

                    {turn.response?.candidate_discussion && turn.response.candidate_discussion.length > 0 && (
                      <div style={{ marginBottom: '16px' }}>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>Candidate Discussion</div>
                        <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          {turn.response.candidate_discussion.map((item, idx) => (
                            <li key={idx}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {turn.response?.uncertainty && (
                      <div style={{ marginBottom: '16px', padding: '12px', backgroundColor: 'rgba(255, 159, 10, 0.05)', borderLeft: '3px solid var(--status-gap)' }}>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--status-gap)', marginBottom: '4px' }}>Uncertainty / Missing Context</div>
                        <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{turn.response.uncertainty}</div>
                      </div>
                    )}

                    <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid var(--bg-tertiary)' }}>
                      <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '12px' }}>Evidence References</div>
                      {turn.response?.evidence_references && turn.response.evidence_references.length > 0 ? (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                          {turn.response.evidence_references.map((ref, idx) => (
                            <span key={idx} style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', padding: '4px 8px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '4px', color: 'var(--text-primary)' }}>
                              {ref}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic' }}>No specific evidence referenced.</div>
                      )}
                    </div>

                  </div>
                )}
              </div>
            ))
          )}
          
          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--text-muted)', fontSize: '13px', padding: '16px' }}>
              <div style={{ width: '16px', height: '16px', border: '2px solid var(--bg-tertiary)', borderTopColor: 'var(--accent-cyan)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
              Local AI is analyzing the context...
            </div>
          )}
          
          {error && (
            <div style={{ backgroundColor: 'rgba(255,59,48,0.1)', color: 'var(--status-fail)', padding: '16px', borderRadius: '8px', fontSize: '13px' }}>
              {error}
            </div>
          )}
          
          <div ref={chatEndRef} />
        </div>

        {/* Input Area */}
        <div style={{ padding: '20px', borderTop: '1px solid var(--bg-tertiary)', backgroundColor: 'var(--bg-primary)' }}>
          <div style={{ display: 'flex', gap: '12px' }}>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !isUnavailable && handleAsk(input)}
              placeholder={isUnavailable ? "Model offline" : "Ask about this investigation (e.g. 'Why did the engine abstain?')..."}
              disabled={isUnavailable || loading}
              style={{
                flex: '1',
                backgroundColor: 'var(--bg-secondary)',
                border: '1px solid var(--bg-tertiary)',
                borderRadius: '6px',
                padding: '12px 16px',
                color: 'var(--text-primary)',
                fontSize: '14px',
                fontFamily: 'inherit',
                opacity: (isUnavailable || loading) ? 0.5 : 1
              }}
            />
            <button
              onClick={() => handleAsk(input)}
              disabled={isUnavailable || loading || !input.trim()}
              style={{
                backgroundColor: 'var(--accent-cyan)',
                color: '#000',
                border: 'none',
                borderRadius: '6px',
                padding: '0 24px',
                fontWeight: 600,
                cursor: (isUnavailable || loading || !input.trim()) ? 'not-allowed' : 'pointer',
                opacity: (isUnavailable || loading || !input.trim()) ? 0.5 : 1
              }}
            >
              Ask
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
