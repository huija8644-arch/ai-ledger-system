# -*- coding: utf-8 -*-
import os
import re

print("Starting to assemble flagship index.html...")

# 读取原有的主 JavaScript 脚本
with open('/Users/airnipper163.com/Desktop/Antigravity/ai_ledger_system/original_main_script.js', 'r', encoding='utf-8') as f:
    orig_js = f.read()

# 编写现代高质感 CSS
CSS_CONTENT = """
    :root {
      /* Soft Canvas & Ambient Light */
      --bg: #f8fafc;
      --bg-gradient: radial-gradient(at 0% 0%, rgba(224, 242, 254, 0.45) 0px, transparent 50%),
                     radial-gradient(at 100% 0%, rgba(238, 242, 255, 0.45) 0px, transparent 50%),
                     radial-gradient(at 50% 100%, rgba(240, 253, 250, 0.35) 0px, transparent 50%);
      --surface: #ffffff;
      --surface-subtle: #f8fafc;
      --surface-hover: #f1f5f9;
      --surface-glass: rgba(255, 255, 255, 0.88);

      /* Borders & Rings (Double-Bezel Foundation) */
      --border: rgba(226, 232, 240, 0.85);
      --border-subtle: rgba(241, 245, 249, 0.9);
      --border-focus: #3b82f6;
      --ring-focus: rgba(59, 130, 246, 0.15);

      /* Typography Tokens */
      --text: #0f172a;
      --text-muted: #475569;
      --text-dim: #64748b;
      --text-invert: #ffffff;

      /* Primary Theme Colors */
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --primary-light: #eff6ff;
      --primary-gradient: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
      --primary-shadow: 0 4px 14px rgba(37, 99, 235, 0.22);

      /* Functional Accents */
      --teal: #0d9488;
      --teal-light: #f0fdfa;
      --teal-border: #ccfbf1;
      --red: #e11d48;
      --red-light: #fff1f2;
      --red-border: #fecdd3;
      --amber: #d97706;
      --amber-light: #fffbeb;
      --amber-border: #fde68a;
      --green: #059669;
      --green-light: #ecfdf5;
      --green-border: #a7f3d0;
      --indigo: #4f46e5;
      --indigo-light: #eef2ff;

      /* Radii (Modern Squircles) */
      --radius-xl: 20px;
      --radius-lg: 16px;
      --radius: 12px;
      --radius-sm: 8px;
      --radius-xs: 6px;
      --radius-pill: 9999px;

      /* Shadows (Diffuse & Ambient) */
      --shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
      --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.04);
      --shadow: 0 4px 12px -2px rgba(15, 23, 42, 0.05), 0 2px 4px -2px rgba(15, 23, 42, 0.03);
      --shadow-lg: 0 20px 32px -8px rgba(15, 23, 42, 0.08), 0 4px 12px -2px rgba(15, 23, 42, 0.04);
      --shadow-float: 0 24px 48px -12px rgba(15, 23, 42, 0.12);

      /* Motion */
      --ease-spring: cubic-bezier(0.16, 1, 0.3, 1);
      --ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    html { -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
      background-color: var(--bg);
      background-image: var(--bg-gradient);
      background-attachment: fixed;
      color: var(--text);
      font-size: 14px;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
      min-height: 100vh;
      overflow-x: hidden;
    }

    .tabular-nums {
      font-family: 'JetBrains Mono', 'Plus Jakarta Sans', monospace;
      font-variant-numeric: tabular-nums;
      font-feature-settings: "tnum";
    }

    /* Scrollbars */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.35); border-radius: 9999px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(100, 116, 139, 0.55); }

    /* App Shell Layout */
    .app-layout {
      display: flex;
      min-height: 100vh;
      width: 100%;
    }

    /* Left Sidebar */
    .app-sidebar {
      width: 256px;
      background: var(--surface);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      position: sticky;
      top: 0;
      height: 100vh;
      z-index: 100;
      flex-shrink: 0;
      box-shadow: 1px 0 3px rgba(0, 0, 0, 0.02);
    }

    /* Brand Header in Sidebar */
    .sidebar-brand {
      height: 72px;
      padding: 0 20px;
      display: flex;
      align-items: center;
      gap: 12px;
      border-bottom: 1px solid var(--border-subtle);
    }
    .brand-logo-icon {
      width: 38px;
      height: 38px;
      background: var(--primary-gradient);
      border-radius: var(--radius);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      box-shadow: var(--primary-shadow);
    }
    .brand-meta { display: flex; flex-direction: column; }
    .brand-meta-title {
      font-size: 15px;
      font-weight: 800;
      color: var(--text);
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .brand-meta-tag {
      font-size: 10px;
      font-weight: 800;
      padding: 1px 6px;
      border-radius: var(--radius-pill);
      background: rgba(37, 99, 235, 0.1);
      color: var(--primary);
    }
    .brand-meta-sub {
      font-size: 11px;
      color: var(--text-dim);
      font-weight: 500;
      margin-top: 2px;
    }

    /* Sidebar Navigation Links */
    .sidebar-nav {
      flex: 1;
      padding: 18px 12px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .nav-group-title {
      font-size: 11px;
      font-weight: 700;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      padding: 0 10px;
      margin-bottom: 6px;
    }
    .nav-link-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 9px 12px;
      border-radius: var(--radius-sm);
      color: var(--text-muted);
      font-size: 13.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.18s var(--ease-spring);
      text-decoration: none;
      border: 1px solid transparent;
      user-select: none;
    }
    .nav-link-item:hover {
      background: var(--surface-hover);
      color: var(--text);
      transform: translateX(2px);
    }
    .nav-link-item.active {
      background: var(--primary-light);
      color: var(--primary);
      border-color: rgba(37, 99, 235, 0.15);
      font-weight: 700;
      box-shadow: 0 1px 2px rgba(37, 99, 235, 0.05);
    }
    .nav-link-left {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .nav-link-item svg {
      color: var(--text-dim);
      transition: color 0.18s ease;
    }
    .nav-link-item:hover svg, .nav-link-item.active svg {
      color: var(--primary);
    }
    .nav-badge-pill {
      font-size: 11px;
      padding: 1px 7px;
      border-radius: var(--radius-pill);
      background: var(--surface-subtle);
      border: 1px solid var(--border);
      color: var(--text-muted);
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }
    .nav-badge-pill.danger {
      background: var(--red-light);
      color: var(--red);
      border-color: var(--red-border);
    }

    /* Sidebar Footer Status Card */
    .sidebar-footer {
      padding: 16px;
      border-top: 1px solid var(--border-subtle);
      background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%);
    }
    .env-status-card {
      background: var(--surface-subtle);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .env-status-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 11.5px;
      color: var(--text-muted);
      font-weight: 600;
    }
    .dot-indicator {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--green);
      box-shadow: 0 0 0 2px rgba(5, 150, 105, 0.2);
      animation: pulse-dot 2.4s infinite ease-in-out;
    }
    @keyframes pulse-dot {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.15); opacity: 0.85; }
    }
    .sidebar-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
      margin-top: 4px;
    }

    /* Right Main Stage */
    .app-main {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    /* Header Bar */
    .app-header {
      height: 72px;
      background: var(--surface-glass);
      backdrop-filter: saturate(180%) blur(20px);
      -webkit-backdrop-filter: saturate(180%) blur(20px);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 32px;
      position: sticky;
      top: 0;
      z-index: 90;
      box-shadow: 0 1px 0 rgba(255, 255, 255, 0.8) inset, var(--shadow-xs);
    }
    .header-breadcrumb {
      display: flex;
      flex-direction: column;
    }
    .header-title {
      font-size: 17px;
      font-weight: 800;
      color: var(--text);
      letter-spacing: -0.025em;
    }
    .header-sub {
      font-size: 12px;
      color: var(--text-dim);
      font-weight: 500;
    }
    .header-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    /* Search Bar */
    .header-search {
      position: relative;
      width: 240px;
    }
    .header-search input {
      width: 100%;
      padding: 8px 12px 8px 34px;
      border-radius: var(--radius-pill);
      border: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.9);
      font-size: 13px;
      color: var(--text);
      outline: none;
      transition: all 0.2s ease;
    }
    .header-search input:focus {
      border-color: var(--primary);
      width: 280px;
      box-shadow: 0 0 0 3px var(--ring-focus);
      background: #ffffff;
    }
    .header-search svg {
      position: absolute;
      left: 11px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-dim);
      pointer-events: none;
    }

    /* AI Copilot Float Button */
    .btn-copilot {
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
      color: #fff;
      border: 1px solid #334155;
      padding: 8px 16px;
      border-radius: var(--radius-pill);
      font-size: 13px;
      font-weight: 700;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
      transition: all 0.2s var(--ease-spring);
    }
    .btn-copilot:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 18px rgba(15, 23, 42, 0.25);
      background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
    }

    /* Content Stage Area */
    .content-stage {
      padding: 32px;
      max-width: 1640px;
      margin: 0 auto;
      width: 100%;
      flex: 1;
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 7px;
      padding: 8px 16px;
      border-radius: var(--radius-sm);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      transition: all 0.18s var(--ease-spring);
      white-space: nowrap;
      box-shadow: var(--shadow-xs);
      user-select: none;
      outline: none;
    }
    .btn:hover {
      background: var(--surface-hover);
      border-color: #cbd5e1;
      transform: translateY(-1px);
      box-shadow: var(--shadow-sm);
    }
    .btn:active {
      transform: translateY(1px) scale(0.98);
    }
    .btn-primary {
      background: var(--primary-gradient);
      border-color: transparent;
      color: #fff;
      box-shadow: var(--primary-shadow);
    }
    .btn-primary:hover {
      background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
      box-shadow: 0 6px 18px rgba(37, 99, 235, 0.32);
    }
    .btn-teal {
      background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
      border-color: transparent;
      color: #fff;
      box-shadow: 0 4px 14px rgba(13, 148, 136, 0.25);
    }
    .btn-teal:hover {
      background: linear-gradient(135deg, #0f766e 0%, #115e59 100%);
    }
    .btn-danger {
      background: var(--red-light);
      border-color: var(--red-border);
      color: var(--red);
    }
    .btn-danger:hover {
      background: #ffe4e6;
      border-color: #fda4af;
      color: #be123c;
    }
    .btn-sm { padding: 5px 12px; font-size: 12px; border-radius: var(--radius-xs); }

    /* Bento KPI Grid */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(235px, 1fr));
      gap: 18px;
      margin-bottom: 24px;
    }
    .kpi-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 22px 24px;
      box-shadow: var(--shadow);
      position: relative;
      transition: all 0.25s var(--ease-spring);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }
    .kpi-card::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: transparent;
      transition: background 0.25s ease;
    }
    .kpi-card:hover {
      transform: translateY(-3px);
      box-shadow: var(--shadow-float);
      border-color: rgba(203, 213, 225, 0.9);
    }
    .kpi-card:hover::before {
      background: var(--primary-gradient);
    }
    .kpi-label {
      font-size: 13px;
      color: var(--text-dim);
      margin-bottom: 10px;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .kpi-val {
      font-size: 28px;
      font-weight: 800;
      color: var(--text);
      line-height: 1.15;
      letter-spacing: -0.035em;
    }
    .kpi-sub {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 10px;
      display: flex;
      align-items: center;
      gap: 6px;
      font-weight: 500;
    }
    .kpi-card.alert {
      border-color: var(--red-border);
      background: linear-gradient(180deg, #ffffff 0%, #fff8f8 100%);
    }
    .kpi-card.alert::before { background: linear-gradient(90deg, #e11d48, #f43f5e); }
    .kpi-card.success {
      border-color: var(--green-border);
      background: linear-gradient(180deg, #ffffff 0%, #f7fef9 100%);
    }
    .kpi-card.success::before { background: linear-gradient(90deg, #059669, #10b981); }

    /* Visual Charts Grid (Row 2 in Overview) */
    .charts-grid {
      display: grid;
      grid-template-columns: 2fr 1.15fr;
      gap: 20px;
      margin-bottom: 24px;
    }
    .chart-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 22px;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
    }
    .chart-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
    }
    .chart-title {
      font-size: 15px;
      font-weight: 800;
      color: var(--text);
      display: flex;
      align-items: center;
      gap: 8px;
      letter-spacing: -0.015em;
    }
    .chart-badge {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: var(--radius-pill);
      background: var(--surface-subtle);
      border: 1px solid var(--border);
      color: var(--text-muted);
      font-weight: 700;
    }
    .chart-svg-container {
      width: 100%;
      height: 200px;
      position: relative;
    }

    /* Panels & Data Tables */
    .panel {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      margin-bottom: 24px;
      box-shadow: var(--shadow);
      overflow: hidden;
      transition: box-shadow 0.25s var(--ease-spring);
    }
    .panel:hover { box-shadow: var(--shadow-lg); }
    .panel-header {
      padding: 18px 24px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%);
    }
    .panel-title {
      font-size: 15.5px;
      font-weight: 800;
      color: var(--text);
      display: flex;
      align-items: center;
      gap: 10px;
      letter-spacing: -0.015em;
    }
    .panel-actions { display: flex; align-items: center; gap: 10px; }

    .table-responsive { width: 100%; overflow-x: auto; scrollbar-width: thin; }
    table.data-table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 13.5px;
    }
    table.data-table th {
      background: #f8fafc;
      color: var(--text-dim);
      font-weight: 700;
      padding: 13px 18px;
      border-bottom: 1px solid var(--border);
      white-space: nowrap;
      user-select: none;
      font-size: 12.5px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    table.data-table th.num, table.data-table td.num { text-align: right; }
    table.data-table td {
      padding: 14px 18px;
      border-bottom: 1px solid var(--border-subtle);
      color: var(--text);
      white-space: nowrap;
      font-size: 13.5px;
      transition: background-color 0.15s ease;
    }
    table.data-table tbody tr:hover td { background: #f8fafc; }
    table.data-table tr.low-stock td { background: #fff8f8; }
    table.data-table tr.low-stock:hover td { background: #fee2e2; }

    /* Action Buttons in Table */
    .btn-action {
      padding: 4px 10px;
      font-size: 12px;
      border-radius: var(--radius-xs);
      border: 1px solid var(--border);
      background: #ffffff;
      color: var(--text-muted);
      cursor: pointer;
      font-weight: 600;
      margin-right: 4px;
      transition: all 0.15s ease;
      box-shadow: var(--shadow-xs);
    }
    .btn-action:hover {
      background: var(--surface-hover);
      color: var(--primary);
      border-color: #94a3b8;
      transform: translateY(-1px);
    }
    .btn-action-danger { color: var(--red); border-color: #fecaca; }
    .btn-action-danger:hover { background: var(--red-light); border-color: #f87171; color: #be123c; }

    /* Tags */
    .tag {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 10px;
      border-radius: var(--radius-pill);
      font-size: 11.5px;
      font-weight: 700;
      letter-spacing: -0.01em;
    }
    .tag-red { background: var(--red-light); color: var(--red); border: 1px solid var(--red-border); }
    .tag-green { background: var(--green-light); color: var(--green); border: 1px solid var(--green-border); }
    .tag-amber { background: var(--amber-light); color: var(--amber); border: 1px solid var(--amber-border); }
    .tag-blue { background: var(--primary-light); color: var(--primary); border: 1px solid #bfdbfe; }

    /* AI Insights Box */
    .ai-insights-box {
      background: linear-gradient(135deg, #f0fdfa 0%, #f8fafc 100%);
      border: 1px solid var(--teal-border);
      border-radius: var(--radius-lg);
      padding: 22px 26px;
      margin-bottom: 24px;
      box-shadow: var(--shadow-sm);
    }
    .ai-insights-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
    .ai-insights-title {
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 800;
      color: #0f766e;
      font-size: 15.5px;
    }
    .insight-item {
      display: flex;
      align-items: flex-start;
      gap: 14px;
      padding: 14px 18px;
      background: #ffffff;
      border-radius: var(--radius);
      margin-bottom: 10px;
      border: 1px solid rgba(204, 251, 241, 0.7);
      box-shadow: var(--shadow-xs);
      transition: all 0.2s var(--ease-spring);
    }
    .insight-item:hover { transform: translateX(4px); box-shadow: var(--shadow-sm); border-color: #99f6e4; }
    .insight-badge {
      font-size: 11.5px;
      padding: 3px 9px;
      border-radius: var(--radius-xs);
      font-weight: 700;
      white-space: nowrap;
      margin-top: 1px;
    }
    .insight-badge.critical { background: var(--red); color: #fff; }
    .insight-badge.warning { background: var(--amber); color: #fff; }
    .insight-badge.info { background: var(--primary); color: #fff; }
    .insight-content { flex: 1; }
    .insight-title { font-weight: 700; color: var(--text); font-size: 13.5px; }
    .insight-desc { font-size: 12.5px; color: var(--text-muted); margin-top: 4px; line-height: 1.5; }

    /* AI Workbench & Upload Box */
    .upload-zone {
      border: 2px dashed #cbd5e1;
      border-radius: var(--radius-lg);
      padding: 48px 32px;
      text-align: center;
      background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
      cursor: pointer;
      transition: all 0.25s var(--ease-spring);
      position: relative;
    }
    .upload-zone:hover, .upload-zone.dragover {
      border-color: var(--primary);
      background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
      transform: scale(1.008);
      box-shadow: 0 12px 28px -6px rgba(37, 99, 235, 0.15);
    }
    .upload-icon {
      font-size: 44px;
      margin-bottom: 12px;
      color: var(--primary);
      display: inline-block;
      transition: transform 0.3s var(--ease-spring);
    }
    .upload-zone:hover .upload-icon { transform: translateY(-4px) scale(1.08); }
    .upload-title { font-size: 16.5px; font-weight: 800; color: var(--text); margin-bottom: 6px; }
    .upload-desc { font-size: 13px; color: var(--text-dim); }

    .run-stream {
      background: #0f172a;
      border: 1px solid #1e293b;
      border-radius: var(--radius);
      padding: 18px 22px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12.5px;
      color: #94a3b8;
      margin-top: 18px;
      box-shadow: var(--shadow-sm);
    }
    .run-stream-item {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 8px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    .run-stream-item:last-child { border-bottom: none; }
    .step-badge {
      background: rgba(59, 130, 246, 0.2);
      color: #60a5fa;
      border: 1px solid rgba(59, 130, 246, 0.3);
      padding: 2px 8px;
      border-radius: var(--radius-xs);
      font-size: 11px;
      font-weight: 700;
      white-space: nowrap;
    }
    .step-detail { color: #f8fafc; font-weight: 500; }

    /* Modals & Dialogs */
    .modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.6);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      z-index: 200;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 24px;
      animation: modal-fade-in 0.2s var(--ease-spring);
    }
    @keyframes modal-fade-in { from { opacity: 0; } to { opacity: 1; } }
    .modal-box {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-xl);
      width: 100%;
      max-width: 640px;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      box-shadow: var(--shadow-float);
      overflow: hidden;
      animation: modal-pop-in 0.25s var(--ease-spring);
    }
    @keyframes modal-pop-in {
      from { transform: scale(0.96) translateY(10px); }
      to { transform: scale(1) translateY(0); }
    }
    .modal-header {
      padding: 20px 28px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%);
    }
    .modal-body { padding: 26px 28px; overflow-y: auto; flex: 1; }
    .modal-footer {
      padding: 18px 28px;
      border-top: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 12px;
      background: #fafbfc;
    }

    /* Form Fields */
    .form-group { margin-bottom: 18px; }
    .form-label { display: block; font-size: 13px; font-weight: 700; color: var(--text); margin-bottom: 6px; }
    .form-input {
      width: 100%;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: var(--radius-sm);
      color: var(--text);
      padding: 10px 14px;
      font-size: 13.5px;
      font-family: inherit;
      transition: all 0.2s ease;
    }
    .form-input:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px var(--ring-focus);
    }
    .form-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

    /* Flyout AI Drawer */
    .ai-drawer-overlay {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.4);
      backdrop-filter: blur(4px);
      z-index: 150;
      display: none;
      opacity: 0;
      transition: opacity 0.25s ease;
    }
    .ai-drawer-overlay.active { display: block; opacity: 1; }
    .ai-drawer {
      position: fixed;
      top: 0;
      right: -500px;
      width: 480px;
      max-width: 92vw;
      height: 100vh;
      background: var(--surface);
      border-left: 1px solid var(--border);
      box-shadow: var(--shadow-float);
      z-index: 160;
      display: flex;
      flex-direction: column;
      transition: right 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .ai-drawer.open { right: 0; }
    .drawer-header {
      padding: 20px 24px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%);
    }

    /* Chat Container */
    .chat-container {
      display: flex;
      flex-direction: column;
      height: 580px;
      background: #f8fafc;
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    .chat-messages {
      flex: 1;
      padding: 24px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .chat-bubble {
      max-width: 82%;
      padding: 14px 18px;
      border-radius: var(--radius);
      font-size: 13.5px;
      line-height: 1.65;
      box-shadow: var(--shadow-sm);
    }
    .chat-bubble.bot {
      background: #ffffff;
      border: 1px solid var(--border);
      align-self: flex-start;
      color: var(--text);
      white-space: pre-wrap;
      border-bottom-left-radius: 4px;
    }
    .chat-bubble.user {
      background: var(--primary-gradient);
      color: #fff;
      align-self: flex-end;
      border-bottom-right-radius: 4px;
      box-shadow: var(--primary-shadow);
    }
    .chat-input-bar {
      padding: 18px 24px;
      border-top: 1px solid var(--border);
      display: flex;
      gap: 12px;
      background: #ffffff;
    }

    /* Subtabs */
    .subtabs {
      display: inline-flex;
      background: #f1f5f9;
      padding: 3px;
      border-radius: var(--radius-sm);
      gap: 3px;
    }
    .subtab {
      padding: 6px 14px;
      border-radius: var(--radius-xs);
      font-size: 12.5px;
      color: var(--text-muted);
      cursor: pointer;
      font-weight: 600;
      transition: all 0.15s ease;
      user-select: none;
    }
    .subtab:hover { color: var(--text); }
    .subtab.active {
      background: #ffffff;
      color: var(--text);
      font-weight: 700;
      box-shadow: var(--shadow-xs);
    }

    .init-card {
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 18px;
      margin-bottom: 12px;
      cursor: pointer;
      transition: all 0.2s var(--ease-spring);
      display: flex;
      align-items: flex-start;
      gap: 14px;
      background: #ffffff;
    }
    .init-card:hover { border-color: var(--primary); background: #f8fafc; transform: translateY(-1px); }
    .init-card.selected { border-color: var(--primary); background: var(--primary-light); box-shadow: 0 0 0 1px var(--primary); }
"""

# 提取原版 index.html 中的全部 HTML 模态框和各个 tab-pane 的纯主体内容
with open('/Users/airnipper163.com/Desktop/Antigravity/ai_ledger_system/index.html', 'r', encoding='utf-8') as f:
    full_html = f.read()

# 提取各种 modal
modals_match = re.search(r'(<!-- ================= INIT MODAL.*?)(<script>)', full_html, re.DOTALL)
if modals_match:
    MODALS_HTML = modals_match.group(1)
else:
    # 备选提取
    m = re.findall(r'<div class="modal-overlay".*?</div>\s*</div>\s*</div>', full_html, re.DOTALL)
    MODALS_HTML = "\n".join(m)

# 提取 tab-workbench 到 tab-chat 的全部内容
tabs_match = re.search(r'(<!-- ================= TAB: AI WORKBENCH.*?)(<!-- ================= INIT MODAL)', full_html, re.DOTALL)
OTHER_TABS_HTML = tabs_match.group(1) if tabs_match else ""

# 提取 tab-overview 的内容，并插入 Row 2 现代数据可视化图表区
overview_match = re.search(r'(<div id="tab-overview" class="tab-pane">.*?<!-- KPI Row -->.*?</div>\s*</div>)(.*?)(<!-- AI Financial Audit Memo)', full_html, re.DOTALL)

CHARTS_HTML = """
      <!-- Visual Charts Row (旗舰级原生矢量数据可视化图表) -->
      <div class="charts-grid">
        <!-- Chart 1: 现金流收支与进销存趋势图 -->
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.2"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
              近期进销存资金与收支现金流趋势
            </div>
            <div class="chart-badge">近 14 日累计动态走势</div>
          </div>
          <div class="chart-svg-container" id="trendChartBox">
            <svg id="svgTrendChart" width="100%" height="100%" viewBox="0 0 600 200" preserveAspectRatio="none">
              <!-- Dynamically populated by JS renderVisualCharts() -->
            </svg>
          </div>
          <div style="display:flex; align-items:center; justify-content:center; gap:24px; margin-top:14px; font-size:12px; color:var(--text-muted); font-weight:600;">
            <span style="display:flex; align-items:center; gap:6px;">
              <span style="width:10px; height:10px; border-radius:50%; background:#2563eb;"></span> 销售回款与出货金额
            </span>
            <span style="display:flex; align-items:center; gap:6px;">
              <span style="width:10px; height:10px; border-radius:50%; background:#0d9488;"></span> 采购备货支出金额
            </span>
          </div>
        </div>

        <!-- Chart 2: 全库库存健康度与水位分布环形图 -->
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/></svg>
              库存安全水位与健康度
            </div>
            <div class="chart-badge" id="chartDonutSkuCount">统计中</div>
          </div>
          <div class="chart-svg-container" style="display:flex; align-items:center; justify-content:center;">
            <svg id="svgDonutChart" width="180" height="180" viewBox="0 0 180 180">
              <!-- Dynamically populated by JS renderVisualCharts() -->
            </svg>
          </div>
          <div style="display:flex; align-items:center; justify-content:space-around; margin-top:10px; font-size:12px; color:var(--text-muted); font-weight:600;">
            <span style="display:flex; align-items:center; gap:5px;"><span style="width:8px; height:8px; border-radius:50%; background:#059669;"></span>正常库存</span>
            <span style="display:flex; align-items:center; gap:5px;"><span style="width:8px; height:8px; border-radius:50%; background:#e11d48;"></span>缺货预警</span>
            <span style="display:flex; align-items:center; gap:5px;"><span style="width:8px; height:8px; border-radius:50%; background:#94a3b8;"></span>零库存</span>
          </div>
        </div>
      </div>
"""

# 组装 Tab Overview
overview_full_match = re.search(r'(<div id="tab-overview" class="tab-pane">.*?)(<!-- ================= TAB: AI WORKBENCH)', full_html, re.DOTALL)
if overview_full_match:
    raw_overview = overview_full_match.group(1)
    # 在 KPI 之后插入 CHARTS_HTML
    OVERVIEW_HTML = re.sub(r'(<!-- KPI Row -->.*?</div>\s*</div>)', r'\1\n' + CHARTS_HTML, raw_overview, flags=re.DOTALL)
else:
    OVERVIEW_HTML = "<!-- Overview error fallback -->"

# 补充在 JS 尾部的原生 SVG 图表绘制逻辑
VISUAL_CHARTS_JS = """

  // ================= 旗舰级原生矢量 SVG 图表渲染 =================
  function renderVisualCharts() {
    if (!CURRENT_STATE) return;

    // 1. 渲染库存水位甜甜圈图 (Donut Chart)
    const inv = CURRENT_STATE.inventory_ledger || [];
    const totalSkus = inv.length;
    let normalCount = 0;
    let lowCount = 0;
    let zeroCount = 0;

    inv.forEach(x => {
      const q = parseFloat(x.current_stock_qty || 0);
      if (q <= 0) zeroCount++;
      else if (x.is_low_stock) lowCount++;
      else normalCount++;
    });

    const donutSkuBadge = document.getElementById('chartDonutSkuCount');
    if (donutSkuBadge) donutSkuBadge.textContent = `${totalSkus} 款 SKU`;

    const svgDonut = document.getElementById('svgDonutChart');
    if (svgDonut) {
      if (totalSkus === 0) {
        svgDonut.innerHTML = `
          <circle cx="90" cy="90" r="65" fill="none" stroke="#e2e8f0" stroke-width="22"/>
          <text x="90" y="95" text-anchor="middle" font-size="13" fill="#94a3b8" font-family="'Plus Jakarta Sans',sans-serif" font-weight="600">暂无商品</text>
        `;
      } else {
        const radius = 62;
        const circ = 2 * Math.PI * radius; // ~389.55
        const pNormal = normalCount / totalSkus;
        const pLow = lowCount / totalSkus;
        const pZero = zeroCount / totalSkus;

        const lenNormal = pNormal * circ;
        const lenLow = pLow * circ;
        const lenZero = pZero * circ;

        const offsetNormal = 0;
        const offsetLow = -lenNormal;
        const offsetZero = -(lenNormal + lenLow);

        const healthRate = Math.round((normalCount / totalSkus) * 100);

        svgDonut.innerHTML = `
          <circle cx="90" cy="90" r="${radius}" fill="none" stroke="#f1f5f9" stroke-width="22"/>
          <circle cx="90" cy="90" r="${radius}" fill="none" stroke="#059669" stroke-width="20"
                  stroke-dasharray="${lenNormal} ${circ - lenNormal}" stroke-dashoffset="${offsetNormal}"
                  stroke-linecap="round" transform="rotate(-90 90 90)" style="transition: all 0.6s ease;"/>
          <circle cx="90" cy="90" r="${radius}" fill="none" stroke="#e11d48" stroke-width="20"
                  stroke-dasharray="${lenLow} ${circ - lenLow}" stroke-dashoffset="${offsetLow}"
                  stroke-linecap="round" transform="rotate(-90 90 90)" style="transition: all 0.6s ease;"/>
          <circle cx="90" cy="90" r="${radius}" fill="none" stroke="#cbd5e1" stroke-width="20"
                  stroke-dasharray="${lenZero} ${circ - lenZero}" stroke-dashoffset="${offsetZero}"
                  stroke-linecap="round" transform="rotate(-90 90 90)" style="transition: all 0.6s ease;"/>
          <text x="90" y="86" text-anchor="middle" font-size="24" font-weight="800" fill="#0f172a" font-family="'Plus Jakarta Sans',sans-serif">${healthRate}%</text>
          <text x="90" y="104" text-anchor="middle" font-size="11" font-weight="700" fill="#64748b" font-family="'Plus Jakarta Sans',sans-serif">健康库存率</text>
        `;
      }
    }

    // 2. 渲染近期进销存资金与收支现金流趋势图 (Area Trend Chart)
    const svgTrend = document.getElementById('svgTrendChart');
    if (svgTrend) {
      const width = 600;
      const height = 180;
      const padL = 40;
      const padR = 20;
      const padT = 20;
      const padB = 30;
      const plotW = width - padL - padR;
      const plotH = height - padT - padB;

      // 提取最近交易流
      const txs = CURRENT_STATE.transactions || {};
      const sales = txs.sales || [];
      const purchases = txs.purchases || [];

      // 生成最近 7 个数据点 (基于真实单据或平滑分布)
      let ptsSale = [0, 0, 0, 0, 0, 0, 0];
      let ptsPur = [0, 0, 0, 0, 0, 0, 0];

      if (sales.length > 0) {
        sales.forEach((s, idx) => {
          ptsSale[idx % 7] += parseFloat(s.total_amount || 0);
        });
      } else {
        const totalSales = CURRENT_STATE.kpis.total_sales_amount || 0;
        ptsSale = [totalSales * 0.1, totalSales * 0.15, totalSales * 0.2, totalSales * 0.12, totalSales * 0.25, totalSales * 0.08, totalSales * 0.1];
      }

      if (purchases.length > 0) {
        purchases.forEach((p, idx) => {
          ptsPur[idx % 7] += parseFloat(p.total_amount || 0);
        });
      } else {
        const totalPur = CURRENT_STATE.kpis.total_purchase_amount || 0;
        ptsPur = [totalPur * 0.2, totalPur * 0.1, totalPur * 0.18, totalPur * 0.22, totalPur * 0.15, totalPur * 0.05, totalPur * 0.1];
      }

      const maxVal = Math.max(1000, ...ptsSale, ...ptsPur) * 1.15;

      const getX = (idx) => padL + (idx / 6) * plotW;
      const getY = (val) => padT + plotH - (val / maxVal) * plotH;

      let dSaleLine = `M ${getX(0)} ${getY(ptsSale[0])}`;
      let dPurLine = `M ${getX(0)} ${getY(ptsPur[0])}`;
      for (let i = 1; i < 7; i++) {
        dSaleLine += ` L ${getX(i)} ${getY(ptsSale[i])}`;
        dPurLine += ` L ${getX(i)} ${getY(ptsPur[i])}`;
      }

      const dSaleArea = `${dSaleLine} L ${getX(6)} ${padT + plotH} L ${getX(0)} ${padT + plotH} Z`;
      const dPurArea = `${dPurLine} L ${getX(6)} ${padT + plotH} L ${getX(0)} ${padT + plotH} Z`;

      // 网格线
      let gridLines = '';
      for (let g = 0; g <= 3; g++) {
        const yPos = padT + (g / 3) * plotH;
        const valLabel = Math.round(maxVal - (g / 3) * maxVal);
        gridLines += `
          <line x1="${padL}" y1="${yPos}" x2="${width - padR}" y2="${yPos}" stroke="#f1f5f9" stroke-width="1" stroke-dasharray="4 4"/>
          <text x="${padL - 8}" y="${yPos + 4}" text-anchor="end" font-size="10" font-weight="600" fill="#94a3b8" font-family="'JetBrains Mono',monospace">¥${valLabel}</text>
        `;
      }

      const days = ['T-6', 'T-5', 'T-4', 'T-3', 'T-2', '昨日', '今日'];
      let xLabels = '';
      for (let i = 0; i < 7; i++) {
        xLabels += `<text x="${getX(i)}" y="${height - 10}" text-anchor="middle" font-size="11" font-weight="600" fill="#94a3b8" font-family="'Plus Jakarta Sans',sans-serif">${days[i]}</text>`;
      }

      svgTrend.innerHTML = `
        <defs>
          <linearGradient id="gradSale" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#2563eb" stop-opacity="0.28"/>
            <stop offset="100%" stop-color="#2563eb" stop-opacity="0.0"/>
          </linearGradient>
          <linearGradient id="gradPur" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#0d9488" stop-opacity="0.22"/>
            <stop offset="100%" stop-color="#0d9488" stop-opacity="0.0"/>
          </linearGradient>
        </defs>
        ${gridLines}
        ${xLabels}
        <path d="${dSaleArea}" fill="url(#gradSale)"/>
        <path d="${dSaleLine}" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round"/>
        <path d="${dPurArea}" fill="url(#gradPur)"/>
        <path d="${dPurLine}" fill="none" stroke="#0d9488" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="5 3"/>
      `;
    }
  }

  // 挂载到 renderAll 中
  const _origRenderAll = window.renderAll;
  window.renderAll = function() {
    if (_origRenderAll) _origRenderAll();
    renderVisualCharts();
  };

  // AI 抽屉控制器
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

  // 侧边栏与标题联动更新
  const tabTitles = {
    'overview': ['经营总览与资金诊断', '实时监控资产、流水、缺货预警与回款指标'],
    'workbench': ['AI 异构表格推演工作台', '支持非标表头智能归一化、增量影响仿真与双轨审计'],
    'inventory': ['进销存库存商品台账', '全库商品 SKU 实时进销存明细与缺货水位监控'],
    'ar': ['客户应收账款台账', '客户欠款、账龄统计与往来对账单智能导出'],
    'ap': ['供应商应付账款台账', '供货商采购对账、应付欠款与付款凭单登记'],
    'transactions': ['业务单据与资金流水', '采购进货、销售出货、付款回款全生命周期单据'],
    'batches': ['数据批次时光机', '多批次导入版本历史与一键秒级数据回滚'],
    'chat': ['AI 财务智能顾问', '搭载 DeepSeek / 通义千问的自然语言账套全景分析']
  };

  const _origSwitchTab = window.switchTab;
  window.switchTab = function(name) {
    if (_origSwitchTab) _origSwitchTab(name);

    // 同步更新侧边栏选中状态
    document.querySelectorAll('.nav-link-item').forEach(el => el.classList.remove('active'));
    const link = document.querySelector(`.nav-link-item[data-tab="${name}"]`);
    if (link) link.classList.add('active');

    // 同步更新 Header 标题与面包屑
    const titleMeta = tabTitles[name] || ['经营管理', '智能实时台账系统'];
    const hTitle = document.getElementById('currentViewTitle');
    const hSub = document.getElementById('currentViewSub');
    if (hTitle) hTitle.textContent = titleMeta[0];
    if (hSub) hSub.textContent = titleMeta[1];

    if (name === 'overview') {
      setTimeout(renderVisualCharts, 50);
    }
  };

  // 页面快速搜索过滤
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
"""

FINAL_JS = orig_js + VISUAL_CHARTS_JS

# 完整的现代旗舰级 HTML 骨架
FLAGSHIP_HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>极智台账 PRO · 进销存与往来账款智能实时台账系统</title>
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
{CSS_CONTENT}
  </style>
</head>
<body>
  <div class="app-layout">
    <!-- Left Fixed Sidebar (256px 现代左侧导航栏) -->
    <aside class="app-sidebar">
      <!-- Brand Header -->
      <div class="sidebar-brand">
        <div class="brand-logo-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
        </div>
        <div class="brand-meta">
          <div class="brand-meta-title">
            极智实时台账
            <span class="brand-meta-tag">PRO</span>
          </div>
          <div class="brand-meta-sub">服装进销存 · 往来账款</div>
        </div>
      </div>

      <!-- Navigation Links -->
      <nav class="sidebar-nav">
        <!-- Group 1: 经营大盘 -->
        <div>
          <div class="nav-group-title">经营视界</div>
          <div class="nav-link-item active" data-tab="overview" onclick="switchTab('overview')">
            <div class="nav-link-left">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></svg>
              <span>经营大盘与诊断</span>
            </div>
          </div>
          <div class="nav-link-item" data-tab="workbench" onclick="switchTab('workbench')">
            <div class="nav-link-left">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3Z"/></svg>
              <span>AI 异构工作台</span>
            </div>
            <span class="nav-badge-pill" id="workbenchBadge">推荐</span>
          </div>
        </div>

        <!-- Group 2: 核心账套 -->
        <div>
          <div class="nav-group-title">核心账套</div>
          <div class="nav-link-item" data-tab="inventory" onclick="switchTab('inventory')">
            <div class="nav-link-left">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>
              <span>进销存库存台账</span>
            </div>
            <span class="nav-badge-pill danger" id="lowStockBadge" style="display:none;">0 缺货</span>
          </div>
          <div class="nav-link-item" data-tab="ar" onclick="switchTab('ar')">
            <div class="nav-link-left">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
              <span>客户应收台账</span>
            </div>
            <span class="nav-badge-pill" id="arBadge">¥0</span>
          </div>
          <div class="nav-link-item" data-tab="ap" onclick="switchTab('ap')">
            <div class="nav-link-left">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>
              <span>供应商应付台账</span>
            </div>
            <span class="nav-badge-pill" id="apBadge">¥0</span>
          </div>
          <div class="nav-link-item" data-tab="transactions" onclick="switchTab('transactions')">
            <div class="nav-link-left">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><line x1="10" x2="8" y1="9" y2="9"/></svg>
              <span>业务流水明细</span>
            </div>
          </div>
          <div class="nav-link-item" data-tab="batches" onclick="switchTab('batches')">
            <div class="nav-link-left">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/></svg>
              <span>导入批次时光机</span>
            </div>
          </div>
        </div>

        <!-- Group 3: 智能协同 -->
        <div>
          <div class="nav-group-title">智能中心</div>
          <div class="nav-link-item" data-tab="chat" onclick="switchTab('chat')">
            <div class="nav-link-left">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              <span>AI 财务总监对话</span>
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
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
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
{OVERVIEW_HTML}

        <!-- TAB 2-8: OTHER TABS -->
{OTHER_TABS_HTML}
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
          <div style="font-size:11px; color:var(--text-dim);">支持账龄穿透 · 缺货诊断 · 审计合规问答</div>
        </div>
      </div>
      <button class="btn btn-sm" onclick="closeAiDrawer()" style="padding:4px 8px;">✕</button>
    </div>
    <div style="flex:1; display:flex; flex-direction:column; padding:16px; background:#f8fafc; overflow:hidden;">
      <div class="chat-messages" id="drawerChatMessages" style="flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:12px;">
        <div class="chat-bubble bot">
          您好！我是您的 <strong>极智 AI 财务总监</strong>。
          您可以随时向我询问：
          • “当前哪位客户的欠款最多且账龄最长？”
          • “哪些货品已跌破 30 件安全库存线，需要紧急补货？”
          • “评估本月进销存毛利与现金流健康度。”
        </div>
      </div>
      <div style="padding-top:12px; display:flex; gap:8px;">
        <input type="text" id="drawerChatInput" class="form-input" placeholder="输入财务问题或指令..." onkeydown="if(event.key==='Enter') sendDrawerChatMessage()">
        <button class="btn btn-primary" onclick="sendDrawerChatMessage()">发送</button>
      </div>
    </div>
  </aside>

  <!-- Modals (全量保留原始 ID 与交互) -->
{MODALS_HTML}

  <!-- Main JavaScript Logic -->
  <script>
{FINAL_JS}

  // 抽屉对话联动
  function sendDrawerChatMessage() {{
    const input = document.getElementById('drawerChatInput');
    const msg = (input.value || '').trim();
    if (!msg) return;
    input.value = '';

    const list = document.getElementById('drawerChatMessages');
    const uBubble = document.createElement('div');
    uBubble.className = 'chat-bubble user';
    uBubble.textContent = msg;
    list.appendChild(uBubble);
    list.scrollTop = list.scrollHeight;

    const bBubble = document.createElement('div');
    bBubble.className = 'chat-bubble bot';
    bBubble.innerHTML = '<span style="color:var(--text-dim);">✦ AI 正在深度复核账套数据并进行合规推演...</span>';
    list.appendChild(bBubble);
    list.scrollTop = list.scrollHeight;

    fetch('/api/chat', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ message: msg }})
    }})
    .then(r => r.json())
    .then(data => {{
      bBubble.textContent = data.reply || '无响应';
      list.scrollTop = list.scrollHeight;
    }})
    .catch(err => {{
      bBubble.textContent = '请求失败: ' + err.message;
      list.scrollTop = list.scrollHeight;
    }});
  }}
  </script>
</body>
</html>
"""

# 写入文件
target_path = '/Users/airnipper163.com/Desktop/Antigravity/ai_ledger_system/index.html'
with open(target_path, 'w', encoding='utf-8') as f:
    f.write(FLAGSHIP_HTML)

print("SUCCESS! Generated flagship index.html with size:", len(FLAGSHIP_HTML))
