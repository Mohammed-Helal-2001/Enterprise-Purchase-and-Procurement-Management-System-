/**
 * Purchase Request System - JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initSidebar();
    initTooltips();
    initModals();
    initFormValidation();
    initDynamicForms();
    initCharts();
    initAnimations();
});

/**
 * Sidebar Toggle for Mobile
 */
function initSidebar() {
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
            if (mainContent) {
                mainContent.classList.toggle('sidebar-active');
            }
        });
    }
}

/**
 * Initialize Tooltips
 */
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            const tooltip = document.createElement('div');
            tooltip.className = 'custom-tooltip';
            tooltip.textContent = this.getAttribute('data-tooltip');
            tooltip.style.cssText = `
                position: absolute;
                background: #1e293b;
                color: #f8fafc;
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                font-size: 0.75rem;
                white-space: nowrap;
                z-index: 1000;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.2s;
            `;
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + rect.width / 2 + 'px';
            tooltip.style.top = rect.top - 40 + 'px';
            tooltip.style.transform = 'translateX(-50%)';
            
            document.body.appendChild(tooltip);
            
            setTimeout(() => {
                tooltip.style.opacity = '1';
            }, 10);
            
            this._tooltip = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.remove();
                this._tooltip = null;
            }
        });
    });
}

/**
 * Modal Management
 */
function initModals() {
    const modalTriggers = document.querySelectorAll('[data-modal]');
    
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            const modalId = this.getAttribute('data-modal');
            const modal = document.getElementById(modalId);
            
            if (modal) {
                openModal(modal);
            }
        });
    });
    
    // Close modal on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this);
            }
        });
    });
    
    // Close modal on close button
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = this.closest('.modal-overlay');
            if (modal) {
                closeModal(modal);
            }
        });
    });
    
    // Close on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.active').forEach(modal => {
                closeModal(modal);
            });
        }
    });
}

function openModal(modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal(modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

/**
 * Form Validation
 */
function initFormValidation() {
    const forms = document.querySelectorAll('.validate-form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const inputs = form.querySelectorAll('[required]');
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('error');
                    
                    // Add error message
                    const errorMsg = document.createElement('div');
                    errorMsg.className = 'error-message';
                    errorMsg.textContent = 'هذا الحقل مطلوب';
                    errorMsg.style.cssText = 'color: #f87171; font-size: 0.75rem; margin-top: 0.25rem;';
                    
                    // Remove previous error
                    const prevError = input.parentNode.querySelector('.error-message');
                    if (prevError) prevError.remove();
                    
                    input.parentNode.appendChild(errorMsg);
                } else {
                    input.classList.remove('error');
                    const prevError = input.parentNode.querySelector('.error-message');
                    if (prevError) prevError.remove();
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
        
        // Remove error on input
        form.querySelectorAll('[required]').forEach(input => {
            input.addEventListener('input', function() {
                this.classList.remove('error');
                const prevError = this.parentNode.querySelector('.error-message');
                if (prevError) prevError.remove();
            });
        });
    });
}

/**
 * Dynamic Forms (Add/Remove Items)
 */
function initDynamicForms() {
    // Add Item Button
    const addItemBtns = document.querySelectorAll('[data-add-item]');
    
    addItemBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const containerId = this.getAttribute('data-add-item');
            const container = document.getElementById(containerId);
            
            if (container) {
                addNewItem(container);
            }
        });
    });
    
    // Remove Item Button
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-item')) {
            const item = e.target.closest('.dynamic-item');
            const container = item.parentElement;
            
            if (container.children.length > 1) {
                item.remove();
                updateItemNumbers(container);
            } else {
                showAlert('لا يمكن حذف العنصر الأخير', 'warning');
            }
        }
    });
}

function addNewItem(container) {
    const template = container.querySelector('.dynamic-item-template');
    
    if (template) {
        const newItem = template.cloneNode(true);
        newItem.classList.remove('dynamic-item-template');
        newItem.classList.add('dynamic-item');
        newItem.style.display = 'block';
        
        // Reset form values
        newItem.querySelectorAll('input, select, textarea').forEach(input => {
            input.value = '';
            if (input.hasAttribute('name')) {
                const baseName = input.getAttribute('name').replace(/-\d+-/, '-__prefix__-');
                input.setAttribute('name', baseName.replace('__prefix__', container.children.length));
            }
        });
        
        container.appendChild(newItem);
        updateItemNumbers(container);
    }
}

function updateItemNumbers(container) {
    const items = container.querySelectorAll('.dynamic-item');
    items.forEach((item, index) => {
        const numberLabel = item.querySelector('.item-number');
        if (numberLabel) {
            numberLabel.textContent = index + 1;
        }
    });
}

/**
 * Charts Initialization
 */
function initCharts() {
    // Check if Chart.js is loaded
    if (typeof Chart !== 'undefined') {
        initDashboardCharts();
    }
}

function initDashboardCharts() {
    // Request Status Chart
    const statusChartEl = document.getElementById('requestStatusChart');
    if (statusChartEl) {
        const statusData = JSON.parse(statusChartEl.dataset.chart || '{}');
        
        new Chart(statusChartEl, {
            type: 'doughnut',
            data: {
                labels: ['مسودة', 'بانتظار الموافقة', 'موافق عليه', 'مرفوض', 'ممنوح'],
                datasets: [{
                    data: [
                        statusData.draft || 0,
                        statusData.pending || 0,
                        statusData.approved || 0,
                        statusData.rejected || 0,
                        statusData.awarded || 0
                    ],
                    backgroundColor: [
                        '#71717a',
                        '#60a5fa',
                        '#4ade80',
                        '#f87171',
                        '#c084fc'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#e2e8f0',
                            padding: 20,
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }
    
    // Monthly Requests Chart
    const monthlyChartEl = document.getElementById('monthlyRequestsChart');
    if (monthlyChartEl) {
        const monthlyData = JSON.parse(monthlyChartEl.dataset.chart || '{}');
        
        new Chart(monthlyChartEl, {
            type: 'bar',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Number of Requests',
                    data: monthlyData.values || [12, 19, 15, 25, 22, 30],
                    backgroundColor: 'rgba(59, 130, 246, 0.5)',
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(71, 85, 105, 0.3)' },
                        ticks: { color: '#94a3b8' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8' }
                    }
                }
            }
        });
    }
}

/**
 * Animations
 */
function initAnimations() {
    // Fade in elements on scroll
    const fadeElements = document.querySelectorAll('.fade-in-on-scroll');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    fadeElements.forEach(el => observer.observe(el));
    
    // Counter animation for stats
    const statValues = document.querySelectorAll('.stat-value[data-value]');
    
    statValues.forEach(stat => {
        const target = parseInt(stat.dataset.value);
        const duration = 2000;
        const step = target / (duration / 16);
        let current = 0;
        
        const counter = setInterval(() => {
            current += step;
            if (current >= target) {
                stat.textContent = target;
                clearInterval(counter);
            } else {
                stat.textContent = Math.floor(current);
            }
        }, 16);
    });
}

/**
 * Alert Messages
 */
function showAlert(message, type = 'info') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 3000);
}

/**
 * Best Supplier Suggestion
 */
async function suggestBestSupplier(prId) {
    const btn = document.querySelector(`[data-pr-id="${prId}"]`);
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Analyzing...';
    }
    
    try {
        const response = await fetch(`/purchasing/suggest-supplier/${prId}/`);
        const data = await response.json();
        
        if (data.success) {
            showAlert(`Best supplier: ${data.best_supplier.name} - Score: ${data.best_score}`, 'success');
            updateQuotationTable(data);
        } else {
            showAlert(data.message || 'An error occurred.', 'danger');
        }
    } catch (error) {
        showAlert('Server connection failed.', 'danger');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-lightbulb"></i> Suggest Supplier';
        }
    }
}

function updateQuotationTable(data) {
    const table = document.getElementById('quotation-table');
    if (table && data.analysis) {
        // Update scores in table
        data.analysis.forEach(item => {
            const row = table.querySelector(`[data-supplier="${item.supplier_id}"]`);
            if (row) {
                const scoreCell = row.querySelector('.score-cell');
                if (scoreCell) {
                    scoreCell.textContent = item.score.toFixed(2);
                }
                
                if (item.is_best) {
                    row.classList.add('best-supplier');
                }
            }
        });
    }
}

/**
 * RFQ Email Sending
 */
async function sendRFQ(prId) {
    const btn = document.querySelector(`[data-send-rfq="${prId}"]`);
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Sending...';
    }
    
    try {
        const response = await fetch(`/purchasing/send-rfq/${prId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        const data = await response.json();
        
        if (data.success) {
            showAlert('RFQ sent successfully.', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showAlert(data.message || 'An error occurred.', 'danger');
        }
    } catch (error) {
        showAlert('Server connection failed.', 'danger');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-paper-plane"></i> Send RFQ';
        }
    }
}

/**
 * PDF Export
 */
/**
 * Approval/Rejection
 */
async function processRequest(prId, action) {
    const reason = prompt('Enter rejection reason:');
    
    if (action === 'reject' && !reason) {
        showAlert('Rejection reason is required.', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/purchasing/${action}-request/${prId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ reason: reason || '' })
        });
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showAlert(data.message || 'An error occurred.', 'danger');
        }
    } catch (error) {
        showAlert('Server connection failed.', 'danger');
    }
}

/**
 * Utility Functions
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ar-SA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('ar-SA', {
        style: 'currency',
        currency: 'SAR'
    }).format(amount);
}

// Export functions to global scope
window.showAlert = showAlert;
window.suggestBestSupplier = suggestBestSupplier;
window.sendRFQ = sendRFQ;
window.processRequest = processRequest;
window.openModal = openModal;
window.closeModal = closeModal;