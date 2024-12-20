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
            console.log('Socket connected');
            this.reconnectAttempts = 0;
            showToast('Connected to server', 'success');
            
            // Rejoin game room if we have a pin
            if (this.gamePin) {
                console.log('Rejoining game room:', this.gamePin);
                this.socket.emit('player_join', { 
                    pin: this.gamePin,
                    rejoin: true 
                });
            }
        });

        // Handle game state synchronization
        this.socket.on('game_state_sync', (data) => {
            console.log('Received game state sync:', data);
            if (data.currentQuestion) {
                this.handleQuestionData(data.currentQuestion);
            }
        });

        // Handle question preparation
        this.socket.on('question_preparing', (data) => {
            console.log('Received question_preparing event:', data);
            if (data.question) {
                this.handleQuestionData(data.question);
            }
        });

        // Add listener for question_started event
        this.socket.on('question_started', (data) => {
            console.log('Received question_started event:', data);
            if (!data || !data.content) {
                console.error('Invalid question data received:', data);
                return;
            }
            this.handleQuestionData(data);
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('Socket disconnected. Reason:', reason);
            showToast('Lost connection to server', 'warning');
            this.stopHeartbeat();
            this.attemptReconnect();
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('Socket connection error:', error);
            this.stopHeartbeat();
            this.attemptReconnect();
        });

        this.socket.on('pong', () => {
            console.log('Received pong from server');
            this.lastHeartbeat = Date.now();
        });

        // Handle forced reconnection request from server
        this.socket.on('force_reconnect', () => {
            console.log('Received force_reconnect request');
            this.socket.disconnect();
            setTimeout(() => {
                console.log('Attempting forced reconnection');
                this.socket.connect();
            }, 1000);
        });

        // Add error event handler
        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            showToast('Connection error occurred', 'danger');
        });

        // Handle answer results
        this.socket.on('answer_result', (data) => {
            console.log('Received answer result:', data);
            
            // Create or get result container
            let resultContainer = document.getElementById('resultContainer');
            if (!resultContainer) {
                resultContainer = document.createElement('div');
                resultContainer.id = 'resultContainer';
                document.body.appendChild(resultContainer);
            }
            
            // Display result
            resultContainer.innerHTML = `
                <div class="alert ${data.is_correct ? 'alert-success' : 'alert-danger'} mt-3">
                    <h5>${data.is_correct ? 'Correct!' : 'Incorrect'}</h5>
                    <p>Points earned: ${data.points_awarded}</p>
                    <p>Current score: ${data.new_score}</p>
                    ${data.new_streak > 1 ? `<p>Streak: ${data.new_streak}</p>` : ''}
                    ${!data.is_correct ? `<p>Correct answer: ${data.correct_answer}</p>` : ''}
                </div>
            `;
        });

        // Handle answer submission errors
        this.socket.on('answer_error', (data) => {
            console.error('Answer submission error:', data);
            showToast(data.message || 'Error submitting answer', 'danger');
            
            // Re-enable answer buttons if there was an error
            document.querySelectorAll('.answer-btn').forEach(btn => {
                btn.disabled = false;
            });
        });

        // Handle game state updates
        this.socket.on('game_state_update', (data) => {
            console.log('Received game state update:', data);
            if (data.status === 'completed') {
                showToast('Game completed!', 'success');
                // Clear question display
                const questionContainer = document.getElementById('questionContainer');
                if (questionContainer) {
                    questionContainer.innerHTML = `
                        <div class="alert alert-info">
                            <h4>Game Over!</h4>
                            <p>Final Score: ${data.final_score}</p>
                            <p>Thanks for playing!</p>
                        </div>
                    `;
                }
            }
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

    handleQuestionData(questionData) {
        console.log('Handling question data:', questionData);
        // Reset question start time for accurate response time calculation
        window.questionStartTime = Date.now();
        
        // Find or create question container
        let questionContainer = document.getElementById('questionContainer');
        if (!questionContainer) {
            console.log('Creating question container');
            questionContainer = document.createElement('div');
            questionContainer.id = 'questionContainer';
            document.body.appendChild(questionContainer);
        }
        
        // Update question display
        questionContainer.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Question ${questionData.id}</h5>
                    <p class="card-text">${questionData.content}</p>
                    <div class="answers-container">
                        ${questionData.answers.map((answer, index) => `
                            <button class="btn btn-primary mb-2 w-100 answer-btn" 
                                    data-answer="${answer}"
                                    onclick="submitAnswer('${answer}', ${questionData.id})">
                                ${answer}
                            </button>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        // Start countdown timer if provided
        if (questionData.time_limit) {
            const timerDisplay = document.createElement('div');
            timerDisplay.id = 'timerDisplay';
            timerDisplay.className = 'alert alert-info mt-3';
            questionContainer.insertBefore(timerDisplay, questionContainer.firstChild);
            
            const timer = new CountdownTimer(
                questionData.time_limit,
                (timeLeft) => {
                    timerDisplay.textContent = `Time remaining: ${timeLeft} seconds`;
                },
                () => {
                    timerDisplay.textContent = 'Time\'s up!';
                    document.querySelectorAll('.answer-btn').forEach(btn => {
                        btn.disabled = true;
                    });
                }
            );
            timer.start();
        }
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

// Answer submission handler
function submitAnswer(answer, questionId) {
    const startTime = window.questionStartTime || Date.now();
    const responseTime = (Date.now() - startTime) / 1000; // Convert to seconds
    
    if (!window.socket) {
        console.error('Socket connection not available');
        showToast('Unable to submit answer - connection error', 'danger');
        return;
    }
    
    // Disable all answer buttons to prevent multiple submissions
    document.querySelectorAll('.answer-btn').forEach(btn => {
        btn.disabled = true;
    });
    
    // Send answer to server
    window.socket.emit('submit_answer', {
        answer: answer,
        question_id: questionId,
        response_time: responseTime
    });
    
    console.log('Answer submitted:', {
        answer: answer,
        question_id: questionId,
        response_time: responseTime
    });
}

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', () => {
    // Store question start time when question is displayed
    window.questionStartTime = Date.now();
    
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
