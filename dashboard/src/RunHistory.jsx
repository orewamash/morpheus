import React from 'react';

const styles = {
  container: { padding: '16px 0' },
  title: { fontSize: 20, fontWeight: 600, marginBottom: 16, color: '#b388ff' },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: { textAlign: 'left', padding: '10px 12px', borderBottom: '1px solid #2a2a4a', color: '#8888aa', fontSize: 12, textTransform: 'uppercase', letterSpacing: 1 },
  td: { padding: '10px 12px', borderBottom: '1px solid #1a1a3a', fontSize: 14 },
  row: { cursor: 'pointer' },
  badge: (mode) => ({
    display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
    background: mode === 'prophecy' ? '#ff6b6b22' : mode === 'oracle' ? '#b388ff22' : mode === 'spy' ? '#ffd43b22' : '#69db7c22',
    color: mode === 'prophecy' ? '#ff6b6b' : mode === 'oracle' ? '#b388ff' : mode === 'spy' ? '#ffd43b' : '#69db7c',
  }),
  error: { color: '#ff6b6b', fontSize: 13 },
  loading: { color: '#8888aa', padding: 20, textAlign: 'center' },
  empty: { color: '#8888aa', padding: 20, textAlign: 'center' },
};

function RunHistory({ runs, loading, onSelectRun }) {
  if (loading) return <div style={styles.loading}>Loading runs...</div>;
  if (!runs || runs.length === 0) return <div style={styles.empty}>No runs yet. Run `morpheus run` to get started.</div>;

  return (
    <div style={styles.container}>
      <div style={styles.title}>Execution History</div>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>File</th>
            <th style={styles.th}>Mode</th>
            <th style={styles.th}>Events</th>
            <th style={styles.th}>Duration</th>
            <th style={styles.th}>Status</th>
          </tr>
        </thead>
        <tbody>
          {runs.map(run => (
            <tr key={run.run_id} style={styles.row} onClick={() => onSelectRun(run.run_id)}>
              <td style={styles.td}>{run.filepath.split('/').pop().split('\\').pop()}</td>
              <td style={styles.td}><span style={styles.badge(run.mode)}>{run.mode}</span></td>
              <td style={styles.td}>{run.event_count}</td>
              <td style={styles.td}>{run.duration_ms.toFixed(1)}ms</td>
              <td style={styles.td}>
                {run.error ? <span style={styles.error}>Error</span> : 'Success'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default RunHistory;
