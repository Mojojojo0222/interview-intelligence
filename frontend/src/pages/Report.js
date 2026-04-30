import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

function Verdict({ verdict }) {
  const map = {
    HIRE: { cls: 'badge-green', label: '✅ HIRE' },
    MAYBE: { cls: 'badge-yellow', label: '⚠ MAYBE' },
    NO_HIRE: { cls: 'badge-red', label: '❌ NO HIRE' },
  };
  const v = map[verdict] || map['MAYBE'];
  return <span className={`badge ${v.cls}`} style={{ fontSize: '1.1rem', padding: '0.5rem 1.5rem' }}>{v.label}</span>;
}

export default function Report() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`/interview/session/${sessionId}`)
      .then(({ data }) => {
        const r = data.report;
        setReport(typeof r === 'string' ? tryParse(r) : r);
      })
      .catch(() => setReport(null))
      .finally(() => setLoading(false));
  }, [sessionId]);

  const tryParse = (str) => { try { return JSON.parse(str); } catch { return { raw: str }; } };

  if (loading) return <div className="loading"><div className="spinner" /><p>Loading report...</p></div>;

  if (!report) return (
    <div className="container">
      <div className="card"><p style={{ color: '#f87171' }}>Report not found.</p></div>
    </div>
  );

  return (
    <div className="container">
      <h1>Interview Report</h1>
      <p style={{ color: '#64748b', marginBottom: '1.5rem' }}>Session: {sessionId.slice(0, 8)}...</p>

      {report.raw ? (
        <div className="card">
          <h2>Report</h2>
          <pre style={{ color: '#94a3b8', whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: '0.9rem' }}>{report.raw}</pre>
        </div>
      ) : (
        <>
          <div className="card" style={{ textAlign: 'center' }}>
            <h2>Final Verdict</h2>
            <Verdict verdict={report.recommendation} />
            {report.recommendation_justification && (
              <p style={{ color: '#94a3b8', marginTop: '1rem' }}>{report.recommendation_justification}</p>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="card">
              <h3>✅ Strengths</h3>
              <ul style={{ paddingLeft: '1.2rem', color: '#86efac' }}>
                {(report.strengths || []).map((s, i) => <li key={i} style={{ marginBottom: '0.4rem' }}>{s}</li>)}
              </ul>
            </div>
            <div className="card">
              <h3>⚠ Knowledge Gaps</h3>
              <ul style={{ paddingLeft: '1.2rem', color: '#fca5a5' }}>
                {(report.knowledge_gaps || []).map((g, i) => <li key={i} style={{ marginBottom: '0.4rem' }}>{g}</li>)}
              </ul>
            </div>
          </div>

          {report.ai_usage_assessment && (
            <div className="card">
              <h3>🤖 AI Usage Assessment</h3>
              <p style={{ color: '#94a3b8' }}>{report.ai_usage_assessment}</p>
            </div>
          )}

          {report.candidate_summary && (
            <div className="card">
              <h3>Candidate Summary</h3>
              <p style={{ color: '#94a3b8' }}>{report.candidate_summary}</p>
            </div>
          )}
        </>
      )}

      <button className="btn" onClick={() => navigate('/')} style={{ marginTop: '1rem' }}>
        ← Start New Interview
      </button>
    </div>
  );
}
