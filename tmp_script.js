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
            statusMap: {
                'QUEUED': 'AGUARDANDO',
                'PROCESSING': 'PROCESSANDO',
                'COMPLETED': 'CONCLUÍDO',
                'SUCCESS': 'CONCLUÍDO',
                'FAILED': 'FALHOU',
                'CANCELLED': 'CANCELADO'
            },
            currentPixPayload: null,
            initialized: false,
            currentModule: null,

            init() {
                if (this.initialized) return;
                this.initialized = true;
                // console.log("HEMN SYSTEM INITIALIZED");


                // Universal Robust Closer (Always Active)
                const handleGlobalClick = (e) => {
                    // Notification dropdown closer
                    const dropdown = document.getElementById('notification-dropdown');
                    const bellBtn = document.getElementById('btn-notifications');
                    if (dropdown) {
                        const isVisible = dropdown.style.display === 'block' || getComputedStyle(dropdown).display === 'block';
                        if (isVisible) {
                            const rect = dropdown.getBoundingClientRect();
                            const isInside = e.clientX >= rect.left && e.clientX <= rect.right && 
                                             e.clientY >= rect.top && e.clientY <= rect.bottom;

                            let onButton = false;
                            if (bellBtn) {
                                const bRect = bellBtn.getBoundingClientRect();
                                onButton = e.clientX >= bRect.left && e.clientX <= bRect.right &&
                                           e.clientY >= bRect.top && e.clientY <= bRect.bottom;
                                if (!onButton) onButton = bellBtn.contains(e.target);
                            }

                            if (!isInside && !onButton && !dropdown.contains(e.target)) {
                                dropdown.style.display = 'none';
                            }
                        }
                    }

                    // User menu robust closer
                    const userWrapper = document.getElementById('user-menu-wrapper');
                    if (userWrapper && userWrapper.classList.contains('open')) {
                        if (!userWrapper.contains(e.target)) {
                            userWrapper.classList.remove('open');
                        }
                    }

                    // Balance menu robust closer
                    const balanceWrapper = document.getElementById('balance-menu-wrapper');
                    if (balanceWrapper && balanceWrapper.classList.contains('open')) {
                        if (!balanceWrapper.contains(e.target)) {
                            balanceWrapper.classList.remove('open');
                        }
                    }
                };
                window.addEventListener('mousedown', handleGlobalClick, true);
                window.addEventListener('touchstart', (e) => {
                    if (e.touches && e.touches[0]) {
                        handleGlobalClick(e.touches[0]);
                    }
                }, true);

                const header = document.getElementById('main-header');
                if (this.token) {
                    if (header) header.style.setProperty('display', 'flex', 'important');
                    document.getElementById('login-overlay').style.display = 'none';

                    // RESTAURAÇÃO BLOQUEADA (Sync)
                    const lastModule = localStorage.getItem('hemn_last_module') || 'inicio';
                    const lastNavEl = document.getElementById(`nav-${lastModule}`);
                    
                    if (lastModule === 'checkout') {
                        // Restore checkout data
                        const type = localStorage.getItem('hemn_checkout_type');
                        const payload = localStorage.getItem('hemn_checkout_payload');
                        if (type && payload) {
                             this.openCheckout(type, payload);
                        } else {
                             this.showModule('inicio');
                        }
                    } else {
                        this.showModule(lastModule, lastNavEl);
                    }

                    this.refreshUser();
                    this.recoverActiveTasks();
                    this.pollTasks();
                    this.refreshDashboard();
                    this.setupDragAndDrop();
                    
                    // Recover uploaded files state (v1.6.6)
                    try {
                        const savedFiles = JSON.parse(localStorage.getItem('hemn_uploaded_files') || '{}');
                        Object.keys(savedFiles).forEach(mid => {
                            if (Array.isArray(savedFiles[mid])) {
                                this.uploadedFiles[mid] = savedFiles[mid];
                                this.uploadedFiles[mid].forEach(id => {
                                    const name = id.split('_').slice(1).join('_') || id;
                                    this.renderFile(mid, name, id);
                                });
                            }
                        });
                    } catch (e) { console.error("Error recovering uploaded files", e); }

                    // Verificar se é primeiro acesso (mudança de senha obrigatória)
                    if (localStorage.getItem('hemn_force_pw_change') === '1') {
                        localStorage.removeItem('hemn_force_pw_change');
                        setTimeout(() => {
                            this.openPasswordModal();
                            // Lock: impedir fechar sem alterar — mostrar aviso no topo do modal
                            const modal = document.getElementById('password-modal');
                            if (modal) {
                                const existing = modal.querySelector('.force-pw-banner');
                                if (!existing) {
                                    const banner = document.createElement('div');
                                    banner.className = 'force-pw-banner';
                                    banner.style.cssText = 'background: rgba(255,72,108,0.15); border: 1px solid var(--status-red); border-radius: 8px; padding: 10px 14px; margin-bottom: 16px; font-size: 12px; color: var(--status-red); font-weight: 700; display: flex; align-items: center; gap: 8px;';
                                    banner.innerHTML = '<i class="fas fa-lock"></i> Primeiro acesso detectado — altere sua senha antes de continuar.';
                                    modal.querySelector('.glass-card').insertBefore(banner, modal.querySelector('.glass-card').firstChild);
                                }
                            }
                        }, 600);
                    }

                    // Global Click Listener to close dropdowns
                    window.addEventListener('click', (e) => {
                        const wrappers = ['.user-menu-wrapper', '.balance-menu-wrapper', '.notification-wrapper'];
                        let matched = false;
                        wrappers.forEach(w => {
                            if (e.target.closest(w)) matched = true;
                        });

                        if (!matched) {
                            this.closeAllDropdowns();
                        }
                    });
                } else {
                    const header = document.getElementById('main-header');
                    if (header) header.style.setProperty('display', 'none', 'important');
                }
                
                // Mostrar o app apenas APÓS o showModule inicial ter definido o display:block!important
                setTimeout(() => {
                    document.getElementById('app').classList.add('app-ready');
                }, 50);
            },
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
                this.showToast(`🔔 ${title}`, type);
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

            closeAllDropdowns(exceptId = null) {
                const wrappers = {
                    'notif': 'notification-wrapper',
                    'user': 'user-menu-wrapper',
                    'balance': 'balance-menu-wrapper'
                };
                
                Object.keys(wrappers).forEach(key => {
                    if (key !== exceptId) {
                        const el = document.getElementById(wrappers[key]);
                        if (el) el.classList.remove('open');
                    }
                });
            },

            toggleNotifications() {
                const wrapper = document.getElementById('notification-wrapper');
                if (!wrapper) return;
                
                this.closeAllDropdowns('notif');
                const isOpen = wrapper.classList.toggle('open');
                if (isOpen) {
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
                sidebar.classList.toggle('active');
                overlay.classList.toggle('active');
            },

            toggleUserMenu() {
                const wrapper = document.getElementById('user-menu-wrapper');
                if (wrapper) {
                    this.closeAllDropdowns('user');
                    wrapper.classList.toggle('open');
                }
            },

            closeUserMenu() {
                const wrapper = document.getElementById('user-menu-wrapper');
                if (wrapper) wrapper.classList.remove('open');
            },

            toggleBalanceMenu() {
                const wrapper = document.getElementById('balance-menu-wrapper');
                if (wrapper) {
                    this.closeAllDropdowns('balance');
                    wrapper.classList.toggle('open');
                }
            },

            closeBalanceMenu() {
                const wrapper = document.getElementById('balance-menu-wrapper');
                if (wrapper) wrapper.classList.remove('open');
            },

            // PREMIUM MODAL SYSTEM
            confirm(title, message, options = {}) {
                return new Promise((resolve) => {
                    const modal = document.getElementById('premium-modal');
                    const titleEl = document.getElementById('modal-title');
                    const msgEl = document.getElementById('modal-message');
                    const btnConfirm = document.getElementById('modal-btn-confirm');
                    const btnCancel = document.getElementById('modal-btn-cancel');
                    const btnRecharge = document.getElementById('modal-btn-recharge');
                    const iconContainer = document.getElementById('modal-icon-container');

                    titleEl.innerText = title;
                    msgEl.innerText = message;
                    btnConfirm.innerText = options.confirmText || 'Confirmar';
                    btnCancel.style.display = (options.showCancel === false) ? 'none' : 'flex';
                    if (options.cancelText) btnCancel.innerText = options.cancelText;

                    // Extra Recharge Button
                    if (options.showRecharge) {
                        btnRecharge.style.display = 'flex';
                        if (options.rechargeText) btnRecharge.innerText = options.rechargeText;
                    } else {
                        btnRecharge.style.display = 'none';
                    }

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
                        btnRecharge.onclick = null;
                        resolve(val);
                    };

                    btnConfirm.onclick = () => cleanup(true);
                    btnCancel.onclick = () => cleanup(false);
                    btnRecharge.onclick = () => cleanup('recharge');
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
                // Update dropdown theme icon/label
                const icon = document.getElementById('theme-toggle-icon');
                const label = document.getElementById('theme-toggle-label');
                if (icon) icon.className = this.theme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
                if (label) label.textContent = this.theme === 'dark' ? 'Modo Escuro' : 'Modo Claro';
            },

            async login() {
                const u = document.getElementById('login-user').value.toLowerCase();
                const p = document.getElementById('login-pass').value;
                try {
                    const res = await fetch(`${API}/login`, {
                        method: 'POST',
                        body: new URLSearchParams({ username: u, password: p })
                    });
                    const data = await res.json();
                    if (res.ok) {
                        localStorage.setItem("hemn_token", data.access_token);
                        localStorage.setItem("hemn_last_module", "inicio");
                        // Reset tema para claro no Login (conforme regra)
                        localStorage.setItem("hemn_theme", "light");
                        document.documentElement.setAttribute('data-theme', 'light');
                        if (data.force_password_change) {
                            localStorage.setItem("hemn_force_pw_change", "1");
                        }
                        this.showToast("acesso autorizado", "success");
                        setTimeout(() => location.reload(), 800);
                    } else {
                        this.showToast("usuário ou senha inválidos", "error");
                    }
                } catch (e) {
                    console.error("login failed", e);
                }
            },

            logout() {
                if (this.taskInterval) clearInterval(this.taskInterval);
                if (this.monInterval) clearInterval(this.monInterval);
                if (this.rechargeInterval) clearInterval(this.rechargeInterval);
                if (this.pollInterval1) clearInterval(this.pollInterval1);
                if (this.pollInterval2) clearInterval(this.pollInterval2);

                localStorage.removeItem("hemn_token");
                localStorage.removeItem("hemn_force_pw_change");
                localStorage.removeItem("hemn_active_tasks");
                localStorage.removeItem("hemn_last_module");
                
                // Reset tema para claro no Logout (conforme regra)
                localStorage.setItem("hemn_theme", "light");
                document.documentElement.setAttribute('data-theme', 'light');
                // Instant UI Reset
                document.documentElement.classList.remove('is-logged-in');
                
                const header = document.getElementById('main-header');
                const loginOverlay = document.getElementById('login-overlay');
                
                if (header) header.style.setProperty('display', 'none', 'important');
                if (loginOverlay) loginOverlay.style.display = 'flex';
                
                // Hide all modules to simulate fresh load
                document.querySelectorAll('.module-view').forEach(mod => mod.classList.remove('module-active'));
                
                this.closeAllDropdowns && this.closeAllDropdowns();
                
                // Clear any sensitive data in memory
                this.user = null;
                this.tasks = [];
                this.adminUsers = [];
                this.token = null;
                this.initialized = false;
                
                // Reset inputs
                const userInp = document.getElementById('user-login');
                const passInp = document.getElementById('pass-login');
                if (userInp) userInp.value = '';
                if (passInp) passInp.value = '';
            },

            openPasswordModal() {
                // Auto-close sidebar on mobile
                const sidebar = document.getElementById('sidebar');
                if (window.innerWidth <= 768 && sidebar && (sidebar.classList.contains('active') || sidebar.classList.contains('open'))) {
                    this.toggleSidebar();
                }
                document.getElementById('password-modal').style.display = 'flex';
                document.getElementById('current-pass').value = '';
                document.getElementById('new-pass').value = '';
                document.getElementById('confirm-pass').value = '';
            },

            closePasswordModal() {
                document.getElementById('password-modal').style.display = 'none';
            },

            async submitPasswordChange() {
                const current = document.getElementById('current-pass').value;
                const next = document.getElementById('new-pass').value;
                const confirm = document.getElementById('confirm-pass').value;

                if (!current || !next || !confirm) {
                    this.showToast('Preencha todos os campos.', 'error');
                    return;
                }
                if (next !== confirm) {
                    this.showToast('As novas senhas não coincidem.', 'error');
                    return;
                }
                if (next.length < 4) {
                    this.showToast('A nova senha deve ter pelo menos 4 caracteres.', 'error');
                    return;
                }

                try {
                    const res = await fetch(`${API}/user/change-password`, {
                        method: 'POST',
                        headers: { 
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${this.token}`
                        },
                        body: JSON.stringify({
                            current_password: current,
                            new_password: next,
                            confirm_password: confirm
                        })
                    });
                    const data = await res.json();
                    if (res.ok) {
                        this.showToast('Senha alterada com sucesso!', 'success');
                        this.closePasswordModal();
                    } else {
                        this.showToast(data.detail || 'Falha ao alterar senha', 'error');
                    }
                } catch (err) {
                    this.showToast('Erro na conexão', 'error');
                }
            },

            async refreshUser() {
                try {
                    const res = await fetch(`${API}/me`, { headers: { 'Authorization': `Bearer ${this.token}` } });
                    const user = await res.json();
                    if (res.ok) {
                        this.user = user;
                        // Populate header user menu (first + last name)
                        const nameParts = (user.full_name || '').trim().split(/\s+/);
                        const displayName = nameParts.length >= 2
                            ? `${nameParts[0]} ${nameParts[nameParts.length - 1]}`
                            : nameParts[0] || 'Usuário';
                        const menuName = document.getElementById('user-menu-name');
                        if (menuName) menuName.textContent = displayName;
                        const menuAvatar = document.getElementById('user-menu-avatar');
                        if (menuAvatar) {
                            const initial = (nameParts[0] || 'U').charAt(0).toUpperCase();
                            menuAvatar.textContent = initial;
                        }

                        if (document.getElementById('user-display')) {
                            document.getElementById('user-display').innerText = nameParts[0] || 'Usuário';
                        }
                        if (document.getElementById('avatar-initial')) {
                            const initial = (nameParts[0] || 'U').charAt(0).toUpperCase();
                            document.getElementById('avatar-initial').innerText = initial;
                        }
                        
                        // Update Sidebar Role
                        const sidebarRole = document.getElementById('sidebar-role-display');
                        if (sidebarRole) {
                            if (user.role === 'ADMIN') sidebarRole.innerText = 'Admin';
                            else if (user.role === 'CLINICAS') sidebarRole.innerText = 'Clínicas';
                            else sidebarRole.innerText = 'Bronze';
                        }

                        if (document.getElementById('credits-display')) {
                            const oldText = document.getElementById('credits-display').innerText;
                            let displayBalance = Math.max(0, user.total_limit - user.current_usage).toFixed(0);
                            if (user.total_limit >= 900000000) displayBalance = "Infinito";
                            
                            const newText = displayBalance === "Infinito" ? "∞" : `${displayBalance} Cr`;
                            if (oldText !== "--" && oldText !== "∞" && oldText !== newText) {
                                this.addNotification("Saldo Atualizado", `Seu saldo agora é: ${displayBalance}`, "info");
                            }
                            document.getElementById('credits-display').innerText = newText;
                        }

                        // Atualiza extrato se estiver na tela de dashboard
                        if (this.currentModule === 'dashboard') this.refreshDashboard();

                        // Update Greeting
                        const hour = new Date().getHours();
                        let greet = "Boa noite";
                        let icon = "fa-moon";
                        if (hour < 5) { greet = "Boa madrugada"; icon = "fa-star"; }
                        else if (hour < 12) { greet = "Bom dia"; icon = "fa-sun"; }
                        else if (hour < 18) { greet = "Boa tarde"; icon = "fa-cloud-sun"; }
                        const userDisplayName = (user.full_name || 'Admin').split(' ')[0];
                        document.getElementById('main-greeting').innerHTML = `${greet}, <span style="background: var(--g-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;">${userDisplayName}</span>!`;
                        
                        // Mobile Greeting (Styled like Desktop - v1.6.2)
                        const mobileGreetEl = document.getElementById('mobile-greeting-text');
                        if (mobileGreetEl) {
                            mobileGreetEl.innerHTML = `${greet}, <b>${userDisplayName}</b>!`;
                        }
                        
                        const mobileIconEl = document.getElementById('mg-dynamic-icon');
                        if (mobileIconEl) mobileIconEl.className = `fas ${icon}`;
                        
                        const iconEl = document.getElementById('pg-dynamic-icon');
                        if (iconEl) iconEl.className = `fas ${icon}`;

                        // Populate Real-Time Balance (Header & Dropdown) - NOW IN CREDITS (Cr)
                        const isUnlimited = (user.total_limit >= 900000000);
                        const currentCr = Math.max(0, user.total_limit - user.current_usage);
                        const totalCr = (user.total_limit || 0);
                        const fmtCr = (v) => v.toLocaleString('pt-BR') + ' Cr';
                        
                        const headBal = document.getElementById('header-balance-amount');
                        if (headBal) headBal.textContent = isUnlimited ? 'Ilimitado' : fmtCr(currentCr);
                        
                        const dropBal = document.getElementById('dropdown-balance-value');
                        if (dropBal) dropBal.textContent = isUnlimited ? 'Ilimitado' : fmtCr(currentCr);
                        
                        const dropLim = document.getElementById('dropdown-limit-value');
                        if (dropLim) dropLim.textContent = isUnlimited ? 'Ilimitado' : fmtCr(totalCr);

                        // Force recharge button visibility (except for MAYK role)
                        const btnRecharge = document.getElementById('btn-recharge-balance');
                        if (btnRecharge) {
                            if (user.role === 'MAYK') btnRecharge.style.display = 'none';
                            else btnRecharge.style.setProperty('display', 'block', 'important');
                        }

                        // Handle Admin & Clinicas Menu
                        console.log("[DEBUG] Checking access for role:", user.role);
                        
                        // Default states
                        document.getElementById('admin-menu').style.display = 'none';
                        if (document.getElementById('admin-card-users')) document.getElementById('admin-card-users').style.display = 'none';
                        if (document.getElementById('admin-card-monitor')) document.getElementById('admin-card-monitor').style.display = 'none';
                        
                        const clinNav = document.getElementById('nav-clinicas');
                        const clinCard = document.getElementById('clinicas-card');
                        const processingLabel = document.getElementById('label-processing');
                        const intelligenceLabel = document.getElementById('label-intelligence');
                        
                        // Individual module elements for strict hiding
                        const manualEls = [document.getElementById('nav-manual'), document.getElementById('manual-card')];
                        const enrichEls = [document.getElementById('nav-enrich'), document.getElementById('enrich-card')];
                        const extractEls = [document.getElementById('nav-extract'), document.getElementById('extract-card')];
                        const unifyEls = [document.getElementById('nav-unify'), document.getElementById('unify-card')];
                        const splitEls = [document.getElementById('nav-split'), document.getElementById('split-card')];
                        const carrierEls = [document.getElementById('nav-carrier'), document.getElementById('carrier-card')];
                        const dashboardEls = [document.getElementById('nav-dashboard'), document.getElementById('dashboard-card')];

                        if (user.role === 'ADMIN') {
                            // ADMIN: Show everything
                            document.getElementById('admin-menu').style.display = 'block';
                            if (document.getElementById('admin-card-users')) document.getElementById('admin-card-users').style.display = 'flex';
                            if (document.getElementById('admin-card-monitor')) document.getElementById('admin-card-monitor').style.display = 'flex';
                            
                            if (clinNav) clinNav.style.setProperty('display', 'flex', 'important');
                            if (clinCard) clinCard.style.setProperty('display', 'flex', 'important');
                            
                            [...manualEls, ...enrichEls, ...extractEls, ...unifyEls, ...splitEls, ...carrierEls, ...dashboardEls].forEach(el => {
                                if (el) el.style.display = el.classList.contains('action-card') ? 'flex' : 'flex';
                            });
                            if (processingLabel) processingLabel.style.display = 'block';
                            if (intelligenceLabel) intelligenceLabel.style.display = 'block';
                            this.populateAdminUserSelect();

                            // Fetch Database Version (ADMIN ONLY) - v1.0.8
                            const versionEl = document.getElementById('admin-db-version-sidebar');
                            if (versionEl) {
                                versionEl.style.display = 'block';
                                fetch(`${API}/me/db_version`, { headers: { 'Authorization': `Bearer ${this.token}` } })
                                    .then(r => r.json())
                                    .then(data => {
                                        const valEl = document.getElementById('db-version-value');
                                        if (valEl) {
                                            const ver = data.version || 'Desconhecida';
                                            valEl.innerText = ver;
                                            
                                            // Alerta de Atualização (Regra: Se Jan/2026, sinaliza que Março/Abril estão próximos)
                                            const alertEl = document.getElementById('db-update-alert');
                                            if (alertEl && (ver.includes('Janeiro') || ver.includes('01/2026'))) {
                                                alertEl.style.setProperty('display', 'flex', 'important');
                                            }
                                        }
                                    })
                                    .catch(err => {
                                        console.error("Fail to fetch DB version", err);
                                        const valEl = document.getElementById('db-version-value');
                                        if (valEl) valEl.innerText = 'Erro';
                                    });
                            }

                            console.log("[DEBUG] Strict RBAC applied for ADMIN");

                        } else if (user.role === 'CLINICAS') {
                            // CLINICAS: STRICT ACCESS (Inicio, Encontre PF, Dashboard)
                            if (clinNav) clinNav.style.setProperty('display', 'flex', 'important');
                            if (clinCard) clinCard.style.setProperty('display', 'flex', 'important');
                            
                            // Show Dashboard (Extrato)
                            dashboardEls.forEach(el => { if (el) el.style.display = el.classList.contains('action-card') ? 'flex' : 'flex'; });
                            
                            // HIDE ALL OTHERS
                            [...manualEls, ...enrichEls, ...extractEls, ...unifyEls, ...splitEls, ...carrierEls].forEach(el => {
                                if (el) el.style.display = 'none';
                            });
                            if (processingLabel) processingLabel.style.display = 'none';
                            if (intelligenceLabel) intelligenceLabel.style.display = 'block'; // Keep for spacing/clinicas
                            
                            console.log("[DEBUG] Strict RBAC applied for CLINICAS");

                        } else if (user.role === 'MAYK') {
                            // MAYK: Same as user but without credits, recharge, and dashboard
                            if (clinNav) clinNav.style.display = 'none';
                            if (clinCard) clinCard.style.display = 'none';
                            
                            // Hide Dashboard/Statement
                            dashboardEls.forEach(el => { if (el) el.style.display = 'none'; });
                            
                            // Hide Subscription/Plans
                            const assNav = document.getElementById('nav-assinatura');
                            const assCard = document.getElementById('assinatura-card');
                            const miniPlan = document.getElementById('dash-mini-plan-card');
                            if (assNav) assNav.style.display = 'none';
                            if (assCard) assCard.style.display = 'none';
                            if (miniPlan) miniPlan.style.display = 'none';

                            // Hide Balance box (Wallet) in Top Bar
                            const balWrapper = document.getElementById('balance-menu-wrapper');
                            if (balWrapper) balWrapper.style.display = 'none';
                            
                            // Hide credit/recharge elements
                            const balanceWrap = document.getElementById('status-balance');
                            if (balanceWrap && balanceWrap.closest('.status-summary-card')) {
                                balanceWrap.closest('.status-summary-card').style.display = 'none';
                            }
                            document.querySelectorAll('button[onclick="app.openRechargeModal()"]').forEach(btn => btn.style.display = 'none');
                            if (document.getElementById('credits-display')) document.getElementById('credits-display').parentElement.style.display = 'none';
                            
                            // Remove costs from buttons visually
                            const btnRealizar = document.querySelector('#module-manual .btn-primary');
                            if (btnRealizar) btnRealizar.innerHTML = '<i class="fas fa-bolt"></i> Realizar Consulta';
                            const btnExtract = document.querySelector('#module-extract .btn-primary');
                            if (btnExtract) btnExtract.innerHTML = '<i class="fas fa-rocket"></i> Iniciar Processamento Massivo';

                            [...manualEls, ...extractEls, ...unifyEls, ...splitEls, ...carrierEls].forEach(el => {
                                if (el) el.style.display = el.classList.contains('action-card') ? 'flex' : 'flex';
                            });
                            if (processingLabel) processingLabel.style.display = 'block';
                            if (intelligenceLabel) intelligenceLabel.style.display = 'block';

                        } else {
                            // Standard USER (Bronze)
                            if (clinNav) clinNav.style.display = 'none';
                            if (clinCard) clinCard.style.display = 'none';
                            
                            // Standard users see everything except Admin and Clinicas
                            [...manualEls, ...extractEls, ...unifyEls, ...splitEls, ...carrierEls, ...dashboardEls].forEach(el => {
                                if (el) el.style.display = el.classList.contains('action-card') ? 'flex' : 'flex';
                            });
                            if (processingLabel) processingLabel.style.display = 'block';
                            if (intelligenceLabel) intelligenceLabel.style.display = 'block';
                        }

                        // Set Welcome Message
                        const welcomeEl = document.getElementById('welcome-title');
                        if (welcomeEl) welcomeEl.innerText = `${greet}, ${userDisplayName}!`;

                        // Update Status Cards
                        const balanceEl = document.getElementById('status-balance');
                        if (balanceEl) {
                            let val = Math.max(0, user.total_limit - user.current_usage).toFixed(1);
                            if (user.total_limit >= 900000000) val = "Ilimitado";
                            balanceEl.innerText = val === "Ilimitado" ? val : `${val} Cr`;
                        }

                        const roleEl = document.getElementById('status-role');
                        if (roleEl) {
                            if (user.role === 'ADMIN') roleEl.innerText = 'Administrador';
                            else if (user.role === 'CLINICAS') roleEl.innerText = 'Perfil Clínicas';
                            else if (user.role === 'MAYK') roleEl.innerText = 'Prioritário (MAYK)';
                            else roleEl.innerText = 'Usuário Comum';
                        }
                    } else {
                        this.logout();
                    }
                } catch (e) {
                    console.error("User refresh failed", e);
                }
            },

            showModule(mid, element) {

                this.currentModule = mid;
                // Persist the current module so F5 restores it
                localStorage.setItem('hemn_last_module', mid);

                // Update Sidebar
                document.querySelectorAll('.nav-link').forEach(n => n.classList.remove('active'));
                if (element) element.classList.add('active');

                // Update Views - Remove block from others, add to target
                document.querySelectorAll('.module-view').forEach(m => {
                    m.classList.remove('module-active');
                    m.style.display = 'none';
                });
                
                const nextModule = document.getElementById(`module-${mid}`);
                if (nextModule) {
                    nextModule.classList.add('module-active');
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

                // Mobile auto-close sidebar when navigating
                if (window.innerWidth <= 768) {
                    const sidebar = document.getElementById('sidebar');
                    if (sidebar && sidebar.classList.contains('active')) {
                        this.toggleSidebar();
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

                    // Update Recent Activities
                    const logContainer = document.getElementById('mon-task-logs');
                    if (data.recent_activities && data.recent_activities.length > 0) {
                        logContainer.innerHTML = data.recent_activities.map(t => {
                            if (!t.created_at) return '';
                            const date = t.created_at.includes('T') ? t.created_at.split('T')[1].split('.')[0] : (t.created_at.includes(' ') ? t.created_at.split(' ')[1] : t.created_at);
                            const statusColor = t.status === 'COMPLETED' ? '#10b981' : (t.status === 'FAILED' ? '#ef4444' : '#3b82f6');
                            const icon = t.status === 'COMPLETED' ? 'fa-check-circle' : (t.status === 'FAILED' ? 'fa-times-circle' : 'fa-spinner fa-spin');
                            const module = t.module || 'TASK';
                            const msg = t.message || 'Sem detalhes';
                            return `
                                <div class="list-item" style="border-bottom: 1px solid rgba(0,0,0,0.05); padding: 8px 0;">
                                    <div style="display:flex; justify-content:space-between; width:100%; align-items:center;">
                                        <div style="display:flex; align-items:center; gap:8px;">
                                            <i class="fas ${icon}" style="color:${statusColor}"></i>
                                            <div>
                                                <div style="font-weight:700; font-size:12px;">${module}</div>
                                                <div style="font-size:10px; color:var(--text-3)">${msg}</div>
                                            </div>
                                        </div>
                                        <div style="text-align:right;">
                                            <div style="font-weight:800; color:${statusColor}">${t.progress}%</div>
                                            <div style="font-size:9px; color:var(--text-4)">${date}</div>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }).join('');
                    } else {
                        logContainer.innerHTML = '<div style="color: var(--text-2); text-align: center; margin-top: 40px;">Nenhuma atividade recente.</div>';
                    }
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

                    const roleLabel = u.role === 'ADMIN' ? 'ADMINISTRADOR' : (u.role === 'MAYK' ? 'PERFIL MAYK' : (u.role === 'CLINICAS' ? 'PERFIL CLÍNICAS' : 'USUÁRIO'));
                    const limitLabel = u.total_limit >= 900000000 ? '∞' : u.total_limit.toLocaleString();
                    const expLabel = (u.role === 'ADMIN' || u.role === 'MAYK') ? 'Ilimitado' : (u.expiration ? u.expiration.split(' ')[0].split('-').reverse().join('/') : 'Sem vencimento');

                    row.innerHTML = `
                        <td data-label="">
                            <div class="admin-user-info-wrapper">
                                <div class="emp-name" style="font-size:14px" title="${u.full_name}">${u.full_name}</div>
                                <div style="font-size:11px; color:var(--text-dim)">@${u.username} | ${roleLabel}</div>
                            </div>
                        </td>
                        <td data-label="Status"><div class="badge ${statusBadge}">${u.status === 'ACTIVE' ? 'ATIVO' : u.status === 'REVOKED' ? 'REVOGADO' : 'BLOQUEADO'}</div></td>
                        <td data-label="Vencimento"><div style="font-size:12px">${expLabel}</div></td>
                        <td data-label="Consumo">
                            <div style="font-size:13px; font-weight:600">${u.current_usage.toLocaleString()} / ${limitLabel}</div>
                            <div style="font-size:10px; color:var(--text-dim)">${usagePct}%</div>
                        </td>
                        <td data-label="">
                            <div style="display:flex; gap:8px; flex-wrap: nowrap; justify-content: flex-end; align-items: center;">
                                <button onclick="app.viewUserDashboard('${u.username}')" title="Ver Extrato" style="display:flex; align-items:center; gap:6px; padding: 7px 14px; border-radius: 20px; border: none; background: #3b82f6; color: white; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s; white-space: nowrap;" onmouseover="this.style.filter='brightness(1.15)'" onmouseout="this.style.filter='brightness(1)'">
                                    <i class="fas fa-file-invoice-dollar" style="font-size: 12px;"></i><span class="pill-action-text"> Extrato</span>
                                </button>
                                <button onclick="app.toggleUserStatus('${u.username}', '${u.status}')" title="${u.status === 'ACTIVE' ? 'Bloquear Usuário' : 'Ativar Usuário'}" style="display:flex; align-items:center; gap:6px; padding: 7px 14px; border-radius: 20px; border: none; background: ${u.status === 'ACTIVE' ? '#4b5563' : '#10b981'}; color: white; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s; white-space: nowrap;" onmouseover="this.style.filter='brightness(1.15)'" onmouseout="this.style.filter='brightness(1)'">
                                    <i class="fas ${u.status === 'ACTIVE' ? 'fa-user-slash' : 'fa-user-check'}" style="font-size: 12px;"></i><span class="pill-action-text"> ${u.status === 'ACTIVE' ? 'Bloquear' : 'Ativar'}</span>
                                </button>
                                <button onclick="app.openUserModal('${u.username}')" title="Editar Usuário" style="display:flex; align-items:center; gap:6px; padding: 7px 14px; border-radius: 20px; border: none; background: #6366f1; color: white; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s; white-space: nowrap;" onmouseover="this.style.filter='brightness(1.15)'" onmouseout="this.style.filter='brightness(1)'">
                                    <i class="fas fa-edit" style="font-size: 12px;"></i><span class="pill-action-text"> Editar</span>
                                </button>
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

            onPlanChange() {
                const PLAN_CREDITS = { essential: '500.000', plus: '1.000.000', premium: '2.500.000', platinum: '5.000.000' };
                const plan = document.getElementById('modal-plan').value;
                const preview = document.getElementById('modal-plan-preview');
                if(preview) preview.innerText = PLAN_CREDITS[plan] + ' créditos';
            },

            onRoleFlagChange(changed) {
                const isAdmin = document.getElementById('modal-is-admin');
                const isMayk = document.getElementById('modal-is-mayk');
                const isClinicas = document.getElementById('modal-is-clinicas');

                if(changed === 'admin' && isAdmin.checked) {
                    isMayk.checked = false;
                    isClinicas.checked = false;
                } else if(changed === 'mayk' && isMayk.checked) {
                    isAdmin.checked = false;
                    isClinicas.checked = false;
                } else if(changed === 'clinicas' && isClinicas.checked) {
                    isAdmin.checked = false;
                    isMayk.checked = false;
                }
                this.updateModalFieldStates();
            },

            updateModalFieldStates() {
                const isAdmin = document.getElementById('modal-is-admin').checked;
                const isMayk = document.getElementById('modal-is-mayk').checked;
                const isClinicas = document.getElementById('modal-is-clinicas').checked;

                const planSelect = document.getElementById('modal-plan');
                const vencimentoSelect = document.getElementById('modal-vencimento');
                const previewDiv = document.getElementById('modal-plan-preview').parentElement;
                const valorMensalGroup = document.getElementById('group-valor-mensal');

                if (isAdmin || isMayk) {
                    // Admin & Mayk: No Plan, No Expiration
                    planSelect.disabled = true;
                    vencimentoSelect.disabled = true;
                    planSelect.style.opacity = '0.5';
                    vencimentoSelect.style.opacity = '0.5';
                    previewDiv.style.opacity = '0';
                    previewDiv.style.pointerEvents = 'none';
                    if (valorMensalGroup) valorMensalGroup.style.display = 'none';
                } else if (isClinicas) {
                    // Clínicas: No Plan, but YES Expiration AND Valor Mensal
                    planSelect.disabled = true;
                    vencimentoSelect.disabled = false;
                    planSelect.style.opacity = '0.5';
                    vencimentoSelect.style.opacity = '1';
                    previewDiv.style.opacity = '0';
                    previewDiv.style.pointerEvents = 'none';
                    if (valorMensalGroup) {
                        valorMensalGroup.style.display = 'block';
                        const valInp = document.getElementById('modal-valor-mensal');
                        if (!valInp.value) valInp.value = "1099.00";
                    }
                } else {
                    // Standard User: Everything enabled
                    planSelect.disabled = false;
                    vencimentoSelect.disabled = false;
                    planSelect.style.opacity = '1';
                    vencimentoSelect.style.opacity = '1';
                    previewDiv.style.opacity = '1';
                    previewDiv.style.pointerEvents = 'auto';
                    if (valorMensalGroup) valorMensalGroup.style.display = 'none';
                }
            },

            async resetUserPassword(username) {
                const confirmed = await this.confirm('Resetar Senha', `Resetar a senha de "@${username}" para a senha padrão "hemn123"?\nO usuário será obrigado a alterar no primeiro acesso.`, { type: 'warning', confirmText: 'Resetar Agora' });
                if (!confirmed) return;
                try {
                    const res = await fetch(`${API}/admin/users/${username}/reset-password`, {
                        method: 'POST',
                        headers: { 'Authorization': `Bearer ${this.token}` }
                    });
                    if (res.ok) {
                        this.showToast(`Senha de ${username} redefinida para hemn123`, 'success');
                    } else {
                        const err = await res.json();
                        this.showToast(err.detail || 'Erro ao resetar senha', 'error');
                    }
                } catch (e) {
                    this.showToast('Erro de rede', 'error');
                }
            },

            async deleteUser(username) {
                const confirmed = await this.confirm('EXCLUIR USUÁRIO', `TEM CERTEZA que deseja excluir "@${username}"?\nEsta ação é IRREVERSÍVEL e apagará TODO o histórico.`, { type: 'error', confirmText: 'Confirmar Exclusão' });
                if (!confirmed) return;
                
                try {
                    const res = await fetch(`${API}/admin/users/${username}`, {
                        method: 'DELETE',
                        headers: { 'Authorization': `Bearer ${this.token}` }
                    });
                    if (res.ok) {
                        this.showToast("Usuário excluído com sucesso!", "success");
                        this.refreshAdminData();
                    } else {
                        const data = await res.json();
                        this.alert("Erro ao Excluir", data.detail || "Erro inesperado.", { type: 'error' });
                    }
                } catch (e) {
                    this.alert("Erro", "Não foi possível contatar o servidor.", { type: 'error' });
                }
            },
            openUserModal(userDataOrUsername = null) {
                const modal = document.getElementById('user-modal');
                const title = document.getElementById('modal-title');
                const dangerActions = document.getElementById('modal-danger-actions');
                let user = null;
                if (typeof userDataOrUsername === 'string') {
                    user = this.adminUsers.find(u => u.username === userDataOrUsername);
                } else {
                    user = userDataOrUsername;
                }

                if (user) {
                    title.innerText = 'Editar Usuário';
                    document.getElementById('edit-username-orig').value = user.username;
                    document.getElementById('modal-full-name').value = user.full_name || '';
                    document.getElementById('modal-username').value = user.username;
                    document.getElementById('modal-document').value = user.document || '';
                    document.getElementById('modal-plan').value = user.plan_type || 'essential';
                    this.onPlanChange();
                    document.getElementById('modal-vencimento').value = user.vencimento_dia || '10';
                    document.getElementById('modal-is-admin').checked = (user.role === 'ADMIN');
                    document.getElementById('modal-is-mayk').checked = (user.role === 'MAYK');
                    document.getElementById('modal-is-clinicas').checked = (user.role === 'CLINICAS');
                    document.getElementById('modal-valor-mensal').value = user.valor_mensal || '';
                    if (dangerActions) dangerActions.style.display = 'flex';
                } else {
                    title.innerText = 'Novo Usuário';
                    document.getElementById('edit-username-orig').value = '';
                    document.getElementById('modal-full-name').value = '';
                    document.getElementById('modal-username').value = '';
                    document.getElementById('modal-document').value = '';
                    document.getElementById('modal-plan').value = 'essential';
                    this.onPlanChange();
                    document.getElementById('modal-vencimento').value = '10';
                    document.getElementById('modal-valor-mensal').value = '';
                    document.getElementById('modal-is-admin').checked = false;
                    document.getElementById('modal-is-mayk').checked = false;
                    document.getElementById('modal-is-clinicas').checked = false;
                    if (dangerActions) dangerActions.style.display = 'none';
                }
                this.updateModalFieldStates();
                modal.style.display = 'flex';
            },

            closeUserModal() {
                document.getElementById('user-modal').style.display = 'none';
            },

            resetPasswordFromModal() {
                const username = document.getElementById('edit-username-orig').value;
                if (username) this.resetUserPassword(username);
            },

            deleteUserFromModal() {
                const username = document.getElementById('edit-username-orig').value;
                if (username) this.deleteUser(username);
            },

            async saveUser() {
                const origUsername = document.getElementById('edit-username-orig').value;
                const isAdmin = document.getElementById('modal-is-admin').checked;
                const isMayk = document.getElementById('modal-is-mayk').checked;
                const isClinicas = document.getElementById('modal-is-clinicas').checked;
                const role = isAdmin ? 'ADMIN' : (isMayk ? 'MAYK' : (isClinicas ? 'CLINICAS' : 'USER'));

                const body = {
                    full_name: document.getElementById('modal-full-name').value,
                    username: document.getElementById('modal-username').value.toLowerCase(),
                    document: document.getElementById('modal-document').value,
                    plan_type: (isAdmin || isMayk || isClinicas) ? null : document.getElementById('modal-plan').value,
                    vencimento_dia: (isAdmin || isMayk) ? null : parseInt(document.getElementById('modal-vencimento').value),
                    valor_mensal: isClinicas ? parseFloat(document.getElementById('modal-valor-mensal').value) || 1099.0 : null,
                    role: role
                };

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
                        this.showToast('Usuário salvo com sucesso', 'success');
                        this.closeUserModal();
                        this.refreshAdminData();
                    } else {
                        const err = await res.json();
                        this.showToast(err.detail || 'Erro ao salvar', 'error');
                    }
                } catch (e) {
                    this.showToast('Erro de rede', 'error');
                }
            },

            PLAN_DETAILS_MAP: {
                'essential': {
                    name: 'Essential',
                    icon: 'fa-paper-plane',
                    desc: 'O ponto de partida ideal para quem busca assertividade e economia em consultas pontuais.',
                    features: [
                        { cat: 'Capacidade', items: ['<b>500.000</b> Créditos inclusos', 'Validade de <b>30 dias</b>', 'Suporte via Ticket'] },
                        { cat: 'Busca Unitária', items: ['Custo de <b>1 crédito</b> por hit', 'Dados Cadastrais Básicos', 'Filtro de Telefone'] },
                        { cat: 'Enriquecimento', items: ['Processamento Standard', 'Até 10k linhas por arquivo', 'Exportação em XLSX'] }
                    ]
                },
                'plus': {
                    name: 'Plus',
                    icon: 'fa-bolt',
                    desc: 'Desenvolvido para times que precisam de escala e redução de custos por consulta.',
                    features: [
                        { cat: 'Capacidade', items: ['<b>1.000.000</b> Créditos inclusos', 'Redução de 50% no custo unitário', 'Suporte Prioritário'] },
                        { cat: 'Busca Unitária', items: ['Apenas <b>0,5 crédito</b> por hit', 'Consulta de Operadora (Unitária)', 'Localização Premium'] },
                        { cat: 'Enriquecimento', items: ['Fila de Alta Prioridade', 'Até 50k linhas por arquivo', 'Higienização de Bases'] }
                    ]
                },
                'premium': {
                    name: 'Premium',
                    icon: 'fa-crown',
                    desc: 'A solução completa para operações de alta performance com buscas unitárias ilimitadas.',
                    features: [
                        { cat: 'Capacidade', items: ['<b>2.500.000</b> Créditos inclusos', '<b>Buscas Unitárias GRATUITAS</b>', 'Gerente de Contas Dedicado'] },
                        { cat: 'Busca Unitária', items: ['Consultas Ilimitadas (Zero Custo)', 'Operadora Completa Inclusa', 'Score de Localização'] },
                        { cat: 'Enriquecimento', items: ['Motor Ultra-Rápido (Turbo)', 'Sem limite de linhas', 'Enriquecimento Multiponto'] }
                    ]
                },
                'platinum': {
                    name: 'Platinum',
                    icon: 'fa-gem',
                    desc: 'O ápice do HEMN SYSTEM. Total liberdade tecnológica e recursos ilimitados.',
                    features: [
                        { cat: 'Capacidade', items: ['<b>5.000.000</b> Créditos inclusos', '<b>Módulos Ilimitados</b>', 'Acesso Antecipado a Betas'] },
                        { cat: 'Busca Unitária', items: ['Consultas Ilimitadas e Isentas', 'API de Integração Direta', 'Dados de Negócios (B2B Full)'] },
                        { cat: 'Enriquecimento', items: ['Processamento Instantâneo', 'Suporte Platinum 24/7', 'Consultoria de Dados'] }
                    ]
                },
                'clinicas': {
                    name: 'Clínicas',
                    icon: 'fa-hospital-user',
                    desc: 'Plano exclusivo para clínicas com consultas ilimitadas e base regionalizada.',
                    features: [
                        { cat: 'Capacidade', items: ['<b>Créditos ILIMITADOS</b>', 'Acesso à Base Regionalizada', 'Suporte Prioritário'] },
                        { cat: 'Busca Unitária', items: ['<b>Consultas Ilimitadas</b>', 'Filtro de Telefone Especializado', 'Dados Médicos/Saúde'] },
                        { cat: 'Gestão', items: ['Painel de Médicos', 'Histórico de Pacientes', 'Exportação Simplificada'] }
                    ]
                },
                'personalizado': {
                    name: 'Personalizado',
                    icon: 'fa-star',
                    desc: 'Plano com condições especiais e limite de créditos customizado para sua operação.',
                    features: [
                        { cat: 'Capacidade', items: ['Créditos Customizados', '<b>Funcionalidades Sob Demanda</b>', 'Prioridade Titanium'] },
                        { cat: 'Busca Unitária', items: ['Consultas Adaptadas', 'Acesso à Base ClickHouse', 'Suporte VIP'] },
                        { cat: 'Gestão', items: ['Painel do Cliente Completo', 'Relatórios Customizados', 'Gerente de Contas'] }
                    ]
                },
                'custom': {
                    name: 'Valor Livre',
                    icon: 'fa-coins',
                    desc: 'Adicione créditos de forma avulsa sem alterar seu plano. Conta vinculada ao formato flexível, ideal para necessidades momentâneas.',
                    features: [
                        { cat: 'Conversão', items: ['Defina o <b>valor desejado</b>', 'Conversão inteligente', 'PIX imediato sem limite minimo'] },
                        { cat: 'Sem Fidelidade', items: ['Não altera seu plano atual', 'Acumulativo ao plano', 'Sem carência'] },
                        { cat: 'Benefícios Adicionais', items: ['Saldo permanente', 'Acesso VIP contínuo', 'Nota fiscal simplificada'] }
                    ]
                }
            },

            updatePlanDetailsCard(planId) {
                const details = this.PLAN_DETAILS_MAP[planId.toLowerCase()];
                if (!details) return;

                // Update selected state visually
                document.querySelectorAll('.plan-card').forEach(c => c.classList.remove('selected'));
                const targetCard = document.getElementById(`plan-card-${planId.toLowerCase()}`);
                if (targetCard) targetCard.classList.add('selected');

                const card = document.getElementById('plan-details-card');
                if (!card) return;

                let gridHtml = '';
                details.features.forEach(col => {
                    let listHtml = col.items.map(item => `<li><i class="fas fa-check"></i> <span>${item}</span></li>`).join('');
                    gridHtml += `
                        <div class="details-column">
                            <h4>${col.cat}</h4>
                            <ul class="details-list">${listHtml}</ul>
                        </div>
                    `;
                });

                let topBarColor = 'linear-gradient(90deg, #0088cc, #00d2ff)';
                let iconColor = 'rgba(0, 136, 204, 0.1)';
                let iconTextColor = '#0088cc';
                let iconBorder = 'rgba(0, 136, 204, 0.2)';

                if (planId.toLowerCase() === 'premium') {
                    topBarColor = 'linear-gradient(90deg, #FFDF00, #B8860B)';
                    iconColor = 'rgba(212, 175, 55, 0.15)';
                    iconTextColor = '#D4AF37';
                    iconBorder = 'rgba(212, 175, 55, 0.3)';
                } else if (planId.toLowerCase() === 'platinum') {
                    topBarColor = 'linear-gradient(90deg, #111111, #444444)';
                    iconColor = 'rgba(0, 0, 0, 0.05)';
                    iconTextColor = '#111111';
                    iconBorder = 'rgba(0, 0, 0, 0.15)';
                } else if (planId.toLowerCase() === 'custom') {
                    topBarColor = 'linear-gradient(90deg, #10b981, #059669)';
                    iconColor = 'rgba(16, 185, 129, 0.1)';
                    iconTextColor = '#10b981';
                    iconBorder = 'rgba(16, 185, 129, 0.2)';
                }

                const currentPlanText = document.getElementById('assinatura-plan-name')?.innerText.toLowerCase() || '';
                let btnHtml = '';
                
                if (details.name.toLowerCase() !== currentPlanText && planId.toLowerCase() !== 'personalizado') {
                    if (planId.toLowerCase() === 'custom') {
                        btnHtml = `<button class="pague-fatura-btn" onclick="app.openRechargeModal()" style="background: linear-gradient(135deg, #10b981, #059669); box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3); color: white;"><i class="fas fa-coins"></i> Adicionar Crédito</button>`;
                    } else {
                        let price = 899;
                        let fullName = 'Plano Essential — 500mil CR';
                        if(planId.toLowerCase() === 'plus') { price = 1399; fullName = 'Plano Plus — 1 Milhão CR'; }
                        if(planId.toLowerCase() === 'premium') { price = 2499; fullName = 'Plano Premium — 2.5 Milhões CR'; }
                        if(planId.toLowerCase() === 'platinum') { price = 3799; fullName = 'Plano Platinum — 5 Milhões CR'; }
                        
                        let btnColor = topBarColor;
                        let textColor = 'white';
                        if (planId.toLowerCase() === 'premium') { btnColor = '#111'; textColor = '#FFDF00'; }
                        if (planId.toLowerCase() === 'platinum') { btnColor = 'linear-gradient(135deg, #e6e9f0, #eef1f5)'; textColor = '#111'; }
                        
                        btnHtml = `<button class="pague-fatura-btn" onclick="app.selectPlan('${planId.toLowerCase()}', ${price}, '${fullName}')" style="background: ${btnColor}; color: ${textColor}; box-shadow: 0 8px 20px rgba(0,0,0,0.1);"><i class="fas fa-shopping-cart"></i> Contrate Já</button>`;
                    }
                }

                const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
                
                let iconBg = iconColor;
                let iconText = iconTextColor;
                let borderCol = iconBorder;

                if (isDarkMode) {
                    if (planId.toLowerCase() === 'premium') {
                        iconBg = 'rgba(212, 175, 55, 0.2)';
                        iconText = '#FFDF00';
                        borderCol = 'rgba(212, 175, 55, 0.4)';
                    } else if (planId.toLowerCase() === 'platinum') {
                        iconBg = 'rgba(255, 255, 255, 0.1)';
                        iconText = '#ffffff';
                        borderCol = 'rgba(255, 255, 255, 0.2)';
                    } else if (planId.toLowerCase() === 'custom') {
                        iconBg = 'rgba(16, 185, 129, 0.2)';
                        iconText = '#10b981';
                        borderCol = 'rgba(16, 185, 129, 0.4)';
                    } else {
                        iconBg = 'rgba(58, 123, 213, 0.2)';
                        iconText = '#00d2ff';
                        borderCol = 'rgba(58, 123, 213, 0.4)';
                    }
                }

                card.innerHTML = `
                    <style>
                        #plan-details-card::before { background: ${topBarColor} !important; }
                        #plan-details-card .details-icon { background: ${iconBg} !important; color: ${iconText} !important; border-color: ${borderCol} !important; }
                    </style>
                    <div class="details-header" style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <div class="details-icon"><i class="fas ${details.icon}"></i></div>
                            <div class="details-title-group">
                                <h3>Detalhes do Plano</h3>
                                <h2>${details.name}</h2>
                            </div>
                        </div>
                        ${btnHtml}
                    </div>
                    <p class="details-description">${details.desc}</p>
                    <div class="details-grid">${gridHtml}</div>
                `;
                card.style.display = 'flex';
                card.style.animation = 'none';
                card.offsetHeight; /* trigger reflow */
                card.style.animation = 'fadeInDetails 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
            },

            showCurrentPlanDetails() {
                const name = document.getElementById('assinatura-plan-name')?.innerText || 'Essential';
                this.updatePlanDetailsCard(name);
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
                        
                        // Mostrar Ilimitado se saldo for muito alto ou papel for CLINICAS/MAYK/ADMIN
                        const isClinicasUser = (stats.role === 'CLINICAS') || (this.user && this.user.role === 'CLINICAS');
                        const isAdminUser = ['ADMIN', 'MAYK'].includes(stats.role) || (this.user && ['ADMIN', 'MAYK'].includes(this.user.role));

                        if (isClinicasUser || isAdminUser || stats.balance >= 900000000) {
                            document.getElementById('dash-balance').innerText = "ILIMITADO";
                        } else {
                            document.getElementById('dash-balance').innerText = stats.balance.toLocaleString('pt-BR');
                        }
                        
                        // Atualizar Card Meu Plano
                        let planName = "Personalizado";
                        let planIcon = "fa-star";
                        
                        if (isAdminUser) {
                            planName = "Acesso Administrador";
                            planIcon = "fa-shield-alt";
                        } else if (isClinicasUser) {
                            planName = "Plano Clínicas";
                            planIcon = "fa-hospital-user";
                        } else if (stats.total_limit === 500000) { planName = "Essential"; planIcon = "fa-paper-plane"; }
                        else if (stats.total_limit === 1000000) { planName = "Plus"; planIcon = "fa-bolt"; }
                        else if (stats.total_limit === 2500000) { planName = "Premium"; planIcon = "fa-crown"; }
                        else if (stats.total_limit === 5000000) { planName = "Platinum"; planIcon = "fa-gem"; }

                        
                        const elPlanName = document.getElementById('dash-plan-name');
                        if (elPlanName) elPlanName.innerText = planName;
                        
                        const elPlanCredits = document.getElementById('dash-plan-credits');
                        if (elPlanCredits) {
                            if (isClinicasUser) {
                                const val = stats.valor_mensal || 1099.0;
                                elPlanCredits.innerText = `R$ ${val.toLocaleString('pt-BR', {minimumFractionDigits:2})} / mês`;
                            } else {
                                elPlanCredits.innerText = (stats.total_limit || 0).toLocaleString('pt-BR') + " Créditos";
                            }
                        }
                        
                        let expDate = stats.expiration;
                        let badgeHtml = "";
                        const elExp = document.getElementById('dash-plan-expiration');
                        if (expDate && expDate !== "Sem vencimento") {
                            const dateStr = expDate.split(' ')[0];
                            const [yyyy, mm, dd] = dateStr.split('-');
                            if (elExp) elExp.innerHTML = `<i class="far fa-calendar-alt"></i> Válido até: ${dd}/${mm}/${yyyy}`;
                            
                            const expParsed = new Date(`${yyyy}-${mm}-${dd}T00:00:00`);
                            const now = new Date();
                            const daysLeft = Math.ceil((expParsed - now) / (1000 * 60 * 60 * 24));
                            
                            if (daysLeft <= 0) {
                                badgeHtml = `<span style="color: var(--status-red);"><i class="fas fa-exclamation-triangle"></i> PLANO EXPIRADO</span>`;
                            } else if (daysLeft <= 5) {
                                badgeHtml = `<span style="color: #f7971e;"><i class="fas fa-clock"></i> Expira em ${daysLeft} dias!</span>`;
                            } else {
                                badgeHtml = `<span style="color: var(--status-green);"><i class="fas fa-check-circle"></i> ${daysLeft} dias restantes</span>`;
                            }
                        } else {
                            if (elExp) {
                                if (isClinicasUser) {
                                    elExp.innerHTML = `<i class="far fa-calendar-check"></i> Pagamento: Todo dia ${stats.vencimento_dia || 10}`;
                                } else {
                                    elExp.innerHTML = `<i class="far fa-calendar-alt"></i> Sem vencimento`;
                                }
                            }
                            badgeHtml = isClinicasUser 
                                ? `<span style="color: var(--status-green);"><i class="fas fa-check-circle"></i> Assinatura Ativa</span>`
                                : `<span style="color: var(--text-2);"><i class="fas fa-infinity"></i> Sem limite de tempo</span>`;
                        }
                        
                        const elBadge = document.getElementById('dash-expiration-badge');
                        if (elBadge) elBadge.innerHTML = badgeHtml;

                        // Also update the Assinatura module
                        const asPlanName = document.getElementById('assinatura-plan-name');
                        if(asPlanName) asPlanName.innerText = planName;
                        
                        const asPlanCredits = document.getElementById('assinatura-plan-credits');
                        if(asPlanCredits) {
                            asPlanCredits.innerText = isClinicasUser ? 'Créditos ILIMITADOS' : ((stats.total_limit || 0).toLocaleString('pt-BR') + ' Créditos');
                        }
                        
                        const asBadge = document.getElementById('assinatura-expiration-badge');
                        if(asBadge) {
                            if (isClinicasUser) {
                                asBadge.innerHTML = `<i class="far fa-calendar-check"></i> Vencimento: todo dia ${stats.vencimento_dia || 10}`;
                                asBadge.className = 'status-detail-item'; // Give it same style as credits
                                asBadge.style.color = 'var(--text-1)';
                            } else {
                                asBadge.innerHTML = badgeHtml;
                                asBadge.className = '';
                                asBadge.style.color = '';
                            }
                        }

                        const asPlanIcon = document.getElementById('assinatura-plan-icon');
                        if(asPlanIcon) asPlanIcon.className = 'fas ' + planIcon;

                        // Theme application
                        const asPlanCard = document.getElementById('current-plan-status-card');
                        if(asPlanCard) {
                            let themeSuffix = planName.toLowerCase().replace(/\s+/g, '-');
                            if (isClinicasUser) themeSuffix = 'clinicas';
                            if (isAdminUser) themeSuffix = 'admin'; // Future proof
                            asPlanCard.className = 'premium-status-card theme-' + themeSuffix + (planName === 'Carregando...' ? ' theme-essential' : '');
                        }

                        // Hide the current plan card from the selection grid
                        const allPlanCards = ['essential', 'plus', 'premium', 'platinum'];
                        allPlanCards.forEach(id => {
                            const el = document.getElementById('plan-card-' + id);
                            if (el) el.style.display = (id === planName.toLowerCase()) ? 'none' : 'flex';
                        });

                        // Initial Plan Details
                        if(planName !== "Carregando...") {
                            this.updatePlanDetailsCard(planName);
                        }


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

            async downloadTask(taskId, count) {
                // Wrapper para compatibilidade e lógica de confirmação se necessário
                return this.downloadFile(taskId);
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
                    this.uploadedFiles[mid] = [];
                    const list = document.getElementById(`file-list-${mid}`);
                    if (list) list.innerHTML = '';
                    localStorage.setItem('hemn_uploaded_files', JSON.stringify(this.uploadedFiles));
                }

                for (let f of files) {
                    const fd = new FormData(); fd.append("file", f);
                    
                    // Create a placeholder for progress
                    const list = document.getElementById(`file-list-${mid}`);
                    const progressItem = document.createElement('div');
                    progressItem.className = 'nav-link fade-in';
                    progressItem.style.marginTop = "8px";
                    progressItem.style.background = "rgba(59, 130, 246, 0.1)";
                    progressItem.style.border = "1px solid rgba(59, 130, 246, 0.2)";
                    progressItem.innerHTML = `
                        <i class="fas fa-sync fa-spin" style="color:#3b82f6; margin-right: 10px;"></i>
                        <span style="flex-grow: 1;">Enviando ${f.name}...</span>
                        <span id="upload-pct-${mid}" style="font-weight:bold; color:#3b82f6; margin-left:10px">0%</span>
                    `;
                    list.appendChild(progressItem);

                    try {
                        const final = await new Promise((resolve, reject) => {
                            const xhr = new XMLHttpRequest();
                            xhr.open('POST', `${API}/upload`);
                            xhr.setRequestHeader('Authorization', `Bearer ${this.token}`);
                            
                            xhr.upload.onprogress = (e) => {
                                if (e.lengthComputable) {
                                    const pct = Math.round((e.loaded / e.total) * 100);
                                    const pctLabel = document.getElementById(`upload-pct-${mid}`);
                                    if (pctLabel) pctLabel.innerText = pct + "%";
                                }
                            };

                            xhr.onload = () => {
                                if (xhr.status >= 200 && xhr.status < 300) {
                                    resolve(JSON.parse(xhr.responseText));
                                } else {
                                    reject(new Error(xhr.responseText));
                                }
                            };
                            xhr.onerror = () => reject(new Error("Network Error"));
                            xhr.send(fd);
                        });

                        progressItem.remove();
                        this.uploadedFiles[mid].push(final.file_id);
                        localStorage.setItem('hemn_uploaded_files', JSON.stringify(this.uploadedFiles));
                        this.renderFile(mid, f.name, final.file_id);
                        this.showToast(`Arquivo Pronto: ${f.name}`, "info");
                    } catch (e) {
                        progressItem.innerHTML = `<i class="fas fa-exclamation-triangle" style="color:#ef4444; margin-right: 10px;"></i> <span style="color:#ef4444">Falha no upload de ${f.name}</span>`;
                        this.showToast("Falha no upload", "error");
                        console.error(e);
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

            async startTask(endpoint, body, midRaw) {
                const mid = (midRaw.includes('enrich') || midRaw.includes('enrique')) ? 'enrich' : 
                            ((midRaw.includes('extract') || midRaw.includes('extra')) ? 'extract' : midRaw);
                // Bloqueio de Multi-tarefas para perfis comuns (Exceto Busca Unitária e Operadora que são rápidas)
                if (this.user && this.user.role !== 'ADMIN' && mid !== 'manual' && mid !== 'carrier') {
                    const activeTasks = this.tasks.filter(t => !t.done);
                    if (activeTasks.length > 0) {
                        this.alert("Processo em Andamento", "Seu perfil permite apenas **uma pesquisa massiva ativa** por vez. Por favor, aguarde o término do processo atual para iniciar um novo.", { type: 'warning' });
                        return null;
                    }
                }

                try {
                    const res = await fetch(`${API}${endpoint}`, {
                        method: 'POST',
                        headers: { 'Authorization': `Bearer ${this.token}`, 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    const data = await res.json();
                    if (!res.ok) {
                        if (data.detail && data.detail.includes("Faça upgrade")) {
                            this.alert("Módulo Bloqueado", data.detail, { type: 'warning' });
                        } else {
                            this.showToast(data.detail || "Erro no processamento", "error");
                        }
                        return null;
                    }

                    if (data.task_id) {
                        const normalizedMid = mid.toLowerCase().includes('enrich') ? 'enrich' : (mid.toLowerCase().includes('extract') ? 'extract' : mid);
                        const taskInfo = { 
                            id: data.task_id, 
                            mid: normalizedMid, 
                            startTime: Date.now(),
                            filters: body.filterSummary || null
                        };
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

                        // Passa o resumo dos filtros para renderização imediata
                        this.renderTaskCard(data.task_id, mid, { filters: body.filterSummary || null });
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
                    if (activeTasks && Array.isArray(activeTasks)) {
                        activeTasks.forEach(task => {
                            // if (!this.tasks.find(t => t.id === task.id)) {
                                let midRaw = (task.module || "").toLowerCase();
                                let mid = (midRaw.includes('enrich') || midRaw.includes('enrique')) ? 'enrich' : 
                                          ((midRaw.includes('extract') || midRaw.includes('extra')) ? 'extract' : midRaw);
                                console.log(`[DEBUG] Task Recovery - TID: ${task.id}, Raw Module: ${task.module}, Normalized Mid: ${mid}`);
                                
                                const taskInfo = {
                                    id: task.id,
                                    mid: mid,
                                    startTime: new Date(task.created_at).getTime(),
                                    done: task.status === 'COMPLETED' || task.status === 'FAILED' || task.status === 'CANCELLED'
                                };
                                this.tasks.push(taskInfo);
                                this.renderTaskCard(task.id, mid, task);
                                this.renderGlobalTaskCard(task.id, mid, task);
                            });
                        }
                } catch (e) {
                    console.error("Task recovery failed", e);
                }
            },

            renderGlobalTaskCard(tid, mid, savedData = null) {
                // We update TWO possible containers for redundancy
                const floatingList = document.getElementById('global-task-list');
                const sidebarList = document.getElementById('global-tasks-container');
                const tracker = document.getElementById('global-task-tracker');
                
                if (!floatingList && !sidebarList) {
                    console.warn("No task containers found for TID:", tid);
                    return;
                }

                // Show tracker if hidden (DISABLED BY USER REQUEST)
                if (tracker) tracker.style.display = 'none'; 

                const moduleLabels = {
                    'enrich': 'ENRIQUECIMENTO',
                    'extract': 'EXTRAÇÃO',
                    'extraction': 'EXTRAÇÃO',
                    'carrier': 'OPERADORA',
                    'unify': 'UNIFICAÇÃO',
                    'split': 'DIVISÃO',
                    'manual': 'BUSCA UNITÁRIA'
                };
                const moduleLabel = moduleLabels[mid] || mid.toUpperCase();
                const rawStatus = savedData?.status?.toUpperCase() || "QUEUED";
                const statusLabel = this.statusMap[rawStatus] || rawStatus;
                const message = savedData?.message || "Iniciando...";
                const progress = savedData?.progress || 0;

                const createCardHtml = (prefix) => `
                    <div class="gtask-name">
                        <span><i class="fas fa-cog"></i> ${moduleLabel} &mdash; TI-${tid.substring(0, 6)}</span>
                        <span id="${prefix}status-${tid}" style="color:var(--text-3); font-weight:600">${statusLabel}</span>
                    </div>
                    <div class="gtask-msg" id="${prefix}msg-${tid}">${message}</div>
                    <div class="gtask-progress">
                        <div class="gtask-bar" id="${prefix}prog-${tid}" style="width: ${progress}%"></div>
                    </div>
                    <div style="position: absolute; top: 10px; right: 10px; display: flex; gap: 8px;">
                        <button class="gtask-dismiss" onclick="this.closest('.gtask-card').remove()" title="Remover Card" style="background:none; border:none; color:var(--text-3); cursor:pointer; font-size:14px; opacity:0.6; transition:opacity 0.2s;" onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.6'">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `;

                // Update Floating List
                if (floatingList) {
                    let card = document.getElementById(`gtask-f-${tid}`);
                    if (!card) {
                        card = document.createElement('div');
                        card.className = 'gtask-card active';
                        card.id = `gtask-f-${tid}`;
                        card.style.position = 'relative';
                        floatingList.prepend(card);
                    }
                    card.innerHTML = createCardHtml('gf-');
                }

                // Update Sidebar List
                if (sidebarList) {
                    let card = document.getElementById(`gtask-s-${tid}`);
                    if (!card) {
                        card = document.createElement('div');
                        card.className = 'gtask-card active';
                        card.id = `gtask-s-${tid}`;
                        card.style.position = 'relative';
                        card.style.background = 'rgba(0,0,0,0.05)';
                        card.style.padding = '10px';
                        card.style.borderRadius = '8px';
                        card.style.fontSize = '10px';
                        sidebarList.prepend(card);
                    }
                    card.innerHTML = createCardHtml('gs-');
                }
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
                try {
                    const tidStr = tid ? String(tid) : 'no-id';
                    console.log(`[DEBUG] renderTaskCard - TID: ${tidStr}, MID: ${mid}`);
                    const title = document.getElementById(`title-${mid}`);
                    if (title) {
                        title.style.display = 'block';
                        title.style.color = 'red';
                        title.innerHTML = `PESQUISAS ATIVAS (EXEC-${mid}):`;
                    }
                    console.log(`[DEBUG] renderTaskCard - TID: ${tidStr}, MID: ${mid}`);
                    const container = document.getElementById(`tasks-${mid}`);
                    if (!container) {
                        console.error(`[CRITICAL] Container tasks-${mid} not found in DOM!`);
                        return;
                    }

                    // Evita duplicar se já foi renderizado (ex: pelo recovery)
                    if (document.getElementById(`task-${tidStr}`)) return;

                    const card = document.createElement('div');
                    card.id = `task-${tidStr}`;
                card.className = "glass-card";
                card.style.marginTop = "15px";
                card.style.borderColor = "var(--border-focus)";

                const rawStatus = (savedData?.status || "QUEUED").toUpperCase();
                const statusLabel = this.statusMap[rawStatus] || rawStatus;
                const message = savedData?.message || "Iniciando motores de busca Titanium...";
                const progress = savedData?.progress || 0;
                const filterText = savedData?.filters || savedData?.filterSummary || '';

                card.innerHTML = `
                    <button onclick="this.closest('.glass-card').remove()" style="position:absolute; top:8px; right:8px; background:rgba(0,0,0,0.1); border:none; color:var(--text-2); cursor:pointer; width:22px; height:22px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:10px; z-index:10; transition:all 0.2s;" onmouseover="this.style.background='rgba(239,68,68,0.2)'; this.style.color='#ef4444'" onmouseout="this.style.background='rgba(0,0,0,0.1)'; this.style.color='var(--text-2)'">
                        <i class="fas fa-times"></i>
                    </button>
                    <div style="display:flex; justify-content:space-between; align-items:center; padding-right:30px">
                        <span style="font-size:12px; font-weight:700">TI-ID: ${tidStr.substring(0, 8)}</span>
                        <div class="badge badge-blue" id="status-${tid}">${statusLabel}</div>
                    </div>
                    <div id="filters-${tid}" style="font-size:10px; color:var(--accent); font-weight:600; margin-top:4px; display:${filterText ? 'flex' : 'none'}; align-items:center; gap:5px">
                        <i class="fas fa-filter" style="font-size:9px"></i>
                        <span>${filterText}</span>
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
                card.style.position = "relative";
                container.appendChild(card);
                
                // Title updated at start of function for diagnostic purposes
                
                // Garantir visibilidade
                setTimeout(() => {
                    const card = document.getElementById(`task-${tid}`);
                    if (card) {
                        card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                        card.style.animation = 'pulse-focus 2s infinite';
                        setTimeout(() => card.style.animation = '', 4000);
                    }
                }, 100);

                if (savedData && (savedData.status === 'COMPLETED' || savedData.status === 'SUCCESS' || savedData.result_file)) {
                    const count = savedData.record_count || 0;
                    const isSplit = mid === 'split';
                    const btnText = isSplit ? "Baixar Arquivos Divididos" : (this.user && this.user.role === 'MAYK' ? "Baixar Arquivos Processados" : `Baixar e Consumir Créditos (${count.toLocaleString()} Cr)`);
                    const btnIcon = isSplit ? "fa-file-archive" : "fa-download";
                    
                    const downloadHtml = `
                        <div style="margin-top:15px; padding-top:12px; border-top:1px solid var(--border-color); color:var(--text-3); font-size:11px">
                            <i class="fas fa-database"></i> ${isSplit ? 'Fatiamento concluído' : `Encontrados: <b>${count.toLocaleString()}</b> registros.`}
                        </div>
                        <button onclick="app.downloadTask('${tid}', ${count})" class="btn-primary" style="margin-top:10px; width:100%; border:none; height:40px; border-radius:8px; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:8px">
                            <i class="fas ${btnIcon}"></i> ${btnText}
                        </button>
                    `;
                    card.insertAdjacentHTML('beforeend', downloadHtml);
                    const cancelZone = document.getElementById(`cancel-zone-${tid}`);
                    if (cancelZone) cancelZone.style.display = 'none';
                    
                    const timeLabel = document.getElementById(`time-label-${tid}`);
                    if (timeLabel) timeLabel.innerHTML = `<i class="fas fa-check-circle" style="color:var(--g-success); margin-right:5px"></i> PROCESSO CONCLUÍDO`;
                }
                } catch (err) {
                    console.error("[FATAL] Error in renderTaskCard:", err);
                }
            },

            dismissTask(tid, mid) {
                const el = document.getElementById(`task-${tid}`);
                if (el) el.remove();
                
                // Se não houver mais cards, esconde o título
                const container = document.getElementById(`tasks-${mid}`);
                if (container && container.children.length === 0) {
                    const title = document.getElementById(`title-${mid}`);
                    if (title) title.style.display = 'none';
                }
            },

            toggleManualMode(isPJ) {
                document.getElementById('manual-fields-pf').style.display = isPJ ? 'none' : 'grid';
                document.getElementById('manual-fields-pj').style.display = isPJ ? 'grid' : 'none';
                
                // Highlight Labels
                if (isPJ) {
                    document.getElementById('label-pj').classList.add('active');
                    document.getElementById('label-pf').classList.remove('active');
                } else {
                    document.getElementById('label-pf').classList.add('active');
                    document.getElementById('label-pj').classList.remove('active');
                }

                // Limpar campos ao trocar
                if (isPJ) {
                    document.getElementById('manual-name').value = '';
                    document.getElementById('manual-cpf').value = '';
                } else {
                    document.getElementById('manual-cnpj').value = '';
                    document.getElementById('manual-phone').value = '';
                }
            },

            async runManualSearch() {
                const isPJ = document.getElementById('manual-mode-switch').checked;
                let name = '', cpf = '', cnpj = '', phone = '';
                
                if (isPJ) {
                    cnpj = document.getElementById('manual-cnpj').value;
                    phone = document.getElementById('manual-phone').value;
                    if (!cnpj && !phone) {
                        this.showToast("Preencha CNPJ ou Telefone", "warning");
                        return;
                    }
                } else {
                    name = document.getElementById('manual-name').value;
                    cpf = document.getElementById('manual-cpf').value;
                    if (!name && !cpf) {
                        this.showToast("Preencha Nome ou CPF/CNPJ", "warning");
                        return;
                    }
                }

                const resultsContainer = document.getElementById('manual-results');
                resultsContainer.style.display = 'block';
                resultsContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="icon fas fa-circle-notch fa-spin"></i>
                        <p>Navegando pela Base Titanium...</p>
                    </div>
                `;

                const searchLabel = isPJ ? (cnpj || phone) : (cpf || name);
                const data = await this.startTask('/tasks/enrich', { 
                    manual: true, 
                    name, 
                    cpf,
                    cnpj,
                    phone,
                    filterSummary: `Busca: ${searchLabel}`
                }, 'manual');

                if (data && Array.isArray(data)) {
                    await this.refreshUser(); // Update balance
                    let saldoAtual = this.user ? Math.max(0, this.user.total_limit - this.user.current_usage).toFixed(1) : '--';
                    this.addNotification("Busca Unitária Concluída", `Foram encontrados ${data.length} resultados. Gastou: 0.5 Cr | Saldo Atual: ${saldoAtual} Cr`, "success");
                    if (data.length === 0) {
                        resultsContainer.innerHTML = `
                            <div class="glass-card fade-in" style="text-align:center; padding: var(--s-8);">
                                <i class="fas fa-search-minus" style="font-size:48px; color:var(--text-3); margin-bottom:15px"></i>
                                <h3>Nenhum registro encontrado</h3>
                                <p style="color:var(--text-dim)">Pode ser necessário verificar a grafia do nome ou a numeração do CPF.</p>
                            </div>
                        `;
                    } else {
                        let html = `
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:var(--s-4)">
                                <div class="nav-label" style="margin:0">PESQUISA: Resultados da Inteligência (${data.length})</div>
                            </div>
                        `;
                        data.forEach((item, i) => {
                            html += `
                            <div class="glass-card fade-in-up" style="margin-bottom: var(--s-4); animation-delay: ${i * 0.1}s">
                                <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:15px; border-bottom:1px solid var(--border); padding-bottom:10px">
                                    <h3 class="gradient-text">${item.razao_social || 'N/A'}</h3>
                                    <div class="badge ${item.situacao == 'ATIVA' ? 'badge-green' : 'badge-red'}">${item.situacao}</div>
                                </div>
                                
                                <div class="form-grid" style="margin-bottom:20px">
                                    <div><label class="nav-label" style="padding:0">CNPJ Principal</label><div class="emp-name">${item.cnpj_completo || 'N/A'}</div></div>
                                    <div><label class="nav-label" style="padding:0">CNAE Principal</label><div class="emp-name">${item.cnae_principal || 'N/A'}</div></div>
                                    <div><label class="nav-label" style="padding:0">MEI (SIM/NÃO)</label><div class="emp-name">${item.cnpj_cpf_socio || 'N/A'}</div></div>
                                    <div><label class="nav-label" style="padding:0">E-mail Corporativo</label><div class="emp-name" style="color:var(--accent)">${item.email_novo || 'N/A'}</div></div>
                                </div>

                                <!-- INFO EXPANSÍVEL -->
                                <div id="details-${i}" style="max-height: 0; overflow: hidden; transition: all 0.5s ease; border-top: 1px dashed var(--border); margin-top: 10px; padding-top: 0; opacity: 0;">
                                    <div class="form-grid" style="padding: 15px 0; gap: 15px;">
                                        <div><label class="nav-label" style="padding:0; font-size:10px">NOME FANTASIA</label><div class="emp-name" style="font-size:12px">${item.nome_fantasia || 'N/A'}</div></div>
                                        <div><label class="nav-label" style="padding:0; font-size:10px">DATA DE ABERTURA</label><div class="emp-name" style="font-size:12px">${item.data_abertura ? item.data_abertura.split('-').reverse().join('/') : 'N/A'}</div></div>
                                        <div><label class="nav-label" style="padding:0; font-size:10px">CAPITAL SOCIAL</label><div class="emp-name" style="font-size:12px">R$ ${parseFloat(item.capital_social || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div></div>
                                        <div><label class="nav-label" style="padding:0; font-size:10px">PORTE</label><div class="emp-name" style="font-size:12px">${item.porte || 'N/A'}</div></div>
                                        <div><label class="nav-label" style="padding:0; font-size:10px">NATUREZA JURÍDICA</label><div class="emp-name" style="font-size:12px">${item.natureza_juridica || 'N/A'}</div></div>
                                        <div><label class="nav-label" style="padding:0; font-size:10px">SÓCIO/RESPONSÁVEL</label><div class="emp-name" style="font-size:12px">${item.socio_nome || 'N/A'}</div></div>
                                        <div style="grid-column: span 2;"><label class="nav-label" style="padding:0; font-size:10px">CNAE SECUNDÁRIO</label><div class="emp-name" style="font-size:11px; white-space: normal; line-height: 1.4;">${item.cnae_secundario || 'Nenhum registrado'}</div></div>
                                    </div>
                                </div>

                                <div style="display:grid; grid-template-columns: 2fr 1fr; gap:var(--s-4); align-items: center">
                                    <div style="display:flex; gap:10px; align-items:center">
                                        <div style="background:var(--bg-hover); padding:15px; border-radius:var(--r-md); text-align: center; flex:1">
                                            <div class="stat-label">📍 LOCALIZAÇÃO</div>
                                            <div class="emp-name" style="font-size:13px">${item.endereco_completo || 'N/A'}</div>
                                        </div>
                                        <button onclick="app.toggleCardDetails('details-${i}', this)" class="btn-secondary" style="height: 60px; width: 60px; padding: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; font-size: 10px; border: 1px solid var(--border);">
                                            <i class="fas fa-chevron-down" style="font-size: 16px; transition: transform 0.3s ease;"></i>
                                            DETALHES
                                        </button>
                                    </div>
                                    <div style="background:var(--g-primary); padding:15px; border-radius:var(--r-md); color:#fff; text-align: center;">
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

            toggleCardDetails(id, btn) {
                const el = document.getElementById(id);
                const icon = btn.querySelector('i');
                if (el.style.maxHeight === '0px' || !el.style.maxHeight || el.style.maxHeight === '0') {
                    el.style.maxHeight = '500px';
                    el.style.opacity = '1';
                    el.style.paddingTop = '15px';
                    icon.style.transform = 'rotate(180deg)';
                    btn.style.color = 'var(--accent)';
                } else {
                    el.style.maxHeight = '0';
                    el.style.opacity = '0';
                    el.style.paddingTop = '0';
                    icon.style.transform = 'rotate(0deg)';
                    btn.style.color = 'inherit';
                }
            },

            async pollTasks() {
                // Tique global para contagem regressiva em tempo real
                if (this.pollInterval1) clearInterval(this.pollInterval1);
                this.pollInterval1 = setInterval(() => {
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

                if (this.pollInterval2) clearInterval(this.pollInterval2);
                this.pollInterval2 = setInterval(async () => {
                    if (this.tasks.length === 0) return;
                    for (let t of this.tasks) {
                        if (t.done) continue;
                        try {
                            const res = await fetch(`${API}/tasks/${t.id}`, { 
                                headers: { 'Authorization': `Bearer ${this.token}` } 
                            });
                            const data = await res.json();

                            if (data.status === 'NOT_FOUND') {
                                t.done = true;
                                let saved = JSON.parse(localStorage.getItem('hemn_active_tasks') || '[]');
                                saved = saved.filter(x => x.id !== t.id);
                                localStorage.setItem('hemn_active_tasks', JSON.stringify(saved));
                                ['f', 's'].forEach(p => {
                                    const card = document.getElementById(`gtask-${p}-${t.id}`);
                                    if (card) card.remove();
                                });
                                continue;
                            }

                            // Update in-memory and storage
                            Object.assign(t, data);
                            let saved = JSON.parse(localStorage.getItem('hemn_active_tasks') || '[]');
                            const idx = saved.findIndex(x => x.id === t.id);
                            if (idx !== -1) {
                                saved[idx] = { ...saved[idx], ...data };
                                localStorage.setItem('hemn_active_tasks', JSON.stringify(saved));
                            }

                            const rawStatus = data.status ? data.status.toUpperCase() : "QUEUED";
                            const statusLabel = this.statusMap[rawStatus] || rawStatus;
                            const isDone = (rawStatus === 'COMPLETED' || rawStatus === 'SUCCESS' || rawStatus === 'FAILED' || rawStatus === 'CANCELLED');

                            // Update Module-Specific Card
                            const statusBadge = document.getElementById(`status-${t.id}`);
                            const progressBar = document.getElementById(`prog-${t.id}`);
                            const msgLabel = document.getElementById(`msg-${t.id}`);
                            const pctLabel = document.getElementById(`pct-${t.id}`);
                            const timeLabel = document.getElementById(`time-label-${t.id}`);

                            if (statusBadge) {
                                statusBadge.innerText = statusLabel;
                                if (isDone) {
                                    statusBadge.className = (rawStatus === 'FAILED' || rawStatus === 'CANCELLED') ? "badge badge-red" : "badge badge-green";
                                }
                            }
                            if (msgLabel && data.message) msgLabel.innerText = data.message;
                            if (progressBar && data.progress !== undefined) {
                                progressBar.style.width = data.progress + "%";
                                if (pctLabel) pctLabel.innerText = data.progress + "%";
                            }

                            // Update Global Cards (Floating and Sidebar Tracker)
                            ['gf-', 'gs-'].forEach(prefix => {
                                const gMsg = document.getElementById(`${prefix}msg-${t.id}`);
                                const gProg = document.getElementById(`${prefix}prog-${t.id}`);
                                const gStatus = document.getElementById(`${prefix}status-${t.id}`);
                                if (gMsg && data.message) gMsg.innerText = data.message;
                                if (gProg && data.progress !== undefined) gProg.style.width = data.progress + '%';
                                if (gStatus) gStatus.innerText = statusLabel;
                            });

                            // ESTIMAÇÃO DE TEMPO (Solo se estiver processando)
                            if (rawStatus === 'PROCESSING' && data.progress > 5 && data.progress < 100) {
                                const elapsed = (Date.now() - t.startTime) / 1000;
                                const total = elapsed / (data.progress / 100);
                                const currentEst = Math.max(0, Math.floor(total - elapsed));
                                if (!t.remaining) t.remaining = currentEst;
                                else t.remaining = Math.floor(t.remaining * 0.7 + currentEst * 0.3); // Suavização

                                if (timeLabel) {
                                    const mins = Math.floor(t.remaining / 60);
                                    const secs = Math.floor(t.remaining % 60);
                                    timeLabel.innerText = `RESTANTE: ~${mins}m ${secs}s`;
                                    timeLabel.style.color = "var(--accent)";
                                }
                            } else if (isDone && timeLabel) {
                                timeLabel.innerHTML = `<i class="fas fa-check-circle" style="color:var(--g-success); margin-right:5px"></i> PROCESSO FINALIZADO`;
                                timeLabel.style.color = "var(--g-success)";
                            }

                            // FINALIZAÇÃO ESPECIALIZADA
                            if (isDone) {
                                t.done = true;
                                const count = (data.record_count !== undefined) ? data.record_count : 0;
                                
                                // Se for sucesso, adiciona botão de download no card do módulo
                                const card = document.getElementById(`task-${t.id}`);
                                if (card && (rawStatus === 'COMPLETED' || rawStatus === 'SUCCESS') && !card.querySelector('.btn-download-ready')) {
                                    const isSplit = t.mid === 'split';
                                    const btnText = isSplit ? "Baixar Arquivos Divididos" : (this.user?.role === 'MAYK' ? "Baixar Arquivos" : `Baixar (${count.toLocaleString()} Cr)`);
                                    const downloadHtml = `
                                        <div class="btn-download-ready" style="margin-top:15px; padding-top:12px; border-top:1px solid var(--border); color:var(--text-3); font-size:11px">
                                            <i class="fas fa-database"></i> ${isSplit ? 'Fatiamento concluído' : `Registros: <b>${count.toLocaleString()}</b>`}
                                        </div>
                                        <button onclick="app.downloadTask('${t.id}', ${count})" class="btn-primary" style="margin-top:10px; width:100%; border:none; height:40px; border-radius:8px; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:8px">
                                            <i class="fas fa-download"></i> ${btnText}
                                        </button>
                                    `;
                                    card.insertAdjacentHTML('beforeend', downloadHtml);
                                      this.showToast(`Concluído: ${count.toLocaleString()} registros!`, "success");
                                      this.addNotification(`Lote Concluído`, `Processo TI-${t.id.substring(0, 6)} finalizado.`, "success");
                                      this.refreshUser();
                                }

                                if (rawStatus === 'FAILED' || rawStatus === 'CANCELLED') {
                                    this.addNotification(`Falha no Lote`, `Processo TI-${t.id.substring(0, 6)} encerrou com erro.`, "error");
                                }
                                
                                // Limpa localStorage
                                let saved = JSON.parse(localStorage.getItem('hemn_active_tasks') || '[]');
                                saved = saved.filter(x => x.id !== t.id);
                                localStorage.setItem('hemn_active_tasks', JSON.stringify(saved));

                                // Remove global cards após delay
                                setTimeout(() => {
                                    ['f', 's'].forEach(p => {
                                        const gc = document.getElementById(`gtask-${p}-${t.id}`);
                                        if (gc) gc.remove();
                                    });
                                    const list = document.getElementById('global-task-list');
                                    const trk = document.getElementById('global-task-tracker');
                                    if (list && !list.children.length && trk) {
                                        trk.style.display = 'none';
                                    }
                                }, 8000);
                            }

                        } catch (e) { console.error("Polling error:", e); }
                    }
                }, 3000);
            },

            startUnify() { 
                const count = this.uploadedFiles.unify?.length || 0;
                this.startTask('/tasks/unify', { 
                    file_ids: this.uploadedFiles.unify,
                    filterSummary: `Unificando ${count} arquivo(s)`
                }, 'unify'); 
            },
            async startEnrich() {
                const btn = document.getElementById('btn-start-enrich');
                if (!btn) return;
                const originalHtml = btn.innerHTML;
                
                try {
                    const fileId = this.uploadedFiles.enrich[0];
                    if (!fileId) {
                        this.showToast("Selecione um arquivo para enriquecer", "error");
                        return;
                    }

                    const perfilEl = document.getElementById('enrich-perfil');
                    const perfil = perfilEl ? perfilEl.value : "TODOS";
                    
                    // Feedback visual imediato
                    btn.disabled = true;
                    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> PROCESSANDO...';

                    console.log("[DEBUG] Iniciar Enriquecimento - Perfil Selecionado:", perfil);
                    const success = await this.startTask('/tasks/enrich', {
                        file_id: fileId,
                        name_col: null,
                        cpf_col: null,
                        perfil: perfil,
                        filterSummary: `Enriquecimento (${perfil})`
                    }, 'enrich');

                    if (success) {
                        // Limpar seleção de arquivos
                        this.uploadedFiles.enrich = [];
                        const dropzone = document.getElementById('dropzone-enrich');
                        if (dropzone) {
                            dropzone.innerHTML = `
                                <i class="fas fa-cloud-upload-alt" style="font-size: 32px; color: var(--accent); margin-bottom: 12px;"></i>
                                <div style="font-weight: 700; color: var(--text-1);">Arraste seu arquivo Excel ou CSV</div>
                                <div style="font-size: 11px; color: var(--text-3); margin-top: 4px;">Até 200MB por processamento</div>
                            `;
                            dropzone.style.borderColor = 'var(--border)';
                        }
                    }
                } catch (e) {
                    console.error("Enrich error:", e);
                    this.showToast("Erro ao iniciar enriquecimento", "error");
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = originalHtml;
                }
            },
            startCarrier() { 
                const phoneCol = document.getElementById('carrier-col').value;
                this.startTask('/tasks/carrier', { 
                    file_id: this.uploadedFiles.carrier[0], 
                    phone_col: phoneCol,
                    filterSummary: `Consulta de Operadoras (Coluna: ${phoneCol})`
                }, 'carrier'); 
            },
            updateClinicasFilters() {
                const scope = document.getElementById('clinicas-search-scope').value;
                document.getElementById('clinicas-filter-region').style.display = (scope === 'regiao') ? 'block' : 'none';
                document.getElementById('clinicas-filter-uf').style.display = (scope === 'estado') ? 'block' : 'none';
            },
            async runClinicasSearch() {
                const type = document.getElementById('clinicas-search-type').value;
                const term = document.getElementById('clinicas-search-term').value;
                const scope = document.getElementById('clinicas-search-scope').value;
                
                if (!term) {
                    this.showToast("Informe o termo de busca", "warning");
                    return;
                }

                const btn = document.getElementById('btn-run-clinicas');
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Pesquisando na Base ClickHouse...';

                try {
                    const body = { 
                        search_type: type, 
                        search_term: term, 
                        scope: scope.toUpperCase() 
                    };
                    if (scope === 'regiao') body.regiao_nome = document.getElementById('clinicas-val-region').value;
                    if (scope === 'estado') body.uf = document.getElementById('clinicas-val-uf').value;

                    const res = await fetch(`${API}/leads/search`, {
                        method: 'POST',
                        headers: { 
                            'Authorization': `Bearer ${this.token}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(body)
                    });
                    const data = await res.json();
                    if (res.ok) {
                        this.renderClinicasResults(data.leads);
                        await this.refreshUser();
                        this.showToast("Pesquisa concluída", "success");
                    } else {
                        this.showToast(data.detail || "Erro na pesquisa de clínicas", "error");
                    }
                } catch (e) {
                    this.showToast("Erro de rede ao acessar ClickHouse", "error");
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-search-dollar"></i> REALIZAR PESQUISA PREMIUM';
                }
            },
            renderClinicasResults(leads) {
                const container = document.getElementById('clinicas-results-container');
                const tbody = document.querySelector('#clinicas-table tbody');
                tbody.innerHTML = '';

                if (!leads || leads.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 40px;">Nenhum lead encontrado com estes critérios.</td></tr>';
                } else {
                    leads.forEach(l => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td style="font-family: monospace; letter-spacing: 1px; color: var(--text-1);">${l.cpf}</td>
                            <td style="font-weight: 800; color: var(--text-1); text-transform: uppercase; letter-spacing: 0.5px;">${l.nome}</td>
                            <td style="font-size: 13px; color: var(--text-2);">${l.dt_nascimento}</td>
                            <td><span class="badge badge-warm" style="width: 42px !important; height: 22px !important;">${l.idade}</span></td>
                            <td><span class="badge badge-blue" style="width: 38px !important; height: 22px !important;">${l.uf}</span></td>
                            <td><span class="badge badge-purple" style="padding: 2px 12px; height: 22px !important;">${l.regiao}</span></td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
                container.style.display = 'block';
                container.scrollIntoView({ behavior: 'smooth' });
            },
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
                            <div class="glass-card fade-in" style="background:${brandColor}; padding:25px; text-align:center; position:relative; overflow:hidden; border:none; box-shadow: 0 10px 30px rgba(0,0,0,0.3); color: #fff;">
                                <i class="fas ${brandIcon}" style="position:absolute; right:-10px; bottom:-10px; font-size:100px; opacity:0.1; transform: rotate(-15deg); color: #fff;"></i>
                                <div style="font-size:10px; opacity:0.8; font-weight:800; letter-spacing:2px; margin-bottom:10px; color: #fff;">OPERADORA IDENTIFICADA</div>
                                <div style="font-size:38px; font-weight:900; letter-spacing:1px; text-shadow: 0 2px 10px rgba(0,0,0,0.2); color: #fff;">${data.operadora || 'NÃO IDENTIFICADA'}</div>
                                <div style="display:flex; align-items:center; justify-content:center; gap:10px; margin-top:15px; color: #fff;">
                                    <div class="badge" style="background:rgba(255,255,255,0.2); border:1px solid rgba(255,255,255,0.3); color:#fff; font-size:11px">${data.tipo || 'Móvel'}</div>
                                    <div style="font-size:12px; opacity:0.9; font-weight:500; color: #fff;">
                                        <i class="fas fa-check-double" style="margin-right:5px; color: #fff;"></i> Inteligência Titanium Ativa
                                    </div>
                                </div>
                            </div>
                        `;
                        await this.refreshUser();
                        let saldoAtual = this.user ? Math.max(0, this.user.total_limit - this.user.current_usage).toFixed(1) : '--';
                        let msgText = this.user && this.user.role === 'MAYK' ? `Número ${phone} é da ${data.operadora || 'NÃO ID.'}.` : `Número ${phone} é da ${data.operadora || 'NÃO ID.'}. Gastou: 0.1 Cr | Saldo Atual: ${saldoAtual} Cr`;
                        this.addNotification("Consulta Operadora", msgText, "success");
                    } else {
                        if (data.detail && data.detail.includes("Faça upgrade")) {
                            this.alert("Módulo Bloqueado", data.detail, { type: 'warning' });
                        } else {
                            this.showToast(data.detail || "Erro na consulta", "error");
                        }
                    }
                } catch (e) {
                    this.showToast("Erro de conexão", "error");
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-search"></i> Consultar';
                }
            },
            startSplit() { 
                if (!this.uploadedFiles.split || this.uploadedFiles.split.length === 0) {
                    this.showToast("Nenhum arquivo submetido para fatiamento", "warning");
                    return;
                }
                this.startTask('/tasks/split', { 
                    file_id: this.uploadedFiles.split[0],
                    filterSummary: "Divisão de Arquivo Heavy"
                }, 'split'); 
            },
            startExtract() {
                const uf = document.getElementById('extract-uf').value.toUpperCase();
                const cidade = document.getElementById('extract-cidade').value.toUpperCase();
                const cnae = document.getElementById('extract-cnae').value;
                const situacao = document.getElementById('extract-status').value;
                
                const sitMap = {"02": "Ativas", "04": "Baixadas", "08": "Suspensas"};
                let summary = [];
                if (uf) summary.push(uf);
                if (cidade) summary.push(cidade);
                if (cnae) summary.push(`CNAE:${cnae}`);
                if (situacao != "TODOS") summary.push(sitMap[situacao] || situacao);

                const body = {
                    uf: uf,
                    cidade: cidade,
                    cnae: cnae,
                    situacao: situacao,
                    tipo_tel: document.getElementById('extract-tipo-tel').value,
                    somente_com_telefone: document.getElementById('extract-somente-tel').checked,
                    sem_governo: document.getElementById('extract-sem-governo').checked,
                    cep_file: this.uploadedFiles.cep[0] || null,
                    operadora_inc: document.getElementById('extract-operadora-inc').value,
                    operadora_exc: document.getElementById('extract-operadora-exc').value,
                    perfil: document.getElementById('extract-perfil').value,
                    filterSummary: summary.join(' | ') || "Extração Personalizada"
                };
                this.startTask('/tasks/extract', body, 'extract');
            },
            async downloadTask(tid, cost) {
                const msgText = (this.user && this.user.role === 'MAYK') ? "Deseja baixar os resultados processados agora?" : `Deseja baixar o resultado? Isso consumirá ${cost.toLocaleString()} créditos do seu saldo.`;
                const ok = await this.confirm("Confirmar Download", msgText, {
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
                        // Flexible parse: match any numbers followed by "Cr"
                        let missingAmount = 0;
                        try {
                            const credits = err.detail.match(/([\d,.]+)\s*Cr/g);
                            if (credits && credits.length >= 2) {
                                const parseNum = (s) => parseFloat(s.replace(/[^\d.]/g, ''));
                                const nec = parseNum(credits[0]);
                                const dis = parseNum(credits[1]);
                                missingAmount = Math.ceil((nec - dis) / 500);
                                if (missingAmount < 5) missingAmount = 5;
                            }
                        } catch(e) { console.error("Erro ao calcular recarga:", e); }

                        const action = await this.confirm("Saldo Insuficiente", err.detail, { 
                            type: 'error',
                            showRecharge: missingAmount > 0,
                            rechargeText: `Recarregar R$ ${missingAmount}`,
                            confirmText: 'Entendido',
                            showCancel: false
                        });

                        if (action === 'recharge') {
                            this.openRechargeModal(missingAmount);
                        }
                        return;
                    }
                    if (resp.ok) {
                        const token = localStorage.getItem('hemn_token');
                        // Usar window.open ou location.href para arquivos grandes, evitando limites de memória do Blob
                        window.location.href = `${API}/download-direct/${tid}?token=${token}`;
                        
                        await this.refreshUser();
                        let saldoAtual = this.user ? Math.max(0, this.user.total_limit - this.user.current_usage).toFixed(1) : '--';
                        this.showToast("Iniciando Download...", "success");
                        let msgText = this.user && this.user.role === 'MAYK' ? `O arquivo está sendo baixado diretamente pelo navegador.` : `O arquivo está sendo baixado diretamente pelo navegador. Gastou: ${cost.toLocaleString()} Cr | Saldo Atual: ${saldoAtual} Cr`;
                        this.addNotification("Download Iniciado", msgText, "success");
                    } else this.alert("Erro no Download", "Ocorreu um problema ao baixar o arquivo.", { type: 'error' });
                } catch (e) { console.error(e); }
            },

            // --- ASAAS RECHARGE (V2 - PIX & CARTÃO) ---
            rechargeMethod: 'PIX',
            checkoutState: { type: 'recharge', planId: null, price: 0 },
            
            openPlanInvoice() {
                // Prioritize user role for robust redirection
                if (this.user && this.user.role === 'CLINICAS') {
                    console.log("[DEBUG] openPlanInvoice: Redirection based on ROLE (CLINICAS)");
                    this.openCheckout('plan', 'clinicas');
                    return;
                }

                // Fallback: Get current plan name from the summary card
                const el = document.getElementById('assinatura-plan-name');
                let nameText = el ? el.innerText.toLowerCase() : '';
                
                // Normalização para ignorar acentos (ex: clínicas -> clinicas)
                const normalizedText = nameText.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                console.log("[DEBUG] openPlanInvoice: nameText=" + nameText + ", normalized=" + normalizedText);

                // If it's a fixed plan, open that plan's checkout
                if (normalizedText.includes('clinica')) {
                    this.openCheckout('plan', 'clinicas');
                } else if (['essential', 'plus', 'premium', 'platinum'].some(p => normalizedText.includes(p))) {
                    const planMatch = ['essential', 'plus', 'premium', 'platinum'].find(p => normalizedText.includes(p));
                    this.openCheckout('plan', planMatch);
                } else {
                    // Otherwise, show the plan selection grid
                    this.showModule('assinatura', document.getElementById('nav-assinatura'));
                }
            },

            openCheckout(type, payload) {
                // Persist for refresh
                localStorage.setItem('hemn_checkout_type', type);
                localStorage.setItem('hemn_checkout_payload', payload);

                this.checkoutState.type = type;
                this.checkoutState.planId = null;
                this.checkoutState.price = 0;
                
                const themeArea = document.getElementById('checkout-theme-area');
                const titleEl = document.getElementById('checkout-title');
                const subtitleEl = document.getElementById('checkout-subtitle');
                const iconEl = document.getElementById('checkout-icon');
                
                const planDetails = document.getElementById('checkout-plan-details');
                const rechargeDetails = document.getElementById('checkout-recharge-details');
                const featuresUl = document.getElementById('checkout-features-ul');
                const priceDisplay = document.getElementById('checkout-price-display');
                
                // Reset Payment Step
                document.getElementById('checkout-pix-step-1').style.display = 'block';
                document.getElementById('checkout-pix-step-2').style.display = 'none';
                document.getElementById('checkout-qrcode-loading').style.display = 'block';
                document.getElementById('checkout-qrcode-img').style.display = 'none';
                document.getElementById('checkout-payment-status').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Aguardando pagamento...';
                document.getElementById('btn-gerar-checkout-pix').disabled = false;
                document.getElementById('btn-gerar-checkout-pix').innerHTML = '<i class="fas fa-bolt"></i> Gerar PIX';
                
                // Clear any polling interval
                if (this.rechargeInterval) clearInterval(this.rechargeInterval);

                if (type === 'plan') {
                    const planId = payload;
                    const details = this.PLAN_DETAILS_MAP[planId.toLowerCase()];
                    if (!details) return;
                    
                    this.checkoutState.planId = planId;
                    
                    let price = 899;
                    if(planId.toLowerCase() === 'plus') { price = 1399; }
                    if(planId.toLowerCase() === 'premium') { price = 2499; }
                    if(planId.toLowerCase() === 'platinum') { price = 3799; }
                    if(planId.toLowerCase() === 'clinicas') { price = 1099; }
                    this.checkoutState.price = price;
                    
                    themeArea.className = 'summary-header theme-' + planId.toLowerCase();
                    titleEl.innerText = `Plano ${details.name}`;
                    subtitleEl.innerText = 'Detalhes da sua contratação';
                    iconEl.className = 'fas ' + details.icon;
                    
                    featuresUl.innerHTML = '';
                    // Skip the first category's first item if it's already used as the "Capacidade" feature
                    const allFeatures = [];
                    details.features.forEach(cat => {
                        cat.items.forEach(item => allFeatures.push(item));
                    });
                    
                    // Filter out the main credits feature from the list to avoid duplication
                    const creditsStr = details.features.find(cat => cat.cat === 'Capacidade')?.items[0] || 'Créditos inclusos';
                    const listFeatures = allFeatures.filter(f => f !== creditsStr).slice(0, 4); // Show up to 4 other features
                    
                    listFeatures.forEach(f => {
                         featuresUl.innerHTML += `<li><i class="fas fa-check"></i> <span>${f}</span></li>`;
                    });
                    
                    featuresUl.innerHTML += `<li style="margin-top: 10px; background: rgba(0,0,0,0.02); border-radius: 8px; border: 1px solid rgba(0,0,0,0.05); transition: all 0.3s ease;"><i class="fas fa-database" style="color:var(--text-2);"></i> <span><b>${creditsStr}</b></span></li>`;
                    
                    planDetails.style.display = 'block';
                    rechargeDetails.style.display = 'none';
                    priceDisplay.innerText = `R$ ${price.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                } else {
                    // Recharge or Custom
                    this.checkoutState.planId = 'custom';
                    
                    themeArea.className = 'summary-header theme-recharge';
                    titleEl.innerText = 'Adicionar Créditos';
                    subtitleEl.innerText = 'Saldo flexível avulso';
                    iconEl.className = 'fas fa-coins';
                    
                    planDetails.style.display = 'none';
                    rechargeDetails.style.display = 'block';
                    
                    document.getElementById('checkout-recharge-slider').value = payload || 50;
                    this.updateCheckoutSlider(payload || 50);
                }
                
                this.showModule('checkout');
            },
            
            updateCheckoutSlider(val) {
                const amount = parseFloat(val);
                this.checkoutState.price = amount;
                const credits = Math.floor(amount * 500);
                document.getElementById('checkout-recharge-credits-gain').innerText = credits.toLocaleString('pt-BR');
                document.getElementById('checkout-price-display').innerText = `R$ ${amount.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            },
            
            async generateCheckoutPix() {
                const amount = this.checkoutState.price;
                const planId = this.checkoutState.planId || 'custom';
                const cpfInput = document.getElementById('checkout-cpf');
                const cpfCnpj = cpfInput ? cpfInput.value : '';
                
                if (!amount || amount <= 0) {
                    this.showToast("Valor inválido", "error");
                    return;
                }
                
                if (!cpfCnpj) {
                    this.showToast("CPF/CNPJ é obrigatório", "error");
                    return;
                }

                const btn = document.getElementById('btn-gerar-checkout-pix');
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';

                try {
                    const resp = await fetch(`${API}/payments/create`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${this.token}`
                        },
                        body: JSON.stringify({
                            plan_id: planId,
                            amount: amount,
                            billingType: 'PIX',
                            cpfCnpj: cpfCnpj
                        })
                    });
                    const data = await resp.json();
                    if (!resp.ok) throw new Error(data.detail || "Erro ao gerar PIX");

                    document.getElementById('checkout-pix-step-1').style.display = 'none';
                    document.getElementById('checkout-pix-step-2').style.display = 'block';
                    
                    const qrImg = document.getElementById('checkout-qrcode-img');
                    qrImg.src = `data:image/png;base64,${data.pix_image_base64}`;
                    qrImg.onload = () => {
                        document.getElementById('checkout-qrcode-loading').style.display = 'none';
                        qrImg.style.display = 'block';
                    };
                    
                    const codeText = document.getElementById('checkout-pix-code-text');
                    if (codeText) codeText.innerText = data.pix_payload;
                    this.currentPixPayload = data.pix_payload;

                    // Start Polling for payment completion
                    if (this.rechargeInterval) clearInterval(this.rechargeInterval);
                    this.rechargeInterval = setInterval(async () => {
                        await this.refreshUser(); // Updates balance in background
                        // NOTE: If API does not expose a strict endpoint to check this specific payment order status, 
                        // refreshing user balance is the standard way. If balance changes, payment succeeded.
                    }, 5000);
                } catch (e) {
                    this.showToast(e.message, "error");
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-bolt"></i> Tentar Novamente';
                }
            },
            
            copyCheckoutPix() {
                const codeText = document.getElementById('checkout-pix-code-text');
                const payload = codeText ? codeText.innerText : (this.currentPixPayload || '');
                if (!payload || payload === '---') return;
                
                navigator.clipboard.writeText(payload).then(() => {
                    this.showToast("Código PIX copiado!", "success");
                });
            },

            maskCPF(i) {
                let v = i.value;
                if (!v) return;
                v = v.replace(/\D/g, "");
                if (v.length <= 11) {
                    v = v.replace(/(\d{3})(\d)/, "$1.$2");
                    v = v.replace(/(\d{3})(\d)/, "$1.$2");
                    v = v.replace(/(\d{3})(\d{1,2})$/, "$1-$2");
                } else {
                    v = v.replace(/^(\d{2})(\d)/, "$1.$2");
                    v = v.replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3");
                    v = v.replace(/\.(\d{3})(\d)/, ".$1/$2");
                    v = v.replace(/(\d{4})(\d)/, "$1-$2");
                }
                i.value = v;
            },

            updateCreditPreview() {
                const amount = parseFloat(document.getElementById('recharge-amount').value) || 0;
                const credits = Math.floor(amount * 500);
                const el = document.getElementById('credit-preview');
                if (el) {
                    el.innerText = `Você receberá: ${credits.toLocaleString()} créditos`;
                    el.style.color = amount >= 5 ? 'var(--accent-color)' : 'var(--text-3)';
                }
            },
            openRechargeModal(type = null, initialAmount = 50) {
               if(typeof type === 'number') {
                   initialAmount = type;
               }
               this.openCheckout('recharge', initialAmount);
            },
            selectAvulso() {
                this.openCheckout('recharge', document.getElementById('input-avulso')?.value || 50);
            },
            selectPlan(planId, price, label = null) {
                if (planId.toLowerCase() === 'custom') {
                    this.openCheckout('recharge', 100);
                } else {
                    this.openCheckout('plan', planId.toLowerCase());
                }
            },

        };
        app.init();
