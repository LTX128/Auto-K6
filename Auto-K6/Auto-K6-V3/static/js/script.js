/**
 * Auto-K6 V2 - Interface Web JavaScript
 */

class AutoK6Interface {
    constructor() {
        this.currentTab = 'dashboard';
        this.activeTestId = null;
        this.testInterval = null;
        this.currentTheme = this.getSavedTheme() || 'dark';
        this.initialize();
    }

    initialize() {
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);

        this.applyTheme(this.currentTheme);
        this.checkK6Status();
        this.loadHistory();
        this.setupEventListeners();
        this.showTab('dashboard');
    }

    getSavedTheme() {
        return localStorage.getItem('autoK6Theme') || 'dark';
    }

    saveTheme(theme) {
        localStorage.setItem('autoK6Theme', theme);
    }

    applyTheme(theme) {
        // Appliquer le thème au document
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        
        // Mettre à jour les boutons du sélecteur de thème
        document.querySelectorAll('.theme-option').forEach(option => {
            option.classList.remove('active');
            if (option.dataset.theme === theme) {
                option.classList.add('active');
            }
        });
        
        // Mettre à jour les prévisualisations des thèmes
        this.updateThemePreviews();
        
        // Sauvegarder le thème
        this.saveTheme(theme);
    }

    updateThemePreviews() {
        // Mettre à jour les prévisualisations selon le thème actuel
        const themePreviews = {
            'dark': {
                primary: '#6a11cb',
                secondary: '#2575fc',
                dark: '#121212',
                darker: '#0a0a0a'
            },
            'light': {
                primary: '#6a11cb',
                secondary: '#2575fc',
                dark: '#f8f9fa',
                darker: '#e9ecef'
            },
            'purple': {
                primary: '#9c27b0',
                secondary: '#673ab7',
                dark: '#1a1a2e',
                darker: '#16213e'
            }
        };
        
        const current = themePreviews[this.currentTheme];
        
        // Mettre à jour les couleurs CSS
        document.documentElement.style.setProperty('--primary', current.primary);
        document.documentElement.style.setProperty('--secondary', current.secondary);
        document.documentElement.style.setProperty('--dark', current.dark);
        document.documentElement.style.setProperty('--darker', current.darker);
    }

    updateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('fr-FR', { hour12: false });
        document.getElementById('currentTime').textContent = timeString;
    }

    async checkK6Status() {
        try {
            const response = await fetch('/api/check_k6');
            const data = await response.json();
            this.updateK6StatusUI(data.installed);
        } catch (error) {
            this.updateK6StatusUI(false);
        }
    }

    updateK6StatusUI(installed) {
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        const k6StatusText = document.getElementById('k6StatusText');
        const settingStatusDot = document.getElementById('settingStatusDot');
        const settingStatusText = document.getElementById('settingStatusText');
        
        if (installed) {
            statusDot.className = 'status-dot connected';
            statusText.textContent = 'k6 Ready';
            k6StatusText.textContent = 'Installed';
            settingStatusDot.className = 'status-dot connected';
            settingStatusText.textContent = 'Installed';
        } else {
            statusDot.className = 'status-dot disconnected';
            statusText.textContent = 'k6 Missing';
            k6StatusText.textContent = 'Not Installed';
            settingStatusDot.className = 'status-dot disconnected';
            settingStatusText.textContent = 'Not Installed';
        }
    }

    async loadHistory() {
        try {
            const response = await fetch('/api/history');
            const history = await response.json();
            this.updateHistoryUI(history);
        } catch (error) {
            console.error('Erreur chargement historique:', error);
            this.showToast('Erreur chargement historique', 'error');
            this.updateHistoryUI([]);
        }
    }

    updateHistoryUI(history) {
        const historyBody = document.getElementById('historyBody');
        const totalTests = document.getElementById('totalTests');
        const lastTest = document.getElementById('lastTest');
        const recentTests = document.getElementById('recentTests');
        
        if (!Array.isArray(history)) {
            history = [];
        }
        
        totalTests.textContent = history.length;
        
        if (history.length > 0) {
            const latest = history[0];
            const date = new Date(latest.timestamp);
            lastTest.textContent = date.toLocaleTimeString('fr-FR', { hour12: false });
            
            recentTests.innerHTML = '';
            history.slice(0, 5).forEach(test => {
                const testEl = document.createElement('div');
                testEl.className = 'recent-test';
                
                const testDate = new Date(test.timestamp);
                const dateStr = testDate.toLocaleDateString('fr-FR');
                const timeStr = testDate.toLocaleTimeString('fr-FR', { hour12: false });
                
                testEl.innerHTML = `
                    <div class="recent-test-header">
                        <span class="recent-test-target">${test.url || test.id}</span>
                        <span class="recent-test-status ${(test.status || 'UNKNOWN').toLowerCase()}">${test.status || 'UNKNOWN'}</span>
                    </div>
                    <div class="recent-test-details">
                        <span>${test.method || 'N/A'} | ${test.vus || 'N/A'} VUs | ${test.duration || 'N/A'}</span>
                        <span>${dateStr} ${timeStr}</span>
                    </div>
                `;
                recentTests.appendChild(testEl);
            });
        } else {
            recentTests.innerHTML = '<div class="empty-state">Aucun test pour le moment</div>';
            lastTest.textContent = '--';
        }
        
        if (history.length === 0) {
            historyBody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-history">
                        <i class="fas fa-history"></i>
                        <p>Aucun test dans l'historique</p>
                    </td>
                </tr>
            `;
        } else {
            historyBody.innerHTML = history.map(test => {
                const date = new Date(test.timestamp);
                const dateStr = date.toLocaleDateString('fr-FR');
                const timeStr = date.toLocaleTimeString('fr-FR', { hour12: false });
                
                const method = test.method || 'GET';
                const methodClass = method.toLowerCase();
                
                const status = test.status || 'UNKNOWN';
                const statusClass = status.toLowerCase();
                
                return `
                    <tr>
                        <td>${dateStr}<br><small>${timeStr}</small></td>
                        <td class="target-cell">${test.url || test.id}</td>
                        <td><span class="method-badge ${methodClass}">${method}</span></td>
                        <td>${test.vus || 'N/A'}</td>
                        <td>${test.duration || 'N/A'}</td>
                        <td><span class="status-badge ${statusClass}">${status}</span></td>
                        <td>
                            <button class="btn btn-secondary btn-sm" onclick="app.viewTestDetails('${test.id}')">
                                <i class="fas fa-eye"></i>
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        }
    }

    setupEventListeners() {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.currentTarget.dataset.tab;
                this.showTab(tab);
            });
        });

        document.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                this.handleQuickAction(action);
            });
        });

        document.getElementById('runUrlTest').addEventListener('click', () => this.runUrlTest());
        document.getElementById('stopUrlTest').addEventListener('click', () => this.stopTest('url'));
        
        document.getElementById('runIpTest').addEventListener('click', () => this.runIpTest());
        document.getElementById('stopIpTest').addEventListener('click', () => this.stopTest('ip'));
        
        document.getElementById('checkSiteBtn').addEventListener('click', () => this.checkSiteStatus());
        document.getElementById('scanSiteBtn').addEventListener('click', () => this.scanWebsite());
        document.getElementById('installK6Btn').addEventListener('click', () => this.installK6());
        document.getElementById('refreshHistory').addEventListener('click', () => this.loadHistory());
        document.getElementById('clearHistory').addEventListener('click', () => this.clearHistory());
        document.getElementById('resetIpForm').addEventListener('click', () => this.resetIpForm());
        
        // Thèmes - correction de l'écouteur d'événements
        document.querySelectorAll('.theme-option').forEach(option => {
            option.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const theme = e.currentTarget.dataset.theme;
                this.setTheme(theme);
                this.showToast(`Thème changé: ${theme}`, 'success');
            });
        });
        
        document.getElementById('method').addEventListener('change', (e) => {
            this.toggleBodyField(e.target.value, 'body');
        });
        
        document.getElementById('ipMethod').addEventListener('change', (e) => {
            this.toggleBodyField(e.target.value, 'ipBody');
        });
        
        document.querySelector('.modal-close')?.addEventListener('click', () => {
            document.getElementById('testDetailsModal').style.display = 'none';
        });
        
        document.getElementById('closeModal')?.addEventListener('click', () => {
            document.getElementById('testDetailsModal').style.display = 'none';
        });
    }

    setTheme(theme) {
        this.applyTheme(theme);
    }

    async clearHistory() {
        if (!confirm('Voulez-vous vraiment effacer tout l\'historique ? Cette action est irréversible.')) {
            return;
        }

        try {
            const response = await fetch('/api/history/clear', {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Historique effacé avec succès', 'success');
                this.loadHistory();
            } else {
                this.showToast('Erreur: ' + result.error, 'error');
            }
        } catch (error) {
            this.showToast('Erreur lors de l\'effacement: ' + error.message, 'error');
        }
    }

    resetIpForm() {
        document.getElementById('ip').value = '';
        document.getElementById('port').value = '80';
        document.getElementById('protocol').value = 'http';
        document.getElementById('hostHeader').value = '';
        document.getElementById('ipMethod').value = 'GET';
        document.getElementById('ipVus').value = '10';
        document.getElementById('ipDuration').value = '10s';
        document.getElementById('ipBody').value = '';
        this.showToast('Formulaire IP réinitialisé', 'info');
    }

    toggleBodyField(method, fieldId) {
        const field = document.getElementById(fieldId);
        const group = document.getElementById(fieldId + 'Group');
        
        if (method === 'POST' || method === 'PUT') {
            field.disabled = false;
            field.style.opacity = '1';
            group.style.opacity = '1';
        } else {
            field.disabled = true;
            field.style.opacity = '0.5';
            group.style.opacity = '0.5';
        }
    }

    toggleStopButton(type, show) {
        const runBtn = type === 'url' ? document.getElementById('runUrlTest') : document.getElementById('runIpTest');
        const stopBtn = type === 'url' ? document.getElementById('stopUrlTest') : document.getElementById('stopIpTest');
        
        if (show) {
            runBtn.style.display = 'none';
            stopBtn.style.display = 'inline-flex';
            runBtn.disabled = true;
        } else {
            runBtn.style.display = 'inline-flex';
            stopBtn.style.display = 'none';
            runBtn.disabled = false;
        }
    }

    async stopTest(type) {
        if (!this.activeTestId) {
            this.showToast('Aucun test en cours', 'warning');
            return;
        }
        
        if (!confirm('Arrêter le test en cours ?')) {
            return;
        }

        try {
            this.showToast('Arrêt du test en cours...', 'info');
            
            const response = await fetch(`/api/test/stop/${this.activeTestId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            
            if (result.success) {
                if (this.testInterval) {
                    clearInterval(this.testInterval);
                    this.testInterval = null;
                }
                
                const outputArea = document.getElementById(type === 'url' ? 'urlOutput' : 'ipOutput');
                const outputContent = document.getElementById(type === 'url' ? 'urlOutputContent' : 'ipOutputContent');
                const outputStatus = outputArea.querySelector('.output-status');
                
                outputStatus.textContent = 'STOPPED';
                outputStatus.className = 'output-status error';
                outputContent.innerHTML = `
                    <div class="test-result">
                        <h4>Test Result</h4>
                        <p><strong>Status:</strong> STOPPED</p>
                        <p><strong>Message:</strong> ${result.message || 'Test arrêté par l\'utilisateur'}</p>
                        <p><strong>Time:</strong> ${new Date().toLocaleTimeString('fr-FR')}</p>
                    </div>
                `;
                
                this.toggleStopButton(type, false);
                this.showToast('Test arrêté avec succès', 'warning');
                
                setTimeout(() => this.loadHistory(), 1000);
            } else {
                this.showToast('Erreur: ' + (result.error || 'Impossible d\'arrêter le test'), 'error');
            }
        } catch (error) {
            console.error('Erreur arrêt test:', error);
            this.showToast('Erreur lors de l\'arrêt: ' + error.message, 'error');
        }
    }

    showTab(tabName) {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.tab === tabName) {
                btn.classList.add('active');
            }
        });
        
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
            if (tab.id === tabName) {
                tab.classList.add('active');
            }
        });
        
        this.currentTab = tabName;
    }

    async runUrlTest() {
        const url = document.getElementById('url').value;
        const method = document.getElementById('method').value;
        const vus = document.getElementById('vus').value;
        const duration = document.getElementById('duration').value;
        const body = document.getElementById('body').value;

        if (!url || !url.startsWith('http')) {
            this.showToast('URL invalide. Doit commencer par http:// ou https://', 'error');
            return;
        }

        const testData = {
            url: url,
            method: method,
            vus: parseInt(vus),
            duration: duration
        };

        if (body && (method === 'POST' || method === 'PUT')) {
            try {
                testData.body = JSON.parse(body);
            } catch (e) {
                this.showToast('JSON invalide dans le corps', 'error');
                return;
            }
        }

        try {
            this.showToast('Démarrage du test...', 'info');
            this.toggleStopButton('url', true);
            
            const response = await fetch('/api/test/url', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(testData)
            });

            const result = await response.json();
            
            if (result.error) {
                this.showToast('Erreur: ' + result.error, 'error');
                this.toggleStopButton('url', false);
                return;
            }

            this.activeTestId = result.test_id;
            this.showToast('Test démarré avec succès!', 'success');
            
            const outputArea = document.getElementById('urlOutput');
            const outputContent = document.getElementById('urlOutputContent');
            outputArea.style.display = 'block';
            outputContent.innerHTML = `
                <div class="loader">
                    <i class="fas fa-spinner fa-spin"></i>
                    Test en cours... ID: ${result.test_id}
                </div>
            `;
            
            this.monitorTest(result.test_id, 'url');
        } catch (error) {
            this.showToast('Erreur: ' + error.message, 'error');
            this.toggleStopButton('url', false);
        }
    }

    async runIpTest() {
        const ip = document.getElementById('ip').value;
        const port = document.getElementById('port').value;
        const protocol = document.getElementById('protocol').value;
        const hostHeader = document.getElementById('hostHeader').value;
        const method = document.getElementById('ipMethod').value;
        const vus = document.getElementById('ipVus').value;
        const duration = document.getElementById('ipDuration').value;
        const body = document.getElementById('ipBody').value;

        const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
        if (!ipRegex.test(ip)) {
            this.showToast('Adresse IP invalide', 'error');
            return;
        }

        const testData = {
            ip: ip,
            port: parseInt(port),
            protocol: protocol,
            host_header: hostHeader,
            method: method,
            vus: parseInt(vus),
            duration: duration
        };

        if (body && (method === 'POST' || method === 'PUT')) {
            try {
                testData.body = JSON.parse(body);
            } catch (e) {
                this.showToast('JSON invalide dans le corps', 'error');
                return;
            }
        }

        try {
            this.showToast('Démarrage du test IP...', 'info');
            this.toggleStopButton('ip', true);
            
            const response = await fetch('/api/test/ip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(testData)
            });

            const result = await response.json();
            
            if (result.error) {
                this.showToast('Erreur: ' + result.error, 'error');
                this.toggleStopButton('ip', false);
                return;
            }

            this.activeTestId = result.test_id;
            this.showToast('Test IP démarré avec succès!', 'success');
            
            const outputArea = document.getElementById('ipOutput');
            const outputContent = document.getElementById('ipOutputContent');
            outputArea.style.display = 'block';
            outputContent.innerHTML = `
                <div class="loader">
                    <i class="fas fa-spinner fa-spin"></i>
                    Test en cours... ID: ${result.test_id}
                </div>
            `;
            
            this.monitorTest(result.test_id, 'ip');
        } catch (error) {
            this.showToast('Erreur: ' + error.message, 'error');
            this.toggleStopButton('ip', false);
        }
    }

    async monitorTest(testId, type) {
        this.testInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/test/status/${testId}`);
                const status = await response.json();
                
                if (status.status === 'stopped') {
                    clearInterval(this.testInterval);
                    this.testInterval = null;
                    this.toggleStopButton(type, false);
                    
                    const outputArea = document.getElementById(type === 'url' ? 'urlOutput' : 'ipOutput');
                    const outputContent = document.getElementById(type === 'url' ? 'urlOutputContent' : 'ipOutputContent');
                    const outputStatus = outputArea.querySelector('.output-status');
                    
                    outputStatus.textContent = 'STOPPED';
                    outputStatus.className = 'output-status error';
                    outputContent.innerHTML = `
                        <div class="test-result">
                            <h4>Test Result</h4>
                            <p><strong>Status:</strong> STOPPED</p>
                            <p><strong>Message:</strong> ${status.message || 'Test arrêté'}</p>
                            <p><strong>Time:</strong> ${status.stopped_at ? new Date(status.stopped_at).toLocaleTimeString('fr-FR') : new Date().toLocaleTimeString('fr-FR')}</p>
                        </div>
                    `;
                    
                    this.showToast('Test arrêté', 'warning');
                    this.loadHistory();
                }
                else if (status.status === 'completed') {
                    clearInterval(this.testInterval);
                    this.testInterval = null;
                    this.toggleStopButton(type, false);
                    
                    const outputArea = document.getElementById(type === 'url' ? 'urlOutput' : 'ipOutput');
                    const outputContent = document.getElementById(type === 'url' ? 'urlOutputContent' : 'ipOutputContent');
                    const outputStatus = outputArea.querySelector('.output-status');
                    
                    if (status.result) {
                        outputStatus.textContent = status.result.status;
                        outputStatus.className = `output-status ${status.result.status.toLowerCase()}`;
                        
                        outputContent.innerHTML = `
                            <div class="test-result">
                                <h4>Test Result</h4>
                                <p><strong>Status:</strong> ${status.result.status}</p>
                                <p><strong>Execution Time:</strong> ${status.result.execution_time || 'N/A'}s</p>
                                <p><strong>Output:</strong></p>
                                <pre>${status.result.output || 'No output'}</pre>
                            </div>
                        `;
                        
                        if (status.result.status === 'SUCCESS') {
                            this.showToast('Test terminé avec succès!', 'success');
                        } else {
                            this.showToast('Test échoué', 'error');
                        }
                        
                        this.loadHistory();
                    }
                } else if (status.status === 'error') {
                    clearInterval(this.testInterval);
                    this.testInterval = null;
                    this.toggleStopButton(type, false);
                    this.showToast('Erreur test: ' + status.error, 'error');
                }
            } catch (error) {
                console.error('Erreur surveillance test:', error);
            }
        }, 2000);
    }

    async checkSiteStatus() {
        const url = document.getElementById('siteCheckUrl').value;
        if (!url) {
            this.showToast('Veuillez entrer une URL', 'warning');
            return;
        }

        try {
            this.showToast('Vérification du site...', 'info');
            
            const response = await fetch('/api/check_site', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            });

            const result = await response.json();
            const resultElement = document.getElementById('siteCheckResult');
            
            if (result.online) {
                resultElement.innerHTML = `
                    <div class="check-success">
                        <p><i class="fas fa-check-circle"></i> <strong>Site en ligne</strong></p>
                        <p><strong>URL:</strong> ${result.url}</p>
                        <p><strong>Status:</strong> <span class="status-success">${result.status_code}</span></p>
                        <p><strong>Temps réponse:</strong> ${result.response_time} ms</p>
                        <p><strong>Taille:</strong> ${this.formatBytes(result.content_length)}</p>
                    </div>
                `;
                this.showToast('Site en ligne!', 'success');
            } else {
                resultElement.innerHTML = `
                    <div class="check-error">
                        <p><i class="fas fa-times-circle"></i> <strong>Site hors ligne</strong></p>
                        <p><strong>URL:</strong> ${result.url}</p>
                        <p><strong>Erreur:</strong> ${result.error}</p>
                    </div>
                `;
                this.showToast('Site hors ligne!', 'error');
            }
        } catch (error) {
            this.showToast('Erreur: ' + error.message, 'error');
        }
    }

    async scanWebsite() {
        const url = document.getElementById('scanUrl').value;
        if (!url) {
            this.showToast('Veuillez entrer une URL', 'warning');
            return;
        }

        try {
            this.showToast('Scan du site en cours...', 'info');
            
            const response = await fetch('/api/scan_website', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            });

            const result = await response.json();
            const resultElement = document.getElementById('scanResult');
            
            let html = `<div class="scan-result">`;
            html += `<h4>Scan Results for ${result.url}</h4>`;
            html += `<p><strong>Scan Time:</strong> ${new Date(result.timestamp).toLocaleString('fr-FR')}</p>`;
            
            if (result.results.response?.success) {
                const resp = result.results.response;
                html += `
                    <div class="scan-section">
                        <h5><i class="fas fa-server"></i> Response Info</h5>
                        <p><strong>Status Code:</strong> ${resp.status_code}</p>
                        <p><strong>Response Time:</strong> ${resp.response_time} ms</p>
                        <p><strong>Content Type:</strong> ${resp.content_type}</p>
                        <p><strong>Content Length:</strong> ${this.formatBytes(resp.content_length)}</p>
                `;
                
                if (resp.technologies?.length > 0) {
                    html += `<p><strong>Technologies:</strong></p><ul>`;
                    resp.technologies.forEach(tech => html += `<li>${tech}</li>`);
                    html += `</ul>`;
                }
                html += `</div>`;
            }
            
            if (result.results.dns?.success) {
                const dns = result.results.dns;
                html += `
                    <div class="scan-section">
                        <h5><i class="fas fa-network-wired"></i> Network Info</h5>
                        <p><strong>IP Address:</strong> ${dns.ip}</p>
                        <p><strong>Hostname:</strong> ${dns.hostname}</p>
                `;
                
                if (dns.org && dns.org !== 'N/A') {
                    html += `<p><strong>Organization:</strong> ${dns.org}</p>`;
                }
                if (dns.city && dns.city !== 'N/A') {
                    html += `<p><strong>Location:</strong> ${dns.city}, ${dns.region}, ${dns.country}</p>`;
                }
                html += `</div>`;
            }
            
            if (result.results.ssl) {
                const ssl = result.results.ssl;
                html += `
                    <div class="scan-section">
                        <h5><i class="fas fa-lock"></i> SSL Certificate</h5>
                `;
                
                if (ssl.success && ssl.valid) {
                    html += `
                        <p><strong>Status:</strong> <span class="status-success">Valid</span></p>
                        <p><strong>Issuer:</strong> ${ssl.issuer}</p>
                        <p><strong>Subject:</strong> ${ssl.subject}</p>
                        <p><strong>Valid Until:</strong> ${ssl.not_after}</p>
                    `;
                } else {
                    html += `
                        <p><strong>Status:</strong> <span class="status-error">Invalid</span></p>
                        <p><strong>Error:</strong> ${ssl.error}</p>
                    `;
                }
                html += `</div>`;
            }
            
            html += `</div>`;
            resultElement.innerHTML = html;
            this.showToast('Scan terminé!', 'success');
        } catch (error) {
            this.showToast('Erreur: ' + error.message, 'error');
        }
    }

    async installK6() {
        if (!confirm('Installer k6 ? Cela peut prendre quelques minutes.')) {
            return;
        }

        try {
            this.showToast('Installation de k6...', 'info');
            
            const response = await fetch('/api/install_k6', {
                method: 'POST'
            });

            const result = await response.json();
            
            if (result.success) {
                this.showToast('k6 installé avec succès!', 'success');
                setTimeout(() => this.checkK6Status(), 5000);
            } else {
                this.showToast('Échec installation: ' + (result.error || 'Erreur inconnue'), 'error');
            }
        } catch (error) {
            this.showToast('Erreur: ' + error.message, 'error');
        }
    }

    handleQuickAction(action) {
        switch (action) {
            case 'url-quick':
                this.showTab('url-test');
                break;
            case 'ip-quick':
                this.showTab('ip-test');
                break;
            case 'check-site':
                this.showTab('tools');
                break;
            case 'view-history':
                this.showTab('history');
                this.loadHistory();
                break;
        }
    }

    async viewTestDetails(testId) {
        try {
            const response = await fetch(`/api/history/${testId}`);
            if (!response.ok) {
                throw new Error('Test non trouvé');
            }
            
            const test = await response.json();
            
            const modal = document.getElementById('testDetailsModal');
            const modalBody = document.getElementById('modalBody');
            
            modalBody.innerHTML = `
                <div class="test-details">
                    <p><strong>ID:</strong> ${test.id}</p>
                    <p><strong>Date:</strong> ${new Date(test.timestamp).toLocaleString('fr-FR')}</p>
                    <p><strong>Type:</strong> ${test.type || 'N/A'}</p>
                    <p><strong>Target:</strong> ${test.url || test.id}</p>
                    <p><strong>Method:</strong> ${test.method || 'N/A'}</p>
                    <p><strong>VUs:</strong> ${test.vus || 'N/A'}</p>
                    <p><strong>Duration:</strong> ${test.duration || 'N/A'}</p>
                    <p><strong>Status:</strong> <span class="status-badge ${(test.status || 'UNKNOWN').toLowerCase()}">${test.status || 'UNKNOWN'}</span></p>
                    ${test.execution_time ? `<p><strong>Execution Time:</strong> ${test.execution_time}s</p>` : ''}
                    ${test.return_code !== undefined ? `<p><strong>Return Code:</strong> ${test.return_code}</p>` : ''}
                    
                    <div class="test-output-details">
                        <h4>Output:</h4>
                        <pre>${test.output || 'Aucune sortie disponible'}</pre>
                    </div>
                </div>
            `;
            
            modal.style.display = 'flex';
        } catch (error) {
            this.showToast('Erreur chargement détails: ' + error.message, 'error');
        }
    }

    formatBytes(bytes) {
        if (!bytes || bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        let icon = 'info-circle';
        if (type === 'success') icon = 'check-circle';
        if (type === 'error') icon = 'times-circle';
        if (type === 'warning') icon = 'exclamation-triangle';
        
        toast.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
}

// Démarrer l'application
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AutoK6Interface();
});