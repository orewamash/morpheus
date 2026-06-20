import React, { useRef, useEffect, useState } from 'react';

const styles = {
  container: { padding: '16px 0' },
  title: { fontSize: 20, fontWeight: 600, marginBottom: 16, color: '#b388ff' },
  canvas: { width: '100%', height: 500, background: '#0d0d1a', borderRadius: 8 },
  empty: { color: '#8888aa', padding: 40, textAlign: 'center' },
  error: { color: '#ff6b6b', padding: 40, textAlign: 'center' },
  legend: { display: 'flex', gap: 16, marginTop: 12, fontSize: 13, color: '#8888aa' },
};

function MindMap({ data }) {
  const svgRef = useRef(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!data || !data.nodes || data.nodes.length === 0) return;
    let cleanup = null;

    import('d3').then(d3 => {
      const width = svgRef.current?.clientWidth || 800;
      const height = 500;
      const svg = d3.select(svgRef.current)
        .attr('width', width)
        .attr('height', height);

      svg.selectAll('*').remove();

      const simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.edges).id(d => d.id).distance(150))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide(50));

      const link = svg.append('g')
        .selectAll('line')
        .data(data.edges)
        .join('line')
        .attr('stroke', '#2a2a4a')
        .attr('stroke-width', 2)
        .attr('stroke-opacity', 0.6);

      const node = svg.append('g')
        .selectAll('circle')
        .data(data.nodes)
        .join('circle')
        .attr('r', d => Math.max(20, Math.min(40, 10 + (d.event_count || 0) * 2)))
        .attr('fill', '#b388ff')
        .attr('stroke', '#7c4dff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .call(d3.drag()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }));

      const label = svg.append('g')
        .selectAll('text')
        .data(data.nodes)
        .join('text')
        .text(d => d.label)
        .attr('text-anchor', 'middle')
        .attr('dy', 4)
        .attr('fill', '#fff')
        .attr('font-size', 12)
        .attr('font-weight', 500);

      node.append('title')
        .text(d => `${d.label}\n${d.title}\nEvents: ${d.event_count}`);

      simulation.on('tick', () => {
        link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);
        node
          .attr('cx', d => d.x)
          .attr('cy', d => d.y);
        label
          .attr('x', d => d.x)
          .attr('y', d => d.y);
      });

      cleanup = () => simulation.stop();
    }).catch(err => setError(String(err)));

    return () => { if (cleanup) cleanup(); };
  }, [data]);

  if (error) return <div style={styles.error}>Error: {error}</div>;
  if (!data) return <div style={styles.empty}>Select a run to view its mind map.</div>;
  if (!data.nodes || data.nodes.length === 0)
    return <div style={styles.empty}>No nodes to display for this run.</div>;

  return (
    <div style={styles.container}>
      <div style={styles.title}>Execution Mind Map</div>
      <svg ref={svgRef} style={styles.canvas}></svg>
      <div style={styles.legend}>
        <span>Node size = event count</span>
        <span>Drag nodes to explore</span>
        <span>Hover for details</span>
      </div>
    </div>
  );
}

export default MindMap;
