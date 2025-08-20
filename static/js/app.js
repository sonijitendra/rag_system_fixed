// Global app functionality

// Initialize tooltips and other Bootstrap components
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
});

// Utility functions
const utils = {
    // Format file size
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // Format date
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    },
    
    // Show loading state
    showLoading: function(element, text = 'Loading...') {
        element.disabled = true;
        element.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${text}`;
    },
    
    // Hide loading state
    hideLoading: function(element, originalText) {
        element.disabled = false;
        element.innerHTML = originalText;
    },
    
    // Show alert
    showAlert: function(message, type = 'info') {
        const alertContainer = document.getElementById('alertContainer') || document.body;
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${type} alert-dismissible fade show`;
        alertElement.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        alertContainer.insertBefore(alertElement, alertContainer.firstChild);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (alertElement && alertElement.parentNode) {
                alertElement.remove();
            }
        }, 5000);
    }
};

// API client
const api = {
    // Base API request
    request: async function(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },
    
    // Upload files
    upload: async function(files) {
        const formData = new FormData();
        for (let file of files) {
            formData.append('files', file);
        }
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        return response.json();
    },
    
    // Query documents
    query: async function(question, k = 5) {
        return this.request('/api/query', {
            method: 'POST',
            body: JSON.stringify({ question, k })
        });
    },
    
    // Get metadata
    getMetadata: async function(page = 1, perPage = 10) {
        return this.request(`/api/metadata?page=${page}&per_page=${perPage}`);
    },
    
    // Get stats
    getStats: async function() {
        return this.request('/api/stats');
    },
    
    // Get system status
    getSystemStatus: async function() {
        return this.request('/system/status');
    }
};

// File validation
const fileValidator = {
    allowedTypes: ['.pdf', '.txt', '.docx', '.doc'],
    maxSize: 100 * 1024 * 1024, // 100MB
    maxFiles: 20,
    
    validate: function(files) {
        const errors = [];
        
        if (files.length > this.maxFiles) {
            errors.push(`Maximum ${this.maxFiles} files allowed`);
            return errors;
        }
        
        for (let file of files) {
            const extension = '.' + file.name.split('.').pop().toLowerCase();
            
            if (!this.allowedTypes.includes(extension)) {
                errors.push(`File ${file.name} has unsupported format. Allowed: ${this.allowedTypes.join(', ')}`);
            }
            
            if (file.size > this.maxSize) {
                errors.push(`File ${file.name} is too large. Maximum size: ${utils.formatFileSize(this.maxSize)}`);
            }
        }
        
        return errors;
    }
};

// Progress tracking
const progressTracker = {
    show: function(container, text = 'Processing...') {
        container.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span>${text}</span>
                <span id="progressText">0%</span>
            </div>
            <div class="progress">
                <div class="progress-bar" role="progressbar" style="width: 0%" id="progressBar"></div>
            </div>
        `;
        container.style.display = 'block';
    },
    
    update: function(percentage) {
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        
        if (progressBar && progressText) {
            progressBar.style.width = percentage + '%';
            progressText.textContent = Math.round(percentage) + '%';
        }
    },
    
    complete: function() {
        this.update(100);
        setTimeout(() => {
            const container = document.getElementById('uploadProgress');
            if (container) {
                container.style.display = 'none';
            }
        }, 1000);
    }
};

// Export utilities for use in other scripts
window.utils = utils;
window.api = api;
window.fileValidator = fileValidator;
window.progressTracker = progressTracker;
