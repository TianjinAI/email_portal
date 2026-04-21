#!/usr/bin/env python3
"""
Email Monitor Web Portal V3 - Account-based view, expandable summaries.
"""

from flask import Flask, render_template_string, jsonify, request
import sqlite3
from datetime import datetime, date
from pathlib import Path
import os
import re
import subprocess
import json
import urllib.request
import urllib.error

app = Flask(__name__)

DB_PATH = str(Path.home() / ".hermes" / "email-monitor" / "emails.db")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="300">
    <title>Email Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            /* Light theme colors */
            --bg-canvas: #f8f9fa;
            --bg-panel: #ffffff;
            --bg-surface: #f1f3f4;
            --bg-surface-2: rgba(0,0,0,0.03);
            --bg-surface-3: rgba(0,0,0,0.06);
            --text-primary: #1a1a2e;
            --text-secondary: #4a4a5a;
            --text-muted: #6b7280;
            --text-subtle: #9ca3af;
            --border-subtle: rgba(0,0,0,0.08);
            --border-strong: rgba(0,0,0,0.12);
            --accent: #4f46e5;
            --accent-hover: #4338ca;
            --urgent-red: #dc2626;
            --urgent-bg: rgba(220,38,38,0.08);
            --important-orange: #ea580c;
            --important-bg: rgba(234,88,12,0.08);
            --newsletter-green: #16a34a;
            --newsletter-bg: rgba(22,163,74,0.08);
            --gmail-color: #ea4335;
            --yahoo-color: #6001d2;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-canvas);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            font-feature-settings: 'cv01', 'ss03';
        }
        
        /* Top Header */
        .top-header {
            background: var(--bg-panel);
            border-bottom: 1px solid var(--border-subtle);
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .current-date {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
        }

        .date-picker {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 4px 8px;
            background: var(--bg-surface-2);
            border: 1px solid var(--border-subtle);
            border-radius: 6px;
        }

        .date-select {
            padding: 4px 8px;
            border: 1px solid var(--border-strong);
            border-radius: 4px;
            background: var(--bg-surface);
            font-size: 12px;
            color: var(--text-primary);
        }

        .refresh-btn {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 6px 12px;
            background: var(--bg-surface-2);
            color: var(--text-secondary);
            border: 1px solid var(--border-subtle);
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s;
        }
        
        .refresh-btn:hover {
            background: var(--bg-surface-3);
            color: var(--text-primary);
        }
        
        .last-sync {
            font-size: 11px;
            color: var(--text-subtle);
        }
        
        /* Stats Bar - Compact */
        .stats-bar {
            display: flex;
            gap: 16px;
            padding: 8px 20px;
            background: var(--bg-panel);
            border-bottom: 1px solid var(--border-subtle);
        }
        
        .stat-item {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .stat-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }
        
        .stat-dot.urgent { background: var(--urgent-red); }
        .stat-dot.important { background: var(--important-orange); }
        .stat-dot.newsletter { background: var(--newsletter-green); }
        
        .stat-number {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .stat-label {
            font-size: 11px;
            color: var(--text-muted);
        }
        
        /* Dashboard Layout */
        .dashboard-container {
            display: grid;
            grid-template-columns: 1fr 280px;
            gap: 16px;
            padding: 16px 20px;
            max-width: 1600px;
            margin: 0 auto;
        }
        
        /* Summary Section */
        .summary-section {
            background: var(--bg-panel);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 16px;
        }
        
        .summary-header {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        
        .summary-content {
            font-size: 12px;
            line-height: 1.5;
            color: var(--text-secondary);
        }
        
        .todo-list {
            margin-top: 8px;
            padding-left: 16px;
        }
        
        .todo-list li {
            font-size: 12px;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }
        
        /* Sidebar */
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .sidebar-card {
            background: var(--bg-panel);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            padding: 12px;
        }
        
        .sidebar-title {
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        /* Weather Section */
        .weather-display {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .weather-icon-large {
            font-size: 32px;
        }
        
        .weather-info {
            flex: 1;
        }
        
        .weather-temp-large {
            font-size: 20px;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .weather-detail {
            font-size: 11px;
            color: var(--text-muted);
        }
        
        /* Calendar Section */
        .calendar-events {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        
        .calendar-event {
            padding: 6px 8px;
            background: var(--bg-surface-2);
            border-radius: 4px;
            border-left: 2px solid var(--accent);
        }
        
        .event-time {
            font-size: 10px;
            color: var(--text-muted);
            font-weight: 500;
        }
        
        .event-title {
            font-size: 12px;
            color: var(--text-primary);
            font-weight: 500;
        }
        
        .event-location {
            font-size: 10px;
            color: var(--text-subtle);
        }
        
        /* Main Content */
        .main-content {
            display: flex;
            flex-direction: column;
        }

        #accounts-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 10px;
        }
        
        /* Account Buckets - Top Level */
        .account-bucket {
            margin: 0 0 16px 0;
            background: var(--bg-panel);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .account-bucket-header {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            cursor: pointer;
            transition: all 0.15s ease;
            user-select: none;
            background: var(--bg-surface-2);
            border-bottom: 1px solid var(--border-subtle);
        }
        
        .account-bucket-header:hover {
            background: var(--bg-surface-3);
        }
        
        .account-bucket.collapsed .account-bucket-header {
            border-bottom: none;
        }
        
        .account-bucket-avatar {
            width: 32px;
            height: 32px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 12px;
            background: var(--account-color, var(--accent));
        }
        
        .account-bucket-name {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .account-bucket-count {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-primary);
            background: var(--bg-surface);
            padding: 2px 10px;
            border-radius: 12px;
            margin-left: auto;
        }
        
        .account-bucket-toggle {
            font-size: 12px;
            color: var(--text-muted);
            transition: transform 0.2s ease;
        }
        
        .account-bucket.collapsed .account-bucket-toggle {
            transform: rotate(-90deg);
        }
        
        .account-bucket-content {
            padding: 12px;
        }
        
        .account-bucket.collapsed .account-bucket-content {
            display: none;
        }
        
        /* Category Sub-groups within Account */
        .category-subgroup {
            margin: 0 0 12px 0;
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 6px;
            overflow: hidden;
        }
        
        .category-subgroup:last-child {
            margin-bottom: 0;
        }
        
        .category-subgroup-header {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            cursor: pointer;
            transition: background 0.15s ease;
            user-select: none;
        }
        
        .category-subgroup-header:hover {
            background: var(--bg-surface-2);
        }
        
        .category-subgroup-icon {
            font-size: 14px;
        }
        
        .category-subgroup-name {
            font-size: 12px;
            font-weight: 600;
            text-transform: capitalize;
        }
        
        .category-subgroup-count {
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
            background: var(--bg-panel);
            padding: 1px 6px;
            border-radius: 10px;
            margin-left: auto;
        }
        
        .category-subgroup-toggle {
            font-size: 10px;
            color: var(--text-muted);
            transition: transform 0.2s ease;
        }
        
        .category-subgroup.collapsed .category-subgroup-toggle {
            transform: rotate(-90deg);
        }
        
        .category-subgroup-emails {
            padding: 8px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        
        .category-subgroup.collapsed .category-subgroup-emails {
            display: none;
        }
        
        /* Category-specific colors for subgroups */
        .category-subgroup.urgent-subgroup .category-subgroup-header {
            background: rgba(220,38,38,0.08);
            border-left: 3px solid var(--urgent-red);
        }
        .category-subgroup.urgent-subgroup .category-subgroup-name { color: var(--urgent-red); }
        
        .category-subgroup.important-subgroup .category-subgroup-header {
            background: rgba(234,88,12,0.08);
            border-left: 3px solid var(--important-orange);
        }
        .category-subgroup.important-subgroup .category-subgroup-name { color: var(--important-orange); }
        
        .category-subgroup.normal-subgroup .category-subgroup-header {
            background: rgba(79,70,229,0.05);
            border-left: 3px solid var(--accent);
        }
        .category-subgroup.normal-subgroup .category-subgroup-name { color: var(--accent); }
        
        .category-subgroup.newsletter-subgroup .category-subgroup-header {
            background: rgba(22,163,74,0.08);
            border-left: 3px solid var(--newsletter-green);
        }
        .category-subgroup.newsletter-subgroup .category-subgroup-name { color: var(--newsletter-green); }
        
        .category-subgroup.spam-subgroup .category-subgroup-header {
            background: rgba(107,114,128,0.08);
            border-left: 3px solid var(--text-muted);
        }
        .category-subgroup.spam-subgroup .category-subgroup-name { color: var(--text-muted); }
        
        /* Email List */
        .email-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        
        .email-card {
            background: var(--bg-surface-2);
            border-radius: 6px;
            border: 1px solid var(--border-subtle);
            overflow: hidden;
            transition: all 0.15s ease;
        }

        .email-card:hover {
            border-color: var(--accent);
            box-shadow: 0 1px 4px rgba(0,0,0,0.1);
        }

        .email-card.urgent-card {
            border-left: 2px solid var(--urgent-red);
            background: var(--urgent-bg);
        }

        .email-card.important-card {
            border-left: 2px solid var(--important-orange);
            background: var(--important-bg);
        }
        
        .email-header {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            padding: 8px 10px;
            cursor: pointer;
        }
        
        .sender-avatar {
            width: 32px;
            height: 32px;
            border-radius: 6px;
            background: var(--bg-surface-3);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: 600;
            color: var(--text-primary);
            flex-shrink: 0;
        }
        
        .email-body {
            flex: 1;
            min-width: 0;
        }
        
        .email-subject {
            font-size: 13px;
            font-weight: 500;
            color: var(--text-primary);
            margin-bottom: 2px;
            line-height: 1.3;
        }
        
        .email-meta {
            display: flex;
            gap: 8px;
            font-size: 11px;
            color: var(--text-muted);
            align-items: center;
        }
        
        .email-sender {
            font-weight: 500;
        }
        
        .account-badge {
            padding: 1px 5px;
            border-radius: 3px;
            font-size: 9px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        
        .account-badge.gmail {
            background: linear-gradient(135deg, #ea4335, #4285f4);
            color: white;
        }
        
        .account-badge.yahoo {
            background: linear-gradient(135deg, #6001d2, #7b2cbf);
            color: white;
        }
        
        .email-right {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 4px;
            min-width: 50px;
        }
        
        .urgency-badge {
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 9px;
            font-weight: 600;
            background: var(--urgent-red);
            color: white;
        }
        
        .urgency-badge.high { background: var(--urgent-red); }
        .urgency-badge.medium { background: var(--important-orange); }
        .urgency-badge.low { background: var(--newsletter-green); }
        
        .email-time {
            font-size: 10px;
            color: var(--text-muted);
        }
        
        /* Expanded Summary */
        .email-summary {
            display: none;
            padding: 8px 10px 8px 50px;
            border-top: 1px solid var(--border-subtle);
            margin-top: 0;
            background: var(--bg-surface);
            max-height: 400px;
            overflow-y: auto;
        }
        
        .email-summary.visible {
            display: block;
        }
        
        .summary-label {
            font-size: 10px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }
        
        .summary-text {
            font-size: 12px;
            color: var(--text-secondary);
            line-height: 1.5;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .summary-loading {
            color: var(--text-muted);
            font-style: italic;
        }
        
        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 32px 24px;
            color: var(--text-muted);
        }
        
        .empty-icon {
            font-size: 32px;
            margin-bottom: 8px;
            opacity: 0.5;
        }
        
        .empty-text {
            font-size: 12px;
        }
        
        .hidden { display: none !important; }
        
        /* Mobile */
        @media (max-width: 768px) {
            .top-header {
                padding: 12px 16px;
                flex-wrap: wrap;
                gap: 12px;
            }
            .current-date {
                font-size: 18px;
            }
            .stats-bar {
                padding: 12px 16px;
                gap: 16px;
                overflow-x: auto;
            }
            .main-content {
                padding: 16px;
            }
            .email-header {
                padding: 12px 16px;
            }
            .email-summary {
                padding: 0 16px 12px 68px;
            }
        }
    </style>
</head>
<body>
    <div class="top-header">
        <div class="header-left">
            <div>
                <div class="current-date">Email Dashboard</div>
                <div class="last-sync" id="selected-date-text">Showing: {{ selected_date }}</div>
            </div>
            <div class="date-picker">
                <span style="font-size:13px;color:var(--text-muted);">Date</span>
                <select id="date-select" class="date-select" onchange="onDateChange(event)">
                    {% for d in available_dates %}
                    <option value="{{ d }}" {% if d == selected_date %}selected{% endif %}>{{ d }}</option>
                    {% endfor %}
                </select>
            </div>
            <button class="refresh-btn" type="button" onclick="refreshCurrentDate()">
                <span>&#8635;</span> Refresh
            </button>
        </div>
        <div class="last-sync" id="last-sync-text">Last sync: {{ last_refresh }}</div>
    </div>
    
    <div class="stats-bar">
        <div class="stat-item">
            <div class="stat-dot urgent"></div>
            <div class="stat-number" id="stat-urgent">{{ stats.urgent }}</div>
            <div class="stat-label">Urgent</div>
        </div>
        <div class="stat-item">
            <div class="stat-dot important"></div>
            <div class="stat-number" id="stat-important">{{ stats.important }}</div>
            <div class="stat-label">Important</div>
        </div>
        <div class="stat-item">
            <div class="stat-dot newsletter"></div>
            <div class="stat-number" id="stat-newsletter">{{ stats.newsletter }}</div>
            <div class="stat-label">Newsletters</div>
        </div>
        <div class="stat-item" style="margin-left: auto;">
            <div class="stat-number" id="stat-total">{{ total_count }}</div>
            <div class="stat-label" id="stat-total-label">Total</div>
        </div>
    </div>
    
    <!-- Dashboard Container -->
    <div class="dashboard-container">
        <!-- Main Content Area -->
        <div class="main-content">
            <!-- Email Summary Section -->
            <div class="summary-section">
                <div class="summary-header">📋 Daily Summary & Action Items</div>
                <div class="summary-content" id="summary-content">
                    {{ email_summary|safe }}
                </div>
            </div>
            
            <!-- Accounts Container -->
            <div id="accounts-container">
                {% for account in accounts %}
                <div class="account-bucket" id="account-{{ account.id }}">
                    <div class="account-bucket-header" onclick="toggleAccount('{{ account.id }}')">
                        <div class="account-bucket-avatar" style="--account-color: {{ account.color }}">{{ account.initial }}</div>
                        <div class="account-bucket-name">{{ account.email }}</div>
                        <div class="account-bucket-count">{{ account.count }}</div>
                        <div class="account-bucket-toggle">▼</div>
                    </div>
                    
                    <div class="account-bucket-content">
                        {% for cat_id, cat_data in account.categories.items() %}
                        {% if cat_data.count > 0 %}
                        <div class="category-subgroup {{ cat_id }}-subgroup" id="account-{{ account.id }}-cat-{{ cat_id }}">
                            <div class="category-subgroup-header" onclick="toggleCategorySubgroup('{{ account.id }}', '{{ cat_id }}')">
                                <span class="category-subgroup-icon">{{ cat_data.icon }}</span>
                                <span class="category-subgroup-name">{{ cat_id }}</span>
                                <span class="category-subgroup-count">{{ cat_data.count }}</span>
                                <span class="category-subgroup-toggle">▼</span>
                            </div>
                            <div class="category-subgroup-emails">
                                {% for email in cat_data.emails %}
                                <div class="email-card {{ email.category }}-card" 
                                     data-email-id="{{ email.email_id }}"
                                     onclick="toggleSummary('{{ email.email_id }}')">
                                    <div class="email-header">
                                        <div class="sender-avatar">{{ email.sender_initial }}</div>
                                        <div class="email-body">
                                            <div class="email-subject">{{ email.subject }}</div>
                                            <div class="email-meta">
                                                <span class="email-sender">{{ email.sender_name or 'Unknown' }}</span>
                                                <span class="email-time">{{ email.time_str }}</span>
                                            </div>
                                        </div>
                                        <div class="email-right">
                                            {% if email.urgency_score > 0 %}
                                            <div class="urgency-badge {{ email.urgency_class }}">{{ email.urgency_display }}</div>
                                            {% endif %}
                                        </div>
                                    </div>
                                    <div class="email-summary" id="summary-{{ email.email_id }}">
                                        <div class="summary-label">Summary</div>
                                        <div class="summary-text" id="summary-text-{{ email.email_id }}">
                                            {% if email.body %}
                                            {{ email.body }}
                                            {% else %}
                                            <span class="summary-loading">No content available</span>
                                            {% endif %}
                                        </div>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                        {% endif %}
                        {% endfor %}
                    </div>
                </div>
                {% endfor %}
            </div>
            
            {% if not accounts %}
            <div class="empty-state">
                <div class="empty-icon">&#128236;</div>
                <div class="empty-text">No emails for today</div>
            </div>
            {% endif %}
        </div>
        
        <!-- Sidebar -->
        <div class="sidebar">
            <!-- Weather Card -->
            <div class="sidebar-card">
                <div class="sidebar-title">🌤️ Weather</div>
                <div class="weather-display" id="weather-display">
                    <span class="weather-icon-large">{{ weather.icon }}</span>
                    <div class="weather-info">
                        <div class="weather-temp-large">{{ weather.temp }}°F</div>
                        <div class="weather-detail">{{ weather.condition }} in {{ weather.city }}</div>
                        {% if not weather.error %}
                        <div class="weather-detail">💧 {{ weather.humidity }}% | 💨 {{ weather.wind }} mph</div>
                        {% endif %}
                    </div>
                </div>
            </div>
            
            <!-- Calendar Card -->
            <div class="sidebar-card">
                <div class="sidebar-title">📅 Today's Events ({{ calendar.events|length }})</div>
                <div class="calendar-events" id="calendar-events">
                    {% if calendar.events %}
                        {% for event in calendar.events %}
                        <div class="calendar-event">
                            <div class="event-time">{{ event.time }}</div>
                            <div class="event-title">{{ event.summary }}</div>
                            {% if event.location %}
                            <div class="event-location">📍 {{ event.location }}</div>
                            {% endif %}
                        </div>
                        {% endfor %}
                    {% else %}
                        <div style="font-size: 12px; color: var(--text-muted); padding: 8px;">
                            {% if calendar.error %}
                                {{ calendar.error }}
                            {% else %}
                                No events scheduled
                            {% endif %}
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        async function toggleSummary(emailId) {
            const summaryEl = document.getElementById('summary-' + emailId);
            if (!summaryEl) return;

            // Lazy load body preview from API if not already loaded
            const summaryTextEl = document.getElementById('summary-text-' + emailId);
            const alreadyLoaded = summaryTextEl && summaryTextEl.dataset.loaded === 'true';

            summaryEl.classList.toggle('visible');

            if (alreadyLoaded || !summaryEl.classList.contains('visible')) {
                return;
            }

            if (summaryTextEl) {
                summaryTextEl.textContent = 'Loading summary...';
            }

            try {
                const res = await fetch(`/api/email/${encodeURIComponent(emailId)}`);
                const data = await res.json();
                let body = (data.body || '').replace(/\s+/g, ' ').trim();
                if (!body && data.subject) {
                    body = data.subject;
                }
                if (!body) {
                    body = 'No preview available';
                }
                // Show full body content with category selector and rule creation
                const senderEmail = escapeHtml(data.sender_email || '');
                const senderName = escapeHtml(data.sender_name || '');
                const subject = escapeHtml(data.subject || '');
                const domain = senderEmail.includes('@') ? senderEmail.split('@')[1] : '';
                
                const categorySelector = `
                    <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border-subtle);">
                        <div style="font-size: 10px; color: var(--text-muted); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;">Re-categorize</div>
                        <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                            <button onclick="event.stopPropagation(); updateCategory('${emailId}', 'urgent')" 
                                    style="padding: 4px 10px; font-size: 11px; border: 1px solid var(--urgent-red); background: ${data.category === 'urgent' ? 'var(--urgent-red)' : 'transparent'}; color: ${data.category === 'urgent' ? 'white' : 'var(--urgent-red)'}; border-radius: 4px; cursor: pointer;">🚨 Urgent</button>
                            <button onclick="event.stopPropagation(); updateCategory('${emailId}', 'important')" 
                                    style="padding: 4px 10px; font-size: 11px; border: 1px solid var(--important-orange); background: ${data.category === 'important' ? 'var(--important-orange)' : 'transparent'}; color: ${data.category === 'important' ? 'white' : 'var(--important-orange)'}; border-radius: 4px; cursor: pointer;">⚠️ Important</button>
                            <button onclick="event.stopPropagation(); updateCategory('${emailId}', 'normal')" 
                                    style="padding: 4px 10px; font-size: 11px; border: 1px solid var(--text-muted); background: ${data.category === 'normal' ? 'var(--text-muted)' : 'transparent'}; color: ${data.category === 'normal' ? 'white' : 'var(--text-muted)'}; border-radius: 4px; cursor: pointer;">📧 Normal</button>
                            <button onclick="event.stopPropagation(); updateCategory('${emailId}', 'newsletter')" 
                                    style="padding: 4px 10px; font-size: 11px; border: 1px solid var(--newsletter-green); background: ${data.category === 'newsletter' ? 'var(--newsletter-green)' : 'transparent'}; color: ${data.category === 'newsletter' ? 'white' : 'var(--newsletter-green)'}; border-radius: 4px; cursor: pointer;">📰 Newsletter</button>
                            <button onclick="event.stopPropagation(); updateCategory('${emailId}', 'spam')" 
                                    style="padding: 4px 10px; font-size: 11px; border: 1px solid var(--text-subtle); background: ${data.category === 'spam' ? 'var(--text-subtle)' : 'transparent'}; color: ${data.category === 'spam' ? 'white' : 'var(--text-subtle)'}; border-radius: 4px; cursor: pointer;">🗑️ Spam</button>
                        </div>
                        <div id="category-msg-${emailId}" style="font-size: 10px; margin-top: 6px; color: var(--accent);"></div>
                        
                        <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border-subtle);">
                            <div style="font-size: 10px; color: var(--text-muted); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;">Create Rule for Future Emails</div>
                            <div style="font-size: 10px; color: var(--text-subtle); margin-bottom: 6px;">Apply this category automatically:</div>
                            <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                                ${senderEmail ? `<button onclick="event.stopPropagation(); createRule('sender', '${senderEmail}', '${data.category}', '${emailId}')" style="padding: 3px 8px; font-size: 10px; border: 1px solid var(--border-strong); background: var(--bg-surface-2); color: var(--text-secondary); border-radius: 3px; cursor: pointer;" title="Apply to all emails from ${senderEmail}">From: ${senderName || senderEmail}</button>` : ''}
                                ${domain ? `<button onclick="event.stopPropagation(); createRule('domain', '${domain}', '${data.category}', '${emailId}')" style="padding: 3px 8px; font-size: 10px; border: 1px solid var(--border-strong); background: var(--bg-surface-2); color: var(--text-secondary); border-radius: 3px; cursor: pointer;" title="Apply to all emails from *@${domain}">Domain: ${domain}</button>` : ''}
                                ${subject ? `<button onclick="event.stopPropagation(); createRule('subject_contains', '${subject.substring(0, 30)}', '${data.category}', '${emailId}')" style="padding: 3px 8px; font-size: 10px; border: 1px solid var(--border-strong); background: var(--bg-surface-2); color: var(--text-secondary); border-radius: 3px; cursor: pointer;" title="Apply to all emails with subject containing '${subject.substring(0, 30)}...'">Subject: ${subject.substring(0, 20)}${subject.length > 20 ? '...' : ''}</button>` : ''}
                            </div>
                            <div id="rule-msg-${emailId}" style="font-size: 10px; margin-top: 6px; color: var(--accent);"></div>
                        </div>
                    </div>
                `;
                if (summaryTextEl) {
                    summaryTextEl.innerHTML = escapeHtml(body) + categorySelector;
                    summaryTextEl.dataset.loaded = 'true';
                }
            } catch (err) {
                if (summaryTextEl) {
                    summaryTextEl.textContent = 'Failed to load summary';
                }
                console.error('Failed to load email summary', err);
            }
        }
        
        // Update email category
        async function updateCategory(emailId, category) {
            try {
                const res = await fetch(`/api/email/${emailId}/category`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ category })
                });
                const data = await res.json();
                if (data.success) {
                    const msgEl = document.getElementById('category-msg-' + emailId);
                    if (msgEl) msgEl.textContent = '✓ Updated to ' + category;
                    // Refresh the page data after a short delay
                    setTimeout(() => {
                        const selectEl = document.getElementById('date-select');
                        if (selectEl && selectEl.value) {
                            loadDate(selectEl.value);
                        }
                    }, 1000);
                } else {
                    const msgEl = document.getElementById('category-msg-' + emailId);
                    if (msgEl) msgEl.textContent = '✗ Failed: ' + (data.error || 'Unknown error');
                }
            } catch (err) {
                console.error('Failed to update category', err);
                const msgEl = document.getElementById('category-msg-' + emailId);
                if (msgEl) msgEl.textContent = '✗ Network error';
            }
        }
        
        // Create a categorization rule
        async function createRule(ruleType, ruleValue, category, emailId) {
            try {
                const res = await fetch('/api/rules', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ rule_type: ruleType, rule_value: ruleValue, category })
                });
                const data = await res.json();
                const msgEl = document.getElementById('rule-msg-' + emailId);
                if (data.success) {
                    if (msgEl) msgEl.textContent = '✓ Rule created: ' + ruleType + ' → ' + category;
                } else {
                    if (msgEl) msgEl.textContent = '✗ ' + (data.error || 'Failed to create rule');
                }
            } catch (err) {
                console.error('Failed to create rule', err);
                const msgEl = document.getElementById('rule-msg-' + emailId);
                if (msgEl) msgEl.textContent = '✗ Network error';
            }
        }

        function escapeHtml(str) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            };
            return (str || '').replace(/[&<>"']/g, c => map[c] || c);
        }

        function renderAccounts(accounts) {
            if (!accounts || accounts.length === 0) {
                return `<div class="empty-state"><div class="empty-icon">&#128236;</div><div class="empty-text">No emails for this day</div></div>`;
            }

            const categoryOrder = ['urgent', 'important', 'normal', 'newsletter', 'spam'];
            const categoryIcons = {
                'urgent': '🚨',
                'important': '⚠️',
                'normal': '📧',
                'newsletter': '📰',
                'spam': '🗑️'
            };

            return accounts.map(account => {
                const categoriesHtml = categoryOrder.map(catId => {
                    const catData = account.categories && account.categories[catId];
                    if (!catData || catData.count === 0) return '';

                    const emailsHtml = (catData.emails || []).map(email => {
                        const categoryClass = `${email.category || 'normal'}-card`;
                        return `
                        <div class="email-card ${categoryClass}" data-email-id="${escapeHtml(email.email_id)}" onclick="toggleSummary('${escapeHtml(email.email_id)}')">
                            <div class="email-header">
                                <div class="sender-avatar">${escapeHtml(email.sender_initial || '?')}</div>
                                <div class="email-body">
                                    <div class="email-subject">${escapeHtml(email.subject)}</div>
                                    <div class="email-meta">
                                        <span class="email-sender">${escapeHtml(email.sender_name || 'Unknown')}</span>
                                        <span class="email-time">${escapeHtml(email.time_str || '')}</span>
                                    </div>
                                </div>
                                <div class="email-right">
                                    ${email.urgency_score ? `<div class="urgency-badge ${escapeHtml(email.urgency_class)}">${escapeHtml(email.urgency_display)}</div>` : ''}
                                </div>
                            </div>
                            <div class="email-summary" id="summary-${escapeHtml(email.email_id)}">
                                <div class="summary-label">Summary</div>
                                <div class="summary-text" id="summary-text-${escapeHtml(email.email_id)}">${escapeHtml(email.body || email.body_preview || 'No content available')}</div>
                            </div>
                        </div>`;
                    }).join('');

                    return `
                    <div class="category-subgroup ${catId}-subgroup" id="account-${escapeHtml(account.id)}-cat-${catId}">
                        <div class="category-subgroup-header" onclick="toggleCategorySubgroup('${escapeHtml(account.id)}', '${catId}')">
                            <span class="category-subgroup-icon">${categoryIcons[catId]}</span>
                            <span class="category-subgroup-name">${catId}</span>
                            <span class="category-subgroup-count">${catData.count}</span>
                            <span class="category-subgroup-toggle">▼</span>
                        </div>
                        <div class="category-subgroup-emails">${emailsHtml}</div>
                    </div>`;
                }).join('');

                return `
                <div class="account-bucket" id="account-${escapeHtml(account.id)}">
                    <div class="account-bucket-header" onclick="toggleAccount('${escapeHtml(account.id)}')">
                        <div class="account-bucket-avatar" style="--account-color: ${escapeHtml(account.color || '#4f46e5')}">${escapeHtml(account.initial)}</div>
                        <div class="account-bucket-name">${escapeHtml(account.email)}</div>
                        <div class="account-bucket-count">${account.count || 0}</div>
                        <div class="account-bucket-toggle">▼</div>
                    </div>
                    <div class="account-bucket-content">${categoriesHtml}</div>
                </div>`;
            }).join('');
        }

        function toggleAccount(accountId) {
            const bucket = document.getElementById('account-' + accountId);
            if (bucket) {
                bucket.classList.toggle('collapsed');
            }
        }

        function toggleCategorySubgroup(accountId, categoryId) {
            const subgroup = document.getElementById('account-' + accountId + '-cat-' + categoryId);
            if (subgroup) {
                subgroup.classList.toggle('collapsed');
            }
        }

        function renderDay(payload) {
            const stats = payload.stats || {};
            const accounts = payload.accounts || [];
            document.getElementById('stat-urgent').textContent = stats.urgent || 0;
            document.getElementById('stat-important').textContent = stats.important || 0;
            document.getElementById('stat-newsletter').textContent = stats.newsletter || 0;
            document.getElementById('stat-total').textContent = payload.total_count || 0;
            document.getElementById('stat-total-label').textContent = `Total (${payload.date || ''})`;
            document.getElementById('selected-date-text').textContent = `Showing: ${payload.date || ''}`;

            const selectEl = document.getElementById('date-select');
            if (selectEl && payload.date) {
                selectEl.value = payload.date;
            }

            // Update summary section
            const summaryContent = document.getElementById('summary-content');
            if (summaryContent && payload.email_summary) {
                summaryContent.innerHTML = payload.email_summary;
            }

            const container = document.getElementById('accounts-container');
            container.innerHTML = renderAccounts(accounts);
        }

        async function loadDate(dateStr) {
            try {
                const res = await fetch(`/api/day?date=${encodeURIComponent(dateStr)}`);
                const data = await res.json();
                renderDay(data);
            } catch (err) {
                console.error('Failed to load date', err);
                alert('Failed to load data for ' + dateStr);
            }
        }

        function onDateChange(event) {
            const dateStr = event.target.value;
            loadDate(dateStr);
        }

        function updateLastSyncText() {
            const lastSyncEl = document.getElementById('last-sync-text');
            if (!lastSyncEl) return;
            const now = new Date();
            const formatted = now.getFullYear() + '-' +
                String(now.getMonth() + 1).padStart(2, '0') + '-' +
                String(now.getDate()).padStart(2, '0') + ' ' +
                String(now.getHours()).padStart(2, '0') + ':' +
                String(now.getMinutes()).padStart(2, '0') + ':' +
                String(now.getSeconds()).padStart(2, '0');
            lastSyncEl.textContent = `Last sync: ${formatted}`;
        }

        async function refreshCurrentDate() {
            const selectEl = document.getElementById('date-select');
            const btn = document.querySelector('.refresh-btn');
            if (btn) btn.disabled = true;
            if (selectEl && selectEl.value) {
                await loadDate(selectEl.value);
                updateLastSyncText();
            }
            if (btn) btn.disabled = false;
        }

        // optional: preload current date data on load to sync with API shape
        document.addEventListener('DOMContentLoaded', () => {
            const selectEl = document.getElementById('date-select');
            if (selectEl && selectEl.value) {
                loadDate(selectEl.value);
            }
            updateWeather();
            updateCalendar();
        });
        
        // Update weather widget
        async function updateWeather() {
            try {
                const res = await fetch('/api/weather');
                const data = await res.json();
                const widget = document.getElementById('weather-widget');
                if (widget && data) {
                    widget.innerHTML = `
                        <span class="weather-icon">${data.icon || '❓'}</span>
                        <span class="weather-temp">${data.temp}°F</span>
                        <span class="weather-condition">${data.condition}</span>
                    `;
                    widget.title = data.error || `${data.city} - ${data.condition}`;
                }
            } catch (err) {
                console.error('Failed to update weather', err);
            }
        }
        
        // Update calendar widget
        async function updateCalendar() {
            try {
                const res = await fetch('/api/calendar');
                const data = await res.json();
                const countEl = document.getElementById('calendar-count');
                const widget = document.getElementById('calendar-widget');
                if (countEl && data) {
                    countEl.textContent = data.events ? data.events.length : '0';
                }
                if (widget && data.error) {
                    widget.title = data.error;
                }
            } catch (err) {
                console.error('Failed to update calendar', err);
            }
        }
    </script>
</body>
</html>
"""

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_available_dates(limit=30):
    """Return a list of distinct YYYY-MM-DD strings sorted desc."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT DISTINCT substr(date, 1, 10) as d
        FROM emails
        WHERE date IS NOT NULL
        ORDER BY d DESC
        LIMIT ?
        """,
        (limit,),
    )
    dates = [row["d"] for row in cursor.fetchall() if row["d"]]
    conn.close()
    return dates

def get_todays_stats(target_date=None):
    """Get stats for the provided YYYY-MM-DD date (default: today)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    date_str = target_date or date.today().isoformat()

    cursor.execute(
        """
        SELECT category, COUNT(*) as count
        FROM emails
        WHERE date LIKE ?
        GROUP BY category
        """,
        (date_str + "%",),
    )

    stats = {"urgent": 0, "important": 0, "newsletter": 0, "normal": 0, "spam": 0}

    for row in cursor.fetchall():
        if row["category"] in stats:
            stats[row["category"]] = row["count"]

    conn.close()
    return stats

def build_quick_summary(subject, sender_name, category, urgency, body):
    """Create a readable summary for expandable email details."""
    normalized_body = re.sub(r"\s+", " ", (body or "")).strip()
    if normalized_body:
        preview = normalized_body[:2000]
        return preview + ("..." if len(normalized_body) > 2000 else "")

    safe_subject = (subject or "(No subject)").strip()
    safe_sender = (sender_name or "Unknown sender").strip()
    safe_category = (category or "normal").capitalize()
    return f"{safe_category} email from {safe_sender} about '{safe_subject}'. Urgency: {urgency}/10."

def generate_email_summary(accounts, stats):
    """Generate a daily summary of urgent/important emails with action items."""
    urgent_emails = []
    important_emails = []
    
    for account in accounts:
        for email in account.get("emails", []):
            if email.get("category") == "urgent":
                urgent_emails.append(email)
            elif email.get("category") == "important":
                important_emails.append(email)
    
    # Sort by urgency score
    urgent_emails.sort(key=lambda x: x.get("urgency_score", 0), reverse=True)
    important_emails.sort(key=lambda x: x.get("urgency_score", 0), reverse=True)
    
    html_parts = []
    
    # Summary stats
    total_urgent = stats.get("urgent", 0)
    total_important = stats.get("important", 0)
    
    if total_urgent == 0 and total_important == 0:
        html_parts.append("<p>No urgent or important emails today. Enjoy your clear inbox!</p>")
    else:
        html_parts.append(f"<p><strong>{total_urgent}</strong> urgent and <strong>{total_important}</strong> important emails require attention.</p>")
    
    # Urgent section
    if urgent_emails:
        html_parts.append("<h4 style='color: var(--urgent-red); margin: 10px 0 6px 0; font-size: 12px;'>🚨 URGENT - Action Required</h4>")
        html_parts.append("<ul class='todo-list'>")
        for email in urgent_emails[:5]:  # Top 5 urgent
            subject = email.get("subject", "No subject")
            sender = email.get("sender_name", "Unknown")
            html_parts.append(f"<li><strong>{subject}</strong> from {sender}</li>")
        if len(urgent_emails) > 5:
            html_parts.append(f"<li><em>... and {len(urgent_emails) - 5} more urgent emails</em></li>")
        html_parts.append("</ul>")
    
    # Important section
    if important_emails:
        html_parts.append("<h4 style='color: var(--important-orange); margin: 10px 0 6px 0; font-size: 12px;'>⚠️ IMPORTANT - Review When Possible</h4>")
        html_parts.append("<ul class='todo-list'>")
        for email in important_emails[:5]:  # Top 5 important
            subject = email.get("subject", "No subject")
            sender = email.get("sender_name", "Unknown")
            html_parts.append(f"<li><strong>{subject}</strong> from {sender}</li>")
        if len(important_emails) > 5:
            html_parts.append(f"<li><em>... and {len(important_emails) - 5} more important emails</em></li>")
        html_parts.append("</ul>")
    
    # Suggested actions
    if urgent_emails or important_emails:
        html_parts.append("<h4 style='margin: 10px 0 6px 0; font-size: 12px;'>✅ Suggested Actions</h4>")
        html_parts.append("<ul class='todo-list'>")
        if urgent_emails:
            html_parts.append("<li>Address urgent emails first - bills, security alerts, deadlines</li>")
        if important_emails:
            html_parts.append("<li>Review important emails for updates and opportunities</li>")
        html_parts.append("<li>Unsubscribe from newsletters you don't read</li>")
        html_parts.append("</ul>")
    
    return "\n".join(html_parts)

# Weather and Calendar Functions
def get_weather_data():
    """Fetch weather from OpenWeatherMap API."""
    api_key = os.environ.get("OPENWEATHER_API_KEY", "")
    city = os.environ.get("WEATHER_CITY", "New York")
    
    if not api_key:
        return {
            "error": "No API key configured",
            "city": city,
            "temp": "--",
            "condition": "Configure OPENWEATHER_API_KEY",
            "icon": "❓"
        }
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            status_code = response.getcode()
        
        if status_code == 200:
            weather_map = {
                "Clear": ("☀️", "Clear"),
                "Clouds": ("☁️", "Cloudy"),
                "Rain": ("🌧️", "Rain"),
                "Drizzle": ("🌦️", "Drizzle"),
                "Thunderstorm": ("⛈️", "Storm"),
                "Snow": ("❄️", "Snow"),
                "Mist": ("🌫️", "Mist"),
                "Fog": ("🌫️", "Fog"),
            }
            main_weather = data["weather"][0]["main"]
            icon, condition = weather_map.get(main_weather, ("🌡️", main_weather))
            
            return {
                "city": city,
                "temp": round(data["main"]["temp"]),
                "feels_like": round(data["main"]["feels_like"]),
                "condition": condition,
                "icon": icon,
                "humidity": data["main"]["humidity"],
                "wind": round(data["wind"]["speed"]),
                "error": None
            }
        else:
            return {
                "error": f"API Error: {data.get('message', 'Unknown')}",
                "city": city,
                "temp": "--",
                "condition": "Error",
                "icon": "❌"
            }
    except urllib.error.HTTPError as e:
        return {
            "error": f"HTTP Error: {e.code}",
            "city": city,
            "temp": "--",
            "condition": "Error",
            "icon": "❌"
        }
    except Exception as e:
        return {
            "error": str(e),
            "city": city,
            "temp": "--",
            "condition": "Error",
            "icon": "❌"
        }

def get_calendar_events():
    """Fetch today's calendar events via Google Workspace CLI."""
    try:
        gapi = Path.home() / ".hermes" / "skills" / "productivity" / "google-workspace" / "scripts" / "google_api.py"
        if not gapi.exists():
            return {"events": [], "error": "Google Workspace not configured"}
        
        # Check if authenticated
        setup = Path.home() / ".hermes" / "skills" / "productivity" / "google-workspace" / "scripts" / "setup.py"
        check_result = subprocess.run(
            ["python3.11", str(setup), "--check"],
            capture_output=True, text=True, timeout=10
        )
        
        if "AUTHENTICATED" not in check_result.stdout:
            return {"events": [], "error": "Google Calendar not authenticated"}
        
        # Get today's events
        today = date.today()
        start = today.isoformat() + "T00:00:00Z"
        end = today.isoformat() + "T23:59:59Z"
        
        result = subprocess.run(
            ["python3.11", str(gapi), "calendar", "list", "--start", start, "--end", end],
            capture_output=True, text=True, timeout=15
        )
        
        if result.returncode == 0:
            events = json.loads(result.stdout)
            # Format events for display
            formatted = []
            for e in events:
                start_time = e.get("start", "")
                # Parse ISO time
                if "T" in start_time:
                    time_part = start_time.split("T")[1][:5]
                else:
                    time_part = "All day"
                formatted.append({
                    "time": time_part,
                    "summary": e.get("summary", "No title"),
                    "location": e.get("location", ""),
                    "id": e.get("id", "")
                })
            return {"events": formatted, "error": None}
        else:
            return {"events": [], "error": f"Calendar API error: {result.stderr}"}
    except Exception as e:
        return {"events": [], "error": str(e)}

def generate_account_avatar(email):
    """Generate unique initial and color for an account email."""
    # Extract local part (before @)
    local_part = email.split('@')[0] if '@' in email else email
    
    # Generate initial from first character, or first letter of each word if separated by dots/underscores
    parts = re.split(r'[._\-+]', local_part)
    if len(parts) >= 2 and len(parts[0]) >= 1 and len(parts[1]) >= 1:
        # Two initials (e.g., "john.smith" -> "JS")
        initial = (parts[0][0] + parts[1][0]).upper()
    else:
        # Single initial
        initial = local_part[0].upper() if local_part else '?'
    
    # Predefined color palette (distinct, accessible colors)
    colors = [
        "#ea4335",  # Red (Gmail-ish)
        "#4285f4",  # Blue
        "#34a853",  # Green
        "#6001d2",  # Purple (Yahoo-ish)
        "#fbbc04",  # Yellow/Gold
        "#ff6d01",  # Orange
        "#00acc1",  # Cyan
        "#e91e63",  # Pink
        "#9c27b0",  # Deep Purple
        "#009688",  # Teal
        "#795548",  # Brown
        "#607d8b",  # Blue Grey
    ]
    
    # Hash email to pick consistent color
    hash_val = sum(ord(c) for c in email) % len(colors)
    color = colors[hash_val]
    
    return initial, color

def get_todays_emails_by_account(target_date=None):
    """Get emails for a given date grouped by account with category sub-groups."""
    conn = get_db_connection()
    cursor = conn.cursor()

    date_str = target_date or date.today().isoformat()

    cursor.execute(
        """
        SELECT email_id, account, subject, sender_name, sender_email,
               date, urgency_score, category, body
        FROM emails
        WHERE date LIKE ?
        ORDER BY account,
            CASE category
                WHEN 'urgent' THEN 1
                WHEN 'important' THEN 2
                WHEN 'normal' THEN 3
                WHEN 'newsletter' THEN 4
                WHEN 'spam' THEN 5
                ELSE 6
            END,
            urgency_score DESC,
            date DESC
        """,
        (date_str + "%",),
    )

    # Group by account
    accounts_dict = {}
    category_order = ['urgent', 'important', 'normal', 'newsletter', 'spam']
    category_icons = {
        'urgent': '🚨',
        'important': '⚠️',
        'normal': '📧',
        'newsletter': '📰',
        'spam': '🗑️'
    }

    for row in cursor.fetchall():
        account_email = row["account"] or "unknown"

        if account_email not in accounts_dict:
            # Generate unique avatar for this account
            account_initial, account_color = generate_account_avatar(account_email)

            accounts_dict[account_email] = {
                "id": account_email.split("@")[0],
                "email": account_email,
                "initial": account_initial,
                "color": account_color,
                "count": 0,
                "emails": [],
                "categories": {cat: {"emails": [], "count": 0, "icon": category_icons[cat]} for cat in category_order},
            }

        # Process email
        sender_name = row["sender_name"] or ""
        sender_initial = sender_name[0].upper() if sender_name else "?"
        cat = row["category"] or "normal"

        # Parse time from date string
        date_str_full = row["date"] or ""
        time_str = ""
        if len(date_str_full) >= 16:
            try:
                dt = datetime.fromisoformat(date_str_full.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M")
            except Exception:
                time_str = date_str_full[11:16]

        # Clamp urgency into a safe display range (0..10)
        raw_urgency = row["urgency_score"] or 0
        urgency = max(0, min(int(raw_urgency), 10))
        urgency_display = f"{urgency}/10"

        if urgency >= 8:
            urgency_class = "high"
        elif urgency >= 5:
            urgency_class = "medium"
        else:
            urgency_class = "low"

        # Store full body for display
        body = row["body"] or ""

        email_data = {
            "email_id": row["email_id"],
            "subject": row["subject"] or "(No subject)",
            "sender_name": sender_name,
            "sender_email": row["sender_email"] or "",
            "sender_initial": sender_initial,
            "date": row["date"],
            "time_str": time_str,
            "urgency_score": urgency,
            "urgency_display": urgency_display,
            "urgency_class": urgency_class,
            "category": cat,
            "body": body,  # Full body stored
            "body_preview": body[:200] + "..." if len(body) > 200 else body,  # Short preview
        }

        accounts_dict[account_email]["emails"].append(email_data)
        accounts_dict[account_email]["categories"][cat]["emails"].append(email_data)
        accounts_dict[account_email]["categories"][cat]["count"] += 1
        accounts_dict[account_email]["count"] += 1

    conn.close()

    # Sort accounts by email domain (Gmail first), then alphabetically
    accounts = list(accounts_dict.values())
    accounts.sort(key=lambda a: (0 if "gmail" in a["email"].lower() else 1, a["email"]))

    return accounts

def get_todays_emails_by_category(target_date=None):
    """Get emails for a given date grouped by category with collapsible buckets."""
    conn = get_db_connection()
    cursor = conn.cursor()

    date_str = target_date or date.today().isoformat()

    cursor.execute(
        """
        SELECT email_id, account, subject, sender_name, sender_email,
               date, urgency_score, category, body
        FROM emails
        WHERE date LIKE ?
        ORDER BY
            CASE category
                WHEN 'urgent' THEN 1
                WHEN 'important' THEN 2
                WHEN 'normal' THEN 3
                WHEN 'newsletter' THEN 4
                WHEN 'spam' THEN 5
                ELSE 6
            END,
            urgency_score DESC,
            date DESC
        """,
        (date_str + "%",),
    )

    # Group by category
    categories_dict = {}
    category_order = ['urgent', 'important', 'normal', 'newsletter', 'spam']
    category_icons = {
        'urgent': '🚨',
        'important': '⚠️',
        'normal': '📧',
        'newsletter': '📰',
        'spam': '🗑️'
    }

    for row in cursor.fetchall():
        cat = row["category"] or "normal"

        if cat not in categories_dict:
            categories_dict[cat] = {
                "id": cat,
                "name": cat,
                "icon": category_icons.get(cat, '📧'),
                "count": 0,
                "emails": [],
            }

        # Process email
        sender_name = row["sender_name"] or ""
        sender_initial = sender_name[0].upper() if sender_name else "?"

        # Parse time from date string
        date_str_full = row["date"] or ""
        time_str = ""
        if len(date_str_full) >= 16:
            try:
                dt = datetime.fromisoformat(date_str_full.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M")
            except Exception:
                time_str = date_str_full[11:16]

        # Clamp urgency into a safe display range (0..10)
        raw_urgency = row["urgency_score"] or 0
        urgency = max(0, min(int(raw_urgency), 10))
        urgency_display = f"{urgency}/10"

        if urgency >= 8:
            urgency_class = "high"
        elif urgency >= 5:
            urgency_class = "medium"
        else:
            urgency_class = "low"

        # Build quick summary
        body = row["body"] or ""
        body_preview = build_quick_summary(
            subject=row["subject"],
            sender_name=sender_name,
            category=cat,
            urgency=urgency,
            body=body,
        )

        # Determine account type and initial
        account_email = row["account"] or "unknown"
        if "yahoo" in account_email.lower():
            account_type = "yahoo"
            account_initial = "Y"
        else:
            account_type = "gmail"
            account_initial = "G"

        categories_dict[cat]["emails"].append(
            {
                "email_id": row["email_id"],
                "subject": row["subject"] or "(No subject)",
                "sender_name": sender_name,
                "sender_email": row["sender_email"] or "",
                "sender_initial": sender_initial,
                "account": account_email,
                "account_type": account_type,
                "account_initial": account_initial,
                "date": row["date"],
                "time_str": time_str,
                "urgency_score": urgency,
                "urgency_display": urgency_display,
                "urgency_class": urgency_class,
                "category": cat,
                "body_preview": body_preview,
            }
        )
        categories_dict[cat]["count"] += 1

    conn.close()

    # Return in priority order
    categories = []
    for cat in category_order:
        if cat in categories_dict:
            categories.append(categories_dict[cat])

    return categories

@app.route("/")
def index():
    requested_date = request.args.get("date")
    available_dates = get_available_dates()

    # default to requested date, else first available, else today
    target_date = requested_date or (available_dates[0] if available_dates else date.today().isoformat())

    stats = get_todays_stats(target_date)
    accounts = get_todays_emails_by_account(target_date)
    weather = get_weather_data()
    calendar = get_calendar_events()
    email_summary = generate_email_summary(accounts, stats)  # Restore grand summary

    total_count = sum(a["count"] for a in accounts)

    return render_template_string(
        HTML_TEMPLATE,
        stats=stats,
        accounts=accounts,
        total_count=total_count,
        current_date=datetime.now().strftime("%A, %B %d, %Y %H:%M"),
        last_refresh=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        available_dates=available_dates,
        selected_date=target_date,
        weather=weather,
        calendar=calendar,
        email_summary=email_summary,
    )

@app.route("/api/emails")
def api_emails():
    account = request.args.get("account", None)
    target_date = request.args.get("date") or date.today().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if account:
        cursor.execute("""
            SELECT * FROM emails 
            WHERE account = ? AND date LIKE ?
            ORDER BY date DESC
        """, (account, target_date + "%"))
    else:
        cursor.execute("""
            SELECT * FROM emails 
            WHERE date LIKE ?
            ORDER BY date DESC
        """, (target_date + "%",))
    
    emails = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({"emails": emails})


@app.route("/api/day")
def api_day():
    target_date = request.args.get("date") or date.today().isoformat()

    stats = get_todays_stats(target_date)
    accounts = get_todays_emails_by_account(target_date)
    total_count = sum(a["count"] for a in accounts)
    email_summary = generate_email_summary(accounts, stats)

    return jsonify(
        {
            "date": target_date,
            "stats": stats,
            "accounts": accounts,
            "total_count": total_count,
            "email_summary": email_summary,
        }
    )

@app.route("/api/email/<email_id>")
def api_email_detail(email_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM emails WHERE email_id = ?", (email_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify(dict(row))
    return jsonify({"error": "Email not found"}), 404

@app.route("/api/email/<email_id>/category", methods=["POST"])
def api_update_category(email_id):
    """Update the category of an email."""
    data = request.get_json()
    if not data or 'category' not in data:
        return jsonify({"success": False, "error": "Missing category"}), 400
    
    new_category = data['category']
    valid_categories = ['urgent', 'important', 'normal', 'newsletter', 'spam']
    
    if new_category not in valid_categories:
        return jsonify({"success": False, "error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if email exists
    cursor.execute("SELECT email_id FROM emails WHERE email_id = ?", (email_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"success": False, "error": "Email not found"}), 404
    
    # Update the category
    cursor.execute(
        "UPDATE emails SET category = ? WHERE email_id = ?",
        (new_category, email_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "email_id": email_id, "category": new_category})

@app.route("/api/weather")
def api_weather():
    return jsonify(get_weather_data())

@app.route("/api/calendar")
def api_calendar():
    return jsonify(get_calendar_events())

# User Rules API Endpoints
@app.route("/api/rules")
def api_list_rules():
    """List all user-defined categorization rules."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, rule_type, rule_value, category, created_at, hit_count FROM user_rules ORDER BY hit_count DESC, created_at DESC")
    rules = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"rules": rules})

@app.route("/api/rules", methods=["POST"])
def api_create_rule():
    """Create a new categorization rule."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Missing request body"}), 400
    
    rule_type = data.get("rule_type")
    rule_value = data.get("rule_value")
    category = data.get("category")
    
    if not rule_type or not rule_value or not category:
        return jsonify({"success": False, "error": "Missing required fields: rule_type, rule_value, category"}), 400
    
    valid_types = ["sender", "domain", "subject_contains"]
    if rule_type not in valid_types:
        return jsonify({"success": False, "error": f"Invalid rule_type. Must be one of: {', '.join(valid_types)}"}), 400
    
    valid_categories = ["urgent", "important", "normal", "newsletter", "spam"]
    if category not in valid_categories:
        return jsonify({"success": False, "error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO user_rules (rule_type, rule_value, category, created_at) VALUES (?, ?, ?, ?)",
            (rule_type, rule_value, category, datetime.now().isoformat())
        )
        conn.commit()
        rule_id = cursor.lastrowid
        conn.close()
        return jsonify({"success": True, "id": rule_id, "rule_type": rule_type, "rule_value": rule_value, "category": category})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "error": "Rule already exists for this type/value combination"}), 409

@app.route("/api/rules/<int:rule_id>", methods=["DELETE"])
def api_delete_rule(rule_id):
    """Delete a categorization rule."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_rules WHERE id = ?", (rule_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    
    if deleted:
        return jsonify({"success": True, "deleted_id": rule_id})
    else:
        return jsonify({"success": False, "error": "Rule not found"}), 404

@app.route("/api/rules/test")
def api_test_rules():
    """Test which rules would match a given email."""
    sender_email = request.args.get("sender_email", "").lower()
    sender_name = request.args.get("sender_name", "")
    subject = request.args.get("subject", "")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    matched_rules = []
    
    # Check sender rules
    cursor.execute("SELECT id, rule_value, category FROM user_rules WHERE rule_type = 'sender' AND LOWER(rule_value) = ?", (sender_email,))
    for row in cursor.fetchall():
        matched_rules.append({"id": row["id"], "type": "sender", "value": row["rule_value"], "category": row["category"]})
    
    # Check domain rules
    if "@" in sender_email:
        domain = sender_email.split("@")[1]
        cursor.execute("SELECT id, rule_value, category FROM user_rules WHERE rule_type = 'domain' AND LOWER(rule_value) = ?", (domain,))
        for row in cursor.fetchall():
            matched_rules.append({"id": row["id"], "type": "domain", "value": row["rule_value"], "category": row["category"]})
    
    # Check subject_contains rules
    cursor.execute("SELECT id, rule_value, category FROM user_rules WHERE rule_type = 'subject_contains'")
    for row in cursor.fetchall():
        if row["rule_value"].lower() in subject.lower():
            matched_rules.append({"id": row["id"], "type": "subject_contains", "value": row["rule_value"], "category": row["category"]})
    
    conn.close()
    return jsonify({"matched_rules": matched_rules, "sender_email": sender_email, "subject": subject})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5051"))
    print("Starting Email Dashboard V3...")
    print(f"Access at: http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
