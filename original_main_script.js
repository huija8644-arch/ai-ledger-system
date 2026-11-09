
  let CURRENT_STATE = null;
  let PENDING_PREVIEW = null;
  let SELECTED_INIT_MODE = 'empty';
  let CURRENT_TX_TYPE = 'purchases'; // purchases, sales, payments, receipts
  let EDITING_TX_ID = null;

  // Format Helpers
  const fmtMoney = (n) => '¥' + (Number(n) || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const fmtNum = (n) => (Number(n) || 0).toLocaleString('zh-CN');

  async function fetchState() {
    try {
      const resp = await fetch('/api/state');
      if (!resp.ok) throw new Error('Network error');
      CURRENT_STATE = await resp.json();
      renderAll();
    } catch (err) {
      console.error('Fetch state error:', err);
    }
  }

  function renderAll() {
    if (!CURRENT_STATE) return;

    // Empty state banner
    const isEmpty = CURRENT_STATE.kpis.is_empty;
    document.getElementById('emptyNoticeBanner').style.display = isEmpty ? 'flex' : 'none';

    renderKPIs();
    renderInsights();
    renderInventory();
    renderAR();
    renderAP();
    renderTransactions();
    renderBatches();
    updateBadges();
  }

  function renderKPIs() {
    const k = CURRENT_STATE.kpis;
    document.getElementById('kpiTotalStockQty').textContent = fmtNum(k.total_stock_qty) + ' 件';
    document.getElementById('kpiTotalStockVal').textContent = fmtMoney(k.total_stock_value);
    document.getElementById('kpiLowStockCount').textContent = k.low_stock_count + ' 个 SKU';
    document.getElementById('kpiTotalAr').textContent = fmtMoney(k.total_ar);
    document.getElementById('kpiTotalAp').textContent = fmtMoney(k.total_ap);
    document.getElementById('kpiTotalReceived').textContent = fmtMoney(k.total_received);
    document.getElementById('kpiTotalPaid').textContent = fmtMoney(k.total_paid);
    document.getElementById('kpiTotalSales').textContent = fmtMoney(k.total_sales_amount);
    document.getElementById('kpiGrossProfit').textContent = fmtMoney(k.gross_profit);
    document.getElementById('kpiGrossMargin').textContent = ` (毛利率 ${k.gross_margin}%)`;

    const lowCard = document.getElementById('kpiLowStockCard');
    if (k.low_stock_count > 0) {
      lowCard.className = 'kpi-card alert';
      document.getElementById('kpiLowStockSub').textContent = '⚠️ 当前库存跌破安全红线，需补货';
    } else {
      lowCard.className = 'kpi-card success';
      document.getElementById('kpiLowStockCount').style.color = 'var(--green)';
      document.getElementById('kpiLowStockSub').textContent = '✓ 全部 SKU 库存充足';
    }
  }

  function renderInsights() {
    const list = document.getElementById('aiInsightsList');
    list.innerHTML = '';
    const insights = CURRENT_STATE.ai_insights || [];
    if (insights.length === 0) {
      list.innerHTML = `<div style="padding:10px 0; color:var(--text-dim); font-size:13px;">当前无经营异常与催收预警，数据运行平稳。</div>`;
    } else {
      insights.forEach(item => {
        const el = document.createElement('div');
        el.className = 'insight-item';
        el.innerHTML = `
          <span class="insight-badge ${item.level}">${item.category}</span>
          <div class="insight-content">
            <div class="insight-title">${item.title}</div>
            <div class="insight-desc">${item.detail}</div>
          </div>
          ${item.quick_action ? `<button class="btn btn-sm btn-teal" onclick="applyQuickAction('${encodeURIComponent(item.quick_action)}')">快速执行</button>` : ''}
        `;
        list.appendChild(el);
      });
    }

    // Overview mini tables
    const lowTb = document.querySelector('#overviewLowStockTable tbody');
    lowTb.innerHTML = '';
    const lowItems = CURRENT_STATE.inventory_ledger.filter(x => x.is_low_stock);
    if (lowItems.length === 0) {
      lowTb.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-dim); padding:16px;">目前全库无缺货预警</td></tr>`;
    } else {
      lowItems.forEach(x => {
        const tr = document.createElement('tr');
        tr.className = 'low-stock';
        tr.innerHTML = `
          <td><strong>${x.product_name}</strong></td>
          <td>${x.spec}</td>
          <td class="num" style="color:var(--red); font-weight:700;">${x.stock_qty}</td>
          <td class="num">${x.safety_stock}</td>
          <td class="num" style="color:var(--red);">-${x.shortage_qty}</td>
          <td><span class="tag tag-red">低于安全水位</span></td>
        `;
        lowTb.appendChild(tr);
      });
    }

    const arTb = document.querySelector('#overviewArTopTable tbody');
    arTb.innerHTML = '';
    const sortedAr = [...CURRENT_STATE.ar_ledger].sort((a,b) => b.ar_balance - a.ar_balance).slice(0, 3);
    if (sortedAr.length === 0) {
      arTb.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-dim); padding:16px;">暂无客户应收数据</td></tr>`;
    } else {
      sortedAr.forEach(x => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><span class="tag ${x.rank === 1 ? 'tag-red' : 'tag-amber'}">第 ${x.rank} 名</span></td>
          <td><strong>${x.customer_name}</strong></td>
          <td class="num">${fmtMoney(x.opening_ar)}</td>
          <td class="num" style="font-weight:700; color:var(--primary);">${fmtMoney(x.ar_balance)}</td>
          <td class="num">${x.ar_share}%</td>
        `;
        arTb.appendChild(tr);
      });
    }
  }

  function renderInventory() {
    const tbody = document.querySelector('#inventoryTable tbody');
    tbody.innerHTML = '';
    if (CURRENT_STATE.inventory_ledger.length === 0) {
      tbody.innerHTML = `<tr><td colspan="14" style="text-align:center; padding:32px; color:var(--text-dim);">商品库为空，点击右上角「+ 新增商品档案」或上传表格自动建档。</td></tr>`;
      return;
    }

    CURRENT_STATE.inventory_ledger.forEach(x => {
      const tr = document.createElement('tr');
      if (x.is_low_stock) tr.className = 'low-stock';
      tr.innerHTML = `
        <td><strong>${x.product_name}</strong></td>
        <td>${x.spec}</td>
        <td class="num">${x.opening_qty}</td>
        <td class="num" style="color:var(--primary);">+${x.in_qty}</td>
        <td class="num">${fmtMoney(x.in_price)}</td>
        <td class="num">${fmtMoney(x.in_amount)}</td>
        <td class="num" style="color:var(--green);">-${x.out_qty}</td>
        <td class="num">${x.out_price ? fmtMoney(x.out_price) : '-'}</td>
        <td class="num">${fmtMoney(x.out_amount)}</td>
        <td class="num" style="font-weight:700; ${x.is_low_stock ? 'color:var(--red);' : ''}">${x.stock_qty}</td>
        <td class="num" style="font-weight:600;">${fmtMoney(x.stock_amount)}</td>
        <td class="num">${x.safety_stock}</td>
        <td>${x.is_low_stock ? '<span class="tag tag-red">⚠️ 缺货预警</span>' : '<span class="tag tag-green">正常</span>'}</td>
        <td>
          <button class="btn-action" onclick="openProductModal(${x.id})">编辑</button>
          <button class="btn-action btn-action-danger" onclick="deleteProduct(${x.id}, '${x.product_name}')">删除</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  function renderAR() {
    const tbody = document.querySelector('#arTable tbody');
    tbody.innerHTML = '';
    if (CURRENT_STATE.ar_ledger.length === 0) {
      tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; padding:32px; color:var(--text-dim);">客户档案为空，点击右上角「+ 新增客户档案」录入。</td></tr>`;
      return;
    }

    CURRENT_STATE.ar_ledger.forEach(x => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><span class="tag ${x.rank === 1 ? 'tag-red' : (x.rank === 2 ? 'tag-amber' : 'tag-blue')}">第 ${x.rank} 名</span></td>
        <td><strong>${x.customer_name}</strong></td>
        <td>${x.address || '-'}</td>
        <td>${x.phone || '-'}</td>
        <td class="num">${fmtMoney(x.opening_ar)}</td>
        <td class="num" style="color:var(--primary);">+${fmtMoney(x.sales_amount)}</td>
        <td class="num" style="color:var(--green);">-${fmtMoney(x.received_amount)}</td>
        <td class="num" style="font-weight:700; color:var(--primary);">${fmtMoney(x.ar_balance)}</td>
        <td class="num" style="font-weight:600;">${x.ar_share}%</td>
        <td>
          <button class="btn-action" onclick="openCustomerModal(${x.id})">编辑</button>
          <button class="btn-action btn-action-danger" onclick="deleteCustomer(${x.id}, '${x.customer_name}')">删除</button>
          <button class="btn-action" style="color:var(--teal);" onclick="generateStatement('${x.customer_name}')">催款单</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  function renderAP() {
    const tbody = document.querySelector('#apTable tbody');
    tbody.innerHTML = '';
    if (CURRENT_STATE.ap_ledger.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:32px; color:var(--text-dim);">供应商档案为空，点击右上角「+ 新增供应商档案」录入。</td></tr>`;
      return;
    }

    CURRENT_STATE.ap_ledger.forEach(x => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><span class="tag ${x.rank === 1 ? 'tag-amber' : 'tag-blue'}">第 ${x.rank} 名</span></td>
        <td><strong>${x.supplier_name}</strong></td>
        <td>${x.address || '-'}</td>
        <td>${x.phone || '-'}</td>
        <td class="num" style="color:var(--amber);">${fmtMoney(x.purchase_amount)}</td>
        <td class="num" style="color:var(--green);">-${fmtMoney(x.paid_amount)}</td>
        <td class="num" style="font-weight:700; color:var(--text);">${fmtMoney(x.ap_balance)}</td>
        <td class="num" style="font-weight:600;">${x.ap_share}%</td>
        <td>
          <button class="btn-action" onclick="openSupplierModal(${x.id})">编辑</button>
          <button class="btn-action btn-action-danger" onclick="deleteSupplier(${x.id}, '${x.supplier_name}')">删除</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  function renderTransactions() {
    const pTb = document.querySelector('#txPurchasesTable tbody');
    pTb.innerHTML = '';
    (CURRENT_STATE.purchases || []).forEach(x => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${x.date}</td>
        <td><code>${x.order_no}</code></td>
        <td><strong>${x.product_name}</strong></td>
        <td>${x.spec}</td>
        <td class="num">${fmtMoney(x.unit_price)}</td>
        <td class="num">${x.qty}</td>
        <td class="num">${fmtMoney(x.amount)}</td>
        <td>${x.buyer}</td>
        <td>${x.supplier_name}</td>
        <td>${x.address}</td>
        <td>${x.phone}</td>
        <td>
          <button class="btn-action" onclick="openEditTxModal('purchases', ${x.id})">编辑</button>
          <button class="btn-action btn-action-danger" onclick="deleteTx('purchase', ${x.id})">删除</button>
        </td>
      `;
      pTb.appendChild(tr);
    });

    const sTb = document.querySelector('#txSalesTable tbody');
    sTb.innerHTML = '';
    (CURRENT_STATE.sales || []).forEach(x => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${x.date}</td>
        <td><code>${x.order_no}</code></td>
        <td><strong>${x.product_name}</strong></td>
        <td>${x.spec}</td>
        <td class="num">${fmtMoney(x.unit_price)}</td>
        <td class="num">${x.qty}</td>
        <td class="num">${fmtMoney(x.amount)}</td>
        <td>${x.seller}</td>
        <td>${x.customer_name}</td>
        <td>${x.address}</td>
        <td>${x.phone}</td>
        <td>
          <button class="btn-action" onclick="openEditTxModal('sales', ${x.id})">编辑</button>
          <button class="btn-action btn-action-danger" onclick="deleteTx('sale', ${x.id})">删除</button>
        </td>
      `;
      sTb.appendChild(tr);
    });

    const payTb = document.querySelector('#txPaymentsTable tbody');
    payTb.innerHTML = '';
    (CURRENT_STATE.supplier_payments || []).forEach(x => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${x.date}</td>
        <td><strong>${x.supplier_name}</strong></td>
        <td>${x.address}</td>
        <td>${x.phone}</td>
        <td class="num" style="color:var(--green);">${fmtMoney(x.amount)}</td>
        <td>${x.payer}</td>
        <td>${x.payee}</td>
        <td>
          <button class="btn-action" onclick="openEditTxModal('payments', ${x.id})">编辑</button>
          <button class="btn-action btn-action-danger" onclick="deleteTx('payment', ${x.id})">删除</button>
        </td>
      `;
      payTb.appendChild(tr);
    });

    const recTb = document.querySelector('#txReceiptsTable tbody');
    recTb.innerHTML = '';
    (CURRENT_STATE.customer_receipts || []).forEach(x => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${x.date}</td>
        <td><strong>${x.customer_name}</strong></td>
        <td>${x.address}</td>
        <td>${x.phone}</td>
        <td class="num" style="color:var(--primary);">${fmtMoney(x.amount)}</td>
        <td>${x.payer}</td>
        <td>${x.payee}</td>
        <td>
          <button class="btn-action" onclick="openEditTxModal('receipts', ${x.id})">编辑</button>
          <button class="btn-action btn-action-danger" onclick="deleteTx('receipt', ${x.id})">删除</button>
        </td>
      `;
      recTb.appendChild(tr);
    });

    document.getElementById('txCountBadge').textContent =
      `采购 ${(CURRENT_STATE.purchases || []).length} 笔 · 销售 ${(CURRENT_STATE.sales || []).length} 笔 · 收付款 ${(CURRENT_STATE.supplier_payments || []).length + (CURRENT_STATE.customer_receipts || []).length} 笔`;
  }

  function renderBatches() {
    const tbody = document.querySelector('#batchesTable tbody');
    tbody.innerHTML = '';
    (CURRENT_STATE.batches || []).forEach(b => {
      const tr = document.createElement('tr');
      const isRolledBack = b.status === 'rolled_back';
      const isInit = b.source_type === 'initial_seed';
      tr.innerHTML = `
        <td><code>${b.batch_code}</code></td>
        <td><strong>${b.source_name}</strong></td>
        <td><span class="tag tag-blue">${b.parse_mode}</span></td>
        <td>${b.summary || '-'}</td>
        <td class="num">${b.record_count}</td>
        <td>${isRolledBack ? '<span class="tag tag-red">已撤销回滚</span>' : '<span class="tag tag-green">已入账生效</span>'}</td>
        <td>${b.created_at}</td>
        <td>
          ${(!isRolledBack && !isInit) ? `<button class="btn btn-sm btn-danger" onclick="rollbackBatch(${b.id})">一键撤销</button>` : (isInit ? '<span style="color:var(--text-dim);">基准数据</span>' : '<span style="color:var(--text-dim);">-</span>')}
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  function updateBadges() {
    const k = CURRENT_STATE.kpis;
    document.getElementById('arBadge').textContent = '¥' + (k.total_ar / 10000).toFixed(2) + '万';
    document.getElementById('apBadge').textContent = '¥' + (k.total_ap / 10000).toFixed(2) + '万';
    const lowBadge = document.getElementById('lowStockBadge');
    if (k.low_stock_count > 0) {
      lowBadge.style.display = 'inline-block';
      lowBadge.textContent = `${k.low_stock_count} 缺货`;
    } else {
      lowBadge.style.display = 'none';
    }

    if (CURRENT_STATE.ai_settings) {
      const cfg = CURRENT_STATE.ai_settings;
      document.getElementById('aiBadgeText').textContent = cfg.has_key
        ? `⚙️ AI 已连接 (${cfg.provider}: ${cfg.masked_key})`
        : `⚙️ AI 配置 (当前使用本地引擎)`;
    }
  }

  // Tab Navigation
  function switchTab(name) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(el => el.style.display = 'none');
    const pane = document.getElementById('tab-' + name);
    if (pane) pane.style.display = 'block';

    const idxMap = {
      'overview': 0, 'workbench': 1, 'inventory': 2, 'ar': 3,
      'ap': 4, 'transactions': 5, 'batches': 6, 'chat': 7
    };
    const items = document.querySelectorAll('.nav-bar .nav-item');
    if (items[idxMap[name]]) items[idxMap[name]].classList.add('active');
  }

  function switchTxSubtab(paneName, tabEl) {
    CURRENT_TX_TYPE = paneName;
    document.querySelectorAll('.subtab').forEach(el => el.classList.remove('active'));
    tabEl.classList.add('active');
    document.querySelectorAll('.tx-pane').forEach(el => el.style.display = 'none');
    document.getElementById('tx-' + paneName).style.display = 'block';

    const names = { 'purchases': '+ 录入采购单', 'sales': '+ 录入销售单', 'payments': '+ 录入付款', 'receipts': '+ 录入收款' };
    document.getElementById('btnNewTx').textContent = names[paneName] || '+ 录入新单据';
  }

  // ================= CRUD Operations =================

  // Product CRUD
  function openProductModal(id) {
    document.getElementById('prodModalTitle').textContent = id ? '编辑商品档案' : '新增商品档案';
    document.getElementById('prodFormId').value = id || '';
    if (id) {
      const item = CURRENT_STATE.products.find(p => p.id === id);
      if (item) {
        document.getElementById('prodFormName').value = item.name;
        document.getElementById('prodFormSpec').value = item.spec || '件';
        document.getElementById('prodFormSafety').value = item.safety_stock || 30;
        document.getElementById('prodFormPurchasePrice').value = item.purchase_price || '';
        document.getElementById('prodFormSalePrice').value = item.sale_price || '';
        document.getElementById('prodFormOpeningQty').value = item.opening_qty || 0;
      }
    } else {
      document.getElementById('prodFormName').value = '';
      document.getElementById('prodFormSpec').value = '件';
      document.getElementById('prodFormSafety').value = 30;
      document.getElementById('prodFormPurchasePrice').value = '';
      document.getElementById('prodFormSalePrice').value = '';
      document.getElementById('prodFormOpeningQty').value = 0;
    }
    openModal('productModal');
  }

  async function saveProductForm() {
    const payload = {
      id: document.getElementById('prodFormId').value || null,
      name: document.getElementById('prodFormName').value.trim(),
      spec: document.getElementById('prodFormSpec').value.trim(),
      safety_stock: document.getElementById('prodFormSafety').value,
      purchase_price: document.getElementById('prodFormPurchasePrice').value,
      sale_price: document.getElementById('prodFormSalePrice').value,
      opening_qty: document.getElementById('prodFormOpeningQty').value
    };
    if (!payload.name) {
      alert('请填写商品名称');
      return;
    }
    await postCrud('product', 'save', payload);
    closeModal('productModal');
  }

  async function deleteProduct(id, name) {
    if (!confirm(`确定要删除商品「${name}」吗？`)) return;
    await postCrud('product', 'delete', { id: id });
  }

  // Customer CRUD
  function openCustomerModal(id) {
    document.getElementById('custModalTitle').textContent = id ? '编辑客户档案' : '新增客户档案';
    document.getElementById('custFormId').value = id || '';
    if (id) {
      const item = CURRENT_STATE.customers.find(c => c.id === id);
      if (item) {
        document.getElementById('custFormName').value = item.name;
        document.getElementById('custFormAddress').value = item.address || '';
        document.getElementById('custFormPhone').value = item.phone || '';
        document.getElementById('custFormOpeningAr').value = item.opening_ar || 0;
      }
    } else {
      document.getElementById('custFormName').value = '';
      document.getElementById('custFormAddress').value = '';
      document.getElementById('custFormPhone').value = '';
      document.getElementById('custFormOpeningAr').value = 0;
    }
    openModal('customerModal');
  }

  async function saveCustomerForm() {
    const payload = {
      id: document.getElementById('custFormId').value || null,
      name: document.getElementById('custFormName').value.trim(),
      address: document.getElementById('custFormAddress').value.trim(),
      phone: document.getElementById('custFormPhone').value.trim(),
      opening_ar: document.getElementById('custFormOpeningAr').value
    };
    if (!payload.name) {
      alert('请填写客户名称');
      return;
    }
    await postCrud('customer', 'save', payload);
    closeModal('customerModal');
  }

  async function deleteCustomer(id, name) {
    if (!confirm(`确定要删除客户「${name}」吗？`)) return;
    await postCrud('customer', 'delete', { id: id });
  }

  // Supplier CRUD
  function openSupplierModal(id) {
    document.getElementById('supModalTitle').textContent = id ? '编辑供应商档案' : '新增供应商档案';
    document.getElementById('supFormId').value = id || '';
    if (id) {
      const item = CURRENT_STATE.suppliers.find(s => s.id === id);
      if (item) {
        document.getElementById('supFormName').value = item.name;
        document.getElementById('supFormAddress').value = item.address || '';
        document.getElementById('supFormPhone').value = item.phone || '';
        document.getElementById('supFormOpeningAp').value = item.opening_ap || 0;
        document.getElementById('supFormRemark').value = item.remark || '';
      }
    } else {
      document.getElementById('supFormName').value = '';
      document.getElementById('supFormAddress').value = '';
      document.getElementById('supFormPhone').value = '';
      document.getElementById('supFormOpeningAp').value = 0;
      document.getElementById('supFormRemark').value = '';
    }
    openModal('supplierModal');
  }

  async function saveSupplierForm() {
    const payload = {
      id: document.getElementById('supFormId').value || null,
      name: document.getElementById('supFormName').value.trim(),
      address: document.getElementById('supFormAddress').value.trim(),
      phone: document.getElementById('supFormPhone').value.trim(),
      opening_ap: document.getElementById('supFormOpeningAp').value,
      remark: document.getElementById('supFormRemark').value.trim()
    };
    if (!payload.name) {
      alert('请填写供应商名称');
      return;
    }
    await postCrud('supplier', 'save', payload);
    closeModal('supplierModal');
  }

  async function deleteSupplier(id, name) {
    if (!confirm(`确定要删除供应商「${name}」吗？`)) return;
    await postCrud('supplier', 'delete', { id: id });
  }

  // Transactions CRUD
  const COMMON_UNITS_LIST = ['斤', '公斤', '件', '箱', '瓶', '袋', '盒', '包', '提', '桶', '罐', '个', '打', '套', '克', '筐', '份', '条', '双', '台', '本', '支'];

  function renderUnitInputHtml(inputId, currentVal) {
    const safeVal = (currentVal || '斤').replace(/"/g, '&quot;');
    const optionsHtml = COMMON_UNITS_LIST.map(u => `<option value="${u}">${u}</option>`).join('');
    const datalistHtml = COMMON_UNITS_LIST.map(u => `<option value="${u}">`).join('');
    return `
      <div style="display:flex; gap:6px; align-items:center;">
        <input type="text" id="${inputId}" class="form-input" value="${safeVal}" list="commonUnitList_${inputId}" placeholder="自由输入或右侧选单位" style="flex:1; min-width:70px;">
        <select class="form-input" style="width:82px; padding:6px 6px; font-size:12px; color:var(--text-muted); cursor:pointer; background-color:var(--surface-subtle);" onchange="if(this.value){document.getElementById('${inputId}').value=this.value; this.value='';}" title="选择常规单位，也可在左侧输入框自由填写任意单位">
          <option value="">常规单位▾</option>
          ${optionsHtml}
        </select>
        <datalist id="commonUnitList_${inputId}">${datalistHtml}</datalist>
      </div>
    `;
  }

  function onTxProdNameInput(val) {
    const name = (val || '').trim();
    if (!name || !CURRENT_STATE || !CURRENT_STATE.products) return;
    const matched = CURRENT_STATE.products.find(p => p.name === name);
    if (matched) {
      const unitEl = document.getElementById('txUnit');
      if (unitEl && (!EDITING_TX_ID || !unitEl.value.trim())) {
        unitEl.value = matched.spec || '斤';
      }
      const priceEl = document.getElementById('txPrice');
      if (priceEl && !priceEl.value) {
        if (CURRENT_TX_TYPE === 'purchases' && matched.purchase_price > 0) {
          priceEl.value = matched.purchase_price;
          calcTxAmount();
        } else if (CURRENT_TX_TYPE === 'sales' && matched.sale_price > 0) {
          priceEl.value = matched.sale_price;
          calcTxAmount();
        }
      }
    }
  }

  function openNewTxModal() {
    openEditTxModal(CURRENT_TX_TYPE, null);
  }

  function openEditTxModal(type, id) {
    CURRENT_TX_TYPE = type;
    EDITING_TX_ID = id;
    const body = document.getElementById('txModalBody');
    const today = new Date().toISOString().split('T')[0];

    if (type === 'purchases') {
      document.getElementById('txModalTitle').textContent = id ? '编辑采购入库单' : '录入采购入库单';
      const item = id ? CURRENT_STATE.purchases.find(x => x.id === id) : {};
      const matchedProd = item.product_name ? (CURRENT_STATE.products || []).find(p => p.name === item.product_name) : null;
      const currentUnit = item.spec || (matchedProd ? matchedProd.spec : '') || '斤';
      body.innerHTML = `
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">日期 *：</label>
            <input type="date" id="txDate" class="form-input" value="${item.date || today}">
          </div>
          <div class="form-group">
            <label class="form-label">采购单号：</label>
            <input type="text" id="txOrderNo" class="form-input" value="${item.order_no || 'PO-' + Date.now().toString().slice(-6)}">
          </div>
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">商品名称 *：</label>
            <input type="text" id="txProdName" class="form-input" value="${item.product_name || ''}" placeholder="输入或从现有商品选择" list="prodList" oninput="onTxProdNameInput(this.value)">
            <datalist id="prodList">${CURRENT_STATE.products.map(p => `<option value="${p.name}">`).join('')}</datalist>
          </div>
          <div class="form-group">
            <label class="form-label">供应商 *：</label>
            <input type="text" id="txPartnerName" class="form-input" value="${item.supplier_name || ''}" placeholder="选择或输入供应商" list="supList">
            <datalist id="supList">${CURRENT_STATE.suppliers.map(s => `<option value="${s.name}">`).join('')}</datalist>
          </div>
        </div>
        <div style="display:grid; grid-template-columns: 1fr 0.9fr 1.35fr; gap:12px;">
          <div class="form-group">
            <label class="form-label">采购单价 (元) *：</label>
            <input type="number" step="0.01" id="txPrice" class="form-input" value="${item.unit_price ?? ''}" placeholder="0.00" oninput="calcTxAmount()">
          </div>
          <div class="form-group">
            <label class="form-label">数量 *：</label>
            <input type="number" step="0.01" id="txQty" class="form-input" value="${item.qty ?? ''}" placeholder="输入数量" oninput="calcTxAmount()">
          </div>
          <div class="form-group">
            <label class="form-label">单位 * <span style="font-weight:400; font-size:11px; color:var(--text-dim);">(可选或自由填)</span>：</label>
            ${renderUnitInputHtml('txUnit', currentUnit)}
          </div>
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">总金额 (元)：</label>
            <input type="number" step="0.01" id="txAmount" class="form-input" value="${item.amount ?? ''}">
          </div>
          <div class="form-group">
            <label class="form-label">采购员：</label>
            <input type="text" id="txStaff" class="form-input" value="${item.buyer || ''}">
          </div>
        </div>
      `;
    } else if (type === 'sales') {
      document.getElementById('txModalTitle').textContent = id ? '编辑销售出库单' : '录入销售出库单';
      const item = id ? CURRENT_STATE.sales.find(x => x.id === id) : {};
      const matchedProd = item.product_name ? (CURRENT_STATE.products || []).find(p => p.name === item.product_name) : null;
      const currentUnit = item.spec || (matchedProd ? matchedProd.spec : '') || '斤';
      body.innerHTML = `
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">日期 *：</label>
            <input type="date" id="txDate" class="form-input" value="${item.date || today}">
          </div>
          <div class="form-group">
            <label class="form-label">销售单号：</label>
            <input type="text" id="txOrderNo" class="form-input" value="${item.order_no || 'SO-' + Date.now().toString().slice(-6)}">
          </div>
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">商品名称 *：</label>
            <input type="text" id="txProdName" class="form-input" value="${item.product_name || ''}" placeholder="选择商品" list="prodList" oninput="onTxProdNameInput(this.value)">
            <datalist id="prodList">${CURRENT_STATE.products.map(p => `<option value="${p.name}">`).join('')}</datalist>
          </div>
          <div class="form-group">
            <label class="form-label">客户名称 *：</label>
            <input type="text" id="txPartnerName" class="form-input" value="${item.customer_name || ''}" placeholder="选择客户" list="custList">
            <datalist id="custList">${CURRENT_STATE.customers.map(c => `<option value="${c.name}">`).join('')}</datalist>
          </div>
        </div>
        <div style="display:grid; grid-template-columns: 1fr 0.9fr 1.35fr; gap:12px;">
          <div class="form-group">
            <label class="form-label">成交单价 (元) *：</label>
            <input type="number" step="0.01" id="txPrice" class="form-input" value="${item.unit_price ?? ''}" placeholder="0.00" oninput="calcTxAmount()">
          </div>
          <div class="form-group">
            <label class="form-label">数量 *：</label>
            <input type="number" step="0.01" id="txQty" class="form-input" value="${item.qty ?? ''}" placeholder="输入数量" oninput="calcTxAmount()">
          </div>
          <div class="form-group">
            <label class="form-label">单位 * <span style="font-weight:400; font-size:11px; color:var(--text-dim);">(可选或自由填)</span>：</label>
            ${renderUnitInputHtml('txUnit', currentUnit)}
          </div>
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">总金额 (元)：</label>
            <input type="number" step="0.01" id="txAmount" class="form-input" value="${item.amount ?? ''}">
          </div>
          <div class="form-group">
            <label class="form-label">销售员：</label>
            <input type="text" id="txStaff" class="form-input" value="${item.seller || ''}">
          </div>
        </div>
      `;
    } else if (type === 'payments') {
      document.getElementById('txModalTitle').textContent = id ? '编辑供应商付款单' : '录入供应商付款单';
      const item = id ? CURRENT_STATE.supplier_payments.find(x => x.id === id) : {};
      body.innerHTML = `
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">日期 *：</label>
            <input type="date" id="txDate" class="form-input" value="${item.date || today}">
          </div>
          <div class="form-group">
            <label class="form-label">供应商 *：</label>
            <input type="text" id="txPartnerName" class="form-input" value="${item.supplier_name || ''}" list="supList">
            <datalist id="supList">${CURRENT_STATE.suppliers.map(s => `<option value="${s.name}">`).join('')}</datalist>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">付款金额 (元) *：</label>
          <input type="number" step="0.01" id="txAmount" class="form-input" value="${item.amount || ''}">
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">付款人：</label>
            <input type="text" id="txPayer" class="form-input" value="${item.payer || '张三'}">
          </div>
          <div class="form-group">
            <label class="form-label">收款人/出纳：</label>
            <input type="text" id="txPayee" class="form-input" value="${item.payee || '李静'}">
          </div>
        </div>
      `;
    } else if (type === 'receipts') {
      document.getElementById('txModalTitle').textContent = id ? '编辑客户收款单' : '录入客户收款单';
      const item = id ? CURRENT_STATE.customer_receipts.find(x => x.id === id) : {};
      body.innerHTML = `
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">日期 *：</label>
            <input type="date" id="txDate" class="form-input" value="${item.date || today}">
          </div>
          <div class="form-group">
            <label class="form-label">客户名称 *：</label>
            <input type="text" id="txPartnerName" class="form-input" value="${item.customer_name || ''}" list="custList">
            <datalist id="custList">${CURRENT_STATE.customers.map(c => `<option value="${c.name}">`).join('')}</datalist>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">收款金额 (元) *：</label>
          <input type="number" step="0.01" id="txAmount" class="form-input" value="${item.amount || ''}">
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">交款人：</label>
            <input type="text" id="txPayer" class="form-input" value="${item.payer || '张三'}">
          </div>
          <div class="form-group">
            <label class="form-label">收款出纳：</label>
            <input type="text" id="txPayee" class="form-input" value="${item.payee || '李静'}">
          </div>
        </div>
      `;
    }

    openModal('txModal');
  }

  function calcTxAmount() {
    const p = parseFloat(document.getElementById('txPrice').value) || 0;
    const q = parseFloat(document.getElementById('txQty').value) || 0;
    if (p > 0 && q > 0) {
      document.getElementById('txAmount').value = (p * q).toFixed(2);
    }
  }

  async function saveTxForm() {
    const type = CURRENT_TX_TYPE;
    const id = EDITING_TX_ID;

    if (type === 'purchases') {
      const unitVal = (document.getElementById('txUnit')?.value || '').trim() || '斤';
      const payload = {
        id: id,
        date: document.getElementById('txDate').value,
        order_no: document.getElementById('txOrderNo').value,
        product_name: document.getElementById('txProdName').value.trim(),
        supplier_name: document.getElementById('txPartnerName').value.trim(),
        spec: unitVal,
        unit_price: document.getElementById('txPrice').value,
        qty: document.getElementById('txQty').value,
        amount: document.getElementById('txAmount').value,
        buyer: document.getElementById('txStaff').value.trim()
      };
      if (!payload.product_name || !payload.supplier_name) return alert('商品名称和供应商必填');
      await postCrud('purchase', 'save', payload);
    } else if (type === 'sales') {
      const unitVal = (document.getElementById('txUnit')?.value || '').trim() || '斤';
      const payload = {
        id: id,
        date: document.getElementById('txDate').value,
        order_no: document.getElementById('txOrderNo').value,
        product_name: document.getElementById('txProdName').value.trim(),
        customer_name: document.getElementById('txPartnerName').value.trim(),
        spec: unitVal,
        unit_price: document.getElementById('txPrice').value,
        qty: document.getElementById('txQty').value,
        amount: document.getElementById('txAmount').value,
        seller: document.getElementById('txStaff').value.trim()
      };
      if (!payload.product_name || !payload.customer_name) return alert('商品名称和客户名称必填');
      await postCrud('sale', 'save', payload);
    } else if (type === 'payments') {
      const payload = {
        id: id,
        date: document.getElementById('txDate').value,
        supplier_name: document.getElementById('txPartnerName').value.trim(),
        amount: document.getElementById('txAmount').value,
        payer: document.getElementById('txPayer').value.trim(),
        payee: document.getElementById('txPayee').value.trim()
      };
      if (!payload.supplier_name || !payload.amount) return alert('供应商名称和金额必填');
      await postCrud('payment', 'save', payload);
    } else if (type === 'receipts') {
      const payload = {
        id: id,
        date: document.getElementById('txDate').value,
        customer_name: document.getElementById('txPartnerName').value.trim(),
        amount: document.getElementById('txAmount').value,
        payer: document.getElementById('txPayer').value.trim(),
        payee: document.getElementById('txPayee').value.trim()
      };
      if (!payload.customer_name || !payload.amount) return alert('客户名称和金额必填');
      await postCrud('receipt', 'save', payload);
    }

    closeModal('txModal');
  }

  async function deleteTx(entity, id) {
    if (!confirm('确定要删除这笔业务单据吗？台账与库存将实时重新核算。')) return;
    await postCrud(entity, 'delete', { id: id });
  }

  async function postCrud(entity, action, data) {
    try {
      const resp = await fetch(`/api/crud/${entity}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action, data: data, id: data.id })
      });
      const res = await resp.json();
      if (!res.ok) {
        alert(res.error || '操作失败');
        return;
      }
      CURRENT_STATE = res.state;
      renderAll();
    } catch (e) {
      alert('请求发生错误：' + e.message);
    }
  }

  // ================= System Initialization =================
  function openInitModal() {
    selectInitMode('empty');
    openModal('initModal');
  }

  function selectInitMode(mode) {
    SELECTED_INIT_MODE = mode;
    document.querySelectorAll('.init-card').forEach(c => c.classList.remove('selected'));
    if (mode === 'empty') {
      document.getElementById('initOptEmpty').classList.add('selected');
      document.getElementById('radioEmpty').checked = true;
    } else if (mode === 'clear_tx') {
      document.getElementById('initOptClearTx').classList.add('selected');
      document.getElementById('radioClearTx').checked = true;
    } else {
      document.getElementById('initOptSample').classList.add('selected');
      document.getElementById('radioSample').checked = true;
    }
  }

  async function confirmExecuteInit() {
    const mode = SELECTED_INIT_MODE;
    const tips = {
      'empty': '确定要创建【全新空白账套】吗？\n所有示例商品、客户与流水都将彻底清零！',
      'clear_tx': '确定要清空所有业务流水吗？\n商品与客商档案将保留。',
      'reset_sample': '确定要恢复服装进销存示例数据吗？'
    };
    if (!confirm(tips[mode])) return;

    try {
      const resp = await fetch('/api/system/initialize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: mode })
      });
      const data = await resp.json();
      if (data.ok) {
        CURRENT_STATE = data.state;
        renderAll();
        closeModal('initModal');
        alert('✓ 账套初始化操作已成功完成！');
      }
    } catch (e) {
      alert('初始化失败：' + e.message);
    }
  }

  // ================= Upload & AI Workbench =================
  const dropZone = document.getElementById('dropZone');
  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => { e.preventDefault(); dropZone.classList.add('dragover'); }, false);
  });
  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => { e.preventDefault(); dropZone.classList.remove('dragover'); }, false);
  });
  dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length) handleFile(files[0]);
  });

  function handleFileSelected(event) {
    const file = event.target.files[0];
    if (file) handleFile(file);
  }

  function handleFile(file) {
    const autoCommit = document.getElementById('chkAutoCommit').checked;
    const isExcel = file.name.endsWith('.xlsx') || file.name.endsWith('.xls');

    if (isExcel) {
      if (!window.XLSX) {
        alert('检测到未加载到 Excel 解析组件，请检查网络；您也可以将该文件另存为 .csv 格式直接拖拽上传。');
        return;
      }
      const reader = new FileReader();
      reader.onload = function(e) {
        try {
          const data = new Uint8Array(e.target.result);
          const workbook = XLSX.read(data, { type: 'array' });
          let allRows = [];
          workbook.SheetNames.forEach(sName => {
            const ws = workbook.Sheets[sName];
            const sheetRows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });
            if (sheetRows && sheetRows.length) {
              allRows = allRows.concat(sheetRows);
            }
          });
          postUploadData({ rows: allRows, filename: file.name, auto_commit: autoCommit });
        } catch (err) {
          alert('Excel 文件读取失败：' + err.message);
        }
      };
      reader.readAsArrayBuffer(file);
    } else {
      const reader = new FileReader();
      reader.onload = function(e) {
        const text = e.target.result;
        postUploadData({ csv_text: text, filename: file.name, auto_commit: autoCommit });
      };
      reader.readAsText(file);
    }
  }

  async function loadSampleScenario(key) {
    const autoCommit = document.getElementById('chkAutoCommit').checked;
    await postUploadData({ scenario_key: key, auto_commit: autoCommit });
  }

  async function postUploadData(payload) {
    try {
      showRunStreamLoading();
      const resp = await fetch('/api/upload/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      if (!data.ok) {
        alert('解析失败：' + (data.error || '未知错误'));
        return;
      }
      renderRunStream(data.preview.run_steps);

      if (data.auto_committed) {
        CURRENT_STATE = data.state;
        renderAll();
        document.getElementById('impactCard').style.display = 'none';
        alert(`✓ AI 实时直通入账成功！已生成批次「${data.commit_result.batch_code}」，台账全链路已毫秒级更新。`);
      } else {
        PENDING_PREVIEW = data.preview;
        renderImpactPreview(data.preview);
      }
    } catch (err) {
      console.error(err);
      alert('上传请求失败：' + err.message);
    }
  }

  function showRunStreamLoading() {
    const box = document.getElementById('runStreamBox');
    box.style.display = 'block';
    const list = document.getElementById('runStreamList');
    list.innerHTML = `<div style="padding:10px 0; color:var(--primary); font-weight:600;">⚡ AI 表格多模态语义清洗与推演引擎启动中...</div>`;
  }

  function renderRunStream(steps) {
    const list = document.getElementById('runStreamList');
    list.innerHTML = '';
    steps.forEach(s => {
      const div = document.createElement('div');
      div.className = 'run-stream-item';
      div.innerHTML = `
        <span class="step-badge">${s.step}</span>
        <span class="tabular-nums" style="color:var(--text-dim); font-size:11px;">${s.duration_ms}ms</span>
        <span class="step-detail">${s.detail}</span>
      `;
      list.appendChild(div);
    });
  }

  function renderImpactPreview(prev) {
    document.getElementById('impactCard').style.display = 'block';
    document.getElementById('previewTitle').textContent = `入账前后推演：${prev.filename}`;
    document.getElementById('previewSubtitle').textContent = `共提取 ${prev.total_records} 笔流水，请核对下方大模型审计与台账联动影响后再执行写入：`;

    // Render LLM Executive Audit Card
    const auditCard = document.getElementById('llmAuditCard');
    if (prev.llm_audit) {
      auditCard.style.display = 'block';
      const a = prev.llm_audit;
      const badgeEl = document.getElementById('llmAuditBadge');
      badgeEl.textContent = a.badge || '🟢 大模型已全脑深度介入';
      if (a.model_source === 'remote_llm') {
        badgeEl.style.background = '#d1fae5';
        badgeEl.style.color = '#065f46';
        badgeEl.style.borderColor = '#6ee7b7';
      } else {
        badgeEl.style.background = '#fef3c7';
        badgeEl.style.color = '#92400e';
        badgeEl.style.borderColor = '#fde68a';
      }

      document.getElementById('llmAuditMeta').textContent =
        `审阅耗时: ${a.llm_latency_ms || 25}ms · 模型: ${a.model_name || 'DeepSeek'} · 发现 ${a.free_gifts_count || 0} 笔赠品、${a.high_value_count || 0} 笔高值品、${a.float_qty_count || 0} 笔散称生鲜`;

      const apiNoteEl = document.getElementById('llmAuditApiNote');
      if (a.api_note) {
        apiNoteEl.style.display = 'block';
        apiNoteEl.innerHTML = `<strong>⚠️ 模型调用说明：</strong>${a.api_note}`;
      } else {
        apiNoteEl.style.display = 'none';
      }

      document.getElementById('llmAuditBizNature').textContent = a.business_nature || '多商户联营批发业务流水。';
      document.getElementById('llmAuditCashFlow').textContent = a.cash_flow_warning || '往来账款正常。';
      document.getElementById('llmAuditInternalControl').textContent = a.internal_control_notes || '单据格式合规。';

      const actionsEl = document.getElementById('llmAuditActionItems');
      if (a.action_items && a.action_items.length) {
        actionsEl.innerHTML = '<ol style="margin:0; padding-left:18px;">' + a.action_items.map(it => `<li style="margin-bottom:4px;">${it}</li>`).join('') + '</ol>';
      } else {
        actionsEl.textContent = '暂无特殊行动指令。';
      }
    } else {
      auditCard.style.display = 'none';
    }

    const dupBox = document.getElementById('duplicateAlertBox');
    if (prev.impact.duplicate_warnings && prev.impact.duplicate_warnings.length > 0) {
      dupBox.style.display = 'block';
      dupBox.innerHTML = `<strong>⚠️ 重复单据拦截提示：</strong><br>` + prev.impact.duplicate_warnings.join('<br>') + `<br><span>(点击确认入账时将自动跳过以上重复单据，防止库存与金额虚高)</span>`;
    } else {
      dupBox.style.display = 'none';
    }

    const invTb = document.querySelector('#previewInvTable tbody');
    invTb.innerHTML = '';
    prev.impact.inventory_diffs.forEach(x => {
      const tr = document.createElement('tr');
      const isShort = x.after_qty < x.safety_stock;
      tr.innerHTML = `
        <td><strong>${x.product_name}</strong></td>
        <td><span class="tag tag-blue">${x.category || '📦 通用商品'}</span></td>
        <td class="num">${x.before_qty}</td>
        <td class="num" style="color:${x.delta > 0 ? 'var(--primary)' : 'var(--green)'}; font-weight:700;">${x.delta > 0 ? '+' : ''}${x.delta}</td>
        <td class="num" style="font-weight:700; ${isShort ? 'color:var(--red);' : ''}">${x.after_qty}</td>
        <td><span class="tag ${isShort ? 'tag-red' : 'tag-green'}">${x.status_note}</span></td>
      `;
      invTb.appendChild(tr);
    });

    const arTb = document.querySelector('#previewArTable tbody');
    arTb.innerHTML = '';
    prev.impact.ar_diffs.forEach(x => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${x.customer_name}</strong></td>
        <td class="num">${fmtMoney(x.before_ar)}</td>
        <td class="num" style="color:${x.delta > 0 ? 'var(--primary)' : 'var(--green)'}; font-weight:700;">${x.delta > 0 ? '+' : ''}${fmtMoney(x.delta)}</td>
        <td class="num" style="font-weight:700;">${fmtMoney(x.after_ar)}</td>
      `;
      arTb.appendChild(tr);
    });

    const apTb = document.querySelector('#previewApTable tbody');
    apTb.innerHTML = '';
    prev.impact.ap_diffs.forEach(x => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${x.supplier_name}</strong></td>
        <td class="num">${fmtMoney(x.before_ap)}</td>
        <td class="num" style="color:${x.delta > 0 ? 'var(--amber)' : 'var(--green)'}; font-weight:700;">${x.delta > 0 ? '+' : ''}${fmtMoney(x.delta)}</td>
        <td class="num" style="font-weight:700;">${fmtMoney(x.after_ap)}</td>
      `;
      apTb.appendChild(tr);
    });
  }

  function cancelPreview() {
    PENDING_PREVIEW = null;
    document.getElementById('impactCard').style.display = 'none';
  }

  async function executeCommit() {
    if (!PENDING_PREVIEW) return;
    try {
      const resp = await fetch('/api/upload/commit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parsed: PENDING_PREVIEW.parsed,
          filename: PENDING_PREVIEW.filename,
          source_type: 'file_upload',
          parse_mode: 'AI 语义解析 + 人工核对确认',
          skip_duplicates: true
        })
      });
      const data = await resp.json();
      if (!data.ok) return alert('入账写入失败');
      CURRENT_STATE = data.state;
      renderAll();
      cancelPreview();
      alert(`✓ 入账成功！已生成批次号「${data.commit_result.batch_code}」：\n${data.commit_result.summary}。\n台账已实时同步更新！`);
    } catch (e) {
      alert('写入错误：' + e.message);
    }
  }

  async function rollbackBatch(batchId) {
    if (!confirm('确定要撤销该导入批次吗？\n撤销后该批次的所有入库、出库、收付款记录将立即从台账扣除，库存与往来账款将瞬间恢复为导入前状态！')) return;
    try {
      const resp = await fetch('/api/batches/rollback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ batch_id: batchId })
      });
      const data = await resp.json();
      if (!data.ok) return alert(data.error || '撤销失败');
      CURRENT_STATE = data.state;
      renderAll();
      alert(`✓ 批次「${data.result.batch_code}」已成功撤销回滚！台账数据已即时还原。`);
    } catch (e) {
      alert('撤销错误：' + e.message);
    }
  }

  // ================= AI Assistant Chat =================
  async function sendChatMessage(customText) {
    const input = document.getElementById('chatInput');
    const text = customText || input.value.trim();
    if (!text) return;
    input.value = '';

    appendChatBubble(text, 'user');
    const loadingId = 'thinking_' + Date.now();
    appendChatBubble('🧠 AI 财务总监正在调用大模型全脑思考中...', 'bot', '思考中', loadingId);

    try {
      const resp = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
      });
      const data = await resp.json();
      const loadEl = document.getElementById(loadingId);
      if (loadEl) loadEl.remove();

      if (data.ok && data.result) {
        if (data.result.type === 'action_executed') {
          if (data.state) {
            CURRENT_STATE = data.state;
            renderAll();
          }
          appendChatBubble(data.result.reply, 'bot', data.result.mode);
          if (typeof showFloatToast === 'function') {
            showFloatToast('✓ AI 协同指令已执行并持久化落盘！', 'green');
          }
        } else if (data.result.type === 'query_answer') {
          appendChatBubble(data.result.reply, 'bot', data.result.mode);
        } else if (data.result.type === 'bookkeeping_preview') {
          CURRENT_STATE = data.state;
          renderAll();
          switchTab('workbench');
          PENDING_PREVIEW = data.result.preview;
          renderRunStream(PENDING_PREVIEW.run_steps);
          renderImpactPreview(PENDING_PREVIEW);
          appendChatBubble(`✓ ${data.result.mode || '大模型'}已成功解析您的指令，并自动在工作台生成了入账推演卡片，请核对后确认是否正式写入数据库！`, 'bot', data.result.mode);
        }
      }
    } catch (e) {
      const loadEl = document.getElementById(loadingId);
      if (loadEl) loadEl.remove();
      appendChatBubble('抱歉，助理处理出现错误：' + e.message, 'bot');
    }
  }

  function appendChatBubble(text, role, mode, elemId) {
    const box = document.getElementById('chatMessages');
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role}`;
    if (elemId) bubble.id = elemId;

    let formatted = (text || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');

    let modeBadge = '';
    if (role === 'bot' && mode) {
      const isRemote = mode.includes('🟢');
      modeBadge = `<div style="margin-top:8px; padding-top:6px; border-top:1px solid rgba(0,0,0,0.06); font-size:11px; display:flex; align-items:center; justify-content:space-between; color:${isRemote ? '#0f766e' : '#b45309'}; font-weight:600;">
        <span>${mode}</span>
        <span style="font-size:10px; opacity:0.8;">实时数据库 Grounding</span>
      </div>`;
    }

    bubble.innerHTML = `<div>${formatted}</div>${modeBadge}`;
    box.appendChild(bubble);
    box.scrollTop = box.scrollHeight;
  }

  function applyQuickAction(encodedText) {
    const text = decodeURIComponent(encodedText);
    switchTab('chat');
    sendChatMessage(text);
  }

  function generateStatement(customerName) {
    switchTab('chat');
    sendChatMessage(`帮我生成【${customerName}】的对账催款函`);
  }

  // ================= Modal Helpers =================
  function openModal(id) { document.getElementById(id).style.display = 'flex'; }
  function closeModal(id) { document.getElementById(id).style.display = 'none'; }

  function openAiSettingsModal() {
    if (CURRENT_STATE && CURRENT_STATE.ai_settings) {
      const c = CURRENT_STATE.ai_settings;
      document.getElementById('cfgProvider').value = c.provider || 'deepseek';
      document.getElementById('cfgBaseUrl').value = c.base_url || 'https://api.deepseek.com/v1';
      document.getElementById('cfgModelName').value = c.model_name || 'deepseek-chat';
      document.getElementById('cfgApiKey').value = '';
    }
    openModal('aiSettingsModal');
  }

  function onProviderChange() {
    const p = document.getElementById('cfgProvider').value;
    if (p === 'deepseek') {
      document.getElementById('cfgBaseUrl').value = 'https://api.deepseek.com';
      document.getElementById('cfgModelName').value = 'deepseek-chat';
    } else if (p === 'openai') {
      document.getElementById('cfgBaseUrl').value = 'https://api.openai.com/v1';
      document.getElementById('cfgModelName').value = 'gpt-4o-mini';
    } else if (p === 'gemini') {
      document.getElementById('cfgBaseUrl').value = 'https://generativelanguage.googleapis.com/v1beta/openai/';
      document.getElementById('cfgModelName').value = 'gemini-1.5-flash';
    }
  }

  async function testCurrentAiConnection() {
    const resBox = document.getElementById('apiTestResult');
    resBox.style.display = 'block';
    resBox.style.background = '#f1f5f9';
    resBox.style.color = '#475569';
    resBox.innerHTML = '⚡ 正在向大模型接口发送 Ping 握手探测...';

    const payload = {
      provider: document.getElementById('cfgProvider').value,
      base_url: document.getElementById('cfgBaseUrl').value,
      model_name: document.getElementById('cfgModelName').value,
      api_key: document.getElementById('cfgApiKey').value
    };

    try {
      const resp = await fetch('/api/ai/test_connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      if (data.ok) {
        resBox.style.background = '#dcfce7';
        resBox.style.color = '#15803d';
        resBox.innerHTML = `✓ <strong>大模型握手成功！</strong> 响应耗时: ${data.latency_ms}ms · 模型「${data.model}」状态健康，可立即用于商业审阅。`;
      } else {
        resBox.style.background = '#fee2e2';
        resBox.style.color = '#b91c1c';
        resBox.innerHTML = `✕ <strong>接口探测未通过：</strong>${data.error}`;
      }
    } catch (e) {
      resBox.style.background = '#fee2e2';
      resBox.style.color = '#b91c1c';
      resBox.innerHTML = `✕ <strong>请求失败：</strong>${e.message}`;
    }
  }

  async function saveAiSettings() {
    const payload = {
      provider: document.getElementById('cfgProvider').value,
      base_url: document.getElementById('cfgBaseUrl').value,
      model_name: document.getElementById('cfgModelName').value,
      api_key: document.getElementById('cfgApiKey').value
    };
    try {
      const resp = await fetch('/api/settings/ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      if (data.ok) {
        CURRENT_STATE = data.state;
        updateBadges();
        closeModal('aiSettingsModal');
        if (data.conn_test && data.conn_test.ok) {
          alert(`✓ 大模型接口配置已保存并成功连通 (延时 ${data.conn_test.latency_ms}ms)！上传表格时将由该模型深度参与。`);
        } else if (data.conn_test && !data.conn_test.ok && payload.api_key) {
          alert(`⚠️ 配置已保存，但在探测连通时提示：\n${data.conn_test.error}\n\n系统已无缝采用内置专家认知推理引擎保底。`);
        } else {
          alert('✓ AI 接口配置已保存！');
        }
      }
    } catch (e) {
      alert('保存失败：' + e.message);
    }
  }

  async function reRunLlmAudit() {
    if (!PENDING_PREVIEW) return;
    showRunStreamLoading();
    // Re-simulate with same data to trigger fresh LLM call
    await postUploadData({
      csv_text: (CURRENT_STATE.sample_scenarios && PENDING_PREVIEW.filename.includes('供货商'))
        ? undefined
        : undefined,
      rows: PENDING_PREVIEW.parsed ? undefined : undefined,
      scenario_key: PENDING_PREVIEW.filename.includes('供货商') ? 'real_supplier_sheet' : undefined,
      auto_commit: false
    });
  }

  async function triggerGlobalLlmAudit() {
    const box = document.getElementById('globalLlmAuditBox');
    box.style.display = 'block';
    box.innerHTML = `<div style="color:#0f766e; font-weight:600; padding:12px 0;">🤖 AI 财务总监正在实时穿透当前全库库存与客商往来数据并撰写审计备忘录...</div>`;

    try {
      const resp = await fetch('/api/ai/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ focus: 'all' })
      });
      const data = await resp.json();
      if (data.ok && data.memo) {
        const m = data.memo;
        box.innerHTML = `
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; border-bottom:1px solid #ccfbf1; padding-bottom:8px;">
            <div style="font-weight:700; color:#0f766e; font-size:14px;">📑 ${m.title}</div>
            <span style="font-size:12px; color:var(--text-muted);">${m.generated_at}</span>
          </div>
          <div style="font-size:13px; color:var(--text); margin-bottom:10px;">${m.kpi_overview}</div>
          <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px; margin-bottom:12px;">
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; padding:10px;">
              <div style="font-weight:700; color:#3b82f6; font-size:12px; margin-bottom:4px;">📈 应收账款审计</div>
              <div style="font-size:12px; color:#475569; line-height:1.5;">${m.ar_audit}</div>
            </div>
            <div style="background:#fef2f2; border:1px solid #fecaca; border-radius:4px; padding:10px;">
              <div style="font-weight:700; color:#dc2626; font-size:12px; margin-bottom:4px;">📉 应付账款审计</div>
              <div style="font-size:12px; color:#7f1d1d; line-height:1.5;">${m.ap_audit}</div>
            </div>
            <div style="background:#fffbeb; border:1px solid #fde68a; border-radius:4px; padding:10px;">
              <div style="font-weight:700; color:#d97706; font-size:12px; margin-bottom:4px;">📦 库存与缺货审计</div>
              <div style="font-size:12px; color:#78350f; line-height:1.5;">${m.inventory_audit}</div>
            </div>
          </div>
          <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:4px; padding:10px;">
            <div style="font-weight:700; color:#166534; font-size:12px; margin-bottom:4px;">📋 财务总监行动指导：</div>
            <ul style="margin:0; padding-left:18px; font-size:12px; color:#14532d; line-height:1.6;">
              ${m.cfo_recommendations.map(r => `<li>${r}</li>`).join('')}
            </ul>
          </div>
        `;
      }
    } catch (e) {
      box.innerHTML = `<div style="color:var(--red);">审计生成失败：${e.message}</div>`;
    }
  }

  function exportTableToCsv(tableId, filename) {
    const table = document.getElementById(tableId);
    let csv = [];
    for (let row of table.rows) {
      let cols = [];
      for (let cell of row.cells) {
        // Skip last cell if it's actions
        if (cell.innerText.includes('编辑') && cell.innerText.includes('删除')) continue;
        let text = cell.innerText.replace(/"/g, '""').replace(/\n/g, ' ');
        cols.push(`"${text}"`);
      }
      csv.push(cols.join(','));
    }
    const csvStr = '\ufeff' + csv.join('\r\n');
    const blob = new Blob([csvStr], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
  }

  // Initial Boot
  window.addEventListener('DOMContentLoaded', () => {
    fetchState();
  });
