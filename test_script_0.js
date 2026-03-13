
        const API = "/areadocliente";
        const app = {
            token: localStorage.getItem("hemn_token"),
            uploadedFiles: { unify: [], enrich: [], carrier: [], split: [], cep: [] },
            tasks: [],
            adminUsers: [], // Store users for edit lookup
            theme: localStorage.getItem("hemn_theme") || "dark",
            notifications: JSON.parse(localStorage.getItem("hemn_notifications") || "[]"),
            monChart: null,
            monInterval: null,

            init() {
                // Override native alert/confirm with toast or modal if needed, 
                // but we will use app.confirm and app.alert explicitly for better control.
                document.documentElement.setAttribute('data-theme', this.theme);
                if (this.token) {
                    document.getElementById('login-overlay').style.display = 'none';
                    this.refreshUser();
                    // Restore from localStorage (INSTANT UI)
                    const savedTasks = JSON.parse(localStorage.getItem('hemn_active_tasks') || '[]');
                    savedTasks.forEach(t => {
                        if (!this.tasks.find(x => x.id === t.id)) {
                            this.tasks.push(t);
                            this.renderGlobalTaskCard(t.id, t.mid || 'status', t);
                            if (t.mid) {
                                this.renderTaskCard(t.id, t.mid, t);
                            }
                        }
                    });

                    // Restore uploaded files state
                    const savedFiles = JSON.parse(localStorage.getItem('hemn_uploaded_files') || '{}');
                    Object.keys(this.uploadedFiles).forEach(mid => {
                        if (savedFiles[mid]) {
                            this.uploadedFiles[mid] = savedFiles[mid];
                            savedFiles[mid].forEach(fid => {
                                const name = fid.split('_').slice(1).join('_') || fid;
                                this.renderFile(mid, name, fid);
                            });
                        }
                    });

                    // Await full recovery from server to sync state
                    this.recoverActiveTasks().then(() => {
                        this.pollTasks();
                    });

                    // Restore last module (persistence)
                    const lastMod = localStorage.getItem('hemn_last_module') || 'inicio';
                    const navEl = document.getElementById(`nav-${lastMod}`);
                    this.showModule(lastMod, navEl);
                    this.setupDragAndDrop();
                    this.renderNotifications();

                    // Universal Robust Closer
                    const handleGlobalClick = (e) => {
                        const dropdown = document.getElementById('notification-dropdown');
                        const bellBtn = document.getElementById('btn-notifications');
                        if (!dropdown || dropdown.style.display !== 'block') return;

                        const rect = dropdown.getBoundingClientRect();
                        const isInside = e.clientX >= rect.left && e.clientX <= rect.right && 
                                         e.clientY >= rect.top && e.clientY <= rect.bottom;

                        let onButton = false;
                        if (bellBtn) {
                            const bRect = bellBtn.getBoundingClientRect();
                            onButton = e.clientX >= bRect.left && e.clientX <= bRect.right &&
                                       e.clientY >= bRect.top && e.clientY <= bRect.bottom;
                        }

                        if (!isInside && !onButton) {
                            dropdown.style.display = 'none';
                        }
                    };
                    window.addEventListener('mousedown', handleGlobalClick, true);
                    window.addEventListener('touchstart', (e) => {
                        if (e.touches && e.touches[0]) {
                            handleGlobalClick(e.touches[0]);
                        }
                    }, true);
                }
            },

            // NOTIFICATIONS SYSTEM
            addNotification(title, message, type = 'info') {
                const notif = {
                    id: Date.now(),
                    title,
                    message,
                    type,
                    time: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
                    date: new Date().toLocaleDateString('pt-BR')
                };
                this.notifications.unshift(notif);
                if (this.notifications.length > 50) this.notifications.pop();
                localStorage.setItem("hemn_notifications", JSON.stringify(this.notifications));
                this.renderNotifications();
                this.showBadge();
            },

            renderNotifications() {
                const list = document.getElementById('notification-list');
                if (!list) return;

                if (this.notifications.length === 0) {
                    list.innerHTML = `<div style="padding: 40px 20px; text-align: center; color: var(--text-3); font-size: 13px;">
                                <i class="fas fa-bell-slash" style="font-size: 24px; display: block; margin-bottom: 10px; opacity: 0.3;"></i>
                                Nenhuma notificação por enquanto.
                            </div>`;
                    return;
                }

                list.innerHTML = this.notifications.map(n => `
                    <div class="notif-item ${n.type}">
                        <div class="notif-title">${n.title}</div>
                        <div class="notif-msg">${n.message}</div>
                        <span class="notif-time">${n.date} às ${n.time}</span>
                    </div>
                `).join('');
            },

            toggleNotifications() {
                const dropdown = document.getElementById('notification-dropdown');
                if (!dropdown) return;

                const isVisible = dropdown.style.display === 'block';

                if (isVisible) {
                    dropdown.style.display = 'none';
                } else {
                    dropdown.style.display = 'block';
                    this.hideBadge();
                }
            },

            clearNotifications() {
                this.notifications = [];
                localStorage.setItem("hemn_notifications", "[]");
                this.renderNotifications();
                this.hideBadge();
            },

            showBadge() {
                const badge = document.getElementById('notification-badge');
                if (badge) {
                    badge.innerText = this.notifications.length > 9 ? '9+' : this.notifications.length;
                    badge.style.display = 'flex';
                }
            },

            hideBadge() {
                const badge = document.getElementById('notification-badge');
                if (badge) badge.style.display = 'none';
            },

            toggleSidebar() {
                const sidebar = document.getElementById('sidebar');
                const overlay = document.getElementById('sidebar-overlay');
                sidebar.classList.toggle('open');
                overlay.classList.toggle('active');
            },

            // PREMIUM MODAL SYSTEM
            confirm(title, message, options = {}) {
                return new Promise((resolve) => {
                    const modal = document.getElementById('premium-modal');
                    const titleEl = document.getElementById('modal-title');
                    const msgEl = document.getElementById('modal-message');
                    const btnConfirm = document.getElementById('modal-btn-confirm');
                    const btnCancel = document.getElementById('modal-btn-cancel');
                    const iconContainer = document.getElementById('modal-icon-container');

                    titleEl.innerText = title;
                    msgEl.innerText = message;
                    btnConfirm.innerText = options.confirmText || 'Confirmar';
                    btnCancel.style.display = (options.showCancel === false) ? 'none' : 'flex';
                    if (options.cancelText) btnCancel.innerText = options.cancelText;

                    // Icon and Color based on type
                    let iconHtml = '<i class="fas fa-exclamation-circle"></i>';
                    let iconColor = 'var(--text-2)';
                    if (options.type === 'error') {
                        iconHtml = '<i class="fas fa-times-circle"></i>';
                        iconColor = '#ef4444';
                    } else if (options.type === 'success') {
                        iconHtml = '<i class="fas fa-check-circle"></i>';
                        iconColor = '#10b981';
                    } else if (options.type === 'warning') {
                        iconHtml = '<i class="fas fa-exclamation-triangle"></i>';
                        iconColor = '#f59e0b';
                    } else if (options.type === 'info') {
                        iconHtml = '<i class="fas fa-info-circle"></i>';
                        iconColor = '#3b82f6';
                    }
                    iconContainer.innerHTML = iconHtml;
                    iconContainer.style.color = iconColor;

                    modal.style.display = 'flex';

                    const cleanup = (val) => {
                        modal.style.display = 'none';
                        btnConfirm.onclick = null;
                        btnCancel.onclick = null;
                        resolve(val);
                    };

                    btnConfirm.onclick = () => cleanup(true);
                    btnCancel.onclick = () => cleanup(false);
                });
            },

            alert(title, message, options = {}) {
                return this.confirm(title, message, { ...options, showCancel: false });
            },

            setupDragAndDrop() {
                const zones = document.querySelectorAll('.drop-zone');
                zones.forEach(zone => {
                    const input = zone.querySelector('input[type="file"]');
                    const mid = input.id.split('-').pop();

                    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
                        zone.addEventListener(evt, e => {
                            e.preventDefault();
                            e.stopPropagation();
                        }, false);
                    });

                    ['dragenter', 'dragover'].forEach(evt => {
                        zone.addEventListener(evt, () => zone.classList.add('drag-over'), false);
                    });

                    ['dragleave', 'drop'].forEach(evt => {
                        zone.addEventListener(evt, () => zone.classList.remove('drag-over'), false);
                    });

                    zone.addEventListener('drop', (e) => {
                        const dt = e.dataTransfer;
                        const files = dt.files;
                        if (files.length > 0) {
                            input.files = files;
                            this.handleFiles(input, mid);
                        }
                    }, false);
                });
            },

            toggleTheme() {
                this.theme = this.theme === 'dark' ? 'light' : 'dark';
                document.documentElement.setAttribute('data-theme', this.theme);
                localStorage.setItem("hemn_theme", this.theme);
                const icon = document.querySelector('.icon-btn i.fa-moon, .icon-btn i.fa-sun');
                if (icon) icon.className = this.theme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
            },

            async login() {
                const u = document.getElementById('login-user').value;
                const p = document.getElementById('login-pass').value;
                try {
                    const res = await fetch(`${API}/login`, {
                        method: 'POST',
                        body: new URLSearchParams({ username: u, password: p })
                    });
                    const data = await res.json();
                    if (res.ok) {
                        localStorage.setItem("hemn_token", data.access_token);
                        this.showToast("acesso autorizado", "success");
                        setTimeout(() => location.reload(), 800);
                    } else {
                        this.showToast("usuário ou senha inválidos", "error");
                    }
                } catch (e) {
                    this.showToast("erro de conexão", "error");
                }
            },

            logout() {
                localStorage.removeItem("hemn_token");
                location.reload();
            },

            async refreshUser() {
                try {
                    const res = await fetch(`${API}/me`, { headers: { 'Authorization': `Bearer ${this.token}` } });
                    const user = await res.json();
                    if (res.ok) {
                        this.user = user;
                        if (document.getElementById('user-display')) document.getElementById('user-display').innerText = user.full_name;
                        if (document.getElementById('avatar-initial')) document.getElementById('avatar-initial').innerText = user.full_name.charAt(0).toUpperCase();
                        if (document.getElementById('credits-display')) {
                            const oldText = document.getElementById('credits-display').innerText;
                            const newBalance = Math.max(0, user.total_limit - user.current_usage).toFixed(1);
                            const newText = `Saldo: ${newBalance} Cr`;
                            if (oldText !== "--" && oldText !== "Saldo: --" && oldText !== newText) {
                                this.addNotification("Saldo Atualizado", `Seu saldo agora é de ${newBalance} créditos.`, "info");
                            }
                            document.getElementById('credits-display').innerText = newText;
                        }

                        // Atualiza extrato se estiver na tela de dashboard
                        if (this.currentModule === 'dashboard') this.refreshDashboard();

                        // Update Greeting
                        const hour = new Date().getHours();
                        let greet = "Boa noite";
                        if (hour < 5) greet = "Boa madrugada";
                        else if (hour < 12) greet = "Bom dia";
                        else if (hour < 18) greet = "Boa tarde";
                        document.getElementById('main-greeting').innerText = `${greet}, ${user.full_name.split(' ')[0]}!`;

                        // Handle Admin Menu
                        if (user.role === 'ADMIN') {
                            document.getElementById('admin-menu').style.display = 'block';
                            if (document.getElementById('admin-card-users')) document.getElementById('admin-card-users').style.display = 'flex';
                            if (document.getElementById('admin-card-monitor')) document.getElementById('admin-card-monitor').style.display = 'flex';
                            this.populateAdminUserSelect();
                        }

                        // Restore last module or default to Inicio
                        const lastModule = localStorage.getItem('hemn_last_module') || 'inicio';
                        const lastNavEl = document.getElementById(`nav-${lastModule}`);
                        this.showModule(lastModule, lastNavEl);

                        // Set Welcome Message
                        const welcomeEl = document.getElementById('welcome-title');
                        if (welcomeEl) welcomeEl.innerText = `${greet}, ${user.full_name.split(' ')[0]}!`;

                        // Update Status Cards
                        const balanceEl = document.getElementById('status-balance');
                        if (balanceEl) balanceEl.innerText = `${Math.max(0, user.total_limit - user.current_usage).toFixed(1)} Cr`;

                        const roleEl = document.getElementById('status-role');
                        if (roleEl) roleEl.innerText = user.role === 'ADMIN' ? 'Administrador' : 'Usuário Bronze';
                    } else {
                        this.logout();
                    }
                } catch (e) {
                    console.error("User refresh failed", e);
                }
            },

            showModule(mid, element) {
                // Persist the current module so F5 restores it
                localStorage.setItem('hemn_last_module', mid);

                // Update Sidebar
                document.querySelectorAll('.nav-link').forEach(n => n.classList.remove('active'));
                if (element) element.classList.add('active');

                // Update Views
                document.querySelectorAll('.module-view').forEach(m => m.style.display = 'none');
                const nextModule = document.getElementById(`module-${mid}`);
                if (nextModule) {
                    nextModule.style.display = 'block';
                    nextModule.classList.add('fade-in-up');
                    if (mid === 'admin') this.refreshAdminData();
                    if (mid === 'dashboard') {
                        // More aggressive visibility check for admins
                        const sel = document.getElementById('admin-user-selector');
                        const isAdmin = (this.user && this.user.role === 'ADMIN') ||
                            (document.getElementById('admin-menu') && document.getElementById('admin-menu').style.display === 'block');

                        if (sel && isAdmin) {
                            sel.style.display = 'block';
                        }
                        this.refreshDashboard();
                    }

                    // Handle Monitoring Lifecycle
                    if (this.monInterval) clearInterval(this.monInterval);
                    if (mid === 'monitor') {
                        this.initMonitorChart();
                        this.updateMonitorStats();
                        this.monInterval = setInterval(() => this.updateMonitorStats(), 3000);
                    }
                }
            },

            initMonitorChart() {
                if (this.monChart) this.monChart.destroy();
                const canvas = document.getElementById('mon-cpuChart');
                if (!canvas) return;
                const ctx = canvas.getContext('2d');
                this.monChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: Array(20).fill(''),
                        datasets: [{
                            label: 'CPU Usage',
                            data: Array(20).fill(0),
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            pointRadius: 0,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { min: 0, max: 100, ticks: { display: false }, grid: { color: 'rgba(255,255,255,0.05)' } },
                            x: { grid: { display: false } }
                        }
                    }
                });
            },

            async updateMonitorStats() {
                try {
                    const res = await fetch(`${API}/admin/monitor/stats`, {
                        headers: { 'Authorization': `Bearer ${this.token}` }
                    });
                    if (!res.ok) throw new Error("Unauthorized");
                    const data = await res.json();

                    document.getElementById('mon-cpu-val').innerText = data.system.cpu;
                    document.getElementById('mon-ram-val').innerText = data.system.ram;
                    document.getElementById('mon-ram-progress').style.width = data.system.ram + '%';
                    document.getElementById('mon-disk-val').innerText = data.system.disk + '%';

                    if (this.monChart) {
                        this.monChart.data.datasets[0].data.shift();
                        this.monChart.data.datasets[0].data.push(data.system.cpu);
                        this.monChart.update('none');
                    }

                    const ch = data.clickhouse;
                    const st = document.getElementById('mon-ch-status');
                    st.innerText = ch.status;
                    st.style.color = ch.status === 'ONLINE' ? '#10b981' : '#ef4444';
                    document.getElementById('mon-ch-version').innerText = ch.version || '--';
                    document.getElementById('mon-ch-queries').innerText = ch.active_queries || '0';
                    document.getElementById('mon-ch-ram').innerText = ch.memory_usage_bytes ? (ch.memory_usage_bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB' : '--';
                    document.getElementById('mon-ch-uptime').innerText = ch.uptime_seconds ? (ch.uptime_seconds / 3600).toFixed(1) + ' hrs' : '--';

                    const eng = data.engine;
                    document.getElementById('mon-engine-active').innerText = eng.tasks.active;
                    document.getElementById('mon-engine-queued').innerText = eng.tasks.queued;
                    document.getElementById('mon-engine-completed').innerText = eng.tasks.completed;
                    document.getElementById('mon-engine-slots').innerText = eng.enrich_slots_available;
                } catch (e) {
                    console.error("Monitor Error:", e);
                }
            },

            // ADMIN MANAGEMENT FUNCTIONS
            async refreshAdminData() {
                try {
                    const res = await fetch(`${API}/admin/users`, { headers: { 'Authorization': `Bearer ${this.token}` } });
                    const users = await res.json();
                    if (res.ok) {
                        this.adminUsers = users; // Cache for editing
                        this.renderAdminTable(users);
                        this.updateAdminStats(users);
                    }
                } catch (e) {
                    this.showToast("Falha ao carregar dados admin", "error");
                }
            },

            renderAdminTable(users) {
                const tbody = document.querySelector("#admin-users-table tbody");
                tbody.innerHTML = "";
                users.forEach(u => {
                    const row = document.createElement("tr");
                    const statusBadge = u.status === "ACTIVE" ? 'badge-green' : 'badge-red';
                    const usagePct = ((u.current_usage / u.total_limit) * 100).toFixed(1);

                    row.innerHTML = `
                        <td>
                            <div class="emp-name" style="font-size:14px">${u.full_name}</div>
                            <div style="font-size:11px; color:var(--text-dim)">@${u.username} | ${u.role === 'ADMIN' ? 'ADMINISTRADOR' : 'USUÁRIO'}</div>
                        </td>
                        <td><div class="badge ${statusBadge}">${u.status === 'ACTIVE' ? 'ATIVO' : u.status === 'REVOKED' ? 'REVOGADO' : 'BLOQUEADO'}</div></td>
                        <td><div style="font-size:12px">${u.expiration.split('-').reverse().join('/')}</div></td>
                        <td>
                            <div style="font-size:13px; font-weight:600">${u.current_usage.toLocaleString()} / ${u.total_limit >= 1000000 ? '∞' : u.total_limit.toLocaleString()}</div>
                            <div style="font-size:10px; color:var(--text-dim)">${usagePct}% consumido</div>
                        </td>
                        <td>
                            <div style="display:flex; gap:8px">
                                <button class="btn-primary" onclick="app.viewUserDashboard('${u.username}')" style="padding: 5px 10px; font-size:11px">
                                    <i class="fas fa-chart-line"></i> Extrato
                                </button>
                                <button class="btn-outline" onclick="app.toggleUserStatus('${u.username}', '${u.status}')" style="padding: 5px 10px; font-size:11px">
                                    ${u.status === 'ACTIVE' ? 'Bloquear' : 'Ativar'}
                                </button>
                                <button class="btn-outline" onclick="app.openUserModal('${u.username}')" style="padding: 5px 10px; font-size:11px">Editar</button>
                            </div>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            },

            updateAdminStats(users) {
                const active = users.filter(u => u.status === 'ACTIVE').length;
                const blocked = users.length - active;
                const usage = users.reduce((acc, curr) => acc + curr.current_usage, 0);

                document.getElementById("admin-stat-active").innerText = active;
                document.getElementById("admin-stat-blocked").innerText = blocked;
                document.getElementById("admin-stat-usage").innerText = usage.toLocaleString() + " Cr";
            },

            async toggleUserStatus(username, currentStatus) {
                const newStatus = currentStatus === "ACTIVE" ? "REVOKED" : "ACTIVE";
                try {
                    const res = await fetch(`${API}/admin/users/${username}`, {
                        method: 'PUT',
                        headers: {
                            'Authorization': `Bearer ${this.token}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ status: newStatus })
                    });
                    if (res.ok) {
                        this.showToast(`Usuário ${username} atualizado`, "success");
                        this.refreshAdminData();
                    }
                } catch (e) {
                    this.showToast("Erro ao atualizar status", "error");
                }
            },

            openUserModal(userDataOrUsername = null) {
                const modal = document.getElementById('user-modal');
                const title = document.getElementById('modal-title');

                let user = null;
                if (typeof userDataOrUsername === 'string') {
                    user = this.adminUsers.find(u => u.username === userDataOrUsername);
                } else {
                    user = userDataOrUsername;
                }

                if (user) {
                    title.innerText = "Editar Usuário";
                    document.getElementById('edit-username-orig').value = user.username;
                    document.getElementById('modal-full-name').value = user.full_name;
                    document.getElementById('modal-username').value = user.username;
                    document.getElementById('modal-password').value = "";
                    document.getElementById('modal-limit').value = user.total_limit;
                    document.getElementById('modal-expiration').value = user.expiration;
                    document.getElementById('modal-role').value = user.role;
                } else {
                    title.innerText = "Novo Usuário";
                    document.getElementById('edit-username-orig').value = "";
                    document.getElementById('modal-full-name').value = "";
                    document.getElementById('modal-username').value = "";
                    document.getElementById('modal-password').value = "";
                    document.getElementById('modal-limit').value = "1000";
                    document.getElementById('modal-expiration').value = "2099-12-31";
                    document.getElementById('modal-role').value = "USER";
                }
                modal.style.display = "flex";
            },

            closeUserModal() {
                document.getElementById('user-modal').style.display = "none";
            },

            async saveUser() {
                const origUsername = document.getElementById('edit-username-orig').value;
                const body = {
                    full_name: document.getElementById('modal-full-name').value,
                    username: document.getElementById('modal-username').value,
                    total_limit: parseFloat(document.getElementById('modal-limit').value),
                    expiration: document.getElementById('modal-expiration').value,
                    role: document.getElementById('modal-role').value
                };

                const pass = document.getElementById('modal-password').value;
                if (pass) body.password = pass;

                try {
                    let res;
                    if (origUsername) {
                        res = await fetch(`${API}/admin/users/${origUsername}`, {
                            method: 'PUT',
                            headers: { 'Authorization': `Bearer ${this.token}`, 'Content-Type': 'application/json' },
                            body: JSON.stringify(body)
                        });
                    } else {
                        res = await fetch(`${API}/admin/users`, {
                            method: 'POST',
                            headers: { 'Authorization': `Bearer ${this.token}`, 'Content-Type': 'application/json' },
                            body: JSON.stringify(body)
                        });
                    }

                    if (res.ok) {
                        this.showToast("Usuário salvo com sucesso", "success");
                        this.closeUserModal();
                        this.refreshAdminData();
                    } else {
                        const err = await res.json();
                        this.showToast(err.detail || "Erro ao salvar", "error");
                    }
                } catch (e) {
                    this.showToast("Erro de rede", "error");
                }
            },

            async refreshDashboard() {
                try {
                    // Admin: check if viewing another user
                    const adminSearch = document.getElementById('admin-view-user-search');
                    const viewingUser = adminSearch ? adminSearch.dataset.username || '' : '';
                    const badge = document.getElementById('admin-viewing-badge');
                    const badgeName = document.getElementById('admin-viewing-name');

                    if (viewingUser && badge) {
                        badge.style.display = 'flex';
                        badgeName.textContent = `Visualizando: ${viewingUser}`;
                    } else if (badge) {
                        badge.style.display = 'none';
                    }

                    // Choose correct endpoints
                    const period = document.getElementById('dash-filter-period')?.value || 'total';
                    let daysParam = "";
                    if (period === 'today') daysParam = "?days=0";
                    else if (period === 'week') daysParam = "?days=7";
                    else if (period === 'month') daysParam = "?days=30";

                    const statsUrl = viewingUser
                        ? `${API}/admin/stats/${encodeURIComponent(viewingUser)}`
                        : `${API}/credits/stats`;
                    const stmtUrl = viewingUser
                        ? `${API}/admin/statement/${encodeURIComponent(viewingUser)}${daysParam}`
                        : `${API}/credits/statement${daysParam}`;

                    // Fetch Stats
                    const resStats = await fetch(statsUrl, { headers: { 'Authorization': `Bearer ${this.token}` } });
                    const stats = await resStats.json();
                    if (resStats.ok) {
                        document.getElementById('dash-spent-today').innerText = stats.spent_today.toFixed(1);
                        document.getElementById('dash-spent-month').innerText = stats.spent_month.toFixed(1);
                        document.getElementById('dash-balance').innerText = stats.balance.toFixed(1);
                        this.renderUsageChart(stats.chart);
                    }

                    // Fetch Statement
                    const resLogs = await fetch(stmtUrl, { headers: { 'Authorization': `Bearer ${this.token}` } });
                    const logs = await resLogs.json();
                    if (resLogs.ok) {
                        this.renderStatementTable(logs);
                    }
                } catch (e) {
                    console.error("Dashboard refresh failed", e);
                }
            },

            async downloadFile(taskId) {
                try {
                    this.showToast("Iniciando download...", "info");
                    const res = await fetch(`${API}/download/${taskId}`, {
                        headers: { 'Authorization': `Bearer ${this.token}` }
                    });

                    if (!res.ok) {
                        const err = await res.json();
                        throw new Error(err.detail || "Erro no download");
                    }

                    const blob = await res.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    const contentDisp = res.headers.get('content-disposition');
                    let filename = `resultado_${taskId}.xlsx`;
                    if (contentDisp && contentDisp.includes('filename=')) {
                        filename = contentDisp.split('filename=')[1].replace(/"/g, '');
                    }

                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    this.showToast("Download concluído", "success");
                    // Refresh para mostrar o novo log de débito se houver
                    this.refreshDashboard();
                } catch (e) {
                    this.showToast(e.message, "error");
                }
            },

            async populateAdminUserSelect() {
                if (!this.user || this.user.role !== 'ADMIN') return;
                const selectorDiv = document.getElementById('admin-user-selector');
                if (selectorDiv) {
                    selectorDiv.style.display = 'block';
                    console.log('Admin selector activated');
                }
                // Fetch all users
                try {
                    const res = await fetch(`${API}/admin/users`, { headers: { 'Authorization': `Bearer ${this.token}` } });
                    if (!res.ok) return;
                    const users = await res.json();
                    const datalist = document.getElementById('admin-users-list');
                    if (!datalist) return;

                    datalist.innerHTML = '';
                    users.forEach(u => {
                        const opt = document.createElement('option');
                        opt.value = `${u.full_name} (@${u.username})`;
                        opt.dataset.username = u.username; // Store for lookup
                        datalist.appendChild(opt);
                    });

                    // Add this for easy lookup mapping
                    this.adminUserMap = users.reduce((acc, u) => {
                        acc[`${u.full_name} (@${u.username})`] = u.username;
                        return acc;
                    }, {});

                } catch (e) {
                    console.error('Failed to fetch users for admin select', e);
                }
            },

            handleUserSearchChange(input) {
                const val = input.value;
                const username = this.adminUserMap ? this.adminUserMap[val] : null;
                if (username) {
                    input.dataset.username = username;
                } else if (!val) {
                    delete input.dataset.username;
                }
                this.refreshDashboard();
            },

            clearUserSearch() {
                const input = document.getElementById('admin-view-user-search');
                if (input) {
                    input.value = '';
                    delete input.dataset.username;
                    this.refreshDashboard();
                }
            },

            viewUserDashboard(username) {
                const input = document.getElementById('admin-view-user-search');
                const user = this.adminUsers ? this.adminUsers.find(u => u.username === username) : null;
                if (input && user) {
                    input.value = `${user.full_name} (@${user.username})`;
                    input.dataset.username = username;
                    this.showModule('dashboard', document.getElementById('nav-dashboard'));
                }
            },

            renderUsageChart(data) {
                const ctx = document.getElementById('usageChart').getContext('2d');
                if (this.usageChartInstance) this.usageChartInstance.destroy();

                this.usageChartInstance = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.map(d => d.date.split('-').reverse().join('/')),
                        datasets: [{
                            label: 'Consumo de Créditos',
                            data: data.map(d => d.amount),
                            borderColor: '#3a7bd5',
                            backgroundColor: 'rgba(58, 123, 213, 0.1)',
                            fill: true,
                            tension: 0.4,
                            pointRadius: 4,
                            pointBackgroundColor: '#3a7bd5'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                            x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                        }
                    }
                });
            },

            renderStatementTable(logs) {
                const tbody = document.getElementById('statement-tbody');
                tbody.innerHTML = "";
                logs.forEach(l => {
                    const dateObj = new Date(l.timestamp);
                    const dateStr = dateObj.toLocaleString('pt-BR');
                    const badgeClass = l.type === 'DEBIT' ? 'badge-red' : 'badge-green';
                    const amountPrefix = l.type === 'DEBIT' ? '-' : '+';

                    const row = document.createElement('tr');
                    let downloadBtn = '';
                    if (l.task_id) {
                        const now = new Date();
                        const diffDays = Math.floor((now - dateObj) / (1000 * 60 * 60 * 24));
                        if (diffDays <= 30) {
                            downloadBtn = `
                                <button class="icon-btn" onclick="app.downloadFile('${l.task_id}')" title="Re-baixar arquivo" style="margin-left:8px; padding:4px; font-size:12px;">
                                    <i class="fas fa-cloud-download-alt" style="color:var(--primary);"></i>
                                </button>
                            `;
                        }
                    }

                    const typeMap = { 'DEBIT': 'DÉBITO', 'CREDIT': 'CRÉDITO' };
                    const moduleMap = {
                        'ENRICH': 'ENRIQUECIMENTO',
                        'EXTRACT': 'EXTRAÇÃO',
                        'EXTRACTION': 'EXTRAÇÃO',
                        'CARRIER': 'OPERADORA',
                        'UNIFY': 'UNIFICAÇÃO',
                        'SPLIT': 'DIVISÃO',
                        'DOWNLOAD': 'DOWNLOAD',
                        'MANUAL': 'MANUAL'
                    };
                    const typeLabel = typeMap[l.type] || l.type;
                    const moduleLabel = moduleMap[l.module] || l.module;

                    row.innerHTML = `
                        <td style="font-size: 11px; font-weight: 500;">${dateStr}</td>
                        <td><span class="badge badge-blue" style="font-size: 10px;">${moduleLabel}</span></td>
                        <td style="font-size: 12px; color: var(--text-2);">${l.description}</td>
                        <td style="font-weight: 700; color: ${l.type === 'DEBIT' ? '#ef4444' : '#10b981'}">${amountPrefix}${l.amount.toFixed(1)}</td>
                        <td style="display: flex; align-items: center; gap: 8px; border: none;"><span class="badge ${badgeClass}">${typeLabel}</span> ${downloadBtn}</td>
                    `;
                    tbody.appendChild(row);
                });
            },

            async handleFiles(input, mid) {
                const files = input.files;
                if (files.length > 0) {
                    // Limpa lista anterior para este módulo (conforme pedido: "nao precisa ficar")
                    this.uploadedFiles[mid] = [];
                    const list = document.getElementById(`file-list-${mid}`);
                    if (list) list.innerHTML = '';
                    localStorage.setItem('hemn_uploaded_files', JSON.stringify(this.uploadedFiles));
                }

                for (let f of files) {
                    const fd = new FormData(); fd.append("file", f);
                    try {
                        const res = await fetch(`${API}/upload`, {
                            method: 'POST',
                            headers: { 'Authorization': `Bearer ${this.token}` },
                            body: fd
                        });
                        const final = await res.json();
                        if (res.ok) {
                            this.uploadedFiles[mid].push(final.file_id);
                            localStorage.setItem('hemn_uploaded_files', JSON.stringify(this.uploadedFiles));
                            this.renderFile(mid, f.name, final.file_id);
                            this.showToast(`Arquivo Pronto: ${f.name}`, "info");
                        }
                    } catch (e) {
                        this.showToast("Falha no upload", "error");
                    }
                }
            },

            removeFile(mid, fid) {
                this.uploadedFiles[mid] = this.uploadedFiles[mid].filter(id => id !== fid);
                localStorage.setItem('hemn_uploaded_files', JSON.stringify(this.uploadedFiles));
                const list = document.getElementById(`file-list-${mid}`);
                if (list) list.innerHTML = '';
                this.uploadedFiles[mid].forEach(id => {
                    const name = id.split('_').slice(1).join('_') || id;
                    this.renderFile(mid, name, id);
                });
            },

            renderFile(mid, name, fid) {
                const list = document.getElementById(`file-list-${mid}`);
                const item = document.createElement('div');
                item.className = 'nav-link fade-in';
                item.style.marginTop = "8px";
                item.style.background = "rgba(16, 185, 129, 0.1)";
                item.style.border = "1px solid rgba(16, 185, 129, 0.2)";
                item.style.display = "flex";
                item.style.alignItems = "center";
                item.innerHTML = `<i class="icon fas fa-file-csv" style="color:#10b981; margin-right: 10px;"></i> <span style="flex-grow: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${name}</span> <i class="fas fa-times" style="color:#ef4444; margin-left:10px; cursor:pointer;" onclick="app.removeFile('${mid}', '${fid}')" title="Remover Arquivo"></i>`;
                list.appendChild(item);
            },

            showToast(msg, type = "info") {
                const container = document.getElementById('toast-container');
                const toast = document.createElement('div');
                toast.className = `toast ${type}`;
                toast.innerHTML = `<div style="display:flex; align-items:center; gap:12px">
                    <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
                    <span>${msg.toUpperCase()}</span>
                </div>`;
                container.appendChild(toast);
                setTimeout(() => toast.remove(), 4000);
            },

            async startTask(endpoint, body, mid) {
                try {
                    const res = await fetch(`${API}${endpoint}`, {
                        method: 'POST',
                        headers: { 'Authorization': `Bearer ${this.token}`, 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    const data = await res.json();
                    if (!res.ok) {
                        this.showToast(data.detail || "Erro no processamento", "error");
                        return null;
                    }

                    if (data.task_id) {
                        const taskInfo = { id: data.task_id, mid: mid, startTime: Date.now() };
                        this.tasks.push(taskInfo);
                        // Persist to localStorage for recovery on refresh
                        const saved = JSON.parse(localStorage.getItem('hemn_active_tasks') || '[]');
                        saved.push(taskInfo);
                        localStorage.setItem('hemn_active_tasks', JSON.stringify(saved));

                        this.showToast("Tarefa iniciada na nuvem", "success");
                        const moduleLabels = {
                            'enrich': 'ENRIQUECIMENTO',
                            'extract': 'EXTRAÇÃO',
                            'extraction': 'EXTRAÇÃO',
                            'carrier': 'OPERADORA',
                            'unify': 'UNIFICAÇÃO',
                            'split': 'DIVISÃO',
                            'manual': 'BUSCA UNITÁRIA'
                        };
                        const moduleName = moduleLabels[mid] || mid.toUpperCase();
                        this.addNotification("Novo Processo", `Sua tarefa de ${moduleName} (TI-${data.task_id.substring(0, 6)}) foi encaminhada para a nuvem.`, "info");

                        this.renderTaskCard(data.task_id, mid);
                        this.renderGlobalTaskCard(data.task_id, mid);
                    }
                    return data;
                } catch (e) {
                    this.showToast("Falha de comunicação", "error");
                    return null;
                }
            },

            async recoverActiveTasks() {
                try {
                    const res = await fetch(`${API}/tasks/active`, { headers: { 'Authorization': `Bearer ${this.token}` } });
                    if (!res.ok) return;
                    const activeTasks = await res.json();
                    activeTasks.forEach(task => {
                        if (!this.tasks.find(t => t.id === task.id)) {
                            const mid = task.module.toLowerCase();
                            const taskInfo = {
                                id: task.id,
                                mid: mid,
                                startTime: new Date(task.created_at).getTime(),
                                done: task.status === 'COMPLETED' || task.status === 'FAILED' || task.status === 'CANCELLED'
                            };
                            this.tasks.push(taskInfo);
                            this.renderTaskCard(task.id, mid, task);
                            this.renderGlobalTaskCard(task.id, mid, task);
                        }
                    });
                } catch (e) {
                    console.error("Task recovery failed", e);
                }
            },

            renderGlobalTaskCard(tid, mid, savedData = null) {
                const container = document.getElementById('global-tasks-container');
                if (!container) return;
                let card = document.getElementById(`gtask-${tid}`);
                if (!card) {
                    card = document.createElement('div');
                    card.className = 'gtask-card active';
                    card.id = `gtask-${tid}`;
                    container.prepend(card);
                }

                const moduleLabels = {
                    'enrich': 'ENRIQUECIMENTO',
                    'extract': 'EXTRAÇÃO',
                    'extraction': 'EXTRAÇÃO',
                    'carrier': 'OPERADORA',
                    'unify': 'UNIFICAÇÃO',
                    'split': 'DIVISÃO'
                };
                const moduleLabel = moduleLabels[mid] || mid.toUpperCase();

                // Use saved data for instant UI or defaults
                const status = savedData?.status?.toUpperCase() || "AGUARDANDO";
                const message = savedData?.message || "Iniciando...";
                const progress = savedData?.progress || 0;

                card.innerHTML = `
                    <div class="gtask-name">
                        <span><i class="fas fa-cog"></i> ${moduleLabel} &mdash; TI-${tid.substring(0, 6)}</span>
                        <span id="gstatus-${tid}" style="color:var(--text-3); font-weight:600">${status}</span>
                    </div>
                    <div class="gtask-msg" id="gmsg-${tid}">${message}</div>
                    <div class="gtask-progress">
                        <div class="gtask-bar" id="gprog-${tid}" style="width: ${progress}%"></div>
                    </div>
                    <button class="gtask-cancel" onclick="app.cancelTask('${tid}')" title="Cancelar Processo">
                        <i class="fas fa-times-circle"></i>
                    </button>
                `;
            },

            async cancelTask(tid) {
                const ok = await this.confirm("Cancelar Processo", "Deseja realmente interromper este processamento?", { type: 'warning' });
                if (!ok) return;
                try {
                    const res = await fetch(`${API}/tasks/${tid}/cancel`, {
                        method: 'POST',
                        headers: { 'Authorization': `Bearer ${this.token}` }
                    });
                    if (res.ok) {
                        this.showToast("Cancelamento solicitado", "info");
                    }
                } catch (e) {
                    this.showToast("Erro ao cancelar", "error");
                }
            },

            renderTaskCard(tid, mid, savedData = null) {
                const container = document.getElementById(`tasks-${mid}`);
                if (!container) return;

                // Evita duplicar se já foi renderizado (ex: pelo recovery)
                if (document.getElementById(`task-${tid}`)) return;

                const card = document.createElement('div');
                card.id = `task-${tid}`;
                card.className = "glass-card";
                card.style.marginTop = "15px";
                card.style.borderColor = "var(--border-focus)";

                const status = savedData?.status?.toUpperCase() || "AGUARDANDO";
                const message = savedData?.message || "Iniciando motores de busca Titanium...";
                const progress = savedData?.progress || 0;

                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center">
                        <span style="font-size:12px; font-weight:700">TI-ID: ${tid.substring(0, 8)}</span>
                        <div class="badge badge-blue" id="status-${tid}">${status}</div>
                    </div>
                    <div id="msg-${tid}" style="font-size:11px; color:var(--text-dim); margin-top:8px">${message}</div>
                    <div style="height:4px; background:var(--bg-input); border-radius:10px; margin:10px 0; overflow:hidden">
                        <div id="prog-${tid}" style="width:${progress}%; height:100%; background:var(--g-primary); transition:width 0.4s ease-out"></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; font-size:10px; font-weight:700">
                         <span id="time-label-${tid}" style="color:var(--text-3); display:flex; align-items:center">
                            <i class="fas fa-circle-notch fa-spin" style="margin-right:5px; opacity:0"></i>
                            ESTIMATIVA: CALCULANDO...
                         </span>
                         <span id="pct-${tid}">${progress}%</span>
                    </div>
                    <div id="cancel-zone-${tid}" style="margin-top:12px; display:flex; justify-content:flex-end">
                        <button onclick="app.cancelTask('${tid}')" class="btn-outline" style="height:28px; font-size:10px; padding:0 12px; color:#ef4444; border-color:rgba(239,68,68,0.2)">
                            <i class="fas fa-stop-circle" style="margin-right:5px"></i> Cancelar Processo
                        </button>
                    </div>
                `;
                container.prepend(card);

                if (savedData && (savedData.status === 'COMPLETED' || savedData.status === 'SUCCESS' || savedData.result_file)) {
                    const count = savedData.record_count || 0;
                    const downloadHtml = `
                        <div style="margin-top:15px; padding-top:12px; border-top:1px solid var(--border-color); color:var(--text-3); font-size:11px">
                            <i class="fas fa-database"></i> Encontrados: <b>${count.toLocaleString()}</b> registros.
                        </div>
                        <button onclick="app.downloadTask('${tid}', ${count})" class="btn-primary" style="margin-top:10px; width:100%; border:none; height:40px; border-radius:8px; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:8px">
                            <i class="fas fa-download"></i> Baixar e Consumir Créditos (${count.toLocaleString()} Cr)
                        </button>
                    `;
                    card.insertAdjacentHTML('beforeend', downloadHtml);
                    const cancelZone = document.getElementById(`cancel-zone-${tid}`);
                    if (cancelZone) cancelZone.style.display = 'none';
                }
            },

            async runManualSearch() {
                const name = document.getElementById('manual-name').value;
                const cpf = document.getElementById('manual-cpf').value;
                const resultsContainer = document.getElementById('manual-results');

                if (!name && !cpf) {
                    this.showToast("Preencha Nome ou CPF/CNPJ", "warning");
                    return;
                }

                resultsContainer.style.display = 'block';
                resultsContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="icon fas fa-circle-notch fa-spin"></i>
                        <p>Navegando pela Base Titanium...</p>
                    </div>
                `;

                const data = await this.startTask('/tasks/enrich', { manual: true, name, cpf }, 'manual');

                if (data && Array.isArray(data)) {
                    this.refreshUser(); // Update balance
                    this.addNotification("Busca Unitária Concluída", `Foram encontrados ${data.length} resultados na base. Saldo atualizado.`, "success");
                    if (data.length === 0) {
                        resultsContainer.innerHTML = `
                            <div class="glass-card fade-in" style="text-align:center; padding: var(--s-8);">
                                <i class="fas fa-search-minus" style="font-size:48px; color:var(--text-3); margin-bottom:15px"></i>
                                <h3>Nenhum registro encontrado</h3>
                                <p style="color:var(--text-dim)">Pode ser necessário verificar a grafia do nome ou a numeração do CPF.</p>
                            </div>
                        `;
                    } else {
                        let html = `<div class="nav-label" style="margin-bottom:var(--s-3)">Resultados da Inteligência (${data.length})</div>`;
                        data.forEach((item, i) => {
                            html += `
                            <div class="glass-card fade-in-up" style="margin-bottom: var(--s-4); animation-delay: ${i * 0.1}s">
                                <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:15px; border-bottom:1px solid var(--border); padding-bottom:10px">
                                    <h3 class="gradient-text">${item.razao_social || 'N/A'}</h3>
                                    <div class="badge ${item.situacao == 'ATIVA' ? 'badge-green' : 'badge-red'}">${item.situacao}</div>
                                </div>
                                
                                <div class="form-grid" style="margin-bottom:20px">
                                    <div><label class="nav-label" style="padding:0">CNPJ Principal</label><div class="emp-name">${item.cnpj_completo || 'N/A'}</div></div>
                                    <div><label class="nav-label" style="padding:0">Sócio/Vínculo</label><div class="emp-name">${item.nome_socio || 'N/A'}</div></div>
                                    <div><label class="nav-label" style="padding:0">CPF / Identificador</label><div class="emp-name">${item.cnpj_cpf_socio || 'N/A'}</div></div>
                                    <div><label class="nav-label" style="padding:0">E-mail Corporativo</label><div class="emp-name" style="color:var(--accent)">${item.email_novo || 'N/A'}</div></div>
                                </div>

                                <div style="display:grid; grid-template-columns: 2fr 1fr; gap:var(--s-4); align-items: center">
                                    <div style="background:var(--bg-hover); padding:15px; border-radius:var(--r-md)">
                                        <div class="stat-label">📍 LOCALIZAÇÃO</div>
                                        <div class="emp-name" style="font-size:13px">${item.endereco_completo || 'N/A'}</div>
                                    </div>
                                    <div style="background:var(--g-primary); padding:15px; border-radius:var(--r-md); color:#fff">
                                        <div class="stat-label" style="color:rgba(255,255,255,0.7)">📞 CONTATO DIRETO</div>
                                        <div class="stat-value" style="font-size:18px">${item.telefone_novo ? '(' + item.ddd_novo + ') ' + item.telefone_novo : '--'}</div>
                                        <div style="font-size:10px; font-weight:700; text-transform:uppercase">${item.tipo_telefone || ''}</div>
                                    </div>
                                </div>
                            </div>`;
                        });
                        resultsContainer.innerHTML = html;
                    }
                }
            },

            async pollTasks() {
                // Tique global para contagem regressiva em tempo real
                setInterval(() => {
                    this.tasks.forEach(t => {
                        if (t.remaining > 0 && !t.done) {
                            t.remaining--;
                            const timeLabel = document.getElementById(`time-label-${t.id}`);
                            if (timeLabel) {
                                const mins = Math.floor(t.remaining / 60);
                                const secs = Math.floor(t.remaining % 60);
                                timeLabel.innerText = `RESTANTE: ~${mins}m ${secs}s`;
                            }
                        }
                    });
                }, 1000);

                setInterval(async () => {
                    if (this.tasks.length === 0) return;
                    for (let t of this.tasks) {
                        if (t.done) continue;
                        try {
                            const res = await fetch(`${API}/tasks/${t.id}`, { headers: { 'Authorization': `Bearer ${this.token}` } });
                            const data = await res.json();

                            // If server restarted, the task is gone from memory — clean up
                            if (data.status === 'NOT_FOUND') {
                                t.done = true;
                                let saved = JSON.parse(localStorage.getItem('hemn_active_tasks') || '[]');
                                saved = saved.filter(x => x.id !== t.id);
                                localStorage.setItem('hemn_active_tasks', JSON.stringify(saved));
                                const gcard = document.getElementById(`gtask-${t.id}`);
                                if (gcard) gcard.remove();
                                const gmsg = document.getElementById(`gmsg-${t.id}`);
                                if (gmsg) gmsg.innerText = 'Servidor reiniciado — processo perdido.';
                                continue;
                            }

                            const statusBadge = document.getElementById(`status-${t.id}`);
                            const progressBar = document.getElementById(`prog-${t.id}`);
                            const msgLabel = document.getElementById(`msg-${t.id}`);
                            const timeLabel = document.getElementById(`time-label-${t.id}`);
                            const pctLabel = document.getElementById(`pct-${t.id}`);

                            // Always update global banner regardless of module card
                            if (data.status) {
                                const gmsg = document.getElementById(`gmsg-${t.id}`);
                                const gprog = document.getElementById(`gprog-${t.id}`);
                                const gstatus = document.getElementById(`gstatus-${t.id}`);
                                if (gmsg && data.message) gmsg.innerText = data.message;
                                if (gprog && data.progress !== undefined) gprog.style.width = data.progress + '%';
                                if (gstatus) gstatus.innerText = data.status.toUpperCase();

                                // Update localStorage to preserve state for next refresh
                                t.status = data.status;
                                t.message = data.message;
                                t.progress = data.progress;
                                let saved = JSON.parse(localStorage.getItem('hemn_active_tasks') || '[]');
                                const idx = saved.findIndex(x => x.id === t.id);
                                if (idx !== -1) {
                                    saved[idx] = { ...saved[idx], ...data };
                                    localStorage.setItem('hemn_active_tasks', JSON.stringify(saved));
                                }

                                if (data.status === 'COMPLETED' || data.status === 'FAILED') {
                                    // Removed premature t.done = true to allow specialized success/fail blocks to run
                                }
                            }

                            if (statusBadge && data.status) {
                                statusBadge.innerText = data.status.toUpperCase();
                                if (msgLabel && data.message) msgLabel.innerText = data.message;
                                if (progressBar && data.progress !== undefined) {
                                    progressBar.style.width = data.progress + "%";
                                    if (pctLabel) pctLabel.innerText = data.progress + "%";
                                }

                                // Lógica de Estimativa (Modo Realidade Extrema)
                                if (data.status === 'PROCESSING') {
                                    if (data.progress > 10 && data.progress < 100) {
                                        const elapsed = (Date.now() - t.startTime) / 1000;
                                        const total = elapsed / (data.progress / 100);
                                        const currentEst = Math.max(0, Math.floor(total - elapsed));

                                        // Suavização exponencial para evitar saltos
                                        if (!t.remaining) t.remaining = currentEst;
                                        else t.remaining = Math.floor(t.remaining * 0.7 + currentEst * 0.3);

                                        if (timeLabel) {
                                            const mins = Math.floor(t.remaining / 60);
                                            const secs = Math.floor(t.remaining % 60);
                                            timeLabel.innerText = `RESTANTE: ~${mins}m ${secs}s`;
                                            timeLabel.style.color = "var(--accent)";
                                        }
                                    } else {
                                        if (timeLabel) {
                                            if (data.progress <= 10) timeLabel.innerHTML = `<i class="fas fa-circle-notch fa-spin" style="margin-right:5px"></i> ESTIMATIVA: REALIDADE EM CURSO...`;
                                            else timeLabel.innerHTML = `<i class="fas fa-circle-notch fa-spin" style="margin-right:5px"></i> ESTIMATIVA: FINALIZANDO...`;
                                        }
                                    }
                                }

                                if (data.status === 'COMPLETED' || data.status === 'SUCCESS' || data.result_file) {
                                    statusBadge.className = "badge badge-green";
                                    progressBar.style.width = "100%";
                                    if (pctLabel) pctLabel.innerText = "100%";
                                    t.remaining = 0;
                                    if (!t.done) {
                                        const count = (data.record_count !== undefined) ? data.record_count : 0;
                                        this.showToast(`Concluído: ${count.toLocaleString()} registros!`, "success");
                                        const card = document.getElementById(`task-${t.id}`);
                                        const downloadHtml = `
                                            <div style="margin-top:15px; padding-top:12px; border-top:1px solid var(--border-color); color:var(--text-3); font-size:11px">
                                                <i class="fas fa-database"></i> Encontrados: <b>${count.toLocaleString()}</b> registros.
                                            </div>
                                            <button onclick="app.downloadTask('${t.id}', ${count})" class="btn-primary" style="margin-top:10px; width:100%; border:none; height:40px; border-radius:8px; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:8px">
                                                <i class="fas fa-download"></i> Baixar e Consumir Créditos (${count.toLocaleString()} Cr)
                                            </button>
                                        `;
                                        card.insertAdjacentHTML('beforeend', downloadHtml);
                                        t.done = true;
                                        const modName = t.mid ? t.mid.toUpperCase() : 'Processo';
                                        this.addNotification(`${modName} Concluído`, `Processamento do lote (TI-${t.id.substring(0, 6)}) finalizado. Foram encontrados ${count} registros prontos para download.`, "success");
                                        this.refreshUser();
                                    }
                                } else if (data.status === 'FAILED' || data.status === 'CANCELLED') {
                                    statusBadge.className = "badge badge-red";
                                    const cancelZone = document.getElementById(`cancel-zone-${t.id}`);
                                    if (cancelZone) cancelZone.style.display = 'none';
                                    t.done = true;
                                    const stName = data.status === 'CANCELLED' ? 'Cancelado' : 'Falhou';
                                    this.addNotification(`Processo ${stName}`, `O lote TI-${t.id.substring(0, 6)} encerrou com status ${data.status}.`, "error");
                                    if (data.status === 'CANCELLED') {
                                        this.showToast(`Tarefa ${t.id.substring(0, 8)} cancelada`, "info");
                                    }
                                }

                                if (t.done) {
                                    const cancelZone = document.getElementById(`cancel-zone-${t.id}`);
                                    if (cancelZone) cancelZone.style.display = 'none';
                                    // Remove from localStorage
                                    let saved = JSON.parse(localStorage.getItem('hemn_active_tasks') || '[]');
                                    saved = saved.filter(x => x.id !== t.id);
                                    localStorage.setItem('hemn_active_tasks', JSON.stringify(saved));
                                    // Remove global card after 5s
                                    setTimeout(() => {
                                        const gcard = document.getElementById(`gtask-${t.id}`);
                                        if (gcard) gcard.remove();
                                        const list = document.getElementById('global-task-list');
                                        if (list && !list.children.length) {
                                            document.getElementById('global-task-tracker').style.display = 'none';
                                        }
                                    }, 5000);
                                }
                            }
                        } catch (e) { console.error(e); }
                    }
                }, 3000);
            },

            startUnify() { this.startTask('/tasks/unify', this.uploadedFiles.unify, 'unify'); },
            startEnrich() {
                this.startTask('/tasks/enrich', {
                    file_id: this.uploadedFiles.enrich[0],
                    name_col: null,
                    cpf_col: null
                }, 'enrich');
            },
            startCarrier() { this.startTask('/tasks/carrier', { file_id: this.uploadedFiles.carrier[0], phone_col: document.getElementById('carrier-col').value }, 'carrier'); },
            async runSingleCarrier() {
                const phone = document.getElementById('carrier-single-phone').value.replace(/\D/g, '');
                if (phone.length < 10) {
                    this.showToast("Número inválido", "warning");
                    return;
                }
                const btn = document.getElementById('btn-single-carrier');
                const resultDiv = document.getElementById('carrier-single-result');
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Consultando...';

                try {
                    const res = await fetch(`${API}/tasks/carrier/single?phone=${phone}`, {
                        headers: { 'Authorization': `Bearer ${this.token}` }
                    });
                    const data = await res.json();
                    if (res.ok) {
                        const op = (data.operadora || 'NÃO CONSTA').toUpperCase();
                        let brandColor = 'var(--g-primary)';
                        let brandIcon = 'fa-signal';
                        let brandLogo = '';

                        if (op.includes('VIVO')) {
                            brandColor = 'linear-gradient(135deg, #662d91 0%, #a82782 100%)';
                            brandIcon = 'fa-mobile-alt';
                        } else if (op.includes('CLARO')) {
                            brandColor = 'linear-gradient(135deg, #e1261c 0%, #ff5248 100%)';
                            brandIcon = 'fa-phone-alt';
                        } else if (op.includes('TIM')) {
                            brandColor = 'linear-gradient(135deg, #004a99 0%, #0072bc 100%)';
                            brandIcon = 'fa-rss';
                        } else if (op.includes('OI')) {
                            brandColor = 'linear-gradient(135deg, #f8c300 0%, #ffdf00 100%)';
                            brandIcon = 'fa-broadcast-tower';
                        } else if (op.includes('ALGAR')) {
                            brandColor = 'linear-gradient(135deg, #00a650 0%, #39b54a 100%)';
                            brandIcon = 'fa-network-wired';
                        } else if (op.includes('SURF')) {
                            brandColor = 'linear-gradient(135deg, #00aeef 0%, #00d2ff 100%)';
                            brandIcon = 'fa-wave-square';
                        } else if (op.includes('NÃO CONSTA') || op.includes('ERRO')) {
                            brandColor = 'linear-gradient(135deg, #4b5563 0%, #6b7280 100%)';
                            brandIcon = 'fa-question-circle';
                        }

                        resultDiv.style.display = 'block';
                        resultDiv.innerHTML = `
                            <div class="glass-card fade-in" style="background:${brandColor}; padding:25px; text-align:center; position:relative; overflow:hidden; border:none; box-shadow: 0 10px 30px rgba(0,0,0,0.3)">
                                <i class="fas ${brandIcon}" style="position:absolute; right:-10px; bottom:-10px; font-size:100px; opacity:0.1; transform: rotate(-15deg)"></i>
                                <div style="font-size:10px; opacity:0.8; font-weight:800; letter-spacing:2px; margin-bottom:10px">OPERADORA IDENTIFICADA</div>
                                <div style="font-size:38px; font-weight:900; letter-spacing:1px; text-shadow: 0 2px 10px rgba(0,0,0,0.2)">${data.operadora || 'NÃO IDENTIFICADA'}</div>
                                <div style="display:flex; align-items:center; justify-content:center; gap:10px; margin-top:15px">
                                    <div class="badge" style="background:rgba(255,255,255,0.2); border:1px solid rgba(255,255,255,0.3); color:#fff; font-size:11px">${data.tipo || 'Móvel'}</div>
                                    <div style="font-size:12px; opacity:0.9; font-weight:500">
                                        <i class="fas fa-check-double" style="margin-right:5px"></i> Inteligência Titanium Ativa
                                    </div>
                                </div>
                            </div>
                        `;
                        this.refreshUser();
                        this.addNotification("Consulta Unitária Operadora", `O telefone ${phone} retornou operadora: ${data.operadora || 'NÃO IDENTIFICADA'}`, "success");
                    } else {
                        this.showToast(data.detail || "Erro na consulta", "error");
                    }
                } catch (e) {
                    this.showToast("Erro de conexão", "error");
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-search"></i> Consultar';
                }
            },
            startSplit() { this.startTask('/tasks/split', { file_id: this.uploadedFiles.split[0] }, 'split'); },
            startExtract() {
                const body = {
                    uf: document.getElementById('extract-uf').value.toUpperCase(),
                    cidade: document.getElementById('extract-cidade').value.toUpperCase(),
                    cnae: document.getElementById('extract-cnae').value,
                    situacao: document.getElementById('extract-status').value,
                    tipo_tel: document.getElementById('extract-tipo-tel').value,
                    somente_com_telefone: document.getElementById('extract-somente-tel').checked,
                    cep_file: this.uploadedFiles.cep[0] || null,
                    operadora_inc: document.getElementById('extract-operadora-inc').value,
                    operadora_exc: document.getElementById('extract-operadora-exc').value,
                    perfil: document.getElementById('extract-perfil').value
                };
                this.startTask('/tasks/extract', body, 'extract');
            },
            async downloadTask(tid, cost) {
                const ok = await this.confirm("Confirmar Download", `Deseja baixar o resultado? Isso consumirá ${cost.toLocaleString()} créditos do seu saldo.`, {
                    type: 'info',
                    confirmText: 'Sim, Baixar',
                    cancelText: 'Agora não'
                });
                if (!ok) return;
                try {
                    const resp = await fetch(`${API}/download/${tid}`, {
                        headers: { 'Authorization': `Bearer ${localStorage.getItem('hemn_token')}` }
                    });
                    if (resp.status === 403) {
                        const err = await resp.json();
                        this.alert("Saldo Insuficiente", err.detail, { type: 'error' });
                        return;
                    }
                    if (resp.ok) {
                        const blob = await resp.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a'); a.href = url;
                        a.download = `Resultado_${tid.substring(0, 8)}.xlsx`;
                        document.body.appendChild(a); a.click(); a.remove();
                        this.showToast("Pronto!", "success"); this.refreshUser();
                    } else this.alert("Erro no Download", "Ocorreu um problema ao baixar o arquivo.", { type: 'error' });
                } catch (e) { console.error(e); }
            }
        };

        window.app = app;
        app.init();
    