import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import Interview from './pages/Interview';
import Report from './pages/Report';

export default function App() {
  return (
    <BrowserRouter>
      <nav className="nav">
        <span className="nav-brand">🤖 Interview Intelligence</span>
        <Link to="/" style={{ color: '#94a3b8', textDecoration: 'none' }}>New Interview</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/interview/:sessionId" element={<Interview />} />
        <Route path="/report/:sessionId" element={<Report />} />
      </Routes>
    </BrowserRouter>
  );
}
