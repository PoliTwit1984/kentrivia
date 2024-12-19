// Toast Notification System
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                    data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

// Form Validation Helper
function validateForm(formId, customValidations = {}) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    let isValid = form.checkValidity();
    if (!isValid) {
        form.classList.add('was-validated');
        return false;
    }
    
    // Run custom validations
    for (const [fieldName, validation] of Object.entries(customValidations)) {
        const field = form.elements[fieldName];
        if (!field) continue;
        
        const result = validation(field.value);
        if (result !== true) {
            showToast(result, 'danger');
            return false;
        }
    }
    
    return true;
}

// Copy to Clipboard Helper
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(err => {
        showToast('Failed to copy text', 'danger');
    });
}

// Countdown Timer
class CountdownTimer {
    constructor(duration, onTick, onComplete) {
        this.duration = duration;
        this.onTick = onTick;
        this.onComplete = onComplete;
        this.timeLeft = duration;
        this.timerId = null;
    }
    
    start() {
        this.timeLeft = this.duration;
        this.tick();
        this.timerId = setInterval(() => this.tick(), 1000);
    }
    
    stop() {
        if (this.timerId) {
            clearInterval(this.timerId);
            this.timerId = null;
        }
    }
    
    tick() {
        if (this.timeLeft <= 0) {
            this.stop();
            if (this.onComplete) this.onComplete();
            return;
        }
        
        if (this.onTick) this.onTick(this.timeLeft);
        this.timeLeft--;
    }
}

// WebSocket Connection Manager
class SocketManager {
    constructor(socket, gamePin = null) {
        this.socket = socket;
        this.gamePin = gamePin;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.heartbeatInterval = null;
        this.lastHeartbeat = Date.now();
        this.setupListeners();
        this.startHeartbeat();
    }
    
    setupListeners() {
        this.socket.on('connect', () => {
            this.reconnectAttempts = 0;
            showToast('Connected to server', 'success');
            
            // Rejoin game room if we have a pin
            if (this.gamePin) {
                this.socket.emit('player_join', { 
                    pin: this.gamePin,
                    rejoin: true 
                });
            }
        });
        
        this.socket.on('disconnect', () => {
            showToast('Lost connection to server', 'warning');
            this.stopHeartbeat();
            this.attemptReconnect();
        });
        
        this.socket.on('connect_error', () => {
            this.stopHeartbeat();
            this.attemptReconnect();
        });

        this.socket.on('pong', () => {
            this.lastHeartbeat = Date.now();
        });

        // Handle forced reconnection request from server
        this.socket.on('force_reconnect', () => {
            this.socket.disconnect();
            setTimeout(() => this.socket.connect(), 1000);
        });
    }
    
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.socket.connected) {
                this.socket.emit('ping');
                
                // Check if we missed too many heartbeats
                if (Date.now() - this.lastHeartbeat > 10000) {
                    console.log('Missed heartbeats, reconnecting...');
                    this.socket.disconnect();
                    this.socket.connect();
                }
            }
        }, 5000);
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            showToast('Unable to connect to server. Please refresh the page.', 'danger');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 10000);
        
        setTimeout(() => {
            if (!this.socket.connected) {
                this.socket.connect();
            }
        }, delay);
    }

    setGamePin(pin) {
        this.gamePin = pin;
    }
}

// Form Data Helper
function getFormData(form) {
    const formData = new FormData(form);
    const data = {};
    
    for (const [key, value] of formData.entries()) {
        if (data[key] !== undefined) {
            if (!Array.isArray(data[key])) {
                data[key] = [data[key]];
            }
            data[key].push(value);
        } else {
            data[key] = value;
        }
    }
    
    return data;
}

// API Request Helper
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }
        
        return data;
    } catch (error) {
        showToast(error.message, 'danger');
        throw error;
    }
}

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize all popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});
