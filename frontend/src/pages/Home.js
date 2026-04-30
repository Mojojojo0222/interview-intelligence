import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function Home() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ candidate_name: '', role: 'DevOps Engineer', level: 'mid' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleStart = async () => {
    if (!form.candidate_name.trim()) return setError('Please enter candidate name');
    setLoading(true);
    setError('');
    try {
      const { data } = await axios.post('/interview/start', form);
      navigate(`/interview/${data.session_id}`, { state: { questions: data.questions, plan: data.plan } });
    } catch (e) {
      setError('Failed to start interview. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1>AI Interview Intelligence System</h1>
        <p style={{ color: '#64748b', marginTop: '0.5rem' }}>
          Detects AI-assisted answers · Adaptive questioning · DevOps/Cloud/SRE focused
        </p>
      </div>

      <div className="card">
        <h2>Start New Interview</h2>

        <label>Candidate Name</label>
        <input
          placeholder="Enter candidate name"
          value={form.candidate_name}
          onChange={e => setForm({ ...form, candidate_name: e.target.value })}
        />

        <label>Role</label>
        <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
          <option>DevOps Engineer</option>
          <option>SRE (Site Reliability Engineer)</option>
          <option>Cloud Engineer (AWS)</option>
          <option>Platform Engineer</option>
          <option>Infrastructure Engineer</option>
        </select>

        <label>Experience Level</label>
        <select value={form.level} onChange={e => setForm({ ...form, level: e.target.value })}>
          <option value="junior">Junior (0-2 years)</option>
          <option value="mid">Mid (2-5 years)</option>
          <option value="senior">Senior (5+ years)</option>
        </select>

        {error && <p style={{ color: '#f87171', marginBottom: '1rem' }}>{error}</p>}

        <button className="btn" onClick={handleStart} disabled={loading}>
          {loading ? 'Setting up interview...' : 'Start Interview →'}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
        {[
          { icon: '🔍', title: 'AI Detection', desc: 'Detects LLM-generated answers using linguistic pattern analysis' },
          { icon: '🎯', title: 'Adaptive Questions', desc: 'Follow-ups that LLMs cannot predict or hallucinate through' },
          { icon: '📊', title: 'Full Report', desc: 'Hire/No-hire recommendation with detailed scoring breakdown' },
        ].map(f => (
          <div className="card" key={f.title} style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{f.icon}</div>
            <h3>{f.title}</h3>
            <p style={{ color: '#64748b', fontSize: '0.9rem' }}>{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
