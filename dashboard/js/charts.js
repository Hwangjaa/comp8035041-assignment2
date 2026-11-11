/**
 * charts.js - Plotly Chart Visualization Engine for DataCo Analytics
 * Adheres to antislop DESIGN.md: functional palette, high legibility, crisp borders.
 */

window.DataCoCharts = (function () {
  'use strict';

  function renderDistributionPlot(containerId, histogramData, threshold) {
    if (!window.Plotly || !histogramData || histogramData.length === 0) return;

    const x = histogramData.map(d => d.mid);
    const y = histogramData.map(d => d.count);
    const colors = x.map(val => val >= threshold ? '#b91c1c' : '#334155');

    const trace = {
      x: x,
      y: y,
      type: 'bar',
      marker: { color: colors, opacity: 0.9 },
      hovertemplate: 'Skor Risiko: %{x:.2f}<br>Jumlah Pesanan: %{y:,}<extra></extra>'
    };

    const maxY = Math.max(...y);

    const layout = {
      margin: { l: 45, r: 15, t: 20, b: 40 },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { family: 'Plus Jakarta Sans, sans-serif' },
      xaxis: {
        title: { text: 'Probabilitas Risiko Model (Spark MLlib)', font: { size: 11, color: '#334155' } },
        tickfont: { size: 10, color: '#64748b' },
        gridcolor: '#f1f5f9'
      },
      yaxis: {
        title: { text: 'Frekuensi Pesanan', font: { size: 11, color: '#334155' } },
        tickfont: { size: 10, color: '#64748b' },
        gridcolor: '#f1f5f9'
      },
      shapes: [{
        type: 'line',
        x0: threshold,
        x1: threshold,
        y0: 0,
        y1: maxY * 1.05,
        line: { color: '#b91c1c', width: 2, dash: 'dash' }
      }],
      annotations: [{
        x: threshold,
        y: maxY,
        xref: 'x',
        yref: 'y',
        text: `Threshold: ${threshold.toFixed(2)}`,
        showarrow: true,
        arrowhead: 2,
        arrowcolor: '#b91c1c',
        font: { size: 10, color: '#b91c1c', weight: 'bold' }
      }]
    };

    Plotly.newPlot(containerId, [trace], layout, { responsive: true, displayModeBar: false });
  }

  function renderGraphHubsPlot(containerId, topCategories) {
    if (!window.Plotly || !topCategories || topCategories.length === 0) return;

    const dataSlice = topCategories.slice(0, 8);
    const names = dataSlice.map(c => `${c.id}: ${c.name}`);
    const degrees = dataSlice.map(c => c.degree);
    const lateRates = dataSlice.map(c => (c.late_rate * 100).toFixed(1));

    const traceDegrees = {
      x: names,
      y: degrees,
      name: 'Koneksi Pesanan (Degree)',
      type: 'bar',
      marker: { color: '#1e3a5f' },
      hovertemplate: '%{x}<br>Total Pesanan: %{y:,}<extra></extra>'
    };

    const traceLateRate = {
      x: names,
      y: lateRates,
      name: '% Terlambat Empiris',
      type: 'scatter',
      mode: 'lines+markers',
      yaxis: 'y2',
      marker: { color: '#b91c1c', size: 7 },
      line: { color: '#b91c1c', width: 2 },
      hovertemplate: '%{x}<br>Tingkat Terlambat: %{y}%<extra></extra>'
    };

    const layout = {
      margin: { l: 55, r: 50, t: 25, b: 90 },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { family: 'Plus Jakarta Sans, sans-serif' },
      showlegend: true,
      legend: { orientation: 'h', x: 0.05, y: 1.15, font: { size: 10, color: '#334155' } },
      xaxis: {
        tickangle: -30,
        tickfont: { size: 10, color: '#475569' },
        gridcolor: '#f1f5f9'
      },
      yaxis: {
        title: { text: 'Derajat Bipartit (Pesanan Unik)', font: { size: 11, color: '#1e3a5f' } },
        tickfont: { size: 10, color: '#64748b' },
        gridcolor: '#f1f5f9'
      },
      yaxis2: {
        title: { text: 'Tingkat Keterlambatan (%)', font: { size: 11, color: '#b91c1c' } },
        tickfont: { size: 10, color: '#b91c1c' },
        overlaying: 'y',
        side: 'right',
        range: [40, 75],
        gridcolor: 'transparent'
      }
    };

    Plotly.newPlot(containerId, [traceDegrees, traceLateRate], layout, { responsive: true, displayModeBar: false });
  }

  function renderShippingModePlot(containerId, shippingModes) {
    if (!window.Plotly || !shippingModes || shippingModes.length === 0) return;

    const modes = shippingModes.map(s => s['Shipping Mode']);
    const avgProb = shippingModes.map(s => (s.avg_prob * 100).toFixed(1));
    const scheduledDays = shippingModes.map(s => s.avg_scheduled_days);

    const traceProb = {
      x: modes,
      y: avgProb,
      name: 'Rata-rata Skor Risiko (%)',
      type: 'bar',
      marker: { color: '#334155' },
      hovertemplate: '%{x}<br>Skor Risiko: %{y}%<extra></extra>'
    };

    const traceDays = {
      x: modes,
      y: scheduledDays,
      name: 'Durasi Janji (Hari)',
      type: 'scatter',
      mode: 'lines+markers',
      yaxis: 'y2',
      marker: { color: '#1e40af', size: 8 },
      line: { color: '#1e40af', width: 2 },
      hovertemplate: '%{x}<br>Jadwal Janji: %{y} hari<extra></extra>'
    };

    const layout = {
      margin: { l: 45, r: 45, t: 25, b: 35 },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { family: 'Plus Jakarta Sans, sans-serif' },
      showlegend: true,
      legend: { orientation: 'h', x: 0.05, y: 1.15, font: { size: 10, color: '#334155' } },
      xaxis: { tickfont: { size: 10, color: '#475569' }, gridcolor: '#f1f5f9' },
      yaxis: {
        title: { text: 'Skor Risiko (%)', font: { size: 11, color: '#334155' } },
        tickfont: { size: 10, color: '#64748b' },
        range: [0, 100],
        gridcolor: '#f1f5f9'
      },
      yaxis2: {
        title: { text: 'Durasi Janji (Hari)', font: { size: 11, color: '#1e40af' } },
        tickfont: { size: 10, color: '#1e40af' },
        overlaying: 'y',
        side: 'right',
        range: [0, 5],
        gridcolor: 'transparent'
      }
    };

    Plotly.newPlot(containerId, [traceProb, traceDays], layout, { responsive: true, displayModeBar: false });
  }

  return {
    renderDistributionPlot: renderDistributionPlot,
    renderGraphHubsPlot: renderGraphHubsPlot,
    renderShippingModePlot: renderShippingModePlot
  };
})();
