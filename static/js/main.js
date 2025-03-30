/**
 * RSEO Dashboard - Main JavaScript File
 */

document.addEventListener('DOMContentLoaded', function() {
    // تبديل الشريط الجانبي
    const sidebarToggle = document.getElementById('sidebarToggle');
    const body = document.body;
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            body.classList.toggle('sidebar-collapsed');
            
            // حفظ حالة الشريط الجانبي في localStorage
            if (body.classList.contains('sidebar-collapsed')) {
                localStorage.setItem('sidebar-collapsed', 'true');
            } else {
                localStorage.setItem('sidebar-collapsed', 'false');
            }
        });
    }
    
    // استعادة حالة الشريط الجانبي
    if (localStorage.getItem('sidebar-collapsed') === 'true') {
        body.classList.add('sidebar-collapsed');
    }
    
    // تفعيل وضع الليل
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = themeToggle ? themeToggle.querySelector('i') : null;
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            body.classList.toggle('dark-theme');
            
            // تحديث الأيقونة
            if (themeIcon) {
                if (body.classList.contains('dark-theme')) {
                    themeIcon.classList.remove('fa-moon');
                    themeIcon.classList.add('fa-sun');
                    localStorage.setItem('theme', 'dark');
                } else {
                    themeIcon.classList.remove('fa-sun');
                    themeIcon.classList.add('fa-moon');
                    localStorage.setItem('theme', 'light');
                }
            }
        });
    }
    
    // استعادة وضع الألوان
    if (localStorage.getItem('theme') === 'dark') {
        body.classList.add('dark-theme');
        if (themeIcon) {
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
        }
    }
    
    // تفعيل Tooltips في Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // إخفاء رسائل التنبيه تلقائياً بعد 5 ثوانٍ
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert && alert.parentNode) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });
    
    // تفعيل التبديل لعناصر الانهيار (Collapse)
    const collapseToggles = document.querySelectorAll('[data-bs-toggle="collapse"]');
    collapseToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function() {
            const icon = this.querySelector('i.fas');
            if (icon) {
                if (icon.classList.contains('fa-chevron-down')) {
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                } else {
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                }
            }
        });
    });
    
    // دعم الشاشات المحمولة - فتح/إغلاق الشريط الجانبي
    if (window.innerWidth < 768) {
        const menuLinks = document.querySelectorAll('.sidebar-menu a');
        menuLinks.forEach(function(link) {
            link.addEventListener('click', function() {
                if (window.innerWidth < 768) {
                    body.classList.remove('sidebar-open');
                }
            });
        });
        
        // زر فتح الشريط الجانبي على الشاشات الصغيرة
        document.addEventListener('click', function(event) {
            if (event.target.closest('#sidebarToggle')) {
                body.classList.toggle('sidebar-open');
                event.preventDefault();
            } else if (!event.target.closest('.sidebar') && body.classList.contains('sidebar-open')) {
                body.classList.remove('sidebar-open');
            }
        });
    }
    
    // تفعيل النصائح السياقية في الأزرار
    const buttons = document.querySelectorAll('[data-toggle="tooltip"]');
    buttons.forEach(function(button) {
        const title = button.getAttribute('title');
        if (title) {
            button.setAttribute('data-bs-toggle', 'tooltip');
            button.setAttribute('data-bs-placement', button.getAttribute('data-placement') || 'top');
            button.setAttribute('data-bs-title', title);
            button.removeAttribute('title');
            button.removeAttribute('data-toggle');
            button.removeAttribute('data-placement');
            
            new bootstrap.Tooltip(button);
        }
    });
    
    // تحقق من تبديل خيارات WordPress
    const wpApiCheckbox = document.getElementById('wp_api');
    const wpCredentials = document.getElementById('wpCredentials');
    
    if (wpApiCheckbox && wpCredentials) {
        wpApiCheckbox.addEventListener('change', function() {
            wpCredentials.style.display = this.checked ? 'flex' : 'none';
        });
        
        // التحقق من الحالة الأولية
        wpCredentials.style.display = wpApiCheckbox.checked ? 'flex' : 'none';
    }
});
