#!/usr/bin/env python3
"""Dashboard routes for the application
"""
from flask import request, render_template_string

from api.v1.views.dashboard import dashboard_bp


@dashboard_bp.route('/', methods=['GET'], strict_slashes=False)
def dashboard():
    """Main dashboard page with full UI and API integration"""

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ReceiptBridge - Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }

            .container {
                max-width: 1400px;
                margin: 0 auto;
            }

            /* Header */
            .header {
                background: white;
                border-radius: 16px;
                padding: 24px;
                margin-bottom: 24px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
            }

            .header h1 {
                color: #333;
                font-size: 28px;
                margin-bottom: 8px;
            }

            .header p {
                color: #666;
            }

            .shop-info {
                background: #f0f0f0;
                padding: 12px 20px;
                border-radius: 12px;
            }

            .shop-info strong {
                color: #667eea;
            }

            .status-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 10px;
            }

            .status-installed {
                background: #4CAF50;
                color: white;
            }

            /* Tabs */
            .tabs {
                display: flex;
                gap: 10px;
                margin-bottom: 24px;
                flex-wrap: wrap;
            }

            .tab-btn {
                background: white;
                border: none;
                padding: 12px 24px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                color: #666;
            }

            .tab-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }

            .tab-btn.active {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }

            /* Stats Grid */
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin-bottom: 24px;
            }

            .stat-card {
                background: white;
                border-radius: 16px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: transform 0.2s;
                cursor: pointer;
            }

            .stat-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 8px 16px rgba(0,0,0,0.15);
            }

            .stat-title {
                font-size: 14px;
                color: #666;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }

            .stat-value {
                font-size: 36px;
                font-weight: bold;
                color: #333;
            }

            .stat-unit {
                font-size: 14px;
                color: #999;
                margin-left: 4px;
            }

            .stat-trend {
                font-size: 12px;
                margin-top: 8px;
                color: #4CAF50;
            }

            /* Cards */
            .card {
                background: white;
                border-radius: 16px;
                padding: 24px;
                margin-bottom: 24px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }

            .card h2 {
                color: #333;
                margin-bottom: 20px;
                font-size: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .card h2 .badge {
                background: #667eea;
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 12px;
            }

            /* Tables */
            .table-container {
                overflow-x: auto;
            }

            table {
                width: 100%;
                border-collapse: collapse;
            }

            th, td {
                text-align: left;
                padding: 12px;
                border-bottom: 1px solid #e0e0e0;
            }

            th {
                background: #f7f7f7;
                font-weight: 600;
                color: #666;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            tr:hover {
                background: #f9f9f9;
            }

            /* Status Labels */
            .status {
                display: inline-block;
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
                text-transform: uppercase;
            }

            .status-pending { background: #FF9800; color: white; }
            .status-printing { background: #2196F3; color: white; }
            .status-completed { background: #4CAF50; color: white; }
            .status-failed { background: #f44336; color: white; }
            .status-assigned { background: #9C27B0; color: white; }

            .badge-online { background: #4CAF50; color: white; }
            .badge-offline { background: #999; color: white; }
            .badge-active { background: #4CAF50; color: white; }
            .badge-inactive { background: #f44336; color: white; }

            /* Buttons */
            .btn {
                padding: 8px 16px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 600;
                transition: all 0.2s;
            }

            .btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }

            .btn-danger {
                background: #f44336;
                color: white;
            }

            .btn-warning {
                background: #FF9800;
                color: white;
            }

            .btn-sm {
                padding: 4px 10px;
                font-size: 11px;
            }

            .btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            }

            /* Loading */
            .loading {
                text-align: center;
                padding: 40px;
                color: #999;
            }

            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            /* Modal */
            .modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 1000;
                justify-content: center;
                align-items: center;
            }

            .modal-content {
                background: white;
                border-radius: 16px;
                padding: 24px;
                max-width: 500px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
            }

            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }

            .close {
                font-size: 28px;
                cursor: pointer;
                color: #999;
            }

            /* Filters */
            .filters {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }

            .filters select, .filters input {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 14px;
            }

            /* Refresh Button */
            .refresh-btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .refresh-btn:hover {
                background: #5a67d8;
            }

            .last-update {
                font-size: 12px;
                color: #999;
                margin-top: 10px;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <div class="header">
                <div>
                    <h1>🖨️ ReceiptBridge Dashboard</h1>
                    <p>Real-time monitoring for your receipt printing infrastructure</p>
                </div>
                <div class="shop-info">
                    <strong>Shop:</strong> <span id="shopDomain">{{ shop or 'Loading...' }}</span>
                    {% if installed == 'true' %}
                        <span class="status-badge status-installed">✓ App Installed</span>
                    {% endif %}
                </div>
            </div>

            <!-- Tabs -->
            <div class="tabs">
                <button class="tab-btn active" onclick="switchTab('overview')">📊 Overview</button>
                <button class="tab-btn" onclick="switchTab('jobs')">🖨️ Print Jobs</button>
                <button class="tab-btn" onclick="switchTab('devices')">📱 Devices</button>
                <button class="tab-btn" onclick="switchTab('queue')">⏳ Queue Monitor</button>
            </div>

            <!-- Overview Tab -->
            <div id="overviewTab" class="tab-content">
                <div class="stats-grid" id="statsGrid">
                    <div class="loading">Loading statistics...</div>
                </div>

                <div class="card">
                    <h2>📈 Quick Actions</h2>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button class="btn btn-primary" onclick="refreshAll()">🔄 Refresh All Data</button>
                        <button class="btn btn-primary" onclick="testWebhook()">🧪 Test Webhook</button>
                        <button class="btn btn-warning" onclick="retryFailedJobs()">🔁 Retry Failed Jobs</button>
                        <button class="btn btn-danger" onclick="cleanupOldJobs()">🗑️ Cleanup Old Jobs</button>
                    </div>
                </div>

                <div class="card">
                    <h2>📋 Recent Print Jobs</h2>
                    <div class="table-container">
                        <table id="recentJobsTable">
                            <thead>
                                <tr><th>Job #</th><th>Order #</th><th>Status</th><th>Device</th><th>Time</th><th>Actions</th></tr>
                            </thead>
                            <tbody><tr><td colspan="6" class="loading">Loading...</td></tr></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Jobs Tab -->
            <div id="jobsTab" class="tab-content" style="display:none;">
                <div class="card">
                    <h2>🔍 Filter Jobs</h2>
                    <div class="filters">
                        <select id="jobStatusFilter">
                            <option value="">All Status</option>
                            <option value="pending">Pending</option>
                            <option value="assigned">Assigned</option>
                            <option value="printing">Printing</option>
                            <option value="completed">Completed</option>
                            <option value="failed">Failed</option>
                        </select>
                        <input type="text" id="orderSearch" placeholder="Search by Order #">
                        <button class="btn btn-primary btn-sm" onclick="loadJobs()">Apply Filters</button>
                    </div>
                </div>

                <div class="card">
                    <h2>📋 All Print Jobs</h2>
                    <div class="table-container">
                        <table id="allJobsTable">
                            <thead>
                                <tr><th>Job #</th><th>Order #</th><th>Status</th><th>Device</th><th>Priority</th><th>Retries</th><th>Created</th><th>Actions</th></tr>
                            </thead>
                            <tbody><tr><td colspan="8" class="loading">Loading...</td></tr></tbody>
                        </table>
                    </div>
                    <div id="jobsPagination" style="margin-top: 20px; text-align: center;"></div>
                </div>
            </div>

            <!-- Devices Tab -->
            <div id="devicesTab" class="tab-content" style="display:none;">
                <div class="card">
                    <h2>📱 Registered Devices</h2>
                    <div class="table-container">
                        <table id="devicesTable">
                            <thead>
                                <tr><th>Device ID</th><th>Name</th><th>Platform</th><th>Status</th><th>Printer</th><th>Jobs Printed</th><th>Last Ping</th><th>Actions</th></tr>
                            </thead>
                            <tbody><tr><td colspan="8" class="loading">Loading...</td></tr></tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
                <h3>🔍 Discover Devices</h3>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button class="btn btn-primary" onclick="discoverPrinters()">
                        🌐 Discover Network Printers
                    </button>
                    <button class="btn btn-primary" onclick="discoverUSBPrinters()">
                        🔌 Discover USB Printers
                    </button>
                    <button class="btn btn-primary" onclick="discoverAll()">
                        🔍 Scan All Devices
                    </button>
                </div>
                
                <div id="discoveryResults" style="margin-top: 15px; display: none;">
                    <h4>Discovery Results:</h4>
                    <div id="discoveredDevices"></div>
                    <div style="margin-top: 10px;">
                        <button class="btn btn-warning btn-sm" onclick="registerSelectedDevice()">
                            ➕ Register Selected Device
                        </button>
                    </div>
                </div>
            </div>

            <!-- Queue Tab -->
            <div id="queueTab" class="tab-content" style="display:none;">
                <div class="stats-grid" id="queueStatsGrid">
                    <div class="loading">Loading queue stats...</div>
                </div>

                <div class="card">
                    <h2>⏳ Pending Queue</h2>
                    <div class="table-container">
                        <table id="queueTable">
                            <thead>
                                <tr><th>Job #</th><th>Order #</th><th>Priority</th><th>Waiting Time</th><th>Actions</th></tr>
                            </thead>
                            <tbody><tr><td colspan="5" class="loading">Loading...</td></tr></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="last-update">
                Last updated: <span id="lastUpdate">Never</span>
                <button class="refresh-btn" onclick="refreshAll()">🔄 Refresh</button>
            </div>
        </div>

        <!-- Modal for Job Details -->
        <div id="jobModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Job Details</h2>
                    <span class="close" onclick="closeModal()">&times;</span>
                </div>
                <div id="jobDetails"></div>
            </div>
        </div>

        <script>
            const API_BASE = window.location.origin + '/api/v1';
            let currentPage = 1;
            let autoRefreshInterval = null;

            // Get shop domain from URL
            const urlParams = new URLSearchParams(window.location.search);
            const shopDomain = urlParams.get('shop') || '{{ shop }}';

            // Headers for API calls
            function getHeaders() {
                return {
                    'Content-Type': 'application/json',
                    'X-Shop-Domain': shopDomain
                };
            }

            // Switch tabs
            function switchTab(tabName) {
                document.querySelectorAll('.tab-content').forEach(tab => {
                    tab.style.display = 'none';
                });
                document.getElementById(tabName + 'Tab').style.display = 'block';

                document.querySelectorAll('.tab-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                event.target.classList.add('active');

                // Load data based on tab
                if (tabName === 'overview') loadOverview();
                else if (tabName === 'jobs') loadJobs();
                else if (tabName === 'devices') loadDevices();
                else if (tabName === 'queue') loadQueue();
            }

            // Load Overview
            async function loadOverview() {
                try {
                    const response = await fetch(`${API_BASE}/dashboard/stats`, {
                        headers: getHeaders()
                    });
                    const data = await response.json();

                    if (data.success) {
                        const stats = data.stats;
                        document.getElementById('statsGrid').innerHTML = `
                            <div class="stat-card" onclick="switchTab('jobs')">
                                <div class="stat-title">Total Jobs</div>
                                <div class="stat-value">${stats.jobs.pending + stats.jobs.processing + stats.jobs.completed + stats.jobs.failed}</div>
                            </div>
                            <div class="stat-card" onclick="switchTab('queue')">
                                <div class="stat-title">Queue Size</div>
                                <div class="stat-value">${stats.jobs.pending + stats.jobs.processing}</div>
                                <div class="stat-trend">${stats.jobs.pending} waiting, ${stats.jobs.processing} printing</div>
                            </div>
                            <div class="stat-card" onclick="switchTab('devices')">
                                <div class="stat-title">Devices</div>
                                <div class="stat-value">${stats.devices.total}</div>
                                <div class="stat-trend">${stats.devices.online} online, ${stats.devices.offline} offline</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-title">Success Rate</div>
                                <div class="stat-value">${stats.performance.success_rate}%</div>
                                <div class="stat-trend">${stats.performance.total_processed} total processed</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-title">Today's Prints</div>
                                <div class="stat-value">${stats.jobs.today}</div>
                                <div class="stat-trend">Completed today</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-title">Failed Jobs</div>
                                <div class="stat-value">${stats.jobs.failed}</div>
                                <div class="stat-trend">Need attention</div>
                            </div>
                        `;
                    }

                    // Load recent jobs
                    const jobsResponse = await fetch(`${API_BASE}/jobs?per_page=10`, {
                        headers: getHeaders()
                    });
                    const jobsData = await jobsResponse.json();

                    if (jobsData.success) {
                        const tbody = document.querySelector('#recentJobsTable tbody');
                        if (jobsData.items && jobsData.items.length > 0) {
                            tbody.innerHTML = jobsData.items.map(job => `
                                <tr>
                                    <td>#${job.job_number}</td>
                                    <td>${job.order_number}</td>
                                    <td><span class="status status-${job.status}">${job.status}</span></td>
                                    <td>${job.assigned_device || 'Unassigned'}</td>
                                    <td>${new Date(job.created_at).toLocaleString()}</td>
                                    <td>
                                        <button class="btn btn-primary btn-sm" onclick="viewJobDetails('${job.id}')">View</button>
                                        ${job.status === 'failed' ? `<button class="btn btn-warning btn-sm" onclick="retryJob('${job.id}')">Retry</button>` : ''}
                                    </td>
                                </tr>
                            `).join('');
                        } else {
                            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No jobs found</td></tr>';
                        }
                    }

                    updateTimestamp();
                } catch (error) {
                    console.error('Error loading overview:', error);
                }
            }

            // Load Jobs
            async function loadJobs(page = 1) {
                currentPage = page;
                const status = document.getElementById('jobStatusFilter').value;
                const search = document.getElementById('orderSearch').value;

                try {
                    let url = `${API_BASE}/jobs?per_page=20&page=${page}`;
                    if (status) url += `&status=${status}`;
                    if (search) url += `&order_by=${search}`;

                    const response = await fetch(url, { headers: getHeaders() });
                    const data = await response.json();

                    if (data.success) {
                        const tbody = document.querySelector('#allJobsTable tbody');
                        if (data.items && data.items.length > 0) {
                            tbody.innerHTML = data.items.map(job => `
                                <tr>
                                    <td>#${job.job_number}</td>
                                    <td>${job.order_number}</td>
                                    <td><span class="status status-${job.status}">${job.status}</span></td>
                                    <td>${job.assigned_device || '-'}</td>
                                    <td>${job.priority}</td>
                                    <td>${job.retry_count}</td>
                                    <td>${new Date(job.created_at).toLocaleString()}</td>
                                    <td>
                                        <button class="btn btn-primary btn-sm" onclick="viewJobDetails('${job.id}')">View</button>
                                        ${job.status === 'failed' ? `<button class="btn btn-warning btn-sm" onclick="retryJob('${job.id}')">Retry</button>` : ''}
                                        ${job.status === 'pending' ? `<button class="btn btn-danger btn-sm" onclick="cancelJob('${job.id}')">Cancel</button>` : ''}
                                    </td>
                                </tr>
                            `).join('');
                        } else {
                            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;">No jobs found</td></tr>';
                        }

                        // Pagination
                        if (data.pagination && data.pagination.total_pages > 1) {
                            let paginationHtml = '';
                            for (let i = 1; i <= Math.min(data.pagination.total_pages, 10); i++) {
                                paginationHtml += `<button class="btn btn-sm ${i === page ? 'btn-primary' : ''}" onclick="loadJobs(${i})" style="margin: 0 2px;">${i}</button>`;
                            }
                            document.getElementById('jobsPagination').innerHTML = paginationHtml;
                        } else {
                            document.getElementById('jobsPagination').innerHTML = '';
                        }
                    }

                    updateTimestamp();
                } catch (error) {
                    console.error('Error loading jobs:', error);
                }
            }

            // Load Devices
            async function loadDevices() {
                try {
                    const response = await fetch(`${API_BASE}/devices`, {
                        headers: getHeaders()
                    });
                    const data = await response.json();

                    if (data.success) {
                        const tbody = document.querySelector('#devicesTable tbody');
                        if (data.items && data.items.length > 0) {
                            tbody.innerHTML = data.items.map(device => `
                                <tr>
                                    <td><code>${device.device_id}</code></td>
                                    <td>${device.name || '-'}</td>
                                    <td>${device.platform || '-'}</td>
                                    <td>
                                        <span class="status ${device.is_online ? 'badge-online' : 'badge-offline'}">
                                            ${device.is_online ? 'Online' : 'Offline'}
                                        </span>
                                        <span class="status ${device.is_active ? 'badge-online' : 'badge-inactive'}">
                                            ${device.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                    <td>${device.printer_model || '-'}<br><small>${device.printer_interface || '-'}</small></td>
                                    <td>${device.total_jobs_printed || 0}</td>
                                    <td>${device.last_ping_at ? new Date(device.last_ping_at).toLocaleString() : 'Never'}</td>
                                    <td>
                                        <button class="btn btn-primary btn-sm" onclick="viewDeviceDetails('${device.device_id}')">View</button>
                                        <button class="btn btn-warning btn-sm" onclick="rotateDeviceKey('${device.device_id}')">Rotate Key</button>
                                    </td>
                                </tr>
                            `).join('');
                        } else {
                            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;">No devices registered</td></tr>';
                        }
                    }

                    updateTimestamp();
                } catch (error) {
                    console.error('Error loading devices:', error);
                }
            }

            // Load Queue
            async function loadQueue() {
                try {
                    const response = await fetch(`${API_BASE}/jobs/pending`, {
                        headers: getHeaders()
                    });
                    const data = await response.json();

                    if (data.success) {
                        // Queue stats
                        document.getElementById('queueStatsGrid').innerHTML = `
                            <div class="stat-card">
                                <div class="stat-title">Pending Jobs</div>
                                <div class="stat-value">${data.queue_summary.total_pending}</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-title">Processing</div>
                                <div class="stat-value">${data.queue_summary.total_processing}</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-title">Failed</div>
                                <div class="stat-value">${data.queue_summary.total_failed}</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-title">Completed</div>
                                <div class="stat-value">${data.queue_summary.total_completed}</div>
                            </div>
                        `;

                        // Pending queue
                        const queueTbody = document.querySelector('#queueTable tbody');
                        if (data.pending_queue && data.pending_queue.length > 0) {
                            queueTbody.innerHTML = data.pending_queue.map(job => `
                                <tr>
                                    <td>#${job.job_number}</td>
                                    <td>${job.order_number}</td>
                                    <td><span class="status-badge" style="background: #FF9800;">Priority ${job.priority}</span></td>
                                    <td>${job.waiting_time || 'Just now'}</td>
                                    <td>
                                        <button class="btn btn-primary btn-sm" onclick="viewJobDetailsByNumber('${job.job_number}')">View</button>
                                    </td>
                                </tr>
                            `).join('');
                        } else {
                            queueTbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No pending jobs</td></tr>';
                        }
                    }

                    updateTimestamp();
                } catch (error) {
                    console.error('Error loading queue:', error);
                }
            }

            // View Job Details
            async function viewJobDetails(jobId) {
                try {
                    const response = await fetch(`${API_BASE}/jobs/${jobId}`, {
                        headers: getHeaders()
                    });
                    const data = await response.json();

                    if (data.success) {
                        const job = data.job;
                        document.getElementById('jobDetails').innerHTML = `
                            <p><strong>Job #:</strong> ${job.job_number}</p>
                            <p><strong>Order #:</strong> ${job.order_number}</p>
                            <p><strong>Status:</strong> <span class="status status-${job.status}">${job.status}</span></p>
                            <p><strong>Priority:</strong> ${job.priority}</p>
                            <p><strong>Retry Count:</strong> ${job.retry_count}</p>
                            <p><strong>Device:</strong> ${job.assigned_device || 'Unassigned'}</p>
                            <p><strong>Created:</strong> ${new Date(job.created_at).toLocaleString()}</p>
                            ${job.completed_at ? `<p><strong>Completed:</strong> ${new Date(job.completed_at).toLocaleString()}</p>` : ''}
                            ${job.error_message ? `<p><strong>Error:</strong> <span style="color:red;">${job.error_message}</span></p>` : ''}
                        `;
                        document.getElementById('jobModal').style.display = 'flex';
                    }
                } catch (error) {
                    alert('Error loading job details');
                }
            }

            // Retry Job
            async function retryJob(jobId) {
                if (!confirm('Retry this job?')) return;

                try {
                    const response = await fetch(`${API_BASE}/jobs/${jobId}/retry`, {
                        method: 'POST',
                        headers: getHeaders()
                    });
                    const data = await response.json();

                    if (data.success) {
                        alert('Job queued for retry');
                        loadJobs(currentPage);
                    }
                } catch (error) {
                    alert('Error retrying job');
                }
            }

            // Cancel Job
            async function cancelJob(jobId) {
                if (!confirm('Cancel this job?')) return;

                try {
                    const response = await fetch(`${API_BASE}/jobs/${jobId}/cancel`, {
                        method: 'POST',
                        headers: getHeaders()
                    });
                    const data = await response.json();

                    if (data.success) {
                        alert('Job cancelled');
                        loadJobs(currentPage);
                    }
                } catch (error) {
                    alert('Error cancelling job');
                }
            }

            // Retry all failed jobs
            async function retryFailedJobs() {
                if (!confirm('Retry all failed jobs?')) return;

                // This would call a bulk retry endpoint
                alert('Bulk retry feature coming soon');
            }

            // Cleanup old jobs
            async function cleanupOldJobs() {
                const days = prompt('Delete jobs older than (days):', '30');
                if (!days) return;

                try {
                    const response = await fetch(`${API_BASE}/jobs/cleanup`, {
                        method: 'POST',
                        headers: getHeaders(),
                        body: JSON.stringify({ days: parseInt(days) })
                    });
                    const data = await response.json();

                    if (data.success) {
                        alert(`Cleaned up ${data.jobs_deleted} jobs`);
                        refreshAll();
                    }
                } catch (error) {
                    alert('Error cleaning up jobs');
                }
            }

            // Test webhook
            async function testWebhook() {
                alert('Test webhook - Create a test order in Shopify to see it in action');
            }

            // View Device Details
            async function viewDeviceDetails(deviceId) {
                alert(`Device details for ${deviceId} - Feature coming soon`);
            }

            // Rotate Device Key
            async function rotateDeviceKey(deviceId) {
                if (!confirm('Rotate API key for this device? The old key will stop working.')) return;

                try {
                    const response = await fetch(`${API_BASE}/devices/${deviceId}/rotate-key`, {
                        method: 'POST',
                        headers: getHeaders()
                    });
                    const data = await response.json();

                    if (data.success) {
                        alert(`New API Key: ${data.new_api_key}\\nSecret: ${data.new_api_secret}\\nSave this immediately!`);
                        loadDevices();
                    }
                } catch (error) {
                    alert('Error rotating key');
                }
            }

            // Refresh all
            async function refreshAll() {
                await loadOverview();
                if (document.getElementById('jobsTab').style.display !== 'none') await loadJobs();
                if (document.getElementById('devicesTab').style.display !== 'none') await loadDevices();
                if (document.getElementById('queueTab').style.display !== 'none') await loadQueue();
            }

            // Update timestamp
            function updateTimestamp() {
                document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
            }

            // Close modal
            function closeModal() {
                document.getElementById('jobModal').style.display = 'none';
            }

            // Close modal on outside click
            window.onclick = function(event) {
                const modal = document.getElementById('jobModal');
                if (event.target === modal) {
                    modal.style.display = 'none';
                }
            }

            // Initial load
            loadOverview();

            // Auto-refresh every 30 seconds
            setInterval(() => {
                if (document.getElementById('overviewTab').style.display !== 'none') loadOverview();
            }, 30000);
            
            // Discover network printers
            async function discoverPrinters() {
                showLoading('Discovering network printers...');
                
                try {
                    const response = await fetch(`${API_BASE}/devices/discover/printers`, {
                        headers: getHeaders()
                    });
                    const data = await response.json();
                    
                    if (data.success) {
                        displayDiscoveredDevices(data.printers, 'printer');
                    } else {
                        alert('Discovery failed: ' + data.error);
                    }
                } catch (error) {
                    alert('Error discovering printers: ' + error.message);
                } finally {
                    hideLoading();
                }
            }
            
            // Discover USB printers
            async function discoverUSBPrinters() {
                showLoading('Discovering USB printers...');
                
                try {
                    const response = await fetch(`${API_BASE}/devices/discover/usb-printers`, {
                        headers: getHeaders()
                    });
                    const data = await response.json();
                    
                    if (data.success) {
                        displayDiscoveredDevices(data.printers, 'printer');
                    }
                } catch (error) {
                    alert('Error discovering USB printers: ' + error.message);
                } finally {
                    hideLoading();
                }
            }
            
            // Discover all devices
            async function discoverAll() {
                showLoading('Scanning network for devices...');
                
                try {
                    const response = await fetch(`${API_BASE}/devices/discover/all`, {
                        headers: getHeaders()
                    });
                    const data = await response.json();
                    
                    if (data.success) {
                        const allDevices = [
                            ...data.devices.network_printers.map(p => ({...p, type: 'Network Printer'})),
                            ...data.devices.network_tablets.map(t => ({...t, type: 'Tablet'})),
                            ...data.devices.usb_printers.map(u => ({...u, type: 'USB Printer'}))
                        ];
                        displayDiscoveredDevices(allDevices, 'all');
                    }
                } catch (error) {
                    alert('Error scanning devices: ' + error.message);
                } finally {
                    hideLoading();
                }
            }
            
            // Display discovered devices
            function displayDiscoveredDevices(devices, type) {
                const resultsDiv = document.getElementById('discoveryResults');
                const devicesDiv = document.getElementById('discoveredDevices');
                
                if (!devices || devices.length === 0) {
                    devicesDiv.innerHTML = '<p>No devices found</p>';
                } else {
                    devicesDiv.innerHTML = `
                        <div style="max-height: 300px; overflow-y: auto;">
                            ${devices.map((device, index) => `
                                <div class="printer-item" style="padding: 10px; margin: 5px; border: 1px solid #ddd; border-radius: 8px; cursor: pointer;" 
                                     onclick="selectDevice(${index})">
                                    <input type="radio" name="selectedDevice" value="${index}" id="device_${index}">
                                    <label for="device_${index}">
                                        <strong>${device.name || device.ip || 'Unknown Device'}</strong><br>
                                        ${device.ip ? `IP: ${device.ip}:${device.port || 9100}<br>` : ''}
                                        ${device.model ? `Model: ${device.model}<br>` : ''}
                                        Type: ${device.type || type}<br>
                                        Status: <span class="badge-online">Online</span>
                                    </label>
                                </div>
                            `).join('')}
                        </div>
                    `;
                }
                
                resultsDiv.style.display = 'block';
                window.discoveredDevicesList = devices;
            }
            
            // Register selected device
            async function registerSelectedDevice() {
                const selected = document.querySelector('input[name="selectedDevice"]:checked');
                if (!selected) {
                    alert('Please select a device first');
                    return;
                }
                
                const device = window.discoveredDevicesList[parseInt(selected.value)];
                
                // Prepare registration data
                const registrationData = {
                    shop_domain: shopDomain,
                    name: device.name || `Auto-discovered ${device.type}`,
                    platform: device.type === 'Tablet' ? 'android_tablet' : 'desktop',
                    printer_model: device.model || 'Generic ESC/POS',
                    printer_interface: device.ip ? 'network' : 'usb',
                    printer_connection_string: device.ip ? `${device.ip}:${device.port || 9100}` : device.device_path
                };
                
                try {
                    const response = await fetch(`${API_BASE}/devices/register`, {
                        method: 'POST',
                        headers: getHeaders(),
                        body: JSON.stringify(registrationData)
                    });
                    
                    const data = await response.json();
                    
                    if (response.status === 201) {
                        alert('Device registered successfully!');
                        document.getElementById('discoveryResults').style.display = 'none';
                        loadDevices(); // Refresh device list
                    } else {
                        alert('Registration failed: ' + data.error);
                    }
                } catch (error) {
                    alert('Error registering device: ' + error.message);
                }
            }
            
            // Helper functions
            function showLoading(message) {
                // You can implement a loading overlay
                console.log(message);
            }
            
            function hideLoading() {
                // Hide loading overlay
            }
        </script>
    </body>
    </html>
    """

    shop = request.args.get('shop', '')
    installed = request.args.get('installed', 'false')

    return render_template_string(html, shop=shop, installed=installed)

