// 导航菜单处理
document.addEventListener('DOMContentLoaded', () => {
    // 移动端菜单切换
    const menuToggle = document.querySelector('.menu-toggle');
    const sideNav = document.querySelector('.side-nav');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            sideNav.classList.toggle('active');
        });
    }

    // 下拉菜单处理
    const dropdowns = document.querySelectorAll('.dropdown');
    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        if (toggle && menu) {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                menu.classList.toggle('show');
            });

            // 点击外部关闭下拉菜单
            document.addEventListener('click', (e) => {
                if (!dropdown.contains(e.target)) {
                    menu.classList.remove('show');
                }
            });
        }
    });
});

// 面包屑导航生成
function updateBreadcrumb(path) {
    const breadcrumb = document.querySelector('.breadcrumb');
    if (!breadcrumb) return;

    const parts = path.split('/').filter(Boolean);
    const crumbs = parts.map((part, index) => {
        const url = '/' + parts.slice(0, index + 1).join('/');
        return `<a href="${url}">${part}</a>`;
    });

    breadcrumb.innerHTML = crumbs.join(' / ');
}

// 页面加载进度条
const progressBar = {
    show() {
        const bar = document.createElement('div');
        bar.className = 'progress-bar';
        document.body.appendChild(bar);
        
        setTimeout(() => {
            bar.style.width = '90%';
        }, 50);
    },
    
    hide() {
        const bar = document.querySelector('.progress-bar');
        if (bar) {
            bar.style.width = '100%';
            setTimeout(() => {
                bar.remove();
            }, 200);
        }
    }
};

// 页面切换处理
window.addEventListener('beforeunload', () => {
    progressBar.show();
});

window.addEventListener('load', () => {
    progressBar.hide();
    updateBreadcrumb(window.location.pathname);
}); 