const SIDEBAR_ITEMS = [
    { key: 'home', label: 'Home', icon: '🏠', href: '/' },
    { key: 'analytics', label: 'Analytics', icon: '📊', href: 'analytics' },
    { key: 'logs', label: 'Logs', icon: '📋', href: 'logs' },
    { key: 'alerts', label: 'Alerts', icon: '🔔', href: 'alerts' }
];

async function injectSidebar() {
    const mount = document.getElementById('appsidebar');
    if (!mount) return;
    
    try {
        const response = await fetch('../components/sidebar.html');
        if (!response.ok) throw new Error('Failed to fetch sidebar template');
        
        const template = await response.text();
        mount.innerHTML = template;
        
        const nav = mount.querySelector('[data-sidebar-nav]');
        if (nav) {
            const currentPage = document.body.dataset.page || 'home';
            
            nav.innerHTML = SIDEBAR_ITEMS.map(item => `
                <a class="sidebar-link ${item.key === currentPage ? 'active' : ''}" href="${item.href}">
                    <span>${item.icon}</span>
                    <span>${item.label}</span>
                </a>
            `).join('');
        }
    } catch (error) {
        mount.innerHTML = '<aside class="sidebar"><p>Sidebar could not be loaded.</p></aside>';
        console.error('Sidebar load failed:', error);
    }
}

if(document.readyState === "loading") {
    document.addEventListener('DOMContentLoaded', injectSidebar);
} else {
    injectSidebar()
}


