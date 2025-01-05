class SettingsManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupTabs();
        this.setupForms();
    }

    setupTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabPanels = document.querySelectorAll('.tab-panel');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabId = button.dataset.tab;
                
                // 更新按钮状态
                tabButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');

                // 更新面板显示
                tabPanels.forEach(panel => {
                    panel.classList.remove('active');
                    if (panel.id === `${tabId}-panel`) {
                        panel.classList.add('active');
                    }
                });

                // 更新URL参数
                const url = new URL(window.location);
                url.searchParams.set('tab', tabId);
                window.history.pushState({}, '', url);
            });
        });

        // 从URL参数恢复选中的标签
        const params = new URLSearchParams(window.location.search);
        const activeTab = params.get('tab');
        if (activeTab) {
            const button = document.querySelector(`.tab-button[data-tab="${activeTab}"]`);
            if (button) {
                button.click();
            }
        }
    }

    setupForms() {
        // 基本设置表单
        document.getElementById('basicSettingsForm')?.addEventListener('submit', e => this.saveSettings(e, 'basic'));

        // 安全设置表单
        document.getElementById('securitySettingsForm')?.addEventListener('submit', e => this.saveSettings(e, 'security'));

        // 备份设置表单
        document.getElementById('backupSettingsForm')?.addEventListener('submit', e => this.saveSettings(e, 'backup'));

        // 通知设置表单
        document.getElementById('notificationSettingsForm')?.addEventListener('submit', e => this.saveSettings(e, 'notification'));

        // 高级设置表单
        document.getElementById('advancedSettingsForm')?.addEventListener('submit', e => this.saveSettings(e, 'advanced'));
    }

    async saveSettings(e, type) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch(`/api/settings/${type}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                showSuccess('设置保存成功');
            } else {
                const error = await response.json();
                showError(error.message || '保存设置失败');
            }
        } catch (error) {
            console.error('Failed to save settings:', error);
            showError('保存设置失败');
        }
    }
}

// 初始化设置管理器
const settingsManager = new SettingsManager();

// 辅助函数
function showError(message) {
    // 实现错误提示逻辑
}

function showSuccess(message) {
    // 实现成功提示逻辑
} 