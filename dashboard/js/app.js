/**
 * app.js - State Management & Interactive Logic for DataCo Dashboard
 * Handles reactive filtering, KPI calculations, accessibility, and state handling.
 */

(function () {
  'use strict';

  // Application State
  const state = {
    currentThreshold: 0.50,
    selectedMarket: 'ALL',
    selectedShippingMode: 'ALL',
    searchQuery: '',
    isLoading: true,
    hasError: false,
    errorMessage: ''
  };

  // DOM Elements Cache
  let elements = {};

  function initElements() {
    elements = {
      appRoot: document.getElementById('dashboardRoot'),
      loadingState: document.getElementById('loadingState'),
      errorState: document.getElementById('errorState'),
      errorMessage: document.getElementById('errorMessage'),
      sliderThreshold: document.getElementById('sliderThreshold'),
      thresholdVal: document.getElementById('thresholdVal'),
      filterMarket: document.getElementById('filterMarket'),
      filterShippingMode: document.getElementById('filterShippingMode'),
      searchOrder: document.getElementById('searchOrder'),
      kpiHighRisk: document.getElementById('kpiHighRisk'),
      kpiHighRiskSub: document.getElementById('kpiHighRiskSub'),
      queueCountBadge: document.getElementById('queueCountBadge'),
      orderTableBody: document.getElementById('orderTableBody')
    };
  }

  function getFilteredOrders() {
    if (!window.DASHBOARD_DATA || !Array.isArray(window.DASHBOARD_DATA.orders)) {
      return [];
    }

    const { selectedMarket, selectedShippingMode, searchQuery } = state;

    return window.DASHBOARD_DATA.orders.filter(item => {
      const matchMarket = (selectedMarket === 'ALL' || item.market === selectedMarket);
      const matchShipping = (selectedShippingMode === 'ALL' || item.shipping_mode === selectedShippingMode);
      const matchSearch = (!searchQuery ||
        item.order_id.toString().includes(searchQuery) ||
        (item.categories && item.categories.toLowerCase().includes(searchQuery)) ||
        (item.shipping_mode && item.shipping_mode.toLowerCase().includes(searchQuery))
      );
      return matchMarket && matchShipping && matchSearch;
    });
  }

  function updateKPIs() {
    if (!window.DASHBOARD_DATA || !window.DASHBOARD_DATA.histogram) return;

    let totalHighRisk = 0;
    window.DASHBOARD_DATA.histogram.forEach(bucket => {
      if (bucket.mid >= state.currentThreshold) {
        totalHighRisk += bucket.count;
      }
    });

    const totalOrders = window.DASHBOARD_DATA.kpi.total_test_orders || 8043;
    const percentage = ((totalHighRisk / totalOrders) * 100).toFixed(1);

    if (elements.kpiHighRisk) {
      elements.kpiHighRisk.textContent = `${totalHighRisk.toLocaleString('id-ID')} (${percentage}%)`;
    }
    if (elements.kpiHighRiskSub) {
      elements.kpiHighRiskSub.textContent = `Probabilitas risiko >= ${state.currentThreshold.toFixed(2)}`;
    }
  }

  function updateTable() {
    if (!elements.orderTableBody) return;

    const filtered = getFilteredOrders();
    elements.orderTableBody.innerHTML = '';

    if (elements.queueCountBadge) {
      elements.queueCountBadge.textContent = `${filtered.length.toLocaleString('id-ID')} Pesanan`;
    }

    if (filtered.length === 0) {
      elements.orderTableBody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-8 text-slate-500 font-medium bg-slate-50/50">
            <div class="flex flex-col items-center justify-center gap-1">
              <span class="text-slate-700 font-semibold text-xs">Tidak Ada Pesanan Ditemukan</span>
              <span class="text-[11px] text-slate-500">Sesuaikan filter wilayah, metode pengiriman, atau kata kunci pencarian Anda.</span>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    // Render first 35 items to maintain peak scrolling performance
    const fragment = document.createDocumentFragment();
    const displayList = filtered.slice(0, 35);

    displayList.forEach(order => {
      const isCritical = order.risk_prob >= state.currentThreshold;
      const row = document.createElement('tr');
      row.className = isCritical
        ? 'bg-rose-50/40 hover:bg-rose-50/80 transition-colors border-b border-slate-100'
        : 'hover:bg-slate-50 transition-colors border-b border-slate-100';

      const isHigh = order.risk_prob >= 0.75;
      const isMedium = order.risk_prob >= 0.50;

      const badgeColor = isHigh
        ? 'bg-rose-50 text-rose-700 border-rose-200'
        : (isMedium ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-slate-50 text-slate-700 border-slate-200');

      row.innerHTML = `
        <td class="py-2.5 px-3 font-mono font-bold text-slate-900">${order.order_id}</td>
        <td class="py-2.5 px-3 text-slate-700">${order.shipping_mode}</td>
        <td class="py-2.5 px-3 font-mono text-slate-600">${order.scheduled_days} hari</td>
        <td class="py-2.5 px-3 font-mono font-bold ${order.risk_prob >= 0.70 ? 'text-rose-700' : 'text-slate-800'}">
          ${(order.risk_prob).toFixed(4)}
        </td>
        <td class="py-2.5 px-3 text-slate-600 truncate max-w-[160px]" title="${order.categories}">
          ${order.categories}
        </td>
        <td class="py-2.5 px-3">
          <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${badgeColor}">
            ${order.action}
          </span>
        </td>
      `;
      fragment.appendChild(row);
    });

    elements.orderTableBody.appendChild(fragment);
  }

  function renderCharts() {
    if (!window.DataCoCharts || !window.DASHBOARD_DATA) return;

    window.DataCoCharts.renderDistributionPlot(
      'plotDistribution',
      window.DASHBOARD_DATA.histogram,
      state.currentThreshold
    );

    window.DataCoCharts.renderGraphHubsPlot(
      'plotGraphHubs',
      window.DASHBOARD_DATA.top_categories_graph
    );

    window.DataCoCharts.renderShippingModePlot(
      'plotShippingMode',
      window.DASHBOARD_DATA.shipping_modes
    );
  }

  function renderAll() {
    updateKPIs();
    updateTable();
    renderCharts();
  }

  function attachListeners() {
    if (elements.sliderThreshold) {
      elements.sliderThreshold.addEventListener('input', (e) => {
        state.currentThreshold = parseFloat(e.target.value);
        if (elements.thresholdVal) {
          elements.thresholdVal.textContent = state.currentThreshold.toFixed(2);
        }
        updateKPIs();
        updateTable();
        // Update distribution plot threshold line
        if (window.DataCoCharts && window.DASHBOARD_DATA) {
          window.DataCoCharts.renderDistributionPlot(
            'plotDistribution',
            window.DASHBOARD_DATA.histogram,
            state.currentThreshold
          );
        }
      });
    }

    if (elements.filterMarket) {
      elements.filterMarket.addEventListener('change', (e) => {
        state.selectedMarket = e.target.value;
        updateTable();
      });
    }

    if (elements.filterShippingMode) {
      elements.filterShippingMode.addEventListener('change', (e) => {
        state.selectedShippingMode = e.target.value;
        updateTable();
      });
    }

    if (elements.searchOrder) {
      elements.searchOrder.addEventListener('input', (e) => {
        state.searchQuery = e.target.value.trim().toLowerCase();
        updateTable();
      });
    }

    // Window resize handler for Plotly responsiveness
    window.addEventListener('resize', () => {
      if (window.Plotly) {
        ['plotDistribution', 'plotGraphHubs', 'plotShippingMode'].forEach(id => {
          const el = document.getElementById(id);
          if (el) window.Plotly.Plots.resize(el);
        });
      }
    });
  }

  function initApp() {
    initElements();

    // Verify DataCo dataset presence
    if (!window.DASHBOARD_DATA) {
      showError('Gagal memuat dataset analitik (DASHBOARD_DATA tidak terdefinisi). Silakan periksa berkas data.js.');
      return;
    }

    if (!window.Plotly) {
      showError('Pustaka visualisasi Plotly.js tidak terdeteksi. Silakan periksa koneksi internet Anda.');
      return;
    }

    // Hide loading screen, show dashboard
    hideLoading();
    attachListeners();
    renderAll();
  }

  function showError(msg) {
    state.hasError = true;
    state.errorMessage = msg;
    if (elements.loadingState) elements.loadingState.classList.add('hidden');
    if (elements.errorState) {
      elements.errorState.classList.remove('hidden');
      if (elements.errorMessage) elements.errorMessage.textContent = msg;
    }
  }

  function hideLoading() {
    state.isLoading = false;
    if (elements.loadingState) elements.loadingState.classList.add('hidden');
    if (elements.appRoot) elements.appRoot.classList.remove('opacity-0');
  }

  // Bootstrap when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
  } else {
    initApp();
  }
})();
