document.addEventListener('DOMContentLoaded', () => {

    let chartInstance = null;

    // Check Auth Status on Load
    fetch('/api/check_auth')
        .then(r => r.json())
        .then(data => {
            if (data.logged_in) {
                showDashboard();
            } else {
                showLogin();
            }
        });

    // Login Form
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const errorMsg = document.getElementById('login-error');

        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();

            if (data.success) {
                errorMsg.textContent = '';
                showDashboard();
            } else {
                errorMsg.textContent = data.message || 'Login failed';
            }
        } catch (err) {
            errorMsg.textContent = 'Server error';
        }
    });

    // Logout
    document.getElementById('logout-btn').addEventListener('click', async () => {
        await fetch('/api/logout', { method: 'POST' });
        showLogin();
    });

    // Navigation — fix page title on tab switch
    document.querySelectorAll('.nav-tab').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));

            e.target.classList.add('active');
            const tabId = e.target.getAttribute('data-tab');
            document.getElementById('tab-' + tabId).classList.add('active');

            // ── FIX: update page title on tab switch ──
            const titles = { overview: 'Dashboard Overview', records: 'Records' };
            document.getElementById('page-title').textContent = titles[tabId] || 'Dashboard';

            if (tabId === 'overview') loadDashboard();
            if (tabId === 'records') loadRecords();
        });
    });

    // Modal logic
    const modal = document.getElementById('modal');
    document.getElementById('add-btn').addEventListener('click', () => {
        document.getElementById('record-form').reset();
        document.getElementById('f-id').readOnly = false;
        document.getElementById('modal-title').textContent = 'Add Disaster';
        modal.classList.add('active');
    });

    document.getElementById('cancel-btn').addEventListener('click', () => {
        modal.classList.remove('active');
    });

    // Search
    document.getElementById('search-input').addEventListener('input', (e) => {
        loadRecords(e.target.value);
    });

    // Form Submission (Add/Edit)
    document.getElementById('record-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const event_id = document.getElementById('f-id').value;
        const payload = {
            event_id,
            name:       document.getElementById('f-name').value,
            type:       document.getElementById('f-type').value,
            region:     document.getElementById('f-region').value,
            country:    document.getElementById('f-country').value,
            date:       document.getElementById('f-date').value,
            magnitude:  document.getElementById('f-mag').value,
            casualties: document.getElementById('f-cas').value,
            status:     document.getElementById('f-status').value
        };

        const isEdit = document.getElementById('f-id').readOnly;
        const url    = isEdit ? `/api/disasters/${event_id}` : '/api/disasters';
        const method = isEdit ? 'PUT' : 'POST';

        try {
            const res  = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (data.success) {
                modal.classList.remove('active');
                loadDashboard();
                loadRecords();
            } else {
                alert(data.message || 'Operation failed');
            }
        } catch (err) {
            alert('Server error');
        }
    });

    // ─────────────────────────────────────────
    function showLogin() {
        document.getElementById('dashboard-view').classList.remove('active');
        document.getElementById('login-view').classList.add('active');
    }

    function showDashboard() {
        document.getElementById('login-view').classList.remove('active');
        document.getElementById('dashboard-view').classList.add('active');
        loadDashboard();
        loadRecords();
    }

    // ─────────────────────────────────────────
    async function loadDashboard() {
        const res = await fetch('/api/dashboard');
        if (res.status === 401) return showLogin();
        const data = await res.json();

        document.getElementById('stat-total').textContent  = data.total;
        document.getElementById('stat-active').textContent = data.active;

        if (data.highest_magnitude) {
            document.getElementById('stat-mag').textContent      = data.highest_magnitude.magnitude;
            document.getElementById('stat-mag-name').textContent = data.highest_magnitude.name;
        } else {
            document.getElementById('stat-mag').textContent      = '-';
            document.getElementById('stat-mag-name').textContent = '-';
        }

        document.getElementById('stat-region').textContent = data.most_affected_region;

        // Deadliest table
        const tbody = document.getElementById('deadliest-tbody');
        tbody.innerHTML = '';
        data.deadliest.forEach(d => {
            if (!d) return;
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d.name}</td>
                <td>${d.type}</td>
                <td>${d.date}</td>
                <td>${d.casualties.toLocaleString()}</td>
                <td><span class="status-badge ${d.status === 'Active' ? 'status-active' : 'status-inactive'}">${d.status}</span></td>
            `;
            tbody.appendChild(tr);
        });

        // ── BAR CHART: casualties by disaster type ──
        renderBarChart(data.deadliest);
    }

    // ─────────────────────────────────────────
    function renderBarChart(deadliest) {
        const ctx = document.getElementById('casualties-chart');
        if (!ctx) return;

        // Aggregate casualties by type
        const typeMap = {};
        deadliest.forEach(d => {
            if (!d) return;
            typeMap[d.type] = (typeMap[d.type] || 0) + d.casualties;
        });

        const labels = Object.keys(typeMap);
        const values = Object.values(typeMap);

        const colors = [
            '#72baff',
            '#6ce0a3',
            '#ffb347',
            '#b794f4',
            '#f6ad55',
        ];

        // Destroy old chart if exists
        if (chartInstance) {
            chartInstance.destroy();
            chartInstance = null;
        }

        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Total Casualties',
                    data: values,
                    backgroundColor: colors.slice(0, labels.length),
                    borderRadius: 10,
                    maxBarThickness: 90,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: ctx => ` ${ctx.parsed.y.toLocaleString()} casualties`
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#9fb0cf', font: { family: 'Inter' } },
                        grid:  { color: 'rgba(255,255,255,0.04)' }
                    },
                    y: {
                        ticks: {
                            color: '#9fb0cf',
                            font: { family: 'Inter' },
                            callback: v => v.toLocaleString()
                        },
                        grid: { color: 'rgba(255,255,255,0.05)' }
                    }
                }
            }
        });
    }

    // ─────────────────────────────────────────
    async function loadRecords(search = '') {
        const url = search ? `/api/disasters?search=${encodeURIComponent(search)}` : '/api/disasters';
        const res = await fetch(url);
        if (res.status === 401) return showLogin();
        const data = await res.json();

        const tbody = document.getElementById('records-tbody');
        tbody.innerHTML = '';

        // ── EMPTY STATE ──
        if (!data.length) {
            document.getElementById('empty-state').hidden = false;
        } else {
            document.getElementById('empty-state').hidden = true;
            data.forEach(d => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${d.event_id}</td>
                    <td>${d.name}</td>
                    <td>${d.type}</td>
                    <td>${d.region}</td>
                    <td>${d.magnitude}</td>
                    <td><span class="status-badge ${d.status === 'Active' ? 'status-active' : 'status-inactive'}">${d.status}</span></td>
                    <td>
                        <button class="action-btn edit"   data-id="${d.event_id}">Edit</button>
                        <button class="action-btn delete" data-id="${d.event_id}">Delete</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        document.getElementById('rec-total').textContent = data.length;
        document.getElementById('rec-active').textContent = data.filter(r => r.status === 'Active').length;
        document.getElementById('rec-inactive').textContent = data.filter(r => r.status === 'Inactive').length;

        document.querySelectorAll('.action-btn.edit').forEach(btn => {
            btn.addEventListener('click', e => editRecord(e.target.getAttribute('data-id'), data));
        });
        document.querySelectorAll('.action-btn.delete').forEach(btn => {
            btn.addEventListener('click', e => deleteRecord(e.target.getAttribute('data-id')));
        });
    }

    // ─────────────────────────────────────────
    function editRecord(id, dataList) {
        const record = dataList.find(d => d.event_id === id);
        if (!record) return;

        document.getElementById('f-id').value      = record.event_id;
        document.getElementById('f-id').readOnly   = true;
        document.getElementById('f-name').value    = record.name;
        document.getElementById('f-type').value    = record.type;
        document.getElementById('f-region').value  = record.region;
        document.getElementById('f-country').value = record.country;
        document.getElementById('f-date').value    = record.date;
        document.getElementById('f-mag').value     = record.magnitude;
        document.getElementById('f-cas').value     = record.casualties;
        document.getElementById('f-status').value  = record.status;

        document.getElementById('modal-title').textContent = 'Edit Disaster';
        modal.classList.add('active');
    }

    // ─────────────────────────────────────────
    async function deleteRecord(id) {
        if (!confirm(`Are you sure you want to delete ${id}?`)) return;

        try {
            const res  = await fetch(`/api/disasters/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                loadDashboard();
                loadRecords(document.getElementById('search-input').value);
            } else {
                alert(data.message || 'Delete failed');
            }
        } catch (err) {
            alert('Server error');
        }
    }
});
