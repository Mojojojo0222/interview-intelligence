import React, { useState, useEffect, useRef, useCallback } from 'react';
import Report from './Report';
import axios from 'axios';

const API = 'http://localhost:8001';
const SILENCE_THRESHOLD = 0.01;
const SILENCE_DURATION = 2500; // 2.5s silence = candidate done speaking
const MIN_SPEECH_DURATION = 3000; // ignore clips under 3s

function AlertCard({ alert }) {
  const styles = {
    SCRIPTED_ANSWER: { bg: '#7f1d1d', border: '#ef4444', emoji: '🚨' },
    VOICE_SIGNAL:    { bg: '#78350f', border: '#f59e0b', emoji: '👁' },
    KNOWLEDGE_GAP:   { bg: '#713f12', border: '#f97316', emoji: '⚠️' },
    DEEP_QUESTION:   { bg: '#1e3a5f', border: '#3b82f6', emoji: '🎯' },
    LAYER2_FAIL:     { bg: '#4c1d95', border: '#8b5cf6', emoji: '❌' },
    REPORT_READY:    { bg: '#14532d', border: '#22c55e', emoji: '📊' },
  };
  const s = styles[alert.type] || { bg: '#1e293b', border: '#475569', emoji: 'ℹ️' };
  return (
    <div style={{ background: s.bg, border: `1px solid ${s.border}`, borderRadius: 10, padding: '1rem', marginBottom: '0.75rem', animation: 'slideIn 0.3s ease' }}>
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.4rem' }}>
        <span style={{ fontSize: '1.2rem' }}>{s.emoji}</span>
        <span style={{ color: '#f1f5f9', fontWeight: 700, fontSize: '0.9rem' }}>{alert.type.replace(/_/g, ' ')}</span>
        <span style={{ color: '#64748b', fontSize: '0.75rem', marginLeft: 'auto' }}>{alert.ts}</span>
      </div>
      <p style={{ color: '#cbd5e1', fontSize: '0.85rem', margin: 0 }}>{alert.message}</p>
      {alert.followup_questions && (
        <div style={{ marginTop: '0.75rem', background: 'rgba(0,0,0,0.3)', borderRadius: 8, padding: '0.75rem' }}>
          <p style={{ color: '#93c5fd', fontSize: '0.8rem', fontWeight: 700, margin: '0 0 0.4rem' }}>ASK ONE OF THESE NOW:</p>
          <p style={{ color: '#bfdbfe', fontSize: '0.85rem', margin: 0, whiteSpace: 'pre-wrap' }}>
            {typeof alert.followup_questions === 'string' ? alert.followup_questions.slice(0, 400) : ''}
          </p>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [phase, setPhase] = useState('setup');
  const [form, setForm] = useState({ candidate_name: '', role: 'Backend Engineer', level: 'junior' });
  const [session, setSession] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [answers, setAnswers] = useState([]);
  const [report, setReport] = useState(null);
  const [status, setStatus] = useState('idle'); // idle | listening | recording | analyzing
  const [transcript, setTranscript] = useState('');
  const [liveText, setLiveText] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [answerCount, setAnswerCount] = useState(0);

  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const silenceTimerRef = useRef(null);
  const speechStartRef = useRef(null);
  const analyserRef = useRef(null);
  const animFrameRef = useRef(null);
  const streamRef = useRef(null);
  const recognitionRef = useRef(null);

  // ── WebSocket for private alerts ──────────────────────────────────────────
  const connectWS = useCallback((sessionId) => {
    const ws = new WebSocket(`ws://localhost:8001/ws/interviewer/${sessionId}`);
    ws.onmessage = (e) => {
      const alert = JSON.parse(e.data);
      const enriched = { ...alert, ts: new Date().toLocaleTimeString() };
      setAlerts(prev => [enriched, ...prev]);
      // Browser notification even when tab is in background
      if (Notification.permission === 'granted' && alert.type !== 'DEEP_QUESTION') {
        new Notification(`Interview Alert: ${alert.type.replace(/_/g, ' ')}`, {
          body: alert.message,
          icon: '/favicon.ico',
        });
      }
    };
    wsRef.current = ws;
  }, []);

  // ── Speech Recognition for live transcript ────────────────────────────────
  const startSpeechRecognition = useCallback(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) return;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SR();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.onresult = (e) => {
      let interim = '';
      let final = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) final += e.results[i][0].transcript;
        else interim += e.results[i][0].transcript;
      }
      setLiveText(interim);
      if (final) setTranscript(prev => prev + ' ' + final);
    };
    recognition.onerror = () => {};
    recognition.onend = () => {
      if (status === 'listening' || status === 'recording') recognition.start();
    };
    recognition.start();
    recognitionRef.current = recognition;
  }, [status]);

  // ── Audio level monitoring for silence detection ──────────────────────────
  const monitorAudio = useCallback((stream) => {
    const ctx = new AudioContext();
    const source = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 512;
    source.connect(analyser);
    analyserRef.current = analyser;

    const data = new Uint8Array(analyser.frequencyBinCount);
    let isRecording = false;

    const check = () => {
      analyser.getByteFrequencyData(data);
      const avg = data.reduce((a, b) => a + b, 0) / data.length / 255;
      const isSpeaking = avg > SILENCE_THRESHOLD;

      if (isSpeaking && !isRecording) {
        // Speech started
        isRecording = true;
        speechStartRef.current = Date.now();
        audioChunksRef.current = [];
        setStatus('recording');
        clearTimeout(silenceTimerRef.current);
      }

      if (isSpeaking && isRecording) {
        // Reset silence timer on every speech frame
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = setTimeout(() => {
          // Silence detected — candidate finished speaking
          const duration = Date.now() - (speechStartRef.current || Date.now());
          if (duration > MIN_SPEECH_DURATION) {
            isRecording = false;
            setStatus('analyzing');
            const finalTranscript = transcript;
            setTranscript('');
            setLiveText('');
            if (finalTranscript.trim().length > 20) {
              analyzeAnswer(finalTranscript.trim());
            } else {
              setStatus('listening');
            }
          } else {
            isRecording = false;
            setStatus('listening');
          }
        }, SILENCE_DURATION);
      }

      animFrameRef.current = requestAnimationFrame(check);
    };
    check();
  }, [transcript]);

  // ── Start mic ─────────────────────────────────────────────────────────────
  const startMic = useCallback(async () => {
    try {
      await Notification.requestPermission();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      streamRef.current = stream;
      monitorAudio(stream);
      startSpeechRecognition();
      setStatus('listening');
    } catch (e) {
      alert('Microphone permission denied. Please allow mic access.');
    }
  }, [monitorAudio, startSpeechRecognition]);

  const stopMic = useCallback(() => {
    cancelAnimationFrame(animFrameRef.current);
    clearTimeout(silenceTimerRef.current);
    if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
    if (recognitionRef.current) recognitionRef.current.stop();
    setStatus('idle');
  }, []);

  // ── Auto analyze when candidate finishes speaking ─────────────────────────
  const analyzeAnswer = useCallback(async (text) => {
    if (!session) return;
    setAnswerCount(prev => prev + 1);
    try {
      const { data } = await axios.post(`${API}/interview/answer`, {
        session_id: session.session_id,
        question: `Auto-captured answer #${answerCount + 1}`,
        answer: text,
        response_time_seconds: speechStartRef.current ? (Date.now() - speechStartRef.current) / 1000 : 0,
      });
      setAnswers(prev => [...prev, { answer: text, result: data, time: new Date().toLocaleTimeString() }]);
    } catch (e) {
      console.error('Analysis failed', e);
    } finally {
      setStatus('listening');
    }
  }, [session, answerCount]);

  // ── Start Interview ───────────────────────────────────────────────────────
  const startInterview = async () => {
    if (!form.candidate_name.trim()) return;
    setLoading(true);
    setLoadingMsg('Setting up interview plan...');
    try {
      const { data } = await axios.post(`${API}/interview/start`, form);
      setSession(data);
      connectWS(data.session_id);
      setPhase('interview');
      await startMic();
    } catch (e) {
      alert('Failed to start. Is the backend running on port 8001?');
    } finally {
      setLoading(false);
    }
  };

  const endInterview = async () => {
    stopMic();
    if (!session || answers.length === 0) { setPhase('setup'); return; }
    setLoading(true);
    setLoadingMsg('Generating report...');
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
  };

  useEffect(() => () => stopMic(), [stopMic]);

  // ── SETUP SCREEN ──────────────────────────────────────────────────────────
  if (phase === 'setup') return (
    <div style={{ minHeight: '100vh', background: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Segoe UI, sans-serif' }}>
      <style>{`@keyframes slideIn { from { opacity:0; transform:translateY(-10px) } to { opacity:1; transform:translateY(0) } } @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }`}</style>
      <div style={{ width: 500, background: '#1e293b', borderRadius: 16, padding: '2.5rem', border: '1px solid #334155' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ fontSize: '3rem' }}>🎙️</div>
          <h1 style={{ color: '#e2e8f0', margin: '0.5rem 0 0' }}>Interview Intelligence</h1>
          <p style={{ color: '#64748b', margin: '0.5rem 0 0', fontSize: '0.9rem' }}>
            Fully automatic · Listens in background · Real-time AI detection
          </p>
        </div>

        <div style={{ background: '#0f172a', borderRadius: 10, padding: '1rem', marginBottom: '1.5rem', border: '1px solid #1e3a5f' }}>
          <p style={{ color: '#93c5fd', fontSize: '0.85rem', margin: 0 }}>
            How it works: Click Start → allow mic → switch to your Google Meet/Zoom tab. 
            The app listens automatically and alerts you here when it detects AI-assisted answers.
          </p>
        </div>

        <label style={{ color: '#94a3b8', fontSize: '0.82rem', display: 'block', marginBottom: '0.4rem' }}>CANDIDATE NAME</label>
        <input value={form.candidate_name} onChange={e => setForm({ ...form, candidate_name: e.target.value })}
          placeholder="Enter candidate name"
          style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, padding: '0.75rem', color: '#e2e8f0', fontSize: '1rem', marginBottom: '1rem', boxSizing: 'border-box' }} />

        <label style={{ color: '#94a3b8', fontSize: '0.82rem', display: 'block', marginBottom: '0.4rem' }}>ROLE</label>
        <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}
          style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, padding: '0.75rem', color: '#e2e8f0', fontSize: '1rem', marginBottom: '1rem' }}>
          {['Backend Engineer', 'DevOps Engineer', 'SRE', 'Cloud Engineer (AWS)', 'Frontend Engineer', 'Data Engineer', 'Full Stack Engineer'].map(r => <option key={r}>{r}</option>)}
        </select>

        <label style={{ color: '#94a3b8', fontSize: '0.82rem', display: 'block', marginBottom: '0.4rem' }}>LEVEL</label>
        <select value={form.level} onChange={e => setForm({ ...form, level: e.target.value })}
          style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, padding: '0.75rem', color: '#e2e8f0', fontSize: '1rem', marginBottom: '1.5rem' }}>
          <option value="junior">Junior (0-2 yrs)</option>
          <option value="mid">Mid (2-5 yrs)</option>
          <option value="senior">Senior (5+ yrs)</option>
        </select>

        <button onClick={startInterview} disabled={loading || !form.candidate_name.trim()}
          style={{ width: '100%', background: loading ? '#334155' : '#3b82f6', color: 'white', border: 'none', borderRadius: 10, padding: '1rem', fontSize: '1.1rem', fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer' }}>
          {loading ? `⏳ ${loadingMsg}` : '🎙️ Start Interview & Allow Mic →'}
        </button>
      </div>
    </div>
  );

  // ── REPORT SCREEN ─────────────────────────────────────────────────────────
  if (phase === 'report') return (
    <Report
      report={report}
      answers={answers}
      form={form}
      session={session}
      onNew={() => { setPhase('setup'); setSession(null); setAnswers([]); setAlerts([]); setReport(null); setAnswerCount(0); }}
      onFeedback={submitFeedback}
    />
  );

  // ── INTERVIEW SCREEN ──────────────────────────────────────────────────────
  const statusConfig = {
    idle:      { color: '#64748b', text: 'Idle',           dot: '#64748b' },
    listening: { color: '#22c55e', text: 'Listening...',   dot: '#22c55e' },
    recording: { color: '#ef4444', text: 'Candidate speaking...', dot: '#ef4444' },
    analyzing: { color: '#f59e0b', text: 'Analyzing answer...', dot: '#f59e0b' },
  };
  const sc = statusConfig[status];

  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', fontFamily: 'Segoe UI, sans-serif', display: 'grid', gridTemplateColumns: '1fr 360px' }}>
      <style>{`@keyframes slideIn { from { opacity:0; transform:translateY(-10px) } to { opacity:1; transform:translateY(0) } } @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }`}</style>

      {/* Left — Interview Monitor */}
      <div style={{ padding: '2rem', overflowY: 'auto' }}>

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div>
            <h2 style={{ color: '#e2e8f0', margin: 0 }}>{form.candidate_name}</h2>
            <p style={{ color: '#64748b', margin: '0.25rem 0 0', fontSize: '0.85rem' }}>{form.role} · {form.level}</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: sc.dot, animation: status === 'recording' ? 'blink 1s infinite' : 'none' }} />
              <span style={{ color: sc.color, fontSize: '0.85rem', fontWeight: 600 }}>{sc.text}</span>
            </div>
            <button onClick={endInterview} disabled={loading}
              style={{ background: '#7f1d1d', color: '#fca5a5', border: '1px solid #ef4444', borderRadius: 8, padding: '0.5rem 1rem', cursor: 'pointer', fontWeight: 700, fontSize: '0.85rem' }}>
              {loading ? loadingMsg : 'End Interview'}
            </button>
          </div>
        </div>

        {/* Suggested Questions */}
        {session?.questions && (
          <div style={{ background: '#1e293b', borderRadius: 12, padding: '1.25rem', marginBottom: '1.5rem', border: '1px solid #1e3a5f' }}>
            <p style={{ color: '#3b82f6', fontSize: '0.75rem', fontWeight: 700, margin: '0 0 0.75rem', letterSpacing: 1 }}>SUGGESTED QUESTIONS — ASK THESE ON YOUR CALL</p>
            <p style={{ color: '#cbd5e1', fontSize: '0.9rem', margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{session.questions}</p>
          </div>
        )}

        {/* Live Transcript */}
        {(status === 'recording' || liveText) && (
          <div style={{ background: '#1e293b', borderRadius: 12, padding: '1.25rem', marginBottom: '1.5rem', border: '1px solid #ef4444' }}>
            <p style={{ color: '#ef4444', fontSize: '0.75rem', fontWeight: 700, margin: '0 0 0.5rem', letterSpacing: 1 }}>LIVE TRANSCRIPT</p>
            <p style={{ color: '#e2e8f0', fontSize: '0.95rem', margin: 0 }}>
              {transcript} <span style={{ color: '#64748b' }}>{liveText}</span>
            </p>
          </div>
        )}

        {/* Answers captured */}
        <p style={{ color: '#64748b', fontSize: '0.8rem', fontWeight: 700, letterSpacing: 1 }}>CAPTURED ANSWERS ({answers.length})</p>
        {answers.length === 0 && (
          <div style={{ background: '#1e293b', borderRadius: 12, padding: '2rem', textAlign: 'center', border: '1px dashed #334155' }}>
            <p style={{ color: '#334155', margin: 0 }}>Waiting for candidate to speak...</p>
            <p style={{ color: '#1e3a5f', fontSize: '0.8rem', margin: '0.5rem 0 0' }}>App is listening in background. You can switch to your meeting tab.</p>
          </div>
        )}
        {answers.map((ans, i) => {
          const aiScore = ans.result?.ai_score || 0;
          const scoreColor = aiScore >= 70 ? '#ef4444' : aiScore >= 40 ? '#f59e0b' : '#22c55e';
          return (
            <div key={i} style={{ background: '#1e293b', borderRadius: 12, padding: '1.25rem', marginBottom: '0.75rem', border: '1px solid #334155', animation: 'slideIn 0.3s ease' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>Answer {i + 1} · {ans.time}</span>
                <span style={{ color: scoreColor, fontWeight: 800, fontSize: '1.2rem' }}>{aiScore}/100</span>
              </div>
              <p style={{ color: '#cbd5e1', fontSize: '0.88rem', margin: 0 }}>{ans.answer.slice(0, 180)}{ans.answer.length > 180 ? '...' : ''}</p>
            </div>
          );
        })}
      </div>

      {/* Right — Private Alert Sidebar */}
      <div style={{ background: '#080f1a', borderLeft: '1px solid #1e293b', padding: '1.5rem', overflowY: 'auto', height: '100vh', position: 'sticky', top: 0 }}>
        <p style={{ color: '#334155', fontSize: '0.7rem', fontWeight: 700, letterSpacing: 2, margin: '0 0 1rem' }}>PRIVATE — CANDIDATE CANNOT SEE</p>
        {alerts.length === 0 ? (
          <div style={{ textAlign: 'center', marginTop: '3rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🔍</div>
            <p style={{ color: '#1e293b', fontSize: '0.85rem' }}>Monitoring in progress...</p>
            <p style={{ color: '#1e293b', fontSize: '0.78rem' }}>Alerts appear here automatically</p>
          </div>
        ) : alerts.map((a, i) => <AlertCard key={i} alert={a} />)}
      </div>
    </div>
  );
}
