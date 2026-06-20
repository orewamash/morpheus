import React, { useState } from 'react';

const styles = {
  container: { padding: '16px 0' },
  title: { fontSize: 20, fontWeight: 600, marginBottom: 16, color: '#ffd43b' },
  inputRow: { display: 'flex', gap: 8, marginBottom: 16 },
  input: { flex: 1, padding: '10px 12px', border: '1px solid #2a2a4a', borderRadius: 6, background: '#1a1a3a', color: '#e0e0e0', fontSize: 14 },
  button: { padding: '10px 20px', border: 'none', borderRadius: 6, background: '#b388ff', color: '#0d0d1a', fontWeight: 600, cursor: 'pointer' },
  report: { background: '#1a1a3a', padding: 16, borderRadius: 8, fontFamily: 'monospace', fontSize: 13, lineHeight: 1.6, whiteSpace: 'pre-wrap' },
  empty: { color: '#8888aa', padding: 20, textAlign: 'center' },
};

function SpyReport() {
  const [filepath, setFilepath] = useState('');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleScan = async () => {
    if (!filepath.trim()) return;
    setLoading(true);
    try {
      const response = await fetch(`/api/spy?file=${encodeURIComponent(filepath.trim())}`);
      const data = await response.json();
      setReport(data.report || 'No report generated.');
    } catch {
      setReport('Could not reach the API. Ensure the server is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.title}>Spy Report Viewer</div>
      <div style={styles.inputRow}>
        <input
          style={styles.input}
          placeholder="Enter file path to scan..."
          value={filepath}
          onChange={e => setFilepath(e.target.value)}
        />
        <button style={styles.button} onClick={handleScan} disabled={loading}>
          {loading ? 'Scanning...' : 'Scan'}
        </button>
      </div>
      {report ? (
        <div style={styles.report}>{report}</div>
      ) : (
        <div style={styles.empty}>Enter a file path and click Scan to view a security report.</div>
      )}
    </div>
  );
}

export default SpyReport;
