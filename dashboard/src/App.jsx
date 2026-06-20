import React, { useState, useEffect } from 'react';
import RunHistory from './RunHistory';
import MindMap from './MindMap';
import SpyReport from './SpyReport';

const API_BASE = '/api';

function App() {
  const [view, setView] = useState('history');
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [mindmapData, setMindmapData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/runs`)
      .then(res => res.json())
      .then(data => {
        setRuns(data.runs || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));

    const params = new URLSearchParams(window.location.search);
    const runId = params.get('run_id');
    if (runId) {
      setSelectedRun(runId);
      setView('mindmap');
    }
  }, []);


  useEffect(() => {
    if (selectedRun) {
      fetch(`${API_BASE}/runs/${selectedRun}/mindmap`)
        .then(res => res.json())
        .then(data => setMindmapData(data))
        .catch(() => setMindmapData(null));
    }
  }, [selectedRun]);

  const styles = {
    container: { maxWidth: 1200, margin: '0 auto', padding: '20px' },
    header: { display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24, padding: '16px 0', borderBottom: '1px solid #2a2a4a' },
    logo: { fontSize: 24, fontWeight: 700, color: '#b388ff' },
    nav: { display: 'flex', gap: 8, marginLeft: 'auto' },
    navBtn: (active) => ({
      padding: '8px 16px', border: 'none', borderRadius: 6, cursor: 'pointer',
      background: active ? '#b388ff' : '#1a1a3a', color: active ? '#0d0d1a' : '#e0e0e0',
      fontWeight: active ? 600 : 400,
    }),
    content: { minHeight: '60vh' },
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div style={styles.logo}>Morpheus</div>
        <nav style={styles.nav}>
          <button style={styles.navBtn(view === 'history')} onClick={() => setView('history')}>Run History</button>
          <button style={styles.navBtn(view === 'mindmap')} onClick={() => setView('mindmap')}>Mind Map</button>
          <button style={styles.navBtn(view === 'spy')} onClick={() => setView('spy')}>Spy Reports</button>
        </nav>
      </header>
      <div style={styles.content}>
        {view === 'history' && (
          <RunHistory runs={runs} loading={loading}
            onSelectRun={(id) => { setSelectedRun(id); setView('mindmap'); }}
          />
        )}
        {view === 'mindmap' && <MindMap data={mindmapData} />}
        {view === 'spy' && <SpyReport />}
      </div>
    </div>
  );
}

export default App;
