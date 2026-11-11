# -*- coding: utf-8 -*-
import os
import re

print("Building flagship v2.2 with Themes & Full Payment sync...")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
src_candidates = [
    os.path.join(BASE_DIR, "windows_release", "index.html"),
    os.path.join(BASE_DIR, "index.html")
]
src_file = next((p for p in src_candidates if os.path.exists(p)), os.path.join(BASE_DIR, "index.html"))
with open(src_file, 'r', encoding='utf-8') as f:
    src_html = f.read()

# 提取 Tab 1 内容，并确保去除任何历史追加的多余图表及标记
t1_match = re.search(r'(<!-- TAB 1: 经营总览与诊断 -->[\s\S]*?)(<!-- TAB 2: AI 上传与实时推演 -->)', src_html)
tab1_raw = t1_match.group(1)
clean_tab1 = re.sub(r'<!-- Visual Charts Row[\s\S]*?</div>\s*</div>\s*</div>', '', tab1_raw)
clean_tab1 = re.sub(r'<div class="charts-grid">[\s\S]*?</div>\s*</div>\s*</div>', '', clean_tab1)
clean_tab1 = re.sub(r'<!-- TAB 2-8: OTHER TABS -->', '', clean_tab1)
tab1_enhanced = clean_tab1.strip()

# 提取 Tab 2 到 Tab 7 内容，并拼接全新升级的多模态 Tab 8 (AI 财务总监对话)
t2_7_match = re.search(r'(<!-- TAB 2: AI 上传与实时推演 -->[\s\S]*?)(<!-- TAB 8: AI 财务助理对话 -->)', src_html)
if not t2_7_match:
    raise ValueError("Could not extract clean Tabs 2-7 from source HTML!")

tabs_2_7 = t2_7_match.group(1).strip()
tabs_2_7 = tabs_2_7.replace('<span style="font-size:22px;">🤖</span>', '<div style="width:28px; height:28px; border-radius:6px; background:var(--primary-light); color:var(--primary); display:flex; align-items:center; justify-content:center;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z"/><rect width="18" height="12" x="3" y="8" rx="2"/><path d="M9 13v2"/><path d="M15 13v2"/></svg></div>')
tabs_2_7 = tabs_2_7.replace('⚡ 换个角度重新审阅', '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg> 重新审阅分析')

# 将表格表头中的“规格”统一升级为更直观的“单位”
tabs_2_7 = tabs_2_7.replace('<th>规格</th>', '<th>单位</th>')

# 确保多次构建 100% 幂等：先剥离可能已存在的独立日期列
tabs_2_7 = re.sub(r'<th>最新业务日期</th>\s*', '', tabs_2_7)
tabs_2_7 = re.sub(r'<th>最新交易日期</th>\s*', '', tabs_2_7)
tabs_2_7 = re.sub(r'<th>最新采购日期</th>\s*', '', tabs_2_7)

# 拆分三大核心台账表头：精准将最新日期从名称列剥离，升级为独立的「最新业务日期 / 最新交易日期 / 最新采购日期」列
tabs_2_7 = re.sub(
    r'(<table[^>]*id="inventoryTable"[^>]*>[\s\S]*?<th>产品名称</th>\s*)<th>单位</th>',
    r'\1<th>最新业务日期</th>\n                <th>单位</th>',
    tabs_2_7,
    count=1
)
tabs_2_7 = re.sub(
    r'(<table[^>]*id="arTable"[^>]*>[\s\S]*?<th>客户名称</th>\s*)<th>地址</th>',
    r'\1<th>最新交易日期</th>\n                <th>地址</th>',
    tabs_2_7,
    count=1
)
tabs_2_7 = re.sub(
    r'(<table[^>]*id="apTable"[^>]*>[\s\S]*?<th>供应商名称</th>\s*)<th>地址</th>',
    r'\1<th>最新采购日期</th>\n                <th>地址</th>',
    tabs_2_7,
    count=1
)


# 全面清理 Tab 1 与 Tab 2-7 中的历史 AI 塑料感 (Emoji & 浮夸宣传语)，升级为专业金融级文案与矢量微图标
de_slop_replacements = [
    ('<span>⚡ AI 经营异常诊断与补货催收建议</span>', '<span style="display:inline-flex; align-items:center; gap:6px;"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>经营异常诊断与决策建议</span>'),
    ('🤖 唤醒大模型出具全局财务总监审计备忘录', '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/></svg> 出具全局财务审计备忘录'),
    ('<div class="panel-title">⚠️ 实时库存缺货与补货看板</div>', '<div class="panel-title" style="display:flex; align-items:center; gap:6px;"><span class="status-pill status-warning"><span class="status-dot"></span>库存预警</span> 实时库存缺货与补货看板</div>'),
    ('<div class="panel-title">💰 客户应收欠款前 3 名</div>', '<div class="panel-title" style="display:flex; align-items:center; gap:6px;"><span class="status-pill status-danger"><span class="status-dot"></span>应收穿透</span> 客户应收账款 Top 3</div>'),
    ('<span>📥 上传新表格 · AI 语义解析与实时入账工作台</span>', '<span style="display:inline-flex; align-items:center; gap:6px;"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>单据表格导入与业务推演工作台</span>'),
    ('<div class="upload-icon">📂</div>', '<div class="upload-icon" style="color:var(--primary); display:flex; align-items:center; justify-content:center;"><svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m16 16-4-4-4 4"/></svg></div>'),
    ('💡 快速载入测试场景表：', '<span style="font-size:12px; font-weight:600; color:var(--text-dim);">预设业务场景导入：</span>'),
    ('✓ 确认写入数据库并刷新台账', '确认记账并同步更新台账'),
    ('<span>🏢 商业业务实质与主体穿透</span>', '<span>业务实质与交易主体</span>'),
    ('<span>⚠️ 往来款项与现金流占用预警</span>', '<span>往来款项与资金占用预警</span>'),
    ('<span>🛡️ 单据合规与赠品防飞单内控 (赠品/散称损耗/高值锁控)</span>', '<span>单据合规与内控复核</span>'),
    ('<span>📋 财务与库管可执行行动清单 (Action Items)</span>', '<span>财务与库管行动建议清单</span>'),
    ('📦 库存变动推演 (Before', '库存变动推演 (Before'),
    ('📈 客户应收变动：', '客户应收变动：'),
    ('📉 供应商应付变动：', '供应商应付变动：'),
    ('<span>📦 进销存实时库存汇总台账</span>', '<span>进销存实时库存台账</span>'),
    ('<span>📈 客户应收账款汇总台账</span>', '<span>客户应收账款台账</span>'),
    ('<span>📉 供应商应付账款汇总台账</span>', '<span>供应商应付账款台账</span>'),
    ('<span>业务流水明细</span>', '<span>业务流水明细</span>'),
]

for old_s, new_s in de_slop_replacements:
    tab1_enhanced = tab1_enhanced.replace(old_s, new_s)
    tabs_2_7 = tabs_2_7.replace(old_s, new_s)

# 先剥离可能已存在的排列选择器或清理批次按钮，确保多次构建 100% 幂等
tabs_2_7 = re.sub(r'<div class="sort-control-wrap"[\s\S]*?</select>\s*</div>\s*', '', tabs_2_7)
tabs_2_7 = re.sub(r'<button[^>]*id="btnClearRolledBack"[\s\S]*?</button>\s*', '', tabs_2_7)

SORT_SELECT_HTML = """<div class="sort-control-wrap" style="display:inline-flex; align-items:center; gap:6px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-sm); padding:4px 10px; box-shadow:var(--shadow-xs);">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--text-dim); flex-shrink:0;"><path d="m3 16 4 4 4-4"/><path d="M7 20V4"/><path d="m21 8-4-4-4 4"/><path d="M17 4v16"/></svg>
              <span style="font-size:12px; font-weight:600; color:var(--text-muted); white-space:nowrap;">排序</span>
              <select class="table-sort-select" onchange="setSystemSortOrder(this.value)" style="border:none; background:transparent; font-size:12px; font-weight:600; color:var(--text); cursor:pointer; outline:none; padding-right:2px;">
                <option value="date_desc">按最新日期 ↓</option>
                <option value="date_asc">按最早日期 ↑</option>
                <option value="stock_desc">按库存数量 (从多到少) ↓</option>
                <option value="stock_asc">按库存数量 (从少到多) ↑</option>
                <option value="amount_desc">按金额大小 (从高到低) ↓</option>
                <option value="amount_asc">按金额大小 (从低到高) ↑</option>
              </select>
            </div>"""

# 为库存、应收、应付、业务流水四大表单注入「🔃 排列方式」选择器
tabs_2_7 = tabs_2_7.replace(
    '<button class="btn btn-sm btn-primary" onclick="openProductModal()">+ 新增商品档案</button>',
    SORT_SELECT_HTML + '\n            <button class="btn btn-sm btn-primary" onclick="openProductModal()">+ 新增商品档案</button>'
)
tabs_2_7 = tabs_2_7.replace(
    '<button class="btn btn-sm btn-primary" onclick="openCustomerModal()">+ 新增客户档案</button>',
    SORT_SELECT_HTML + '\n            <button class="btn btn-sm btn-primary" onclick="openCustomerModal()">+ 新增客户档案</button>'
)
tabs_2_7 = tabs_2_7.replace(
    '<button class="btn btn-sm btn-primary" onclick="openSupplierModal()">+ 新增供应商档案</button>',
    SORT_SELECT_HTML + '\n            <button class="btn btn-sm btn-primary" onclick="openSupplierModal()">+ 新增供应商档案</button>'
)
tabs_2_7 = tabs_2_7.replace(
    '<button class="btn btn-sm btn-primary" id="btnNewTx" onclick="openNewTxModal()">+ 录入新单据</button>',
    SORT_SELECT_HTML + '\n            <button class="btn btn-sm btn-primary" id="btnNewTx" onclick="openNewTxModal()">+ 录入新单据</button>'
)

# 为导入批次时光机面板头部注入「🔃 排列方式」与「🧹 清理已撤销/空批次」按钮
batches_header_new = f"""<!-- TAB 7: 导入批次与时光机 -->
    <div id="tab-batches" class="tab-pane" style="display:none;">
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title" style="display:flex; align-items:center; gap:8px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--primary);"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/></svg>
            <span style="font-weight:700;">导入批次审计与数据时光机</span>
            <span style="font-size:12px; color:var(--text-dim); font-weight:normal;">(支持单批次撤回回滚、以及物理删除错误或已撤销的占位批次)</span>
          </div>
          <div class="panel-actions" style="display:flex; align-items:center; gap:8px;">
            {SORT_SELECT_HTML}
            <button class="btn btn-sm btn-outline-danger" id="btnClearRolledBack" onclick="clearRolledBackBatches()" style="display:inline-flex; align-items:center; gap:5px;" title="一键彻底删除所有已撤销回滚或 0 条记录的占位批次">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
              清理无效批次
            </button>
          </div>
        </div>"""

tabs_2_7 = re.sub(
    r'<!-- TAB 7: 导入批次与时光机 -->\s*<div id="tab-batches"[\s\S]*?<div class="panel-header">[\s\S]*?</div>\s*</div>',
    batches_header_new,
    tabs_2_7,
    count=1
)

TAB_8_CHAT_HTML = """<!-- TAB 8: AI 财务助理对话 -->
    <div id="tab-chat" class="tab-pane" style="display:none;">
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title" style="display:flex; align-items:center; gap:8px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--primary);"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            <span style="font-weight:700;">AI 财务总监 · 智能单据识别与协同中心</span>
          </div>
          <div class="panel-actions" style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:12px; color:var(--text-dim);">支持 Excel/CSV 表格与单据照片（可拖拽或直接粘贴截图），核对确认后原子入账</span>
            <button class="btn btn-sm btn-primary" onclick="document.getElementById('chatFileInput').click()" style="display:inline-flex; align-items:center; gap:5px;">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
              上传表格 / 单据图片
            </button>
          </div>
        </div>
        <div class="chat-container" id="mainChatDropZone">
          <!-- Quick Prompt Pills -->
          <div style="padding:10px 16px; background:var(--surface-subtle); border-bottom:1px solid var(--border); display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
            <span style="font-size:11.5px; color:var(--text-dim); font-weight:600;">快捷指令：</span>
            <button class="btn btn-xs btn-outline-primary" onclick="document.getElementById('chatFileInput').click()">上传单据图片/表格</button>
            <button class="btn btn-xs btn-outline-secondary" onclick="sendChatMessage('帮我分析下目前欠款最多的客户，并为他生成一封专业的催款对账函')">生成催款对账函</button>
            <button class="btn btn-xs btn-outline-secondary" onclick="sendChatMessage('评估当前供应商应付款总额与最大的两家供货商，给出30天现金流风险预警')">应付款与现金流预警</button>
            <button class="btn btn-xs btn-outline-secondary" onclick="sendChatMessage('帮我盘点全库跌破安全水位的商品，并给出紧急采购补货建议')">缺货盘点与补货建议</button>
            <button class="btn btn-xs btn-outline-secondary" onclick="sendChatMessage('向西藏腾格商贸采购雪花啤酒50件，单价65元')">记账指令示例</button>
          </div>
          <div class="chat-messages" id="chatMessages">
            <div class="chat-bubble bot">
              <div>您好，我是 <strong>AI 财务总监与协同助手</strong>。系统已全量同步当前库存资产、往来账款与流水明细。

您可以随时执行以下操作：
1. <strong>上传单据图片或表格入账</strong>：点击下方「上传表格/单据图」或直接在窗口内 <code>Ctrl+V</code> 粘贴截图、拖拽文件，系统将智能提取品名、数量、单位、单价与往来单位，并在您<strong>核对确认后正式录入</strong>。
2. <strong>自然语言记账指令</strong>：如「将坚果类商品安全库存统一设为10」或「向西藏腾格商贸进货雪花啤酒50件单价65元」。
3. <strong>财务经营诊断</strong>：「分析当前应付欠款最高的两家供应商」或「为欠款最多客户生成对账单」。</div>
              <div style="margin-top:8px; padding-top:6px; border-top:1px solid rgba(0,0,0,0.06); font-size:11px; display:flex; align-items:center; justify-content:space-between; color:var(--text-dim);">
                <span class="status-pill status-success" style="font-size:11px;"><span class="status-dot"></span>多模态识别与数据库实时关联</span>
                <span style="font-size:10px;">支持 Excel / CSV / 单据照片</span>
              </div>
            </div>
          </div>
          <div class="chat-input-bar" style="display:flex; gap:8px; align-items:center;">
            <input type="file" id="chatFileInput" accept=".xlsx,.xls,.csv,.png,.jpg,.jpeg,.webp,.bmp" multiple style="display:none;" onchange="handleChatFileUpload(this.files, 'main'); this.value='';">
            <button type="button" class="btn" onclick="document.getElementById('chatFileInput').click()" title="上传表格或单据照片（支持拖拽或直接粘贴截图）" style="display:inline-flex; align-items:center; gap:6px; padding:0 14px; height:40px; font-weight:600; color:var(--primary); border-color:var(--border); background:var(--surface); flex-shrink:0;">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
              上传表格/单据
            </button>
            <input type="text" id="chatInput" class="form-input" placeholder="输入记账指令、财务问题，或点击左侧上传单据图片/表格（支持直接粘贴截图）..." onkeydown="if(event.key==='Enter') sendChatMessage()">
            <button class="btn btn-primary" onclick="sendChatMessage()" style="height:40px; padding:0 20px; flex-shrink:0;">发送</button>
          </div>
        </div>
      </div>
    </div>"""

tabs_2_8 = tabs_2_7 + "\n\n    " + TAB_8_CHAT_HTML

# 提取 Modals 内容：精准提取原生的 6 个基础 Modals（从 MODALS 注释开始，直至 aiSettingsModal 的完整闭合处）
# 彻底截断任何历史执行或热重载残留的付款模态框碎片，从根源杜绝重复堆叠
clean_modals_match = re.search(r'(<!-- ================= MODALS ================= -->[\s\S]*?<div class="modal-overlay" id="aiSettingsModal">[\s\S]*?saveAiSettings\(\)">保存配置并连接</button>\s*</div>\s*</div>\s*</div>)', src_html)
if clean_modals_match:
    modals_html = clean_modals_match.group(1) + "\n</div>"
    # De-slop: 清理原生 Modals 中的 Emoji
    modals_html = modals_html.replace('🛠️ 账套初始化与重置', '账套初始化与重置')
    modals_html = modals_html.replace('⚙️ 大模型 API 接口配置与在线诊断', '大模型 API 接口配置与在线诊断')
    modals_html = modals_html.replace('💡 <strong>配置提示</strong>：', '<strong>配置提示</strong>：')
    modals_html = modals_html.replace('🔌 测试 API 连接', '测试 API 连接')
    modals_html = modals_html.replace('💳 同时登记/调整已付金额', '登记/调整已付金额')
else:
    raise ValueError("Could not find clean base modals in source HTML!")

# 升级 productModal 中的计量单位字段：支持常规单位下拉选择 + 自由输入
prod_unit_new_html = """<div class="form-group">
          <label class="form-label">单位 * <span style="font-weight:400; font-size:11px; color:var(--text-dim);">(常规选择或自由填写)</span>：</label>
          <div style="display:flex; gap:6px; align-items:center;">
            <input type="text" id="prodFormSpec" class="form-input" list="commonUnitList_global" placeholder="自由输入或右侧选择单位" style="flex:1;">
            <select class="form-input" style="width:88px; padding:6px; font-size:12px; color:var(--text-muted); cursor:pointer; background-color:var(--surface-subtle);" onchange="if(this.value){document.getElementById('prodFormSpec').value=this.value; this.value='';}">
              <option value="">常规单位▾</option>
              <option value="斤">斤</option><option value="公斤">公斤</option><option value="件">件</option><option value="箱">箱</option>
              <option value="瓶">瓶</option><option value="袋">袋</option><option value="盒">盒</option><option value="包">包</option>
              <option value="提">提</option><option value="桶">桶</option><option value="罐">罐</option><option value="个">个</option>
              <option value="打">打</option><option value="套">套</option><option value="克">克</option><option value="筐">筐</option><option value="份">份</option>
            </select>
          </div>
        </div>"""

modals_html = re.sub(
    r'<div class="form-group">\s*<label class="form-label">计量单位[^<]*</label>[\s\S]*?<input type="text" id="prodFormSpec"[^>]*>(?:\s*<select[\s\S]*?</select>\s*</div>)?\s*</div>',
    prod_unit_new_html,
    modals_html,
    count=1
)

GLOBAL_UNIT_DATALIST = """
  <datalist id="commonUnitList_global">
    <option value="斤"><option value="公斤"><option value="件"><option value="箱"><option value="瓶">
    <option value="袋"><option value="盒"><option value="包"><option value="提"><option value="桶">
    <option value="罐"><option value="个"><option value="打"><option value="套"><option value="克">
    <option value="筐"><option value="份"><option value="条"><option value="双"><option value="台">
  </datalist>
"""
if 'commonUnitList_global' not in modals_html:
    modals_html = modals_html + "\n" + GLOBAL_UNIT_DATALIST

# 在 supplierModal 中增加已付金额和付款时间录入字段
sup_modal_replacement = """
      <div style="background:var(--surface-subtle); border:1px solid var(--border); border-radius:var(--radius); padding:12px 14px; margin-top:10px;">
        <div style="font-weight:700; font-size:12.5px; color:var(--text); margin-bottom:8px; display:flex; align-items:center; justify-content:space-between;">
          <span style="display:flex; align-items:center; gap:6px;">登记/调整已付金额 (选填，自动同步流水)</span>
          <span style="font-size:11.5px; color:var(--text-muted);">累计已付: <strong id="supFormCurrentPaid" style="color:var(--green);">¥0.00</strong></span>
        </div>
        <div class="form-grid-2">
          <div class="form-group" style="margin-bottom:0;">
            <label class="form-label" style="font-size:12px;">已付金额 (元)：</label>
            <input type="number" step="0.01" id="supFormAddPayment" class="form-input" placeholder="选填，录入已付金额">
          </div>
          <div class="form-group" style="margin-bottom:0;">
            <label class="form-label" style="font-size:12px;">付款时间：</label>
            <input type="date" id="supFormPaymentDate" class="form-input">
          </div>
        </div>
        <div style="margin-top:6px; text-align:right;">
          <a href="javascript:void(0)" onclick="openSupplierPaymentHistoryModal(document.getElementById('supFormName').value)" style="font-size:11.5px; color:var(--primary); font-weight:600; text-decoration:underline;">查看/修改/撤回该供应商已付明细 &gt;</a>
        </div>
      </div>
    </div>
"""

if 'supFormAddPayment' not in modals_html:
    modals_html = modals_html.replace('    </div>\n    <div class="modal-footer">\n      <button class="btn" onclick="closeModal(\'supplierModal\')">取消</button>', sup_modal_replacement + '    <div class="modal-footer">\n      <button class="btn" onclick="closeModal(\'supplierModal\')">取消</button>')

# 直接从纯净的 original_main_script.js 读取底层业务代码，避免任何历史追加产生的重复声明污染
with open(os.path.join(BASE_DIR, 'original_main_script.js'), 'r', encoding='utf-8') as f_orig:
    main_js = f_orig.read()

# 对 main_js 进行 De-slop 净化
main_js_de_slop = [
    ("mode.includes('🟢')", "Boolean(mode && !mode.includes('本地'))"),
    ("✓ ${data.result.mode || '大模型'}已成功解析您的指令，并自动在工作台生成了入账推演卡片，请核对后确认是否正式写入数据库！", "${data.result.mode || '大模型'}已成功解析记账指令，并在工作台生成入账推演卡片，请核对确认。"),
    ("✓ AI 实时直通入账成功！", "AI 直通入账成功！"),
    ("✓ 入账成功！", "入账成功！"),
    ("✓ 批次「", "批次「"),
    ("✓ AI 协同指令已执行并持久化落盘！", "AI 协同指令已执行并持久化落盘"),
    ("✓ 大模型已成功解析您的指令", "已成功解析记账指令"),
    ("✓ <strong>大模型握手成功！</strong>", "<strong>接口连接成功！</strong>"),
    ("✕ <strong>接口探测未通过：</strong>", "<strong>接口探测未通过：</strong>"),
    ("✕ <strong>请求失败：</strong>", "<strong>请求失败：</strong>"),
    ("✓ 大模型接口配置已保存并成功连通", "大模型接口配置已保存并成功连通"),
    ("⚠️ 配置已保存，但在探测连通时提示：", "配置已保存，但在探测连通时提示："),
    ("✓ AI 接口配置已保存！", "AI 接口配置已保存！"),
    ("⚠️ 缺货预警", "缺货预警"),

    ("⚠️ 当前库存跌破安全红线，需补货", "当前库存跌破安全红线，需尽快补货"),
    ("✓ 全部 SKU 库存充足", "全库 SKU 库存状态健康"),
    ("⚙️ AI 已连接", "AI 引擎: 已连接"),
    ("⚙️ AI 配置 (当前使用本地引擎)", "AI 配置 (本地引擎)"),
    ("⚡ AI 表格多模态语义清洗", "单据数据结构化解析中"),
    ("🟢 大模型已全脑深度介入", "大模型多模态解析就绪"),
    ("⚠️ 模型调用说明：", "模型调用说明："),
    ("⚠️ 重复单据拦截提示：", "单号重复提示："),
    ("📦 通用商品", "通用商品"),
    ("✓ 账套初始化操作已成功完成！", "账套初始化操作已成功完成！"),
    ("🧠 AI 财务总监正在调用大模型全脑思考中...", "AI 正在实时分析账套数据与业务实质..."),
    ("✓ 大模型已成功解析您的指令", "已成功解析记账指令"),
    ("⚡ 正在向大模型接口发送 Ping 握手探测...", "正在向大模型接口发送握手探测..."),
    ("✓ <strong>大模型握手成功！</strong>", "<strong>接口连接成功！</strong>"),
    ("🤖 AI 财务总监正在实时穿透", "正在生成财务审计与业务诊断报告"),
    ("📑 ", ""),
    ("📈 应收账款审计", "应收账款审计"),
    ("📉 应付账款审计", "应付账款审计"),
    ("📦 库存与缺货审计", "库存与缺货审计"),
    ("📋 财务总监行动指导：", "财务总监行动指导："),
]
for o_str, n_str in main_js_de_slop:
    main_js = main_js.replace(o_str, n_str)


# 供应商付款与撤回中心专属模态框
PAYMENT_MODAL_HTML = """
  <!-- ================= 供应商付款登记/修改模态框 ================= -->
  <div class="modal-overlay" id="supplierPaymentModal">
    <div class="modal-box" style="max-width:540px; width:92%;">
      <div class="modal-header">
        <div style="display:flex; align-items:center; gap:10px;">
          <div style="width:34px; height:34px; border-radius:8px; background:var(--green-light); color:var(--green); display:flex; align-items:center; justify-content:center;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>
          </div>
          <div>
            <div style="font-weight:800; font-size:16px; color:var(--text);" id="supPayModalTitle">登记供应商付款 · 冲销应付款</div>
            <div style="font-size:12px; color:var(--text-dim);" id="supPayModalSubtitle">录入已付金额与付款时间，自动实时同步整个系统</div>
          </div>
        </div>
        <button class="btn btn-sm" onclick="closeModal('supplierPaymentModal')">✕</button>
      </div>
      <div class="modal-body">
        <input type="hidden" id="supPaySupplierId">
        <input type="hidden" id="supPayPaymentId">

        <!-- 编辑模式提示横条 -->
        <div id="supPayEditBanner" style="display:none; background:var(--amber-light); border:1px solid var(--amber-border); color:var(--amber); padding:8px 12px; border-radius:8px; margin-bottom:14px; font-size:12px; font-weight:700; align-items:center; justify-content:space-between;">
          <span>正在修改付款单据 <span id="supPayEditingIdText"></span></span>
          <button type="button" class="btn btn-sm" style="padding:2px 8px; font-size:11px;" onclick="resetSupPayFormToNew()">取消修改 (切回新增)</button>
        </div>

        <div style="background:var(--surface-subtle); border:1px solid var(--border); border-radius:var(--radius); padding:14px; margin-bottom:16px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-size:13px; color:var(--text-dim); font-weight:600;">收款供应商：</span>
            <strong style="font-size:15px; color:var(--text);" id="supPaySupplierName">--</strong>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:13px; color:var(--text-dim); font-weight:600;">当前待付欠款余额：</span>
            <span style="font-size:16px; font-weight:800; color:var(--red);" id="supPayBalance">¥0.00</span>
          </div>
        </div>

        <div class="form-group">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <label class="form-label" style="margin-bottom:0;">已付金额 (¥) <span style="color:var(--red);">*</span></label>
            <button type="button" class="btn btn-sm" style="padding:2px 8px; font-size:11px;" onclick="fillSupPayFullBalance()">一键全额结清</button>
          </div>
          <input type="number" id="supPayAmount" class="form-input tabular-nums" placeholder="请输入付款金额，如 5000" step="0.01" min="0.01">
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">付款时间 / 日期 <span style="color:var(--red);">*</span></label>
            <input type="date" id="supPayDate" class="form-input">
          </div>
          <div class="form-group">
            <label class="form-label">付款经办出纳</label>
            <input type="text" id="supPayPayer" class="form-input" placeholder="默认：出纳">
          </div>
        </div>

        <div class="form-group" style="margin-bottom:12px;">
          <label class="form-label">付款凭证单号 / 银行流水备注</label>
          <input type="text" id="supPayRemark" class="form-input" placeholder="选填，如：网银转账 / 现结">
        </div>

        <!-- 历史付款明细（支持就地修改与撤回） -->
        <div id="supPayHistorySection" style="border-top:1px dashed var(--border); padding-top:12px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:12.5px; font-weight:700; color:var(--text);">该供应商已付记录 (<span id="supPayHistoryCount">0</span> 笔)</span>
            <span style="font-size:11px; color:var(--text-dim);">若录入有误，可点击【修改】更正或【撤回】删除</span>
          </div>
          <div id="supPayHistoryList" style="max-height:150px; overflow-y:auto; border:1px solid var(--border); border-radius:8px; font-size:12px; background:var(--surface);"></div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn" onclick="closeModal('supplierPaymentModal')">取消</button>
        <button class="btn btn-primary" id="supPaySubmitBtn" onclick="saveSupplierPaymentForm()">确认入账并实时同步</button>
      </div>
    </div>
  </div>

  <!-- ================= 供应商已付款记录与撤回中心模态框 ================= -->
  <div class="modal-overlay" id="supplierPaymentHistoryModal">
    <div class="modal-box" style="max-width:680px; width:92%;">
      <div class="modal-header">
        <div style="display:flex; align-items:center; gap:10px;">
          <div style="width:34px; height:34px; border-radius:8px; background:var(--amber-light); color:var(--amber); display:flex; align-items:center; justify-content:center;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
          </div>
          <div>
            <div style="font-weight:800; font-size:16px; color:var(--text);" id="histModalTitle">已付记录明细与撤回中心</div>
            <div style="font-size:12px; color:var(--text-dim);">支持针对录入有误的已付金额进行单据【修改】或【撤回/作废】，账套实时自动核算</div>
          </div>
        </div>
        <button class="btn btn-sm" onclick="closeModal('supplierPaymentHistoryModal')">✕</button>
      </div>
      <div class="modal-body">
        <input type="hidden" id="histSupplierNameHidden">
        <!-- 统计卡片条 -->
        <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; background:var(--surface-subtle); border:1px solid var(--border); border-radius:var(--radius); padding:12px; margin-bottom:16px;">
          <div>
            <div style="font-size:11px; color:var(--text-dim); font-weight:600;">供应商名称</div>
            <div style="font-size:14px; font-weight:800; color:var(--text);" id="histSupName">--</div>
          </div>
          <div>
            <div style="font-size:11px; color:var(--text-dim); font-weight:600;">累计已付金额</div>
            <div style="font-size:14px; font-weight:800; color:var(--green);" id="histPaidTotal">¥0.00</div>
          </div>
          <div>
            <div style="font-size:11px; color:var(--text-dim); font-weight:600;">待付欠款余额</div>
            <div style="font-size:14px; font-weight:800; color:var(--red);" id="histBalanceTotal">¥0.00</div>
          </div>
        </div>

        <!-- 付款记录表格 -->
        <div class="table-responsive" style="max-height:280px; overflow-y:auto; border:1px solid var(--border); border-radius:8px;">
          <table class="data-table" style="margin:0; font-size:12.5px;">
            <thead>
              <tr>
                <th style="width:45px;">序号</th>
                <th>付款日期</th>
                <th class="num">付款金额</th>
                <th>经办出纳</th>
                <th>凭证/备注</th>
                <th style="text-align:center; width:130px;">单据操作</th>
              </tr>
            </thead>
            <tbody id="histPaymentsTbody"></tbody>
          </table>
        </div>
      </div>
      <div class="modal-footer" style="display:flex; justify-content:space-between; align-items:center;">
        <button class="btn btn-sm btn-primary" onclick="openPaymentModalFromHistory()">+ 录入新付款</button>
        <button class="btn" onclick="closeModal('supplierPaymentHistoryModal')">关闭</button>
      </div>
    </div>
  </div>
"""

full_modals_html = modals_html + "\n" + PAYMENT_MODAL_HTML

# 读取纯正独立的多套主题 CSS
with open(os.path.join(BASE_DIR, 'theme_style.css'), 'r', encoding='utf-8') as f_theme:
    CSS_THEMES = f_theme.read()

# 增强 JS：修复 postCrud 参数，挂载付款逻辑，增强供应商编辑保存联动
ADDITIONAL_JS = """
  // ================= 主题切换系统 (Theme Switcher) =================
  function setTheme(themeName) {
    if (themeName === 'default' || themeName === 'slate') {
      document.documentElement.removeAttribute('data-theme');
    } else {
      document.documentElement.setAttribute('data-theme', themeName);
    }
    localStorage.setItem('ledger_app_theme', themeName);
    const labelMap = {
      'slate': '深空极智蓝',
      'apple': '苹果极简黑',
      'emerald': '翡翠财税绿',
      'indigo': '皇家紫罗兰',
      'dark': '暗夜护眼黑'
    };
    const label = document.getElementById('currentThemeLabel');
    if (label) label.textContent = labelMap[themeName] || '配色主题';
    toggleThemeDropdown(false);
  }

  function toggleThemeDropdown(forceState) {
    const dd = document.getElementById('themeDropdownMenu');
    if (!dd) return;
    if (typeof forceState === 'boolean') {
      if (forceState) dd.classList.add('show');
      else dd.classList.remove('show');
    } else {
      dd.classList.toggle('show');
    }
  }

  document.addEventListener('click', function(e) {
    const box = document.querySelector('.theme-selector-box');
    if (box && !box.contains(e.target)) {
      toggleThemeDropdown(false);
    }
  });

  const savedTheme = localStorage.getItem('ledger_app_theme') || 'slate';
  setTheme(savedTheme);

  // ================= 供应商付款登记与撤回系统 (Full CRUD & Retract) =================
  let currentPaymentSupplierBalance = 0;

  function showFloatToast(msg, type = 'green') {
    const isRed = type === 'red' || type === 'danger';
    const isAmber = type === 'amber' || type === 'warning';
    const toastClass = isRed ? 'toast-red' : (isAmber ? 'toast-amber' : 'toast-success');
    
    const iconSvg = isRed 
      ? '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>'
      : (isAmber 
        ? '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
        : '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>');

    // 剔除旧消息中残留的纯文本 Emoji
    const cleanMsg = (msg || '').replace(/[✓✔⚠️❌🚫🗑️✨🧹🔃]/g, '').trim();

    const alertNotice = document.createElement('div');
    alertNotice.className = `toast-notice ${toastClass}`;
    alertNotice.innerHTML = `${iconSvg}<span>${cleanMsg}</span>`;
    document.body.appendChild(alertNotice);
    setTimeout(() => {
      alertNotice.style.opacity = '0';
      alertNotice.style.transform = 'translateY(-6px)';
      alertNotice.style.transition = 'all 0.2s ease';
      setTimeout(() => alertNotice.remove(), 220);
    }, 3200);
  }

  function openSupplierPaymentModal(supId, supName, apBalance, editPaymentItem) {
    if (!supName && supId) {
      const s = (CURRENT_STATE.ap_ledger || []).find(x => x.id === supId) || (CURRENT_STATE.suppliers || []).find(x => x.id === supId);
      if (s) supName = s.supplier_name || s.name;
    }
    document.getElementById('supPaySupplierId').value = supId || '';
    document.getElementById('supPaySupplierName').textContent = supName || '--';

    if (apBalance !== null && apBalance !== undefined) {
      currentPaymentSupplierBalance = parseFloat(apBalance || 0);
    } else {
      const sup = (CURRENT_STATE.ap_ledger || []).find(s => s.supplier_name === supName);
      currentPaymentSupplierBalance = sup ? parseFloat(sup.ap_balance || 0) : 0;
    }
    document.getElementById('supPayBalance').textContent = fmtMoney(currentPaymentSupplierBalance);

    if (editPaymentItem) {
      document.getElementById('supPayPaymentId').value = editPaymentItem.id || '';
      document.getElementById('supPayModalTitle').textContent = '修改供应商付款单 (单号 #' + editPaymentItem.id + ')';
      document.getElementById('supPayModalSubtitle').textContent = '修改已付金额或付款时间，保存后账套将实时全量重算';
      document.getElementById('supPayAmount').value = editPaymentItem.amount || '';
      document.getElementById('supPayDate').value = editPaymentItem.date || new Date().toISOString().split('T')[0];
      document.getElementById('supPayPayer').value = editPaymentItem.payer || '财务出纳';
      document.getElementById('supPayRemark').value = (editPaymentItem.phone || '').replace(/^备注:/, '');
      document.getElementById('supPaySubmitBtn').textContent = '保存修改并实时同步';
      document.getElementById('supPayEditBanner').style.display = 'flex';
      document.getElementById('supPayEditingIdText').textContent = '#' + editPaymentItem.id;
    } else {
      resetSupPayFormToNew();
    }

    renderModalPaymentHistory(supName);
    openModal('supplierPaymentModal');
    setTimeout(() => {
      document.getElementById('supPayAmount').focus();
    }, 100);
  }

  function resetSupPayFormToNew() {
    document.getElementById('supPayPaymentId').value = '';
    document.getElementById('supPayModalTitle').textContent = '登记供应商付款 · 冲销应付款';
    document.getElementById('supPayModalSubtitle').textContent = '录入已付金额与付款时间，自动实时同步整个系统';
    document.getElementById('supPaySubmitBtn').textContent = '确认入账并实时同步';
    document.getElementById('supPayEditBanner').style.display = 'none';
    document.getElementById('supPayAmount').value = '';
    document.getElementById('supPayDate').value = new Date().toISOString().split('T')[0];
    document.getElementById('supPayPayer').value = '财务出纳';
    document.getElementById('supPayRemark').value = '';
    const sname = document.getElementById('supPaySupplierName').textContent;
    if (sname && sname !== '--') {
      renderModalPaymentHistory(sname);
    }
  }

  function loadPaymentForEdit(paymentId) {
    const p = (CURRENT_STATE.supplier_payments || []).find(x => x.id === paymentId);
    if (!p) return alert('未找到该付款单据');
    document.getElementById('supPayPaymentId').value = p.id;
    document.getElementById('supPayModalTitle').textContent = '修改供应商付款单 (单号 #' + p.id + ')';
    document.getElementById('supPayModalSubtitle').textContent = '修改已付金额或付款时间，保存后账套将实时全量重算';
    document.getElementById('supPayAmount').value = p.amount;
    document.getElementById('supPayDate').value = p.date;
    document.getElementById('supPayPayer').value = p.payer || '财务出纳';
    document.getElementById('supPayRemark').value = (p.phone || '').replace(/^备注:/, '');
    document.getElementById('supPaySubmitBtn').textContent = '保存修改并实时同步';
    document.getElementById('supPayEditBanner').style.display = 'flex';
    document.getElementById('supPayEditingIdText').textContent = '#' + p.id;
    renderModalPaymentHistory(p.supplier_name);
    document.getElementById('supPayAmount').focus();
  }

  function renderModalPaymentHistory(supName) {
    const listEl = document.getElementById('supPayHistoryList');
    const countEl = document.getElementById('supPayHistoryCount');
    if (!listEl) return;
    const list = (CURRENT_STATE.supplier_payments || []).filter(p => p.supplier_name === supName);
    if (countEl) countEl.textContent = list.length;
    if (list.length === 0) {
      listEl.innerHTML = '<div style="padding:14px; text-align:center; color:var(--text-dim);">该供应商暂无已付款记录</div>';
      return;
    }
    const currentEditId = document.getElementById('supPayPaymentId').value;
    const safeSupName = (supName || '').replace(/'/g, "\'");
    listEl.innerHTML = list.map(p => `
      <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 10px; border-bottom:1px solid var(--border-light); ${p.id == currentEditId ? 'background:var(--primary-light);' : ''}">
        <div>
          <span style="font-weight:700; color:var(--green); font-family:var(--font-mono);">¥${fmtNum(p.amount)}</span>
          <span style="color:var(--text-dim); margin-left:8px;">${p.date}</span>
          <span style="color:var(--text-muted); margin-left:6px;">(${p.payer || '出纳'})</span>
          ${p.phone ? `<span style="color:var(--text-dim); margin-left:6px; font-size:11px;">${p.phone}</span>` : ''}
        </div>
        <div style="display:flex; gap:4px;">
          <button type="button" class="btn btn-sm" style="padding:2px 7px; font-size:11px;" onclick="loadPaymentForEdit(${p.id})">修改</button>
          <button type="button" class="btn btn-sm btn-action-danger" style="padding:2px 7px; font-size:11px;" onclick="deleteSupplierPaymentRecord(${p.id}, ${p.amount}, '${safeSupName}')">↩️ 撤回</button>
        </div>
      </div>
    `).join('');
  }

  function fillSupPayFullBalance() {
    if (currentPaymentSupplierBalance > 0) {
      document.getElementById('supPayAmount').value = currentPaymentSupplierBalance.toFixed(2);
    }
  }

  async function saveSupplierPaymentForm() {
    const paymentId = document.getElementById('supPayPaymentId').value;
    const sname = document.getElementById('supPaySupplierName').textContent;
    const amount = parseFloat(document.getElementById('supPayAmount').value || 0);
    const date = document.getElementById('supPayDate').value;
    const payer = document.getElementById('supPayPayer').value || '财务出纳';
    const remark = document.getElementById('supPayRemark').value;

    if (!amount || amount <= 0) {
      alert('请输入有效的付款金额！');
      document.getElementById('supPayAmount').focus();
      return;
    }
    if (!date) {
      alert('请选择付款日期时间！');
      return;
    }

    const payData = {
      supplier_name: sname,
      amount: amount,
      date: date,
      payer: payer,
      payee: sname,
      address: '',
      phone: remark ? `备注:${remark}` : ''
    };
    if (paymentId) {
      payData.id = parseInt(paymentId);
    }

    await postCrud('payment', 'save', payData);
    closeModal('supplierPaymentModal');

    if (document.getElementById('supplierPaymentHistoryModal') && document.getElementById('supplierPaymentHistoryModal').classList.contains('active')) {
      renderSupplierPaymentHistory(sname);
    }

    showFloatToast(paymentId ? `成功修改【${sname}】付款单据为 ¥${fmtNum(amount)}，账套已实时全量更新` : `成功为【${sname}】录入已付款 ¥${fmtNum(amount)}，账套与图表已实时全量同步！`);
  }

  async function deleteSupplierPaymentRecord(paymentId, amount, supplierName) {
    if (!confirm(`确定要撤回作废这笔已付账款吗？

供应商：${supplierName}
撤回金额：¥${fmtNum(amount)}

撤回后，该笔款项将作废，待付账款与财务大盘将自动实时回滚！`)) {
      return;
    }
    await postCrud('payment', 'delete', { id: paymentId });

    if (document.getElementById('supplierPaymentHistoryModal') && document.getElementById('supplierPaymentHistoryModal').classList.contains('active')) {
      renderSupplierPaymentHistory(supplierName);
    }
    if (document.getElementById('supplierPaymentModal') && document.getElementById('supplierPaymentModal').classList.contains('active')) {
      resetSupPayFormToNew();
      renderModalPaymentHistory(supplierName);
      const sup = (CURRENT_STATE.ap_ledger || []).find(s => s.supplier_name === supplierName);
      if (sup) {
        currentPaymentSupplierBalance = sup.ap_balance;
        document.getElementById('supPayBalance').textContent = fmtMoney(sup.ap_balance);
      }
    }
    showFloatToast(`↩️ 已成功撤回【${supplierName}】的 ¥${fmtNum(amount)} 付款单据，应付款账套已实时回滚！`, 'amber');
  }

  function openSupplierPaymentHistoryModal(supplierName) {
    if (!supplierName) return;
    document.getElementById('histSupplierNameHidden').value = supplierName;
    renderSupplierPaymentHistory(supplierName);
    openModal('supplierPaymentHistoryModal');
  }

  function renderSupplierPaymentHistory(supplierName) {
    const sup = (CURRENT_STATE.ap_ledger || []).find(s => s.supplier_name === supplierName) || {};
    document.getElementById('histModalTitle').textContent = `【${supplierName}】已付明细与撤回中心`;
    document.getElementById('histSupName').textContent = supplierName;
    document.getElementById('histPaidTotal').textContent = fmtMoney(sup.paid_amount || 0);
    document.getElementById('histBalanceTotal').textContent = fmtMoney(sup.ap_balance || 0);

    const tbody = document.getElementById('histPaymentsTbody');
    if (!tbody) return;
    const list = (CURRENT_STATE.supplier_payments || []).filter(p => p.supplier_name === supplierName);
    if (list.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:32px; color:var(--text-dim);">该供应商暂无已付款记录。</td></tr>';
      return;
    }
    const safeSupName = (supplierName || '').replace(/'/g, "\'");
    tbody.innerHTML = list.map((p, idx) => `
      <tr>
        <td style="color:var(--text-dim); font-size:11px;">#${idx + 1}</td>
        <td><strong>${p.date}</strong></td>
        <td class="num" style="color:var(--green); font-weight:800; font-family:var(--font-mono);">¥${fmtNum(p.amount)}</td>
        <td>${p.payer || '-'}</td>
        <td style="color:var(--text-muted); font-size:11.5px;">${p.phone ? p.phone.replace(/^备注:/, '') : '-'}</td>
        <td style="text-align:center; white-space:nowrap;">
          <button class="btn btn-sm" style="padding:2px 8px; font-size:11px;" onclick="editPaymentFromHistory(${p.id})">修改</button>
          <button class="btn btn-sm btn-action-danger" style="padding:2px 8px; font-size:11px; margin-left:4px;" onclick="deleteSupplierPaymentRecord(${p.id}, ${p.amount}, '${safeSupName}')">↩️ 撤回</button>
        </td>
      </tr>
    `).join('');
  }

  function openPaymentModalFromHistory() {
    const sname = document.getElementById('histSupplierNameHidden').value;
    closeModal('supplierPaymentHistoryModal');
    openSupplierPaymentModal(null, sname);
  }

  function editPaymentFromHistory(paymentId) {
    const p = (CURRENT_STATE.supplier_payments || []).find(x => x.id === paymentId);
    if (!p) return alert('未找到该付款单据');
    closeModal('supplierPaymentHistoryModal');
    openSupplierPaymentModal(null, p.supplier_name, null, p);
  }

  // ================= 全系统多维排列引擎 + 导入批次删除引擎 =================
  window.CURRENT_SORT_MODE = localStorage.getItem('ledger_sort_mode') || 'date_desc';
  if (!['date_desc', 'date_asc', 'stock_desc', 'stock_asc', 'amount_desc', 'amount_asc'].includes(window.CURRENT_SORT_MODE)) {
    window.CURRENT_SORT_MODE = 'date_desc';
  }

  function normalizeDateForSort(dStr) {
    if (!dStr) return '0000-00-00';
    const s = String(dStr).trim();
    const m = s.match(/(\\d{4})[-\\/\\.](\\d{1,2})[-\\/\\.](\\d{1,2})(.*)/);
    if (m) {
      return `${m[1]}-${m[2].padStart(2, '0')}-${m[3].padStart(2, '0')}${m[4] || ''}`;
    }
    return s;
  }

  function syncSortDropdowns() {
    document.querySelectorAll('.table-sort-select').forEach(sel => {
      if (sel.value !== window.CURRENT_SORT_MODE) {
        sel.value = window.CURRENT_SORT_MODE;
      }
    });
  }

  window.setSystemSortOrder = function(mode) {
    window.CURRENT_SORT_MODE = mode || 'date_desc';
    localStorage.setItem('ledger_sort_mode', window.CURRENT_SORT_MODE);
    syncSortDropdowns();
    renderAll();
    const labelMap = {
      'date_desc': '按最新日期往下排列 ↓',
      'date_asc': '按最早日期往下排列 ↑',
      'stock_desc': '按库存/数量从多到少排列 ↓',
      'stock_asc': '按库存/数量从少到多排列 ↑',
      'amount_desc': '按金额从高到低排列 ↓',
      'amount_asc': '按金额从低到高排列 ↑'
    };
    if (typeof showFloatToast === 'function') {
      showFloatToast(`已切换表单排列方式：${labelMap[window.CURRENT_SORT_MODE] || mode}`, 'green');
    }
  };

  function sortSystemRecords(list, tableType) {
    const arr = [...(list || [])];
    const mode = window.CURRENT_SORT_MODE || 'date_desc';

    const getDateKey = (item) => {
      if (tableType === 'batches') return normalizeDateForSort(item.created_at || '');
      if (tableType === 'tx') return normalizeDateForSort(item.date || '');
      return normalizeDateForSort(item.latest_date || item.date || '');
    };
    const getTieId = (item) => Number(item.latest_tx_id ?? item.id ?? 0);

    const getStockVal = (item) => {
      if (tableType === 'inventory') return parseFloat(item.stock_qty ?? 0);
      if (tableType === 'tx') return parseFloat(item.qty ?? item.amount ?? 0);
      if (tableType === 'batches') return parseFloat(item.record_count ?? 0);
      if (tableType === 'ar') return parseFloat(item.sales_amount ?? item.ar_balance ?? 0);
      if (tableType === 'ap') return parseFloat(item.purchase_amount ?? item.ap_balance ?? 0);
      return 0;
    };

    const getAmountVal = (item) => {
      if (tableType === 'inventory') return parseFloat(item.stock_amount ?? item.stock_value ?? item.in_amount ?? 0);
      if (tableType === 'ar') return parseFloat(item.ar_balance ?? 0);
      if (tableType === 'ap') return parseFloat(item.ap_balance ?? 0);
      if (tableType === 'tx') return parseFloat(item.amount ?? 0);
      if (tableType === 'batches') return parseFloat(item.record_count ?? 0);
      return 0;
    };

    arr.sort((a, b) => {
      if (mode === 'date_desc') {
        const cmp = getDateKey(b).localeCompare(getDateKey(a));
        if (cmp !== 0) return cmp;
        const idDiff = getTieId(b) - getTieId(a);
        return idDiff !== 0 ? idDiff : (Number(b.id || 0) - Number(a.id || 0));
      }
      if (mode === 'date_asc') {
        const cmp = getDateKey(a).localeCompare(getDateKey(b));
        if (cmp !== 0) return cmp;
        const idDiff = getTieId(a) - getTieId(b);
        return idDiff !== 0 ? idDiff : (Number(a.id || 0) - Number(b.id || 0));
      }
      if (mode === 'stock_desc') {
        const diff = getStockVal(b) - getStockVal(a);
        return diff !== 0 ? diff : (getDateKey(b).localeCompare(getDateKey(a)));
      }
      if (mode === 'stock_asc') {
        const diff = getStockVal(a) - getStockVal(b);
        return diff !== 0 ? diff : (getDateKey(b).localeCompare(getDateKey(a)));
      }
      if (mode === 'amount_desc') {
        const diff = getAmountVal(b) - getAmountVal(a);
        return diff !== 0 ? diff : (getDateKey(b).localeCompare(getDateKey(a)));
      }
      if (mode === 'amount_asc') {
        const diff = getAmountVal(a) - getAmountVal(b);
        return diff !== 0 ? diff : (getDateKey(b).localeCompare(getDateKey(a)));
      }
      return 0;
    });
    return arr;
  }

  window.renderInventory = function() {
    const tbody = document.querySelector('#inventoryTable tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    const invList = sortSystemRecords(CURRENT_STATE.inventory_ledger || [], 'inventory');
    if (invList.length === 0) {
      tbody.innerHTML = `<tr><td colspan="15" style="text-align:center; padding:32px; color:var(--text-dim);">商品库为空，点击右上角「+ 新增商品档案」或上传表格自动建档。</td></tr>`;
      return;
    }

    invList.forEach(x => {
      const tr = document.createElement('tr');
      if (x.is_low_stock) tr.className = 'low-stock';
      const safeProdName = (x.product_name || '').replace(/'/g, "\\\\'");
      const dateText = (x.latest_date && x.latest_date !== '0000-00-00') ? x.latest_date : '-';
      tr.innerHTML = `
        <td><strong style="color:var(--text);">${x.product_name}</strong></td>
        <td><span class="cell-sub-date">${dateText}</span></td>
        <td>${x.spec || '件'}</td>
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
        <td>${x.is_low_stock ? '<span class="status-pill status-danger"><span class="status-dot"></span>缺货预警</span>' : '<span class="status-pill status-success"><span class="status-dot"></span>充足</span>'}</td>
        <td>
          <button class="btn btn-xs" onclick="openProductModal(${x.id})">编辑</button>
          <button class="btn btn-xs btn-outline-danger" onclick="deleteProduct(${x.id}, '${safeProdName}')">删除</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  };

  window.renderAR = function() {
    const tbody = document.querySelector('#arTable tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    const arList = sortSystemRecords(CURRENT_STATE.ar_ledger || [], 'ar');
    if (arList.length === 0) {
      tbody.innerHTML = `<tr><td colspan="11" style="text-align:center; padding:32px; color:var(--text-dim);">客户档案为空，点击右上角「+ 新增客户档案」录入。</td></tr>`;
      return;
    }

    arList.forEach(x => {
      const tr = document.createElement('tr');
      const safeCustName = (x.customer_name || '').replace(/'/g, "\\\\'");
      const dateText = (x.latest_date && x.latest_date !== '0000-00-00') ? x.latest_date : '-';
      tr.innerHTML = `
        <td><span class="tag ${x.rank === 1 ? 'tag-red' : (x.rank === 2 ? 'tag-amber' : 'tag-blue')}">第 ${x.rank} 名</span></td>
        <td><strong style="color:var(--text);">${x.customer_name}</strong></td>
        <td><span class="cell-sub-date">${dateText}</span></td>
        <td>${x.address || '-'}</td>
        <td>${x.phone || '-'}</td>
        <td class="num">${fmtMoney(x.opening_ar)}</td>
        <td class="num" style="color:var(--primary);">+${fmtMoney(x.sales_amount)}</td>
        <td class="num" style="color:var(--green);">-${fmtMoney(x.received_amount)}</td>
        <td class="num" style="font-weight:700; color:var(--primary);">${fmtMoney(x.ar_balance)}</td>
        <td class="num" style="font-weight:600;">${x.ar_share}%</td>
        <td>
          <button class="btn btn-xs" onclick="openCustomerModal(${x.id})">编辑</button>
          <button class="btn btn-xs btn-outline-danger" onclick="deleteCustomer(${x.id}, '${safeCustName}')">删除</button>
          <button class="btn btn-xs btn-outline-secondary" onclick="generateStatement('${safeCustName}')">催款单</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  };

  // 重写 renderAP 以支持多维排序、付款明细与登记付款联动
  window.renderAP = function() {
    const tbody = document.querySelector('#apTable tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    const apList = sortSystemRecords(CURRENT_STATE.ap_ledger || [], 'ap');
    if (apList.length === 0) {
      tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; padding:32px; color:var(--text-dim);">供应商档案为空，点击右上角「+ 新增供应商档案」录入。</td></tr>`;
      return;
    }

    apList.forEach(x => {
      const tr = document.createElement('tr');
      const safeName = (x.supplier_name || '').replace(/'/g, "\'");
      const dateText = (x.latest_date && x.latest_date !== '0000-00-00') ? x.latest_date : '-';
      tr.innerHTML = `
        <td><span class="tag ${x.rank === 1 ? 'tag-amber' : 'tag-blue'}">第 ${x.rank} 名</span></td>
        <td><strong style="color:var(--text);">${x.supplier_name}</strong></td>
        <td><span class="cell-sub-date">${dateText}</span></td>
        <td>${x.address || '-'}</td>
        <td>${x.phone || '-'}</td>
        <td class="num" style="color:var(--amber); font-weight:600;">${fmtMoney(x.purchase_amount)}</td>
        <td class="num">
          ${x.paid_amount > 0 ? `
            <button type="button" class="badge-paid-clickable" onclick="openSupplierPaymentHistoryModal('${safeName}')" title="已付 -¥${fmtMoney(x.paid_amount)}，点击查看明细、修改金额或撤回单据">
              -${fmtMoney(x.paid_amount)}
            </button>
          ` : `
            <span style="color:var(--text-dim);">-¥0.00</span>
          `}
        </td>
        <td class="num" style="font-weight:800; color:${x.ap_balance > 0 ? 'var(--red)' : 'var(--text)'};">${fmtMoney(x.ap_balance)}</td>
        <td class="num" style="font-weight:600;">${x.ap_share}%</td>
        <td style="white-space:nowrap;">
          <button class="btn btn-xs btn-outline-success" onclick="openSupplierPaymentModal(${x.id}, '${safeName}', ${x.ap_balance})">登记付款</button>
          ${x.paid_amount > 0 ? `<button class="btn btn-xs btn-outline-secondary" onclick="openSupplierPaymentHistoryModal('${safeName}')" title="查看所有已付记录，支持修改金额或撤回作废">付款明细</button>` : ''}
          <button class="btn btn-xs" onclick="openSupplierModal(${x.id})">编辑</button>
          <button class="btn btn-xs btn-outline-danger" onclick="deleteSupplier(${x.id}, '${safeName}')">删除</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  };

  window.renderTransactions = function() {
    const pTb = document.querySelector('#txPurchasesTable tbody');
    if (pTb) {
      pTb.innerHTML = '';
      sortSystemRecords(CURRENT_STATE.purchases || [], 'tx').forEach(x => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${x.date}</strong></td>
          <td><code>${x.order_no}</code></td>
          <td><strong>${x.product_name}</strong></td>
          <td>${x.spec}</td>
          <td class="num">${fmtMoney(x.unit_price)}</td>
          <td class="num">${x.qty}</td>
          <td class="num" style="font-weight:700;">${fmtMoney(x.amount)}</td>
          <td>${x.buyer || '-'}</td>
          <td>${x.supplier_name}</td>
          <td>${x.address || '-'}</td>
          <td>${x.phone || '-'}</td>
          <td>
            <button class="btn-action" onclick="openEditTxModal('purchases', ${x.id})">编辑</button>
            <button class="btn-action btn-action-danger" onclick="deleteTx('purchase', ${x.id})">删除</button>
          </td>
        `;
        pTb.appendChild(tr);
      });
    }

    const sTb = document.querySelector('#txSalesTable tbody');
    if (sTb) {
      sTb.innerHTML = '';
      sortSystemRecords(CURRENT_STATE.sales || [], 'tx').forEach(x => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${x.date}</strong></td>
          <td><code>${x.order_no}</code></td>
          <td><strong>${x.product_name}</strong></td>
          <td>${x.spec}</td>
          <td class="num">${fmtMoney(x.unit_price)}</td>
          <td class="num">${x.qty}</td>
          <td class="num" style="font-weight:700;">${fmtMoney(x.amount)}</td>
          <td>${x.seller || '-'}</td>
          <td>${x.customer_name}</td>
          <td>${x.address || '-'}</td>
          <td>${x.phone || '-'}</td>
          <td>
            <button class="btn-action" onclick="openEditTxModal('sales', ${x.id})">编辑</button>
            <button class="btn-action btn-action-danger" onclick="deleteTx('sale', ${x.id})">删除</button>
          </td>
        `;
        sTb.appendChild(tr);
      });
    }

    const payTb = document.querySelector('#txPaymentsTable tbody');
    if (payTb) {
      payTb.innerHTML = '';
      sortSystemRecords(CURRENT_STATE.supplier_payments || [], 'tx').forEach(x => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${x.date}</strong></td>
          <td><strong>${x.supplier_name}</strong></td>
          <td>${x.address || '-'}</td>
          <td>${x.phone || '-'}</td>
          <td class="num" style="color:var(--green); font-weight:700;">${fmtMoney(x.amount)}</td>
          <td>${x.payer || '-'}</td>
          <td>${x.payee || '-'}</td>
          <td>
            <button class="btn-action" onclick="openEditTxModal('payments', ${x.id})">编辑</button>
            <button class="btn-action btn-action-danger" onclick="deleteTx('payment', ${x.id})">删除</button>
          </td>
        `;
        payTb.appendChild(tr);
      });
    }

    const recTb = document.querySelector('#txReceiptsTable tbody');
    if (recTb) {
      recTb.innerHTML = '';
      sortSystemRecords(CURRENT_STATE.customer_receipts || [], 'tx').forEach(x => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${x.date}</strong></td>
          <td><strong>${x.customer_name}</strong></td>
          <td>${x.address || '-'}</td>
          <td>${x.phone || '-'}</td>
          <td class="num" style="color:var(--primary); font-weight:700;">${fmtMoney(x.amount)}</td>
          <td>${x.payer || '-'}</td>
          <td>${x.payee || '-'}</td>
          <td>
            <button class="btn-action" onclick="openEditTxModal('receipts', ${x.id})">编辑</button>
            <button class="btn-action btn-action-danger" onclick="deleteTx('receipt', ${x.id})">删除</button>
          </td>
        `;
        recTb.appendChild(tr);
      });
    }

    const badgeEl = document.getElementById('txCountBadge');
    if (badgeEl) {
      badgeEl.textContent = `采购 ${(CURRENT_STATE.purchases || []).length} 笔 · 销售 ${(CURRENT_STATE.sales || []).length} 笔 · 收付款 ${(CURRENT_STATE.supplier_payments || []).length + (CURRENT_STATE.customer_receipts || []).length} 笔`;
    }
  };

  window.renderBatches = function() {
    const tbody = document.querySelector('#batchesTable tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    const sortedBatches = sortSystemRecords(CURRENT_STATE.batches || [], 'batches');
    if (sortedBatches.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:32px; color:var(--text-dim);">暂无导入批次记录。</td></tr>`;
      return;
    }

    sortedBatches.forEach(b => {
      const tr = document.createElement('tr');
      const isRolledBack = b.status === 'rolled_back';
      const isInit = b.source_type === 'initial_seed';
      const safeCode = (b.batch_code || '').replace(/'/g, "\\\\'");
      let actionHtml = '';
      if (isInit) {
        actionHtml = '<span style="color:var(--text-dim); font-size:12px;">系统基准数据</span>';
      } else if (isRolledBack) {
        actionHtml = `
          <div style="display:flex; align-items:center; gap:6px; white-space:nowrap;">
            <button class="btn btn-xs btn-outline-danger" onclick="deleteBatchRecord(${b.id}, '${safeCode}', true)" title="彻底删除该占位批次记录">删除记录</button>
          </div>
        `;
      } else {
        actionHtml = `
          <div style="display:flex; align-items:center; gap:6px; white-space:nowrap;">
            <button class="btn btn-xs btn-outline-warning" onclick="rollbackBatch(${b.id})" title="撤回该批次导入的数据，保留批次日志">撤回</button>
            <button class="btn btn-xs btn-outline-danger" onclick="deleteBatchRecord(${b.id}, '${safeCode}', false)" title="撤销该批次数据并直接从列表中彻底删除该批次记录">删除</button>
          </div>
        `;
      }
      tr.innerHTML = `
        <td><code>${b.batch_code}</code></td>
        <td><strong>${b.source_name}</strong></td>
        <td><span class="tag tag-blue">${b.parse_mode}</span></td>
        <td>${b.summary || '-'}</td>
        <td class="num">${b.record_count}</td>
        <td>${isRolledBack ? '<span class="status-pill status-danger"><span class="status-dot"></span>已撤销</span>' : '<span class="status-pill status-success"><span class="status-dot"></span>已入账</span>'}</td>
        <td style="font-size:12px; font-family:monospace;">${b.created_at}</td>
        <td>${actionHtml}</td>
      `;
      tbody.appendChild(tr);
    });
  };

  window.deleteBatchRecord = async function(batchId, batchCode, isRolledBack) {
    const confirmMsg = isRolledBack
      ? `确定要将已撤销的批次记录「${batchCode}」从列表中彻底删除吗？`
      : `确定要彻底删除批次「${batchCode}」吗？\n\n该批次处于“已生效”状态，删除将自动回滚清除该批次导入的所有业务流水，并从记录中彻底移除。`;
    if (!confirm(confirmMsg)) return;
    try {
      const resp = await fetch('/api/batches/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ batch_id: batchId })
      });
      const data = await resp.json();
      if (!data.ok) {
        alert((data.result && data.result.error) || data.error || '删除批次失败');
        return;
      }
      CURRENT_STATE = data.state;
      renderAll();
      if (typeof showFloatToast === 'function') {
        showFloatToast(`已彻底删除批次记录「${batchCode}」，台账已实时同步`, 'amber');
      }
    } catch (e) {
      alert('删除批次错误：' + e.message);
    }
  };

  window.clearRolledBackBatches = async function() {
    const rolledCount = (CURRENT_STATE.batches || []).filter(b => b.source_type !== 'initial_seed' && (b.status === 'rolled_back' || b.record_count <= 0)).length;
    if (rolledCount === 0) {
      if (typeof showFloatToast === 'function') {
        showFloatToast('当前列表中没有已撤销或无记录的占位批次', 'green');
      } else {
        alert('当前列表中没有已撤销或 0 记录的占位批次');
      }
      return;
    }
    if (!confirm(`确定要一键清理全部 ${rolledCount} 条【已撤销回滚 / 0记录】的占位批次吗？\n清理后列表将只保留有效入账批次。`)) return;
    try {
      const resp = await fetch('/api/batches/clear_rolled_back', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await resp.json();
      if (!data.ok) {
        alert(data.error || '清理失败');
        return;
      }
      CURRENT_STATE = data.state;
      renderAll();
      if (typeof showFloatToast === 'function') {
        showFloatToast(`已成功清理 ${data.result.removed_count} 条无效占位批次记录`, 'green');
      }
    } catch (e) {
      alert('清理请求异常：' + e.message);
    }
  };

  // 扩展原有的 openSupplierModal 与 saveSupplierForm，增强与已付金额的历史联动
  const baseOpenSupplierModal = window.openSupplierModal;
  window.openSupplierModal = function(id) {
    if (baseOpenSupplierModal) baseOpenSupplierModal(id);
    const paidEl = document.getElementById('supFormCurrentPaid');
    const addPayEl = document.getElementById('supFormAddPayment');
    const payDateEl = document.getElementById('supFormPaymentDate');
    if (addPayEl) addPayEl.value = '';
    if (payDateEl) payDateEl.value = new Date().toISOString().split('T')[0];
    if (paidEl && id) {
      const s = (CURRENT_STATE.ap_ledger || []).find(x => x.id === id);
      paidEl.textContent = fmtMoney(s ? s.paid_amount : 0);
    } else if (paidEl) {
      paidEl.textContent = '¥0.00';
    }
  };

  const baseSaveSupplierForm = window.saveSupplierForm;
  window.saveSupplierForm = async function() {
    const sname = document.getElementById('supFormName').value.trim();
    const addPayment = parseFloat(document.getElementById('supFormAddPayment') ? document.getElementById('supFormAddPayment').value || 0 : 0);
    const paymentDate = document.getElementById('supFormPaymentDate') ? document.getElementById('supFormPaymentDate').value : '';

    if (baseSaveSupplierForm) {
      await baseSaveSupplierForm();
    }

    // 如果填入了已付金额，自动追加保存一条付款记录并实时同步
    if (sname && addPayment > 0) {
      const pDate = paymentDate || new Date().toISOString().split('T')[0];
      await postCrud('payment', 'save', {
        supplier_name: sname,
        amount: addPayment,
        date: pDate,
        payer: '财务出纳',
        payee: sname,
        address: '',
        phone: '供应商档案登记同步'
      });
    }
  };

  const baseRenderAll = window.renderAll;
  window.renderAll = function() {
    syncSortDropdowns();
    if (baseRenderAll) baseRenderAll();
  };

  function openAiDrawer() {
    const drawer = document.getElementById('aiDrawer');
    const overlay = document.getElementById('aiDrawerOverlay');
    if (drawer && overlay) {
      overlay.classList.add('active');
      drawer.classList.add('open');
    }
  }

  function closeAiDrawer() {
    const drawer = document.getElementById('aiDrawer');
    const overlay = document.getElementById('aiDrawerOverlay');
    if (drawer && overlay) {
      overlay.classList.remove('active');
      drawer.classList.remove('open');
    }
  }

  const tabTitles = {
    'overview': ['经营总览与资金诊断', '实时监控资产、流水、缺货预警与回款指标'],
    'workbench': ['AI 异构表格推演工作台', '支持非标表头智能归一化、增量影响仿真与双轨审计'],
    'inventory': ['进销存库存商品台账', '全库商品 SKU 实时进销存明细与缺货水位监控'],
    'ar': ['客户应收账款台账', '客户欠款、账龄统计与往来对账单智能导出'],
    'ap': ['供应商应付账款台账', '供货商采购对账、应付欠款与已付款实时登记'],
    'transactions': ['业务单据与资金流水', '采购进货、销售出货、付款回款全生命周期单据'],
    'batches': ['数据批次时光机', '多批次导入版本历史与一键秒级数据回滚'],
    'chat': ['AI 财务智能顾问', '搭载 DeepSeek / 通义千问的自然语言账套全景分析']
  };

  const baseSwitchTab = window.switchTab;
  window.switchTab = function(name) {
    if (baseSwitchTab) baseSwitchTab(name);

    document.querySelectorAll('.tab-pane').forEach(el => el.style.display = 'none');
    const pane = document.getElementById('tab-' + name);
    if (pane) pane.style.display = 'block';

    document.querySelectorAll('.nav-link-item').forEach(el => el.classList.remove('active'));
    const link = document.querySelector(`.nav-link-item[data-tab="${name}"]`);
    if (link) link.classList.add('active');

    const titleMeta = tabTitles[name] || ['经营管理', '智能实时台账系统'];
    const hTitle = document.getElementById('currentViewTitle');
    const hSub = document.getElementById('currentViewSub');
    if (hTitle) hTitle.textContent = titleMeta[0];
    if (hSub) hSub.textContent = titleMeta[1];
  };

  function handleGlobalSearch(query) {
    query = (query || '').toLowerCase().trim();
    const rows = document.querySelectorAll('.data-table tbody tr');
    rows.forEach(r => {
      const text = r.textContent.toLowerCase();
      if (!query || text.includes(query)) {
        r.style.display = '';
      } else {
        r.style.display = 'none';
      }
    });
  }

  // ================= 多模态表格与单据图片上传识别 + 交互式确认录入 =================
  window.CHAT_PENDING_UPLOADS = {};
  window.LAST_PENDING_UPLOAD_ID = null;

  function readFileAsDataURL(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = e => {
        const rawDataUrl = e.target.result;
        // 若图片体积较大，自动在前端 Canvas 进行无损清晰度缩放压缩（最大边 1600px），防止超大 Base64 传输中断
        if (file.size && file.size > 600 * 1024 && file.type && file.type.startsWith('image/')) {
          const img = new Image();
          img.onload = () => {
            const maxDim = 1600;
            let w = img.width;
            let h = img.height;
            if (w > maxDim || h > maxDim) {
              if (w > h) {
                h = Math.round((h * maxDim) / w);
                w = maxDim;
              } else {
                w = Math.round((w * maxDim) / h);
                h = maxDim;
              }
            }
            const canvas = document.createElement('canvas');
            canvas.width = w;
            canvas.height = h;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, w, h);
            resolve(canvas.toDataURL('image/jpeg', 0.88));
          };
          img.onerror = () => resolve(rawDataUrl);
          img.src = rawDataUrl;
        } else {
          resolve(rawDataUrl);
        }
      };
      reader.onerror = () => reject(new Error('文件读取失败'));
      reader.readAsDataURL(file);
    });
  }

  function parseSpreadsheetFileToRows(file) {
    return new Promise((resolve, reject) => {
      const ext = file.name.split('.').pop().toLowerCase();
      if (ext === 'csv') {
        const reader = new FileReader();
        reader.onload = e => resolve({ csv_text: e.target.result });
        reader.onerror = () => reject(new Error('CSV读取失败'));
        reader.readAsText(file, 'utf-8');
      } else if (typeof XLSX !== 'undefined') {
        const reader = new FileReader();
        reader.onload = e => {
          try {
            const data = new Uint8Array(e.target.result);
            const wb = XLSX.read(data, { type: 'array' });
            const firstSheet = wb.SheetNames[0];
            const ws = wb.Sheets[firstSheet];
            const rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });
            resolve({ rows: rows });
          } catch (err) {
            reject(err);
          }
        };
        reader.onerror = () => reject(new Error('Excel读取失败'));
        reader.readAsArrayBuffer(file);
      } else {
        reject(new Error('浏览器端 Excel 解析组件未就绪'));
      }
    });
  }

  async function handleChatFileUpload(files, target = 'main') {
    if (!files || files.length === 0) return;
    const msgContainerId = target === 'drawer' ? 'drawerChatMessages' : 'chatMessages';
    const inputId = target === 'drawer' ? 'drawerChatInput' : 'chatInput';
    const listEl = document.getElementById(msgContainerId);
    const inputEl = document.getElementById(inputId);
    const userHintText = inputEl ? (inputEl.value || '').trim() : '';
    if (inputEl) inputEl.value = '';

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const fname = file.name || ('粘贴单据图片_' + new Date().toTimeString().slice(0, 8).replace(/:/g, '') + '.png');
      const ext = fname.split('.').pop().toLowerCase();
      const isImage = file.type.startsWith('image/') || ['png', 'jpg', 'jpeg', 'webp', 'bmp'].includes(ext);

      // 1. 渲染用户上传气泡
      const uBubble = document.createElement('div');
      uBubble.className = 'chat-bubble user';
      let previewHtml = `<div style="display:flex; align-items:center; gap:6px; font-weight:700;">
        <span>${isImage ? '已上传单据图像：' : '已上传业务表格：'}${fname}</span>
      </div>`;
      if (userHintText) {
        previewHtml += `<div style="margin-top:4px; font-size:12px; opacity:0.92;">备注说明：${userHintText}</div>`;
      }

      let payload = {
        filename: fname,
        text: userHintText
      };

      try {
        if (isImage) {
          const dataUrl = await readFileAsDataURL(file);
          payload.file_type = 'image';
          payload.image_base64 = dataUrl;
          previewHtml += `<img src="${dataUrl}" alt="${fname}" style="max-width:260px; max-height:170px; border-radius:8px; margin-top:8px; border:1px solid rgba(255,255,255,0.35); display:block; cursor:zoom-in;" onclick="window.open(this.src)">`;
        } else {
          payload.file_type = 'table';
          const parsedTable = await parseSpreadsheetFileToRows(file);
          if (parsedTable.rows) {
            payload.rows = parsedTable.rows;
            previewHtml += `<div style="font-size:11.5px; opacity:0.85; margin-top:4px;">共读取 ${parsedTable.rows.length} 行原始表格数据，请求 AI 识别并准备入账</div>`;
          } else if (parsedTable.csv_text) {
            payload.csv_text = parsedTable.csv_text;
          }
        }
      } catch (readErr) {
        alert('读取文件失败：' + readErr.message);
        continue;
      }

      uBubble.innerHTML = previewHtml;
      listEl.appendChild(uBubble);
      listEl.scrollTop = listEl.scrollHeight;

      // 2. 渲染 AI 识别中加载气泡
      const bBubble = document.createElement('div');
      bBubble.className = 'chat-bubble bot';
      bBubble.style.maxWidth = '92%';
      bBubble.innerHTML = `<div style="display:flex; align-items:center; gap:8px; color:var(--primary); font-weight:700;">
        <span>多模态视觉引擎正在解析「${fname}」商品、数量、单位与往来明细...</span>
      </div>`;
      listEl.appendChild(bBubble);
      listEl.scrollTop = listEl.scrollHeight;

      // 3. 调用后端多模态识别接口
      try {
        const resp = await fetch('/api/ai/multimodal_recognize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await resp.json();
        const res = data.result || data;
        if (!data.ok || !res.ok) {
          const errMsg = (res.reply || res.error || data.error || '未能从该文件中提取出有效的单据明细。')
            .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
            .replace(/\\n/g, '<br>');
          bBubble.innerHTML = `<div style="color:var(--text);">${errMsg}</div>`;
          listEl.scrollTop = listEl.scrollHeight;
          continue;
        }

        renderMultimodalConfirmationCard(bBubble, res, target);
        listEl.scrollTop = listEl.scrollHeight;
      } catch (err) {
        bBubble.innerHTML = `<span style="color:var(--red);">多模态识别请求失败：${err.message}</span>`;
        listEl.scrollTop = listEl.scrollHeight;
      }
    }
  }

  function renderMultimodalConfirmationCard(containerBubble, res, target = 'main') {
    const cardId = 'mm_card_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
    // 将识别出的采购/销售/收付款合并为可编辑行列表
    const parsed = res.parsed || {};
    const editableRows = [];
    (parsed.purchases || []).forEach(p => {
      editableRows.push({
        biz_type: 'purchase',
        date: p.date || new Date().toISOString().split('T')[0],
        order_no: p.order_no || '',
        partner_name: p.supplier_name || '默认供应商',
        product_name: p.product_name || '',
        qty: p.qty ?? 1,
        spec: p.spec || '斤',
        unit_price: p.unit_price ?? 0,
        amount: p.amount ?? 0,
        staff: p.buyer || '',
        address: p.address || '',
        phone: p.phone || ''
      });
    });
    (parsed.sales || []).forEach(s => {
      editableRows.push({
        biz_type: 'sale',
        date: s.date || new Date().toISOString().split('T')[0],
        order_no: s.order_no || '',
        partner_name: s.customer_name || '默认客户',
        product_name: s.product_name || '',
        qty: s.qty ?? 1,
        spec: s.spec || '斤',
        unit_price: s.unit_price ?? 0,
        amount: s.amount ?? 0,
        staff: s.seller || '',
        address: s.address || '',
        phone: s.phone || ''
      });
    });

    window.CHAT_PENDING_UPLOADS[cardId] = {
      cardId: cardId,
      filename: res.filename || '上传单据',
      file_type: res.file_type || 'table',
      mode: res.mode || '多模态智能核验',
      parsed: parsed,
      editableRows: editableRows,
      preview: res.preview || {},
      committed: false
    };
    window.LAST_PENDING_UPLOAD_ID = cardId;

    paintConfirmationCardDom(containerBubble, cardId, res.reply || '', target);
  }

  function paintConfirmationCardDom(containerBubble, cardId, replySummary, target) {
    const stateObj = window.CHAT_PENDING_UPLOADS[cardId];
    if (!stateObj) return;
    const rows = stateObj.editableRows || [];
    const payments = (stateObj.parsed && stateObj.parsed.payments) || [];
    const receipts = (stateObj.parsed && stateObj.parsed.receipts) || [];
    const dupWarnings = (stateObj.preview && stateObj.preview.impact && stateObj.preview.impact.duplicate_warnings) || [];

    const totalQty = rows.reduce((acc, r) => acc + (parseFloat(r.qty) || 0), 0);
    const totalAmt = rows.reduce((acc, r) => acc + (parseFloat(r.amount) || 0), 0);

    let rowsHtml = '';
    rows.forEach((r, idx) => {
      const isPur = r.biz_type === 'purchase';
      rowsHtml += `
        <tr data-row-idx="${idx}">
          <td>
            <select class="form-input" style="padding:3px 6px; font-size:11.5px; height:28px; width:76px; font-weight:700; color:${isPur ? 'var(--primary)' : 'var(--green)'};" onchange="updateConfirmRowField('${cardId}', ${idx}, 'biz_type', this.value)">
              <option value="purchase" ${isPur ? 'selected' : ''}>采购入库</option>
              <option value="sale" ${!isPur ? 'selected' : ''}>销售出库</option>
            </select>
          </td>
          <td><input type="text" class="form-input" style="padding:3px 6px; font-size:11.5px; height:28px; min-width:95px;" value="${(r.date || '').replace(/"/g, '&quot;')}" onchange="updateConfirmRowField('${cardId}', ${idx}, 'date', this.value)"></td>
          <td><input type="text" class="form-input" style="padding:3px 6px; font-size:11.5px; height:28px; min-width:120px;" value="${(r.partner_name || '').replace(/"/g, '&quot;')}" onchange="updateConfirmRowField('${cardId}', ${idx}, 'partner_name', this.value)"></td>
          <td><input type="text" class="form-input" style="padding:3px 6px; font-size:11.5px; height:28px; min-width:110px; font-weight:700;" value="${(r.product_name || '').replace(/"/g, '&quot;')}" onchange="updateConfirmRowField('${cardId}', ${idx}, 'product_name', this.value)"></td>
          <td><input type="number" step="0.01" class="form-input tabular-nums" style="padding:3px 6px; font-size:11.5px; height:28px; width:72px; text-align:right; font-weight:700;" value="${r.qty}" oninput="updateConfirmRowField('${cardId}', ${idx}, 'qty', this.value, true)"></td>
          <td>
            <input type="text" class="form-input" list="commonUnitList_global" placeholder="自由填单位" style="padding:3px 6px; font-size:11.5px; height:28px; width:72px; text-align:center;" value="${(r.spec || '斤').replace(/"/g, '&quot;')}" onchange="updateConfirmRowField('${cardId}', ${idx}, 'spec', this.value)" title="可选择常规单位或自由输入任意单位">
          </td>
          <td><input type="number" step="0.01" class="form-input tabular-nums" style="padding:3px 6px; font-size:11.5px; height:28px; width:78px; text-align:right;" value="${r.unit_price}" oninput="updateConfirmRowField('${cardId}', ${idx}, 'unit_price', this.value, true)"></td>
          <td><input type="number" step="0.01" id="confirmRowAmt_${cardId}_${idx}" class="form-input tabular-nums" style="padding:3px 6px; font-size:11.5px; height:28px; width:88px; text-align:right; font-weight:700; color:var(--primary);" value="${r.amount}" onchange="updateConfirmRowField('${cardId}', ${idx}, 'amount', this.value)"></td>
        </tr>
      `;
    });

    let dupAlertHtml = '';
    if (dupWarnings.length > 0) {
      dupAlertHtml = `
        <div style="margin-top:8px; padding:8px 10px; background:var(--amber-light); border:1px solid var(--amber-border); border-radius:6px; font-size:11.5px; color:var(--amber);">
          <div style="font-weight:700; margin-bottom:4px; color:var(--amber);">检测到 ${dupWarnings.length} 笔单据可能与历史记录存在相同单号：</div>
          <label style="display:inline-flex; align-items:center; gap:6px; cursor:pointer; font-weight:600; color:var(--text);">
            <input type="checkbox" id="skipDup_${cardId}" ${stateObj.file_type === 'image' ? '' : 'checked'}>
            入账时自动跳过已存在的重复单据（若您希望强制录入新单据，请取消勾选）
          </label>
        </div>
      `;
    }

    containerBubble.id = 'bubble_' + cardId;
    containerBubble.innerHTML = `
      <div style="font-size:13px; line-height:1.55;">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid var(--border);">
          <span style="font-weight:800; color:var(--primary); font-size:14px;">
            ${stateObj.file_type === 'image' ? '多模态单据识别结果' : '表格结构化解析结果'} · ${stateObj.filename}
          </span>
          <span class="tag tag-blue" style="font-size:11px;">共 ${rows.length + payments.length + receipts.length} 笔明细</span>
        </div>

        <div style="margin-bottom:8px; color:var(--text-muted); font-size:12px;">
          请核对下方单据明细，支持微调<strong>数量</strong>与<strong>单位</strong>（单位支持下拉选择或自由输入），核对无误后确认入账：
        </div>

        ${rows.length > 0 ? `
        <div class="table-responsive" style="max-height:240px; overflow-y:auto; border:1px solid var(--border); border-radius:8px; background:var(--surface); margin-bottom:8px;">
          <table class="data-table" style="margin:0; font-size:12px;">
            <thead>
              <tr>
                <th>单据类型</th>
                <th>日期</th>
                <th>供应商 / 客户</th>
                <th>商品名称</th>
                <th class="num">数量</th>
                <th style="text-align:center;">单位(可自由填)</th>
                <th class="num">单价(¥)</th>
                <th class="num">金额(¥)</th>
              </tr>
            </thead>
            <tbody>${rowsHtml}</tbody>
          </table>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; font-size:12px; padding:4px 8px; background:var(--surface-subtle); border-radius:6px; margin-bottom:8px;">
          <span>明细汇总：共 <strong>${rows.length}</strong> 项商品，合计数量 <strong id="confirmSumQty_${cardId}">${Number(totalQty.toFixed(2))}</strong></span>
          <span>合计总金额：<strong style="color:var(--primary); font-size:13.5px;" id="confirmSumAmt_${cardId}">¥${totalAmt.toFixed(2)}</strong></span>
        </div>
        ` : ''}

        ${dupAlertHtml}

        <div id="confirmActionBox_${cardId}" style="margin-top:10px; padding-top:10px; border-top:1px dashed var(--border); display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
          <span style="font-weight:700; color:var(--text); font-size:12.5px;">核对无误后，是否确认录入并同步系统台账？</span>
          <div style="display:flex; gap:8px; align-items:center;">
            <button type="button" class="btn btn-xs btn-outline-secondary" onclick="toggleChatUploadDirection('${cardId}', '${target}')">切换采购/销售</button>
            <button type="button" class="btn btn-xs btn-outline-secondary" onclick="cancelChatUploadCommit('${cardId}')">取消</button>
            <button type="button" class="btn btn-sm btn-primary" style="font-weight:800; padding:6px 14px;" onclick="confirmChatUploadCommit('${cardId}', '${target}')">
              确认录入并同步更新
            </button>
          </div>
        </div>

        <div style="margin-top:8px; padding-top:6px; border-top:1px solid rgba(0,0,0,0.06); font-size:11px; display:flex; align-items:center; justify-content:space-between; color:#0f766e; font-weight:600;">
          <span>${stateObj.mode}</span>
          <span style="font-size:10px; opacity:0.8;">支持点击按钮或回复“确认”入账</span>
        </div>
      </div>
    `;
  }

  function updateConfirmRowField(cardId, idx, field, val, recalcAmt = false) {
    const stateObj = window.CHAT_PENDING_UPLOADS[cardId];
    if (!stateObj || !stateObj.editableRows[idx]) return;
    const row = stateObj.editableRows[idx];
    if (field === 'qty' || field === 'unit_price' || field === 'amount') {
      row[field] = parseFloat(val) || 0;
    } else {
      row[field] = (val || '').trim();
    }
    if (recalcAmt) {
      const q = parseFloat(row.qty) || 0;
      const p = parseFloat(row.unit_price) || 0;
      if (q > 0 && p > 0) {
        row.amount = parseFloat((q * p).toFixed(2));
        const amtInput = document.getElementById(`confirmRowAmt_${cardId}_${idx}`);
        if (amtInput) amtInput.value = row.amount;
      }
    }
    // 更新底部汇总
    const totalQty = stateObj.editableRows.reduce((acc, r) => acc + (parseFloat(r.qty) || 0), 0);
    const totalAmt = stateObj.editableRows.reduce((acc, r) => acc + (parseFloat(r.amount) || 0), 0);
    const qEl = document.getElementById(`confirmSumQty_${cardId}`);
    const aEl = document.getElementById(`confirmSumAmt_${cardId}`);
    if (qEl) qEl.textContent = Number(totalQty.toFixed(2));
    if (aEl) aEl.textContent = '¥' + totalAmt.toFixed(2);
  }

  function toggleChatUploadDirection(cardId, target) {
    const stateObj = window.CHAT_PENDING_UPLOADS[cardId];
    if (!stateObj || stateObj.committed) return;
    stateObj.editableRows.forEach(r => {
      r.biz_type = (r.biz_type === 'purchase') ? 'sale' : 'purchase';
    });
    const bubble = document.getElementById('bubble_' + cardId);
    if (bubble) paintConfirmationCardDom(bubble, cardId, '', target);
  }

  function cancelChatUploadCommit(cardId) {
    const stateObj = window.CHAT_PENDING_UPLOADS[cardId];
    if (!stateObj) return;
    delete window.CHAT_PENDING_UPLOADS[cardId];
    if (window.LAST_PENDING_UPLOAD_ID === cardId) window.LAST_PENDING_UPLOAD_ID = null;
    const actionBox = document.getElementById('confirmActionBox_' + cardId);
    if (actionBox) {
      actionBox.innerHTML = `<span style="color:var(--text-dim); font-weight:600;">已取消本次单据录入（系统账套数据保持不变）。</span>`;
    }
  }

  async function confirmChatUploadCommit(cardId, target = 'main') {
    const stateObj = window.CHAT_PENDING_UPLOADS[cardId];
    if (!stateObj || stateObj.committed) return;

    const skipDupCheckbox = document.getElementById('skipDup_' + cardId);
    const skipDuplicates = skipDupCheckbox ? skipDupCheckbox.checked : false;

    // 将 editableRows 组装回 parsed 结构
    const newPurchases = [];
    const newSales = [];
    (stateObj.editableRows || []).forEach(r => {
      if (!r.product_name) return;
      if (r.biz_type === 'purchase') {
        newPurchases.push({
          date: r.date || new Date().toISOString().split('T')[0],
          order_no: r.order_no || ('PO-' + Date.now().toString().slice(-6)),
          product_name: r.product_name,
          spec: (r.spec || '斤').trim() || '斤',
          qty: parseFloat(r.qty) || 0,
          unit_price: parseFloat(r.unit_price) || 0,
          amount: parseFloat(r.amount) || 0,
          buyer: r.staff || 'AI多模态录入',
          supplier_name: r.partner_name || '默认供应商',
          address: r.address || '',
          phone: r.phone || ''
        });
      } else {
        newSales.push({
          date: r.date || new Date().toISOString().split('T')[0],
          order_no: r.order_no || ('SO-' + Date.now().toString().slice(-6)),
          product_name: r.product_name,
          spec: (r.spec || '斤').trim() || '斤',
          qty: parseFloat(r.qty) || 0,
          unit_price: parseFloat(r.unit_price) || 0,
          amount: parseFloat(r.amount) || 0,
          seller: r.staff || 'AI多模态录入',
          customer_name: r.partner_name || '默认客户',
          address: r.address || '',
          phone: r.phone || ''
        });
      }
    });

    const finalParsed = {
      purchases: newPurchases,
      sales: newSales,
      payments: (stateObj.parsed && stateObj.parsed.payments) || [],
      receipts: (stateObj.parsed && stateObj.parsed.receipts) || []
    };

    const actionBox = document.getElementById('confirmActionBox_' + cardId);
    if (actionBox) {
      actionBox.innerHTML = `<span style="color:var(--primary); font-weight:600;">正在将核对后的单据明细原子写入 SQLite 数据库并同步台账...</span>`;
    }

    try {
      const resp = await fetch('/api/upload/commit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parsed: finalParsed,
          filename: stateObj.filename,
          source_type: stateObj.file_type === 'image' ? 'image_ocr_chat' : 'table_chat',
          parse_mode: 'AI财务总监多模态识别 + 人工确认入账',
          skip_duplicates: skipDuplicates
        })
      });
      const data = await resp.json();
      if (!data.ok) {
        if (actionBox) actionBox.innerHTML = `<span style="color:var(--red); font-weight:600;">录入失败：${data.error || '未知错误'}</span>`;
        return;
      }

      stateObj.committed = true;
      if (window.LAST_PENDING_UPLOAD_ID === cardId) window.LAST_PENDING_UPLOAD_ID = null;

      if (data.state) {
        CURRENT_STATE = data.state;
        renderAll();
      }

      const cr = data.commit_result || {};
      if (actionBox) {
        actionBox.innerHTML = `
          <div style="width:100%; padding:8px 12px; background:var(--green-light); border:1px solid var(--green-border); border-radius:8px; color:var(--green); font-weight:700; display:flex; align-items:center; justify-content:space-between;">
            <span>已确认录入并全量同步账套！（批次号：<code>${cr.batch_code || '-'}</code> · ${cr.summary || '已生效'}）</span>
            <button type="button" class="btn btn-sm" onclick="switchTab('transactions')" style="font-size:11px; padding:2px 8px;">查看流水台账 &gt;</button>
          </div>
        `;
      }
      if (typeof showFloatToast === 'function') {
        showFloatToast(`单据已确认录入系统！批次「${cr.batch_code || ''}」已实时生效`, 'green');
      }
    } catch (err) {
      if (actionBox) actionBox.innerHTML = `<span style="color:var(--red);">写入请求异常：${err.message}</span>`;
    }
  }

  // 增强主聊天窗口 sendChatMessage：支持直接回复“确认/确认录入”触发待确认单据入账，且自然语言记账也在对话框内直接弹出确认卡片
  const origSendChatMessage = window.sendChatMessage;
  window.sendChatMessage = async function(customText) {
    const input = document.getElementById('chatInput');
    const text = (customText || (input ? input.value : '') || '').trim();
    if (!text) return;

    const confirmKeywords = ['确认', '确认录入', '确认入账', '确认更新', '同意', '好的', '可以', '确定', '立即录入', 'yes', 'ok'];
    const cancelKeywords = ['取消', '取消录入', '不录入', '算了', 'no'];
    if (window.LAST_PENDING_UPLOAD_ID && window.CHAT_PENDING_UPLOADS[window.LAST_PENDING_UPLOAD_ID] && !window.CHAT_PENDING_UPLOADS[window.LAST_PENDING_UPLOAD_ID].committed) {
      if (confirmKeywords.includes(text.toLowerCase())) {
        if (input) input.value = '';
        appendChatBubble(text, 'user');
        await confirmChatUploadCommit(window.LAST_PENDING_UPLOAD_ID, 'main');
        return;
      } else if (cancelKeywords.includes(text.toLowerCase())) {
        if (input) input.value = '';
        appendChatBubble(text, 'user');
        cancelChatUploadCommit(window.LAST_PENDING_UPLOAD_ID);
        return;
      }
    }

    if (input) input.value = '';
    appendChatBubble(text, 'user');
    const loadingId = 'thinking_' + Date.now();
    appendChatBubble('AI 财务总监正在分析账套数据与业务实质...', 'bot', '分析中', loadingId);

    try {
      const resp = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
      });
      const data = await resp.json();
      const loadEl = document.getElementById(loadingId);

      if (data.ok && data.result) {
        if (data.result.type === 'action_executed') {
          if (loadEl) loadEl.remove();
          if (data.state) {
            CURRENT_STATE = data.state;
            renderAll();
          }
          appendChatBubble(data.result.reply, 'bot', data.result.mode);
          if (typeof showFloatToast === 'function') {
            showFloatToast('AI 协同指令已执行并持久化落盘', 'green');
          }
        } else if (data.result.type === 'multimodal_confirmation' || data.result.type === 'bookkeeping_preview') {
          const previewObj = data.result.preview || {};
          const synthRes = {
            ok: true,
            filename: previewObj.filename || '自然语言记账指令',
            file_type: 'text_command',
            mode: data.result.mode || 'AI 语义记账',
            parsed: data.result.parsed || previewObj.parsed || {},
            preview: previewObj,
            reply: data.result.reply || '已提取记账明细，请核对后确认录入：'
          };
          if (loadEl) {
            loadEl.style.maxWidth = '92%';
            renderMultimodalConfirmationCard(loadEl, synthRes, 'main');
          }
        } else {
          if (loadEl) loadEl.remove();
          appendChatBubble(data.result.reply || '已处理完成。', 'bot', data.result.mode);
        }
      } else {
        if (loadEl) loadEl.remove();
        appendChatBubble('抱歉，处理未能完成。', 'bot');
      }
    } catch (e) {
      const loadEl = document.getElementById(loadingId);
      if (loadEl) loadEl.remove();
      appendChatBubble('抱歉，助理处理出现错误：' + e.message, 'bot');
    }
  };

  async function sendDrawerChatMessage() {
    const input = document.getElementById('drawerChatInput');
    const msg = (input.value || '').trim();
    if (!msg) return;
    input.value = '';

    const list = document.getElementById('drawerChatMessages');
    const confirmKeywords = ['确认', '确认录入', '确认入账', '确认更新', '同意', '好的', '可以', '确定', '立即录入', 'yes', 'ok'];
    if (window.LAST_PENDING_UPLOAD_ID && window.CHAT_PENDING_UPLOADS[window.LAST_PENDING_UPLOAD_ID] && !window.CHAT_PENDING_UPLOADS[window.LAST_PENDING_UPLOAD_ID].committed) {
      if (confirmKeywords.includes(msg.toLowerCase())) {
        const uBubble = document.createElement('div');
        uBubble.className = 'chat-bubble user';
        uBubble.textContent = msg;
        list.appendChild(uBubble);
        await confirmChatUploadCommit(window.LAST_PENDING_UPLOAD_ID, 'drawer');
        list.scrollTop = list.scrollHeight;
        return;
      }
    }

    const uBubble = document.createElement('div');
    uBubble.className = 'chat-bubble user';
    uBubble.textContent = msg;
    list.appendChild(uBubble);
    list.scrollTop = list.scrollHeight;

    const bBubble = document.createElement('div');
    bBubble.className = 'chat-bubble bot';
    bBubble.innerHTML = '<span style="color:var(--text-dim);">AI 正在复核账套数据并执行协同操作...</span>';
    list.appendChild(bBubble);
    list.scrollTop = list.scrollHeight;

    try {
      const resp = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: msg, message: msg })
      });
      const data = await resp.json();

      if (data.ok && data.state) {
        CURRENT_STATE = data.state;
        renderAll();
      }

      const res = data.result || {};
      if (res.type === 'multimodal_confirmation' || res.type === 'bookkeeping_preview') {
        const previewObj = res.preview || {};
        const synthRes = {
          ok: true,
          filename: previewObj.filename || '自然语言记账指令',
          file_type: 'text_command',
          mode: res.mode || 'AI 顾问语义记账',
          parsed: res.parsed || previewObj.parsed || {},
          preview: previewObj,
          reply: res.reply || '已提取记账明细，请核对后确认录入：'
        };
        bBubble.style.maxWidth = '96%';
        renderMultimodalConfirmationCard(bBubble, synthRes, 'drawer');
        list.scrollTop = list.scrollHeight;
        return;
      }

      const replyText = res.reply || data.reply || '已处理完成。';
      const mode = res.mode || data.mode || '';

      let formatted = replyText
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
        .replace(/\\n/g, '<br>');

      let badgeHtml = '';
      if (mode) {
        const isRemote = Boolean(mode && !mode.includes('本地'));
        badgeHtml = `<div style="margin-top:8px; padding-top:6px; border-top:1px solid rgba(0,0,0,0.06); font-size:11px; display:flex; align-items:center; justify-content:space-between; color:${isRemote ? '#0f766e' : '#b45309'}; font-weight:700;">
          <span>${mode}</span>
          <span style="font-size:10px; color:var(--text-dim);">数据已实时落盘</span>
        </div>`;
      }

      bBubble.innerHTML = formatted + badgeHtml;
      list.scrollTop = list.scrollHeight;

      if (res.type === 'action_executed') {
        if (typeof showFloatToast === 'function') {
          showFloatToast('AI 协同指令已执行并持久化落盘', 'green');
        }
      }
    } catch (err) {
      bBubble.innerHTML = '<span style="color:var(--red);">请求失败: ' + err.message + '</span>';
      list.scrollTop = list.scrollHeight;
    }
  }

  // 绑定聊天窗口的拖拽上传与剪贴板 Ctrl+V 粘贴图片事件
  window.addEventListener('DOMContentLoaded', () => {
    const bindDropAndPaste = (zoneEl, target) => {
      if (!zoneEl) return;
      zoneEl.addEventListener('dragover', e => {
        e.preventDefault();
        zoneEl.style.outline = '2px dashed var(--primary)';
      });
      zoneEl.addEventListener('dragleave', () => {
        zoneEl.style.outline = '';
      });
      zoneEl.addEventListener('drop', e => {
        e.preventDefault();
        zoneEl.style.outline = '';
        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          handleChatFileUpload(e.dataTransfer.files, target);
        }
      });
    };

    bindDropAndPaste(document.getElementById('mainChatDropZone'), 'main');
    bindDropAndPaste(document.getElementById('aiDrawer'), 'drawer');

    window.addEventListener('paste', e => {
      const chatPane = document.getElementById('tab-chat');
      const drawerEl = document.getElementById('aiDrawer');
      const isDrawerOpen = drawerEl && drawerEl.classList.contains('open');
      const isChatVisible = chatPane && chatPane.style.display !== 'none';
      if (!isDrawerOpen && !isChatVisible) return;

      const items = (e.clipboardData || e.originalEvent.clipboardData || {}).items;
      if (!items) return;
      const files = [];
      for (let i = 0; i < items.length; i++) {
        if (items[i].kind === 'file') {
          const f = items[i].getAsFile();
          if (f) files.push(f);
        }
      }
      if (files.length > 0) {
        e.preventDefault();
        handleChatFileUpload(files, isDrawerOpen ? 'drawer' : 'main');
      }
    });
  });
"""

FINAL_JS = main_js + "\n" + ADDITIONAL_JS

# 组合最终旗舰级 HTML
FINAL_HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>极智台账 PRO · 进销存与往来账款智能实时台账系统</title>
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="default">
  <meta name="apple-mobile-web-app-title" content="极智台账 PRO">
  <meta name="application-name" content="极智台账 PRO">
  <meta name="theme-color" content="#1e293b">
  <link rel="icon" type="image/png" href="/static/favicon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <!-- SheetJS Offline First with fallback -->
  <script src="/static/xlsx.full.min.js"></script>
  <script>
    if (typeof XLSX === 'undefined') {{
      document.write('<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"><\\/script>');
    }}
  </script>
  <style>
{CSS_THEMES}
  </style>
</head>
<body>
  <div class="app-layout">
    <!-- Left Fixed Sidebar (256px 现代左侧导航栏) -->
    <aside class="app-sidebar">
      <!-- Brand Header -->
      <div class="sidebar-brand">
        <img src="/static/app_icon.png" class="brand-logo-img" alt="应用图标">
        <div class="brand-meta">
          <div class="brand-meta-title">
            极智实时台账
            <span class="brand-meta-tag">PRO</span>
          </div>
          <div style="font-size:11px; color:var(--text-dim); margin-top:2px; display:flex; align-items:center; gap:5px; font-weight:500;">
            <span style="width:6px; height:6px; border-radius:50%; background:#10b981; display:inline-block; box-shadow:0 0 6px rgba(16,185,129,0.6);"></span>
            <span>独立桌面客户端</span>
          </div>
        </div>
      </div>

      <!-- Navigation Links -->
      <nav class="sidebar-nav">
        <!-- Group 1: 经营视界 -->
        <div class="nav-section-card section-insight">
          <div class="nav-section-header">
            <div class="nav-section-title-wrap">
              <span class="nav-group-dot dot-blue"></span>
              <span class="nav-section-title">经营视界</span>
            </div>
            <span class="nav-section-tag tag-blue">大盘</span>
          </div>
          <div class="nav-link-item active" data-tab="overview" onclick="switchTab('overview')">
            <div class="nav-link-left">
              <div class="nav-icon-box icon-blue">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></svg>
              </div>
              <span class="nav-text">经营大盘与诊断</span>
            </div>
          </div>
          <div class="nav-link-item" data-tab="workbench" onclick="switchTab('workbench')">
            <div class="nav-link-left">
              <div class="nav-icon-box icon-cyan">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3Z"/></svg>
              </div>
              <span class="nav-text">AI 异构工作台</span>
            </div>
            <span class="nav-badge-pill pill-cyan" id="workbenchBadge">推荐</span>
          </div>
        </div>

        <!-- Group 2: 核心账套 -->
        <div class="nav-section-card section-core">
          <div class="nav-section-header">
            <div class="nav-section-title-wrap">
              <span class="nav-group-dot dot-teal"></span>
              <span class="nav-section-title">核心账套</span>
            </div>
            <span class="nav-section-tag tag-teal">台账</span>
          </div>
          <div class="nav-link-item" data-tab="inventory" onclick="switchTab('inventory')">
            <div class="nav-link-left">
              <div class="nav-icon-box icon-amber">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>
              </div>
              <span class="nav-text">进销存库存台账</span>
            </div>
            <span class="nav-badge-pill danger" id="lowStockBadge" style="display:none;">0 缺货</span>
          </div>
          <div class="nav-link-item" data-tab="ar" onclick="switchTab('ar')">
            <div class="nav-link-left">
              <div class="nav-icon-box icon-emerald">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
              </div>
              <span class="nav-text">客户应收台账</span>
            </div>
            <span class="nav-badge-pill pill-emerald" id="arBadge">¥0</span>
          </div>
          <div class="nav-link-item" data-tab="ap" onclick="switchTab('ap')">
            <div class="nav-link-left">
              <div class="nav-icon-box icon-rose">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>
              </div>
              <span class="nav-text">供应商应付台账</span>
            </div>
            <span class="nav-badge-pill pill-rose" id="apBadge">¥0</span>
          </div>
          <div class="nav-link-item" data-tab="transactions" onclick="switchTab('transactions')">
            <div class="nav-link-left">
              <div class="nav-icon-box icon-slate">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><line x1="10" x2="8" y1="9" y2="9"/></svg>
              </div>
              <span class="nav-text">业务流水明细</span>
            </div>
          </div>
          <div class="nav-link-item" data-tab="batches" onclick="switchTab('batches')">
            <div class="nav-link-left">
              <div class="nav-icon-box icon-indigo">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/></svg>
              </div>
              <span class="nav-text">导入批次时光机</span>
            </div>
          </div>
        </div>

        <!-- Group 3: 智能中心 -->
        <div class="nav-section-card section-ai">
          <div class="nav-section-header">
            <div class="nav-section-title-wrap">
              <span class="nav-group-dot dot-purple"></span>
              <span class="nav-section-title">智能中心</span>
            </div>
            <span class="nav-section-tag tag-purple">AI 核心</span>
          </div>
          <div class="nav-link-item" data-tab="chat" onclick="switchTab('chat')">
            <div class="nav-link-left">
              <div class="nav-icon-box icon-purple">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              </div>
              <span class="nav-text">AI 财务总监对话</span>
            </div>
          </div>
        </div>
      </nav>

      <!-- Sidebar Status Footer -->
      <div class="sidebar-footer">
        <div class="env-status-card">
          <div class="env-status-row">
            <span>本地 SQLite 数据库</span>
            <span style="display:flex; align-items:center; gap:5px; color:var(--green);">
              <span class="dot-indicator"></span> 正常落盘
            </span>
          </div>
          <div class="env-status-row">
            <span>AI 识别引擎状态</span>
            <span style="color:var(--primary); font-weight:700;" id="aiBadgeText">已连接</span>
          </div>
          <div class="sidebar-actions">
            <button class="btn btn-sm" onclick="openAiSettingsModal()" title="配置大模型 API">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1 0-2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
              设置
            </button>
            <button class="btn btn-sm btn-danger" onclick="openInitModal()" title="重置或清空账套">
              重置账套
            </button>
          </div>
        </div>
      </div>
    </aside>

    <!-- Right Main Stage (主舞台区) -->
    <div class="app-main">
      <!-- Top Header Bar -->
      <header class="app-header">
        <div class="header-breadcrumb">
          <div class="header-title" id="currentViewTitle">经营总览与资金诊断</div>
          <div class="header-sub" id="currentViewSub">实时监控资产、流水、缺货预警与回款指标</div>
        </div>

        <div class="header-actions">
          <!-- 主题切换选择器 (Theme Selector) -->
          <div class="theme-selector-box">
            <button class="btn-theme" onclick="toggleThemeDropdown()">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><path d="M12 2a7 7 0 0 0 7 7c0 2-2 3-2 3s1 1 1 2a2 2 0 0 1-2 2h-1a2 2 0 0 0-2 2c0 2-2 4-4 4a7 7 0 0 1-7-7c0-3.87 3.13-7 7-7Z"/></svg>
              <span id="currentThemeLabel">深空极智蓝</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
            </button>
            <div class="theme-dropdown" id="themeDropdownMenu">
              <div class="theme-opt-item" onclick="setTheme('slate')">
                <span class="theme-color-dot" style="background:#1e40af;"></span>
                <span>深空极智蓝</span>
              </div>
              <div class="theme-opt-item" onclick="setTheme('apple')">
                <span class="theme-color-dot" style="background:#18181b;"></span>
                <span>苹果极简黑</span>
              </div>
              <div class="theme-opt-item" onclick="setTheme('emerald')">
                <span class="theme-color-dot" style="background:#0f766e;"></span>
                <span>翡翠财税绿</span>
              </div>
              <div class="theme-opt-item" onclick="setTheme('indigo')">
                <span class="theme-color-dot" style="background:#4f46e5;"></span>
                <span>皇家紫罗兰</span>
              </div>
              <div class="theme-opt-item" onclick="setTheme('dark')">
                <span class="theme-color-dot" style="background:#090d16; border-color:#38bdf8;"></span>
                <span>暗夜护眼黑</span>
              </div>
            </div>
          </div>

          <!-- 全局表单排列方式选择器 -->
          <div class="sort-control-wrap" style="display:inline-flex; align-items:center; gap:6px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-sm); padding:4px 10px; box-shadow:var(--shadow-xs);" title="全局切换所有台账与流水表单的排列方式">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--text-dim); flex-shrink:0;"><path d="m3 16 4 4 4-4"/><path d="M7 20V4"/><path d="m21 8-4-4-4 4"/><path d="M17 4v16"/></svg>
            <span style="font-size:12px; font-weight:600; color:var(--text-muted); white-space:nowrap;">排序</span>
            <select id="globalSortSelect" class="table-sort-select" onchange="setSystemSortOrder(this.value)" style="border:none; background:transparent; font-size:12px; font-weight:600; color:var(--text); cursor:pointer; outline:none;">
              <option value="date_desc">按最新日期 ↓</option>
              <option value="date_asc">按最早日期 ↑</option>
              <option value="stock_desc">按库存数量 (从多到少) ↓</option>
              <option value="stock_asc">按库存数量 (从少到多) ↑</option>
              <option value="amount_desc">按金额大小 (从高到低) ↓</option>
              <option value="amount_asc">按金额大小 (从低到高) ↑</option>
            </select>
          </div>

          <!-- 实时过滤搜索框 -->
          <div class="header-search">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            <input type="text" placeholder="输入商品/客户/单号过滤..." oninput="handleGlobalSearch(this.value)">
          </div>

          <!-- 一键导出当前台账为 Excel -->
          <button class="btn btn-sm" onclick="exportTableToCsv('inventoryTable', '库存台账导出.csv')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
            导出 Excel
          </button>

          <!-- 唤醒 AI 财务顾问抽屉 -->
          <button class="btn-copilot" onclick="openAiDrawer()">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3Z"/></svg>
            AI 财务总监
          </button>
        </div>
      </header>

      <!-- Main Content Stage -->
      <main class="content-stage">
        <!-- 空状态提醒横幅 (兼容 ID) -->
        <div id="emptyNoticeBanner" style="display:none;" class="empty-banner">
          <div>
            <h4 style="color:#1e40af; font-weight:800; font-size:15px; margin-bottom:4px;">当前账套为空（未录入任何初始数据）</h4>
            <p style="color:#3b82f6; font-size:13px;">您可以点击右侧按钮加载内置的服装行业标准示例数据，或直接进入 AI 异构工作台拖入您的 Excel 表格。</p>
          </div>
          <button class="btn btn-primary" onclick="loadSampleScenario('restock_and_sales')">
            立即加载标准演示数据
          </button>
        </div>

        <!-- TAB 1: OVERVIEW -->
{tab1_enhanced}

        <!-- TAB 2-8: OTHER TABS -->
{tabs_2_8}
      </main>
    </div>
  </div>

  <!-- Flyout AI Drawer (沉浸式右侧滑出抽屉) -->
  <div class="ai-drawer-overlay" id="aiDrawerOverlay" onclick="closeAiDrawer()"></div>
  <aside class="ai-drawer" id="aiDrawer">
    <div class="drawer-header">
      <div style="display:flex; align-items:center; gap:10px;">
        <div style="width:32px; height:32px; border-radius:8px; background:var(--primary-gradient); display:flex; align-items:center; justify-content:center; color:#fff;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3Z"/></svg>
        </div>
        <div>
          <div style="font-weight:800; font-size:15px; color:var(--text);">AI 财务顾问 · 实时协查</div>
          <div style="font-size:11px; color:var(--text-dim);">支持上传表格/单据图片识别 · 账龄穿透 · 协同落盘</div>
        </div>
      </div>
      <button class="btn btn-sm" onclick="closeAiDrawer()" style="padding:4px 8px;">✕</button>
    </div>
    <div style="flex:1; display:flex; flex-direction:column; padding:16px; background:var(--surface-subtle); overflow:hidden;">
      <div class="chat-messages" id="drawerChatMessages" style="flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:12px;">
        <div class="chat-bubble bot">
          您好！我是您的 <strong>极智 AI 财务总监</strong>。<br>
          您可以点击下方 <strong>「上传」</strong> 发送 Excel 表格或单据照片（支持直接粘贴截图），我将智能识别并在您确认后录入更新数据；或直接输入指令：
          • “将零食、坚果、水果类的安全库存统一设为10”
          • “当前哪位供应商的应付欠款最多？”
        </div>
      </div>
      <div style="padding-top:12px; display:flex; gap:6px; align-items:center;">
        <input type="file" id="drawerFileInput" accept=".xlsx,.xls,.csv,.png,.jpg,.jpeg,.webp,.bmp" multiple style="display:none;" onchange="handleChatFileUpload(this.files, 'drawer'); this.value='';">
        <button type="button" class="btn" onclick="document.getElementById('drawerFileInput').click()" title="上传表格或单据照片（支持直接粘贴截图）" style="padding:0 10px; height:38px; font-weight:600; color:var(--primary); border-color:var(--border); background:var(--surface); flex-shrink:0;">上传</button>
        <input type="text" id="drawerChatInput" class="form-input" placeholder="输入指令或上传表格/单据图片..." onkeydown="if(event.key==='Enter') sendDrawerChatMessage()">
        <button class="btn btn-primary" onclick="sendDrawerChatMessage()" style="height:38px; flex-shrink:0;">发送</button>
      </div>
    </div>
  </aside>

  <!-- Modals (包含全部原生模态框 + 供应商付款登记模态框) -->
{full_modals_html}

  <!-- Main JavaScript Logic -->
  <script>
{FINAL_JS}
  </script>
</body>
</html>
"""

paths = [
    os.path.join(BASE_DIR, 'index.html'),
]
release_index = os.path.join(BASE_DIR, 'windows_release', 'index.html')
if os.path.exists(os.path.dirname(release_index)):
    paths.append(release_index)

for p in paths:
    with open(p, 'w', encoding='utf-8') as f:
        f.write(FINAL_HTML)

print("SUCCESS: Assembled Flagship UI v2.2 to all targets. Total Size:", len(FINAL_HTML))
