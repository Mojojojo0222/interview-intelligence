import React, { useState } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';

function AIBadge({ score }) {
  if (score === undefined) return null;
  if (score >= 70) return <span className="badge badge-red">⚠ Likely AI ({score}/100)</span>;
  if (score >= 40) return <span className="badge badge-yellow">? Possibly AI ({score}/100)</span>;
  return <span className="badge badge-green">✓ Likely Human ({score}/100)</span>;
}

function ScoreRow({ label, value }) {
  return (
    <div style={{ marginBottom: '0.75rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: '0.25rem' }}>
        <span>{label}</span><span style={{ color: '#93c5fd' }}>{value}/10</span>
      </div>
      <div className="score-bar"><div className="score-fill" style={{ width: `${value * 10}%` }} /></div>
    </div>
  );
}

export default function Interview() {
  const { sessionId } = useParams();
  const { state } = useLocation();
  const navigate = useNavigate();

  const [currentAnswer, setCurrentAnswer] = useState('');
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);

  const submitAnswer = async () => {
    if (!currentQuestion.trim() || !currentAnswer.trim()) return;
    setLoading(true);
    try {
      const { data } = await axios.post('/interview/answer', {
        session_id: sessionId,
        question: currentQuestion,
        answer: currentAnswer,
      });
      setResults(prev => [...prev, { question: currentQuestion, answer: currentAnswer, ...data }]);
      setCurrentQuestion('');
      setCurrentAnswer('');
    } catch (e) {
      alert('Error analyzing answer. Check backend.');
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    setReportLoading(true);
    try {
      await axios.post('/interview/report', { session_id: sessionId });
      navigate(`/report/${sessionId}`);
    } catch (e) {
      alert('Error generating report.');
    } finally {
      setReportLoading(false);
    }
  };

  const parseJSON = (str) => {
    try { return typeof str === 'object' ? str : JSON.parse(str); } catch { return null; }
  };

  return (
    <div className="container">
      <h1>Interview Session</h1>
      <p style={{ color: '#64748b', marginBottom: '1.5rem' }}>Session: {sessionId.slice(0, 8)}...</p>

      {state?.questions && (
        <div className="card">
          <h2>📋 Suggested Questions</h2>
          <pre style={{ color: '#94a3b8', fontSize: '0.85rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {typeof state.questions === 'string' ? state.questions : JSON.stringify(state.questions, null, 2)}
          </pre>
        </div>
      )}

      <div className="card">
        <h2>Submit Answer for Analysis</h2>
        <label>Question Asked</label>
        <input
          placeholder="Paste or type the question you asked..."
          value={currentQuestion}
          onChange={e => setCurrentQuestion(e.target.value)}
        />
        <label>Candidate's Answer</label>
        <textarea
          placeholder="Paste or type the candidate's answer..."
          value={currentAnswer}
          onChange={e => setCurrentAnswer(e.target.value)}
        />
        <button className="btn" onClick={submitAnswer} disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze Answer →'}
        </button>
      </div>

      {loading && (
        <div className="loading">
          <div className="spinner" />
          <p>Agents are analyzing the answer...</p>
        </div>
      )}

      {results.map((r, i) => {
        const analysis = parseJSON(r.analysis);
        const detection = parseJSON(r.ai_detection);
        const followups = parseJSON(r.followup_questions);

        return (
          <div className="card" key={i}>
            <h2>Q{i + 1}: {r.question.slice(0, 80)}...</h2>

            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
              {detection && <AIBadge score={detection.ai_likelihood_score} />}
            </div>

            {analysis && (
              <div style={{ marginBottom: '1rem' }}>
                <h3>Answer Quality</h3>
                <ScoreRow label="Technical Depth" value={analysis.technical_depth || analysis.depth || 0} />
                <ScoreRow label="Specificity" value={analysis.specificity || 0} />
                <ScoreRow label="Clarity" value={analysis.clarity || 0} />
                <ScoreRow label="Authenticity" value={analysis.authenticity || 0} />
              </div>
            )}

            {detection && (
              <div style={{ marginBottom: '1rem' }}>
                <h3>AI Detection</h3>
                <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
                  Patterns: {Array.isArray(detection.detected_patterns) ? detection.detected_patterns.join(', ') : detection.detected_patterns}
                </p>
              </div>
            )}

            {followups && (
              <div>
                <h3>🎯 Follow-up Questions</h3>
                {(Array.isArray(followups) ? followups : []).map((fq, j) => (
                  <div key={j} style={{ background: '#0f172a', padding: '0.75rem', borderRadius: '8px', marginBottom: '0.5rem' }}>
                    <p style={{ color: '#93c5fd', fontWeight: 600 }}>{fq.question}</p>
                    {fq.why_this_question && <p style={{ color: '#64748b', fontSize: '0.85rem', marginTop: '0.25rem' }}>{fq.why_this_question}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}

      {results.length > 0 && (
        <button className="btn btn-success" onClick={generateReport} disabled={reportLoading} style={{ width: '100%' }}>
          {reportLoading ? 'Generating Report...' : '📊 Generate Final Report'}
        </button>
      )}
    </div>
  );
}
