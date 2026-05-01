import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';

const API = 'http://localhost:8001';

// ── Alert Sidebar ──────────────────────────────────────────────────────────────
function AlertSidebar({ alerts }) {
  const colors = {
    SCRIPTED_ANSWER: { bg: '#7f1d1d', border: '#ef4444', icon: '🚨' },
    VOICE_SIGNAL:    { bg: '#78350f', border: '#f59e0b', icon: '👁' },
    KNOWLEDGE_GAP:   { bg: '#713f12', border: '#f97316', icon: '⚠️' },
    DEEP_QUESTION:   { bg: '#1e3a5f', border: '#3b82f6', icon: '🎯' },
    LAYER2_FAIL:     { bg: '#4c1d95', border: '#8b5cf6', icon: '❌' },
    REPORT_READY:    { bg: '#14532d', border: '#22c55e', icon: '📊' },
  };

  return (
    <div style={{ width: 320, background: '#0f172a', borderLeft: '1px solid #1e293b', padding: '1rem', overflowY: 'auto', height: '100vh', position: 'fixed', right: 0, top: 0 }}>
      <div style={{ color: '#94a3b8', fontSize: '0.75rem', fontWeight: 700, letterSpacing: 2, marginBottom: '1rem' }}>
        PRIVATE ALERTS — CANDIDATE CANNOT SEE THIS
      </div>
      {alerts.length === 0 && (
        <div style={{ color: '#334155', textAlign: 'center', marginTop: '2rem', fontSize: '0.9rem' }}>
          Alerts will appear here during the interview
        </div>
      )}
      {[...alerts].reverse().map((alert, i) => {
        const style = colors[alert.type] || { bg: '#1e293b', border: '#334155', icon: 'ℹ️' };
        return (
          <div key={i} style={{ background: style.bg, border: `1px solid ${style.border}`, borderRadius: 8, padding: '0.75rem', marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
              <span>{style.icon}</span>
              <span style={{ color: '#e2e8f0', fontWeight: 700, fontSize: '0.85rem' }}>{alert.type.replace(/_/g, ' ')}</span>
            </div>
            <p style={{ color: '#cbd5e1', fontSize: '0.82rem', margin: 0 }}>{alert.message}</p>
            {alert.followup_questions && (
              <div style={{ marginTop: '0.5rem', background: 'rgba(0,0,0,0.3)', borderRadius: 6, padding: '0.5rem' }}>
                <p style={{ color: '#93c5fd', fontSize: '0.78rem', fontWeight: 600, margin: '0 0 0.25rem' }}>Ask this:</p>
                <p style={{ color: '#bfdbfe', fontSize: '0.78rem', margin: 0 }}>{typeof alert.followup_questions === 'string' ? alert.followup_questions.slice(0, 200) : ''}</p>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Score Badge ────────────────────────────────────────────────────────────────
function ScoreBadge({ score, label }) {
  const color = score >= 70 ? '#ef4444' : score >= 40 ? '#f59e0b' : '#22c55e';
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ fontSize: '1.8rem', fontWeight: 800, color }}>{score}</div>
      <div style={{ fontSize: '0.7rem', color: '#64748b' }}>{label}</div>
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────────
export default function App() {
  const [phase, setPhase] = useState('setup'); // setup | interview | report
  const [session, setSession] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [answers, setAnswers] = useState([]);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [currentQ, setCurrentQ] = useState('');
  const [currentA, setCurrentA] = useState('');
  const [responseStart, setResponseStart] = useState(null);
  const [layer2Mode, setLayer2Mode] = useState(null);
  const [layer2Answer, setLayer2Answer] = useState('');
  const wsRef = useRef(null);

  // Setup form
  const [form, setForm] = useState({ candidate_name: '', role: 'DevOps Engineer', level: 'mid' });

  // Connect WebSocket for private alerts
  const connectWS = useCallback((sessionId) => {
    const ws = new WebSocket(`ws://localhost:8001/ws/interviewer/${sessionId}`);
    ws.onmessage = (e) => {
      const alert = JSON.parse(e.data);
      setAlerts(prev => [...prev, { ...alert, ts: new Date().toLocaleTimeString() }]);
    };
    wsRef.current = ws;
  }, []);

  const startInterview = async () => {
    if (!form.candidate_name.trim()) return;
    setLoading(true);
    setLoadingMsg('Setting up interview plan...');
    try {
      const { data } = await axios.post(`${API}/interview/start`, form);
      setSession(data);
      connectWS(data.session_id);
      setPhase('interview');
    } catch (e) {
      alert('Failed to start. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  const markResponseStart = () => setResponseStart(Date.now());

  const submitAnswer = async () => {
    if (!currentQ.trim() || !currentA.trim()) return;
    const responseTime = responseStart ? (Date.now() - responseStart) / 1000 : 0;
    setLoading(true);
    setLoadingMsg('Analyzing answer... agents working...');
    try {
      const { data } = await axios.post(`${API}/interview/answer`, {
        session_id: session.session_id,
        question: currentQ,
        answer: currentA,
        response_time_seconds: responseTime,
      });
      setAnswers(prev => [...prev, {
        question: currentQ,
        answer: currentA,
        result: data,
        responseTime,
      }]);
      setCurrentQ('');
      setCurrentA('');
      setResponseStart(null);
    } catch (e) {
      alert('Error analyzing answer');
    } finally {
      setLoading(false);
    }
  };

  const submitLayer2 = async (ans) => {
    if (!layer2Answer.trim()) return;
    setLoading(true);
    setLoadingMsg('Analyzing deep follow-up...');
    try {
      const { data } = await axios.post(`${API}/interview/layer2`, {
        session_id: session.session_id,
        experience_id: ans.result.experience_id,
        followup_question: layer2Mode.question,
        followup_answer: layer2Answer,
        response_time_seconds: 0,
      });
      setAnswers(prev => prev.map((a, i) =>
        a.result.experience_id === ans.result.experience_id
          ? { ...a, layer2: data }
          : a
      ));
      setLayer2Mode(null);
      setLayer2Answer('');
    } catch (e) {
      alert('Error');
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    setLoading(true);
    setLoadingMsg('Generating final report...');
    try {
      const { data } = await axios.post(`${API}/interview/report`, { session_id: session.session_id });
      setReport(data.report);
      setPhase('report');
    } catch (e) {
      alert('Error generating report');
    } finally {
      setLoading(false);
    }
  };

  const submitFeedback = async (expId, label) => {
    await axios.post(`${API}/feedback`, { experience_id: expId, correct_label: label, notes: '' });
    alert(`Feedback saved: ${label}. System will learn from this.`);
  };

  // ── Setup Screen ─────────────────────────────────────────────────────────────
  if (phase === 'setup') return (
    <div style={{ minHeight: '100vh', background: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Segoe UI, sans-serif' }}>
      <div style={{ width: 480, background: '#1e293b', borderRadius: 16, padding: '2.5rem', border: '1px solid #334155' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🤖</div>
          <h1 style={{ color: '#e2e8f0', fontSize: '1.5rem', margin: 0 }}>Interview Intelligence</h1>
          <p style={{ color: '#64748b', marginTop: '0.5rem', fontSize: '0.9rem' }}>AI detection · Real-time alerts · Deep analysis</p>
        </div>

        {['candidate_name', 'role', 'level'].map(field => (
          <div key={field} style={{ marginBottom: '1rem' }}>
            <label style={{ color: '#94a3b8', fontSize: '0.85rem', display: 'block', marginBottom: '0.4rem' }}>
              {field.replace('_', ' ').toUpperCase()}
            </label>
            {field === 'role' ? (
              <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}
                style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, padding: '0.75rem', color: '#e2e8f0', fontSize: '1rem' }}>
                {['DevOps Engineer', 'SRE', 'Cloud Engineer (AWS)', 'Platform Engineer', 'Backend Engineer', 'Data Engineer'].map(r => <option key={r}>{r}</option>)}
              </select>
            ) : field === 'level' ? (
              <select value={form.level} onChange={e => setForm({ ...form, level: e.target.value })}
                style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, padding: '0.75rem', color: '#e2e8f0', fontSize: '1rem' }}>
                <option value="junior">Junior (0-2 yrs)</option>
                <option value="mid">Mid (2-5 yrs)</option>
                <option value="senior">Senior (5+ yrs)</option>
              </select>
            ) : (
              <input value={form.candidate_name} onChange={e => setForm({ ...form, candidate_name: e.target.value })}
                placeholder="Candidate full name"
                style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, padding: '0.75rem', color: '#e2e8f0', fontSize: '1rem', boxSizing: 'border-box' }} />
            )}
          </div>
        ))}

        <button onClick={startInterview} disabled={loading}
          style={{ width: '100%', background: loading ? '#334155' : '#3b82f6', color: 'white', border: 'none', borderRadius: 8, padding: '0.9rem', fontSize: '1rem', fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', marginTop: '0.5rem' }}>
          {loading ? loadingMsg : 'Start Interview →'}
        </button>
      </div>
    </div>
  );

  // ── Report Screen ─────────────────────────────────────────────────────────────
  if (phase === 'report') {
    const rec = report?.recommendation || 'MAYBE';
    const recColor = rec === 'HIRE' ? '#22c55e' : rec === 'NO_HIRE' ? '#ef4444' : '#f59e0b';
    return (
      <div style={{ minHeight: '100vh', background: '#0f172a', fontFamily: 'Segoe UI, sans-serif', paddingRight: 340 }}>
        <div style={{ maxWidth: 800, margin: '0 auto', padding: '2rem' }}>
          <h1 style={{ color: '#e2e8f0' }}>Interview Report</h1>
          <p style={{ color: '#64748b' }}>{session?.candidate_name} · {form.role} · {form.level}</p>

          <div style={{ background: '#1e293b', borderRadius: 12, padding: '2rem', marginBottom: '1.5rem', textAlign: 'center', border: `2px solid ${recColor}` }}>
            <div style={{ fontSize: '3rem', fontWeight: 800, color: recColor }}>{rec}</div>
            <p style={{ color: '#94a3b8', marginTop: '0.5rem' }}>{report?.summary || report?.raw?.slice(0, 300)}</p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={{ background: '#1e293b', borderRadius: 12, padding: '1.5rem' }}>
              <h3 style={{ color: '#22c55e', marginTop: 0 }}>Strengths</h3>
              <p style={{ color: '#94a3b8' }}>{report?.strengths || 'See raw report'}</p>
            </div>
            <div style={{ background: '#1e293b', borderRadius: 12, padding: '1.5rem' }}>
              <h3 style={{ color: '#ef4444', marginTop: 0 }}>Knowledge Gaps</h3>
              <p style={{ color: '#94a3b8' }}>{report?.gaps || 'See raw report'}</p>
            </div>
          </div>

          <div style={{ background: '#1e293b', borderRadius: 12, padding: '1.5rem', marginBottom: '1.5rem' }}>
            <h3 style={{ color: '#f59e0b', marginTop: 0 }}>AI Usage Assessment</h3>
            <p style={{ color: '#94a3b8' }}>Suspicion level: <strong style={{ color: '#e2e8f0' }}>{report?.ai_usage?.toUpperCase() || 'UNKNOWN'}</strong></p>
            <p style={{ color: '#94a3b8' }}>{report?.ai_note}</p>
            {report?.layer2_summary && (
              <p style={{ color: '#94a3b8' }}>
                Deep follow-up results: {report.layer2_summary.ai_gaps} AI gaps, {report.layer2_summary.knowledge_gaps} knowledge gaps out of {report.layer2_summary.total_followups} tested
              </p>
            )}
          </div>

          <h3 style={{ color: '#e2e8f0' }}>Answer-by-Answer Breakdown</h3>
          {answers.map((ans, i) => (
            <div key={i} style={{ background: '#1e293b', borderRadius: 12, padding: '1.5rem', marginBottom: '1rem', border: '1px solid #334155' }}>
              <p style={{ color: '#93c5fd', fontWeight: 600 }}>Q{i + 1}: {ans.question}</p>
              <p style={{ color: '#64748b', fontSize: '0.85rem' }}>{ans.answer.slice(0, 150)}...</p>
              <div style={{ display: 'flex', gap: '1.5rem', marginTop: '1rem' }}>
                <ScoreBadge score={ans.result?.ai_score || 0} label="AI Score" />
                <ScoreBadge score={ans.result?.surface_score * 10 || 0} label="Quality" />
                {ans.layer2 && <div style={{ color: ans.layer2.gap_type === 'PASSED' ? '#22c55e' : '#ef4444', fontWeight: 700, alignSelf: 'center' }}>{ans.layer2.gap_type}</div>}
              </div>
              {ans.result?.experience_id && (
                <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
                  <span style={{ color: '#64748b', fontSize: '0.8rem' }}>Was this detection correct?</span>
                  <button onClick={() => submitFeedback(ans.result.experience_id, 'human')} style={{ background: '#14532d', color: '#86efac', border: 'none', borderRadius: 4, padding: '0.2rem 0.6rem', cursor: 'pointer', fontSize: '0.8rem' }}>Human</button>
                  <button onClick={() => submitFeedback(ans.result.experience_id, 'ai')} style={{ background: '#7f1d1d', color: '#fca5a5', border: 'none', borderRadius: 4, padding: '0.2rem 0.6rem', cursor: 'pointer', fontSize: '0.8rem' }}>AI</button>
                </div>
              )}
            </div>
          ))}

          <button onClick={() => { setPhase('setup'); setSession(null); setAnswers([]); setAlerts([]); setReport(null); }}
            style={{ background: '#3b82f6', color: 'white', border: 'none', borderRadius: 8, padding: '0.75rem 1.5rem', cursor: 'pointer', fontWeight: 700 }}>
            New Interview
          </button>
        </div>
        <AlertSidebar alerts={alerts} />
      </div>
    );
  }

  // ── Interview Screen ──────────────────────────────────────────────────────────
  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', fontFamily: 'Segoe UI, sans-serif', paddingRight: 340 }}>
      <div style={{ maxWidth: 800, margin: '0 auto', padding: '2rem' }}>

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div>
            <h2 style={{ color: '#e2e8f0', margin: 0 }}>Interviewing: {form.candidate_name}</h2>
            <p style={{ color: '#64748b', margin: 0, fontSize: '0.85rem' }}>{form.role} · {form.level} · {answers.length} answers analyzed</p>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#22c55e', animation: 'pulse 2s infinite' }} />
            <span style={{ color: '#22c55e', fontSize: '0.8rem' }}>LIVE</span>
          </div>
        </div>

        {/* Suggested Questions */}
        {session?.questions && (
          <div style={{ background: '#1e293b', borderRadius: 12, padding: '1.25rem', marginBottom: '1.5rem', border: '1px solid #334155' }}>
            <p style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: 700, margin: '0 0 0.5rem' }}>SUGGESTED QUESTIONS</p>
            <p style={{ color: '#cbd5e1', fontSize: '0.9rem', margin: 0, whiteSpace: 'pre-wrap' }}>{session.questions.slice(0, 500)}</p>
          </div>
        )}

        {/* Answer Input */}
        <div style={{ background: '#1e293b', borderRadius: 12, padding: '1.5rem', marginBottom: '1.5rem', border: '1px solid #334155' }}>
          <p style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: 700, margin: '0 0 1rem' }}>CURRENT QUESTION & ANSWER</p>

          <input value={currentQ} onChange={e => setCurrentQ(e.target.value)}
            placeholder="Type the question you just asked..."
            style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, padding: '0.75rem', color: '#e2e8f0', fontSize: '0.95rem', marginBottom: '0.75rem', boxSizing: 'border-box' }} />

          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <button onClick={markResponseStart}
              style={{ background: responseStart ? '#14532d' : '#1e3a5f', color: responseStart ? '#86efac' : '#93c5fd', border: 'none', borderRadius: 6, padding: '0.4rem 0.8rem', cursor: 'pointer', fontSize: '0.8rem' }}>
              {responseStart ? '⏱ Timing...' : '▶ Start Timer (when candidate begins)'}
            </button>
          </div>

          <textarea value={currentA} onChange={e => setCurrentA(e.target.value)}
            placeholder="Type or paste candidate's answer here..."
            rows={5}
            style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, padding: '0.75rem', color: '#e2e8f0', fontSize: '0.95rem', resize: 'vertical', boxSizing: 'border-box' }} />

          <button onClick={submitAnswer} disabled={loading || !currentQ || !currentA}
            style={{ width: '100%', background: loading ? '#334155' : '#3b82f6', color: 'white', border: 'none', borderRadius: 8, padding: '0.85rem', fontSize: '1rem', fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', marginTop: '0.75rem' }}>
            {loading ? loadingMsg : 'Analyze Answer →'}
          </button>
        </div>

        {/* Previous Answers */}
        {answers.map((ans, i) => (
          <div key={i} style={{ background: '#1e293b', borderRadius: 12, padding: '1.25rem', marginBottom: '1rem', border: '1px solid #334155' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <p style={{ color: '#93c5fd', fontWeight: 600, margin: 0, flex: 1 }}>Q{i + 1}: {ans.question.slice(0, 80)}...</p>
              <div style={{ display: 'flex', gap: '1rem', marginLeft: '1rem' }}>
                <ScoreBadge score={ans.result?.ai_score || 0} label="AI" />
                <ScoreBadge score={Math.round((ans.result?.surface_score || 5) * 10)} label="Quality" />
              </div>
            </div>

            {/* Layer 2 trigger */}
            {!ans.layer2 && ans.result?.followup_questions && (
              <button onClick={() => setLayer2Mode({ ansIndex: i, question: ans.result.followup_questions.slice(0, 200), expId: ans.result.experience_id })}
                style={{ marginTop: '0.75rem', background: '#1e3a5f', color: '#93c5fd', border: '1px solid #3b82f6', borderRadius: 6, padding: '0.4rem 0.8rem', cursor: 'pointer', fontSize: '0.82rem' }}>
                Test Deep Follow-up →
              </button>
            )}

            {ans.layer2 && (
              <div style={{ marginTop: '0.75rem', background: ans.layer2.gap_type === 'PASSED' ? '#14532d' : '#7f1d1d', borderRadius: 6, padding: '0.5rem 0.75rem' }}>
                <span style={{ color: ans.layer2.gap_type === 'PASSED' ? '#86efac' : '#fca5a5', fontWeight: 700, fontSize: '0.85rem' }}>
                  Layer 2: {ans.layer2.gap_type} — {ans.layer2.conclusion}
                </span>
              </div>
            )}
          </div>
        ))}

        {/* Layer 2 Input */}
        {layer2Mode && (
          <div style={{ background: '#1e293b', borderRadius: 12, padding: '1.5rem', marginBottom: '1.5rem', border: '2px solid #8b5cf6' }}>
            <p style={{ color: '#a78bfa', fontWeight: 700, margin: '0 0 0.5rem' }}>DEEP FOLLOW-UP TEST</p>
            <p style={{ color: '#cbd5e1', fontSize: '0.9rem', marginBottom: '0.75rem' }}>{layer2Mode.question}</p>
            <textarea value={layer2Answer} onChange={e => setLayer2Answer(e.target.value)}
              placeholder="Candidate's answer to the follow-up..."
              rows={4}
              style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, padding: '0.75rem', color: '#e2e8f0', fontSize: '0.95rem', resize: 'vertical', boxSizing: 'border-box' }} />
            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.75rem' }}>
              <button onClick={() => submitLayer2(answers[layer2Mode.ansIndex])} disabled={loading}
                style={{ flex: 1, background: '#7c3aed', color: 'white', border: 'none', borderRadius: 8, padding: '0.75rem', fontWeight: 700, cursor: 'pointer' }}>
                {loading ? 'Analyzing...' : 'Analyze Deep Answer →'}
              </button>
              <button onClick={() => setLayer2Mode(null)}
                style={{ background: '#334155', color: '#94a3b8', border: 'none', borderRadius: 8, padding: '0.75rem 1rem', cursor: 'pointer' }}>
                Skip
              </button>
            </div>
          </div>
        )}

        {/* End Interview */}
        {answers.length > 0 && (
          <button onClick={generateReport} disabled={loading}
            style={{ width: '100%', background: loading ? '#334155' : '#22c55e', color: 'white', border: 'none', borderRadius: 8, padding: '1rem', fontSize: '1.1rem', fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer' }}>
            {loading ? loadingMsg : 'End Interview & Generate Report →'}
          </button>
        )}
      </div>

      <AlertSidebar alerts={alerts} />
    </div>
  );
}
