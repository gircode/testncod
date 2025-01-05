// Dashboard JavaScript

// Auto-refresh functionality
function setupAutoRefresh(interval) {
    setInterval(() => {
        location.reload();
    }, interval * 1000);
}

// Initialize tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize progress bars
function initProgressBars() {
    const progressBars = document.querySelectorAll('.progress');
    progressBars.forEach(progress => {
        const value = progress.getAttribute('data-progress');
        if (value !== null) {
            progress.setAttribute('aria-valuenow', value);
            progress.setAttribute('aria-valuemin', '0');
            progress.setAttribute('aria-valuemax', '100');
        }
    });
}

// Update progress bar
function updateProgressBar(element, progress) {
    const progressBar = element.querySelector('.progress-bar');
    if (progressBar) {
        // 移除所有宽度类
        progressBar.classList.forEach(className => {
            if (className.startsWith('progress-width-')) {
                progressBar.classList.remove(className);
            }
        });
        // 四舍五入到最接近的10
        const roundedProgress = Math.round(progress / 10) * 10;
        progressBar.classList.add(`progress-width-${roundedProgress}`);
    }
}

// Update metrics
function updateMetrics() {
    fetch('/api/metrics/performance')
        .then(response => response.json())
        .then(data => {
            // Update metric values
            Object.entries(data.metrics).forEach(([key, value]) => {
                const element = document.getElementById(`metric-${key}`);
                if (element) {
                    element.textContent = value;
                }
            });
            
            // Calculate and update progress
            const completed = parseInt(document.getElementById('metric-completed_tasks').textContent);
            const total = parseInt(document.getElementById('metric-total_tasks').textContent);
            if (!isNaN(completed) && !isNaN(total) && total > 0) {
                const progress = Math.round((completed / total) * 100);
                updateProgressBar(progress);
            }
        })
        .catch(error => console.error('Error fetching metrics:', error));
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initTooltips();
    
    // Initialize progress bars
    initProgressBars();
    
    // Setup auto-refresh (30 seconds)
    setupAutoRefresh(30);
    
    // Initial metrics update
    updateMetrics();
    
    // Setup periodic metrics update (5 seconds)
    setInterval(updateMetrics, 5000);
});

// 更新时间显示
function updateLastUpdateTime() {
    const now = new Date();
    document.getElementById('lastUpdate').textContent = now.toLocaleString();
}

// 初始化图表
function initCharts(performanceData) {
    // CPU使用率图表
    const cpuCtx = document.getElementById('cpuChart').getContext('2d');
    new Chart(cpuCtx, {
        type: 'line',
        data: {
            labels: performanceData.cpu_usage.map(d => new Date(d.timestamp).toLocaleTimeString()),
            datasets: [{
                label: 'CPU使用率',
                data: performanceData.cpu_usage.map(d => d.value),
                borderColor: '#4CAF50',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    // 内存使用率图表
    const memoryCtx = document.getElementById('memoryChart').getContext('2d');
    new Chart(memoryCtx, {
        type: 'line',
        data: {
            labels: performanceData.memory_usage.map(d => new Date(d.timestamp).toLocaleTimeString()),
            datasets: [{
                label: '内存使用率',
                data: performanceData.memory_usage.map(d => d.value),
                borderColor: '#2196F3',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

// 刷新数据
async function refreshData() {
    try {
        const [clusters, tasks, performance] = await Promise.all([
            fetch('/api/clusters').then(r => r.json()),
            fetch('/api/tasks').then(r => r.json()),
            fetch('/api/performance').then(r => r.json())
        ]);

        // 更新页面数据
        updateClusters(clusters);
        updateTasks(tasks);
        updateCharts(performance);
        updateLastUpdateTime();
    } catch (error) {
        console.error('Failed to refresh data:', error);
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    updateLastUpdateTime();
    initCharts(window.performance || {
        cpu_usage: [],
        memory_usage: []
    });
    
    // 每30秒自动刷新一次
    setInterval(refreshData, 30000);
});

// 更新任务列表
function updateTasks(tasks) {
    const taskList = document.querySelector('.task-list');
    if (taskList) {
        tasks.forEach(task => {
            const taskElement = taskList.querySelector(`[data-task-id="${task.id}"]`);
            if (taskElement) {
                updateProgressBar(taskElement, task.progress);
            }
        });
    }
}

// 任务管理函数
function createNewTask() {
    const taskType = prompt("请选择任务类型 (sync/backup/check):");
    if (!taskType) return;
    
    fetch('/api/tasks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            type: taskType
        })
    })
    .then(response => response.json())
    .then(data => {
        refreshData();
    })
    .catch(error => console.error('Error creating task:', error));
}

function cancelTask(taskId) {
    if (!confirm('确定要取消此任务吗？')) return;
    
    fetch(`/api/tasks/${taskId}/cancel`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        refreshData();
    })
    .catch(error => console.error('Error cancelling task:', error));
}

function viewTaskDetails(taskId) {
    fetch(`/api/tasks/${taskId}`)
    .then(response => response.json())
    .then(task => {
        // 显示任务详情对话框
        const details = `
            任务ID: ${task.id}
            名称: ${task.name}
            类型: ${task.type}
            状态: ${task.status}
            进度: ${task.progress}%
            创建时间: ${new Date(task.created_at).toLocaleString()}
            ${task.completed_at ? '完成时间: ' + new Date(task.completed_at).toLocaleString() : ''}
            ${task.error ? '错误信息: ' + task.error : ''}
        `;
        alert(details); // 这里可以改用更好的对话框UI
    })
    .catch(error => console.error('Error fetching task details:', error));
}

function filterTasks() {
    const status = document.getElementById('taskFilter').value;
    const tasks = document.querySelectorAll('.task-item');
    
    tasks.forEach(task => {
        if (status === 'all' || task.classList.contains(status)) {
            task.style.display = '';
        } else {
            task.style.display = 'none';
        }
    });
} 