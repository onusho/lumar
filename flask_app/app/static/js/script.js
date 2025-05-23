// static/js/script.js
document.addEventListener('DOMContentLoaded', function () {
    // Tab persistence for App Dashboard
    const appDashboardTabs = document.querySelectorAll('#appTabs .nav-link');
    appDashboardTabs.forEach(tab => {
        tab.addEventListener('click', function (event) {
            localStorage.setItem('activeAppTab', event.target.getAttribute('href'));
            // If you want to inform the server (optional, for more complex state)
            // fetch(`/app/set_active_tab/${event.target.getAttribute('href').substring(1)}`, { method: 'POST' });
        });
    });

    const activeAppTab = localStorage.getItem('activeAppTab');
    if (activeAppTab) {
        const tabToActivate = document.querySelector(`#appTabs .nav-link[href="${activeAppTab}"]`);
        if (tabToActivate) {
            new bootstrap.Tab(tabToActivate).show();
        }
    } else {
        // Activate the first tab by default if no tab is stored
        const firstTab = document.querySelector('#appTabs .nav-link');
        if (firstTab) {
             new bootstrap.Tab(firstTab).show();
        }
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            new bootstrap.Alert(alert).close();
        }, 5000);
    });

    // Custom file input label update
    const fileInputs = document.querySelectorAll('input[type="file"].custom-file-input- vervangen'); // Using a placeholder class
    fileInputs.forEach(input => {
        input.addEventListener('change', event => {
            const label = input.nextElementSibling;
            const fileName = event.target.files.length > 0 ? event.target.files[0].name : label.getAttribute('data-original-title');
            label.textContent = fileName;
        });
    });

    // Scroll chat to bottom
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Handle sidebar navigation active state based on current URL (simple version)
    const sidebarLinks = document.querySelectorAll('.sidebar .nav-link');
    const currentPath = window.location.pathname;
    sidebarLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

});