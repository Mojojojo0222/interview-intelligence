import React from 'react';

const COLORS = {
  HIRE:     { bg: '#14532d', border: '#22c55e', text: '#86efac', emoji: '✅' },
  MAYBE:    { bg: '#713f12', border: '#f59e0b', text: '#fde68a', emoji: '⚠️' },
  NO_HIRE:  { bg: '#7f1d1d', border: '#ef4444', text: '#fca5a5', emoji: '❌' },
};

const AI_COLORS = {
  CLEAN:            { color: '#22c55e', label: 'No AI Use Detected' },
  SUSPICIOUS:       { color: '#f59e0b', label: 'Suspicious — Possible AI Use' },
  CONFIRMED_AI_USE: { color: '#ef4444', label: 'Confirmed AI Assistance' },
};

function Section({ title, icon, children, accent = '#334155' }) {
  return (
    <div style={{ background: '#1e293b', borderRadius: 12, padding: '1.5rem', marginBottom: '1rem', borderLeft: `4px solid ${accent}` }}>
      <h3 style={{ color: '#e2e8f0', margin: '0 0 1rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span>{icon}</span>{title}
      </h3>
      {children}
    </div>
  );
}

function ScoreBar({ label, value, max = 10, color = '#3b82f6' }) {
  const pct = Math.round((value / max) * 100);
  const barColor = pct >= 70 ? '#22c55e' : pct >= 40 ? '#f59e0b' : '#ef4444';
  return (
    <div style={{ marginBottom: '0.75rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
        <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>{label}</span>
        <span style={{ color: '#e2e8f0', fontWeight: 700, fontSize: '0.85rem' }}>{value}/{max}</span>
      </div>
      <div style={{ height: 6, background: '#0f172a', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: barColor, borderRadius: 3, transition: 'width 1s ease' }} />
      </div>
    </div>
  );
}

function AiScoreMeter({ score }) {
  const color = score >= 70 ? '#ef4444' : score >= 40 ? '#f59e0b' : '#22c55e';
  const label = score >= 70 ? 'HIGH RISK' : score >= 40 ? 'MEDIUM RISK' : 'LOW RISK';
  return (
    <div style={{ textAlign: 'center', padding: '1rem' }}>
      <div style={{ fontSize: '3.5rem', fontWeight: 900, color }}>{score}</div>
      <div style={{ color, fontWeight: 700, fontSize: '0.85rem', letterSpacing: 1 }}>{label}</div>
      <div style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '0.25rem' }}>AI Likelihood Score</div>
    </div>
  );
}

function parseList(text) {
  if (!text) return [];
  return text.split('\n').map(l => l.replace(/^[-•*]\s*/, '').trim()).filter(Boolean);
}

function parseField(raw, field) {
  if (!raw) return '';
  const regex = new RegExp(`${field}:\\s*(.+?)(?=\\n[A-Z_]+:|$)`, 'si');
  const match = raw.match(regex);
  return match ? match[1].trim() : '';
}

export default function Report({ report, answers, form, session, onNew, onFeedback }) {
  const raw = report?.raw || '';
  const rec = parseField(raw, 'VERDICT') || report?.recommendation || 'MAYBE';
  const confidence = parseField(raw, 'CONFIDENCE') || '70%';
  const execSummary = parseField(raw, 'EXECUTIVE_SUMMARY') || report?.summary || '';
  const aiVerdict = parseField(raw, 'AI_VERDICT') || (report?.ai_usage === 'high' ? 'CONFIRMED_AI_USE' : 'SUSPICIOUS');
  const aiExplanation = parseField(raw, 'AI_EXPLANATION') || report?.ai_note || '';
  const strengthsRaw = parseField(raw, 'STRENGTHS');
  const concernsRaw = parseField(raw, 'CONCERNS');
  const knowsWell = parseField(raw, 'KNOWS_WELL') || '';
  const surfaceOnly = parseField(raw, 'SURFACE_ONLY') || '';
  const gaps = parseField(raw, 'GAPS') || '';
  const behavioral = parseField(raw, 'BEHAVIORAL_SIGNALS') || '';
  const finalNote = parseField(raw, 'FINAL_NOTE') || '';

  const strengths = parseList(strengthsRaw);
  const concerns = parseList(concernsRaw);

  const recStyle = COLORS[rec] || COLORS.MAYBE;
  const aiStyle = AI_COLORS[aiVerdict] || AI_COLORS.SUSPICIOUS;

  // Compute stats from answers
  const aiScores = answers.map(a => a.result?.ai_score || 0);
  const avgAi = aiScores.length ? Math.round(aiScores.reduce((a, b) => a + b, 0) / aiScores.length) : 0;
  const flaggedCount = aiScores.filter(s => s >= 60).length;
  const layer2Results = answers.map(a => a.layer2).filter(Boolean);
  const aiGaps = layer2Results.filter(r => r?.gap_type === 'AI_GAP').length;
  const knowledgeGaps = layer2Results.filter(r => r?.gap_type === 'KNOWLEDGE_GAP').length;

  const interviewDate = session?.started_at
    ? new Date(session.started_at).toLocaleString('en-US', { dateStyle: 'full', timeStyle: 'short' })
    : new Date().toLocaleString();

  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', fontFamily: 'Segoe UI, sans-serif', color: '#e2e8f0' }}>
      <style>{`@keyframes fadeIn { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} } * { box-sizing: border-box; }`}</style>

      {/* Header */}
      <div style={{ background: '#1e293b', borderBottom: '1px solid #334155', padding: '1.5rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.4rem' }}>Interview Intelligence Report</h1>
          <p style={{ margin: '0.25rem 0 0', color: '#64748b', fontSize: '0.85rem' }}>{interviewDate}</p>
        </div>
        <button onClick={onNew} style={{ background: '#3b82f6', color: 'white', border: 'none', borderRadius: 8, padding: '0.6rem 1.2rem', cursor: 'pointer', fontWeight: 700 }}>
          New Interview
        </button>
      </div>

      <div style={{ maxWidth: 1000, margin: '0 auto', padding: '2rem', animation: 'fadeIn 0.5s ease' }}>

        {/* Candidate Info Bar */}
        <div style={{ background: '#1e293b', borderRadius: 12, padding: '1.25rem 1.5rem', marginBottom: '1.5rem', display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1rem', border: '1px solid #334155' }}>
          {[
            { label: 'Candidate', value: form.candidate_name },
            { label: 'Role', value: form.role },
            { label: 'Level', value: form.level.charAt(0).toUpperCase() + form.level.slice(1) },
            { label: 'Answers Analyzed', value: answers.length },
            { label: 'Session ID', value: session?.session_id?.slice(0, 8) + '...' },
          ].map(({ label, value }) => (
            <div key={label}>
              <div style={{ color: '#64748b', fontSize: '0.72rem', fontWeight: 700, letterSpacing: 1, marginBottom: '0.25rem' }}>{label.toUpperCase()}</div>
              <div style={{ color: '#e2e8f0', fontWeight: 600, fontSize: '0.95rem' }}>{value}</div>
            </div>
          ))}
        </div>

        {/* VERDICT — Big and clear */}
        <div style={{ background: recStyle.bg, border: `2px solid ${recStyle.border}`, borderRadius: 16, padding: '2rem', marginBottom: '1.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '4rem', marginBottom: '0.5rem' }}>{recStyle.emoji}</div>
          <div style={{ fontSize: '2.5rem', fontWeight: 900, color: recStyle.text, letterSpacing: 2 }}>{rec.replace('_', ' ')}</div>
          <div style={{ color: recStyle.text, opacity: 0.7, fontSize: '0.9rem', marginTop: '0.25rem' }}>Confidence: {confidence}</div>
          {execSummary && (
            <p style={{ color: '#e2e8f0', maxWidth: 600, margin: '1rem auto 0', fontSize: '1rem', lineHeight: 1.6 }}>{execSummary}</p>
          )}
        </div>

        {/* Stats Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
          {[
            { label: 'Avg AI Score', value: `${avgAi}/100`, color: avgAi >= 60 ? '#ef4444' : avgAi >= 40 ? '#f59e0b' : '#22c55e', sub: 'across all answers' },
            { label: 'Flagged Answers', value: `${flaggedCount}/${answers.length}`, color: flaggedCount > 0 ? '#ef4444' : '#22c55e', sub: 'AI score above 60' },
            { label: 'AI Gaps Found', value: aiGaps, color: aiGaps > 0 ? '#ef4444' : '#22c55e', sub: 'failed deep follow-up with AI' },
            { label: 'Knowledge Gaps', value: knowledgeGaps, color: knowledgeGaps > 1 ? '#f59e0b' : '#22c55e', sub: 'genuine knowledge missing' },
          ].map(({ label, value, color, sub }) => (
            <div key={label} style={{ background: '#1e293b', borderRadius: 12, padding: '1.25rem', textAlign: 'center', border: '1px solid #334155' }}>
              <div style={{ fontSize: '2rem', fontWeight: 900, color }}>{value}</div>
              <div style={{ color: '#e2e8f0', fontSize: '0.85rem', fontWeight: 600, marginTop: '0.25rem' }}>{label}</div>
              <div style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '0.2rem' }}>{sub}</div>
            </div>
          ))}
        </div>

        {/* AI Detection */}
        <Section title="AI Usage Assessment" icon="🤖" accent={aiStyle.color}>
          <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '1.5rem', alignItems: 'center' }}>
            <div style={{ background: '#0f172a', borderRadius: 12, padding: '1rem', textAlign: 'center' }}>
              <AiScoreMeter score={avgAi} />
              <div style={{ color: aiStyle.color, fontWeight: 700, fontSize: '0.85rem', marginTop: '0.5rem' }}>{aiStyle.label}</div>
            </div>
            <div>
              <p style={{ color: '#cbd5e1', lineHeight: 1.7, margin: 0 }}>{aiExplanation || 'AI analysis complete. See answer breakdown below for details.'}</p>
            </div>
          </div>
        </Section>

        {/* Strengths & Concerns */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
          <Section title="Strengths" icon="✅" accent="#22c55e">
            {strengths.length > 0 ? strengths.map((s, i) => (
              <div key={i} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.6rem', alignItems: 'flex-start' }}>
                <span style={{ color: '#22c55e', marginTop: '0.1rem' }}>•</span>
                <span style={{ color: '#cbd5e1', fontSize: '0.9rem', lineHeight: 1.5 }}>{s}</span>
              </div>
            )) : <p style={{ color: '#64748b', margin: 0 }}>See full report for details</p>}
          </Section>
          <Section title="Concerns" icon="⚠️" accent="#ef4444">
            {concerns.length > 0 ? concerns.map((c, i) => (
              <div key={i} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.6rem', alignItems: 'flex-start' }}>
                <span style={{ color: '#ef4444', marginTop: '0.1rem' }}>•</span>
                <span style={{ color: '#cbd5e1', fontSize: '0.9rem', lineHeight: 1.5 }}>{c}</span>
              </div>
            )) : <p style={{ color: '#64748b', margin: 0 }}>See full report for details</p>}
          </Section>
        </div>

        {/* Knowledge Map */}
        <Section title="Knowledge Map — What They Actually Know" icon="🗺️" accent="#8b5cf6">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
            {[
              { label: 'Knows Well', value: knowsWell, color: '#22c55e', bg: '#14532d' },
              { label: 'Surface Only (Faked)', value: surfaceOnly, color: '#f59e0b', bg: '#713f12' },
              { label: 'Clear Gaps', value: gaps, color: '#ef4444', bg: '#7f1d1d' },
            ].map(({ label, value, color, bg }) => (
              <div key={label} style={{ background: bg, borderRadius: 10, padding: '1rem' }}>
                <div style={{ color, fontWeight: 700, fontSize: '0.8rem', marginBottom: '0.5rem', letterSpacing: 1 }}>{label.toUpperCase()}</div>
                <p style={{ color: '#e2e8f0', margin: 0, fontSize: '0.88rem', lineHeight: 1.5 }}>{value || 'Not enough data'}</p>
              </div>
            ))}
          </div>
        </Section>

        {/* Behavioral Signals */}
        {behavioral && (
          <Section title="Behavioral Signals" icon="🎙️" accent="#06b6d4">
            <p style={{ color: '#cbd5e1', lineHeight: 1.7, margin: 0 }}>{behavioral}</p>
          </Section>
        )}

        {/* Answer Timeline */}
        <Section title="Answer-by-Answer Timeline" icon="📋" accent="#3b82f6">
          {answers.map((ans, i) => {
            const det = ans.result?.ai_detection || {};
            const ana = ans.result?.analysis || {};
            const voice = ans.result?.voice_signals || {};
            const aiScore = ans.result?.ai_score || 0;
            const scoreColor = aiScore >= 70 ? '#ef4444' : aiScore >= 40 ? '#f59e0b' : '#22c55e';
            const ts = ans.time || '';

            return (
              <div key={i} style={{ background: '#0f172a', borderRadius: 10, padding: '1.25rem', marginBottom: '1rem', border: `1px solid ${scoreColor}33` }}>

                {/* Answer header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ background: scoreColor, color: '#000', borderRadius: 6, padding: '0.2rem 0.6rem', fontWeight: 900, fontSize: '0.8rem' }}>
                      AI: {aiScore}/100
                    </div>
                    <span style={{ color: '#64748b', fontSize: '0.8rem' }}>Answer {i + 1}</span>
                  </div>
                  <span style={{ color: '#475569', fontSize: '0.78rem' }}>{ts}</span>
                </div>

                {/* Answer text */}
                <p style={{ color: '#94a3b8', fontSize: '0.85rem', margin: '0 0 1rem', fontStyle: 'italic', lineHeight: 1.5 }}>
                  "{ans.answer?.slice(0, 200)}{ans.answer?.length > 200 ? '...' : ''}"
                </p>

                {/* Scores grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  {[
                    { label: 'Technical Depth', val: ana.technical_depth || 5 },
                    { label: 'Specificity', val: ana.specificity || 5 },
                    { label: 'Clarity', val: ana.clarity || 5 },
                    { label: 'Authenticity', val: ana.authenticity || 5 },
                  ].map(({ label, val }) => (
                    <div key={label} style={{ background: '#1e293b', borderRadius: 8, padding: '0.6rem', textAlign: 'center' }}>
                      <div style={{ color: '#e2e8f0', fontWeight: 700 }}>{val}/10</div>
                      <div style={{ color: '#64748b', fontSize: '0.7rem', marginTop: '0.2rem' }}>{label}</div>
                    </div>
                  ))}
                </div>

                {/* Voice signals */}
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
                  {[
                    { label: `${voice.response_time || 0}s response`, warn: voice.response_time < 5 },
                    { label: `${voice.wpm || 0} WPM`, warn: voice.wpm > 160 },
                    { label: `${voice.hesitations || 0} hesitations`, warn: voice.hesitations === 0 },
                    { label: voice.reading_signal ? 'Reading detected' : 'No reading signal', warn: voice.reading_signal },
                    { label: `${det.red_flags_found || 0}/7 red flags`, warn: det.red_flags_found >= 4 },
                  ].map(({ label, warn }) => (
                    <span key={label} style={{ background: warn ? '#7f1d1d' : '#1e293b', color: warn ? '#fca5a5' : '#64748b', borderRadius: 4, padding: '0.2rem 0.5rem', fontSize: '0.75rem', border: `1px solid ${warn ? '#ef444433' : '#334155'}` }}>
                      {label}
                    </span>
                  ))}
                </div>

                {/* Layer 2 result */}
                {ans.layer2 && (
                  <div style={{ background: ans.layer2.gap_type === 'PASSED' ? '#14532d' : '#7f1d1d', borderRadius: 8, padding: '0.75rem', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.85rem', color: ans.layer2.gap_type === 'PASSED' ? '#86efac' : '#fca5a5' }}>
                      Deep Follow-up: {ans.layer2.gap_type?.replace('_', ' ')} — {ans.layer2.conclusion}
                    </span>
                  </div>
                )}

                {/* Feedback buttons */}
                {ans.result?.experience_id && (
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginTop: '0.5rem' }}>
                    <span style={{ color: '#475569', fontSize: '0.75rem' }}>Was this detection correct?</span>
                    <button onClick={() => onFeedback(ans.result.experience_id, 'human')}
                      style={{ background: '#14532d', color: '#86efac', border: 'none', borderRadius: 4, padding: '0.2rem 0.6rem', cursor: 'pointer', fontSize: '0.75rem' }}>
                      Human ✓
                    </button>
                    <button onClick={() => onFeedback(ans.result.experience_id, 'ai')}
                      style={{ background: '#7f1d1d', color: '#fca5a5', border: 'none', borderRadius: 4, padding: '0.2rem 0.6rem', cursor: 'pointer', fontSize: '0.75rem' }}>
                      AI ✓
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </Section>

        {/* Final Note */}
        {finalNote && (
          <div style={{ background: '#1e293b', borderRadius: 12, padding: '1.5rem', border: '1px solid #334155', textAlign: 'center' }}>
            <p style={{ color: '#94a3b8', fontSize: '0.8rem', margin: '0 0 0.5rem', letterSpacing: 1 }}>FINAL RECOMMENDATION</p>
            <p style={{ color: '#e2e8f0', fontSize: '1.05rem', margin: 0, lineHeight: 1.6 }}>{finalNote}</p>
          </div>
        )}

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: '2rem', color: '#334155', fontSize: '0.78rem' }}>
          Generated by Interview Intelligence System · {new Date().toLocaleString()} · System v2.0
        </div>
      </div>
    </div>
  );
}
