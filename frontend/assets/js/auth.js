// ===================================
// FIXED auth.js - Authentication Logic
// ===================================

let currentUser = null;

/**
 * Handle login form submission
 */
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');
    const loginBtn = event.target.querySelector('button[type="submit"]');
    
    try {
        // Hide previous errors
        errorDiv.style.display = 'none';
        
        // Disable button during login
        loginBtn.disabled = true;
        loginBtn.textContent = 'Logging in...';
        
        // Call login API
        const result = await api.login(username, password);
        
        if (!result.access_token) {
            throw new Error('No access token received');
        }
        
        // Store token and user info
        localStorage.setItem('access_token', result.access_token);
        localStorage.setItem('user', JSON.stringify(result.user));
        
        currentUser = result.user;
        
        // Show main app
        showMainApp();
        
    } catch (error) {
        console.error('Login error:', error);
        errorDiv.textContent = error.message || 'Login failed';
        errorDiv.style.display = 'block';
        
        // Re-enable button
        loginBtn.disabled = false;
        loginBtn.textContent = 'Login';
    }
}

/**
 * Show main application (hide login)
 */
function showMainApp() {
    console.log('Showing main app...');
    
    // Hide login section
    const loginSection = document.getElementById('loginSection');
    if (loginSection) {
        loginSection.style.display = 'none';
    }
    
    // Show main app
    const mainApp = document.getElementById('mainApp');
    if (mainApp) {
        mainApp.style.display = 'block';
    }
    
    // Update user info in header
    const userInfo = document.getElementById('userInfo');
    const userName = document.getElementById('userName');
    
    if (currentUser && userName) {
        userName.textContent = currentUser.username;
        if (userInfo) {
            userInfo.style.display = 'flex';
        }
    }
    
    // Update API status
    updateStatus(true);
    
    // Load initial data
    if (typeof loadPositions === 'function') loadPositions();
    if (typeof loadDashboard === 'function') loadDashboard();
}

/**
 * Show login section (hide main app)
 */
function showLogin() {
    console.log('Showing login...');
    
    // Show login section
    const loginSection = document.getElementById('loginSection');
    if (loginSection) {
        loginSection.style.display = 'flex';
    }
    
    // Hide main app
    const mainApp = document.getElementById('mainApp');
    if (mainApp) {
        mainApp.style.display = 'none';
    }
    
    // Hide user info
    const userInfo = document.getElementById('userInfo');
    if (userInfo) {
        userInfo.style.display = 'none';
    }
    
    // Update status
    updateStatus(false);
}

/**
 * Logout user
 */
async function logout() {
    console.log('Logging out...');
    
    try {
        // Call logout API (optional, may fail if token expired)
        await api.logout().catch(err => {
            console.warn('Logout API call failed:', err);
        });
    } catch (error) {
        console.warn('Logout error:', error);
    }
    
    // Clear local storage
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    
    // Clear current user
    currentUser = null;
    
    // Show login screen
    showLogin();
    
    // Reset login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.reset();
    }
    
    // Clear any error messages
    const errorDiv = document.getElementById('loginError');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

/**
 * Update API connection status indicator
 */
function updateStatus(connected) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    
    if (statusDot) {
        if (connected) {
            statusDot.classList.add('active');
        } else {
            statusDot.classList.remove('active');
        }
    }
    
    if (statusText) {
        statusText.textContent = connected ? 'Connected' : 'Disconnected';
    }
}

/**
 * Check authentication status on page load
 * FIXED: No redirect to login.html, just show/hide sections
 */
async function checkAuth() {
    console.log('Checking authentication...');
    
    const token = localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user');
    
    if (!token || !userStr) {
        console.log('No token found, showing login');
        showLogin();
        return false;
    }
    
    try {
        // Parse stored user
        currentUser = JSON.parse(userStr);
        
        // Verify token is still valid
        const user = await api.getCurrentUser();
        
        if (!user) {
            throw new Error('Invalid token');
        }
        
        // Update current user with fresh data
        currentUser = user;
        localStorage.setItem('user', JSON.stringify(user));
        
        console.log('Authentication valid, showing main app');
        showMainApp();
        return true;
        
    } catch (error) {
        console.error('Auth check failed:', error);
        
        // Clear invalid token
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        currentUser = null;
        
        // Show login
        showLogin();
        return false;
    }
}

/**
 * Initialize authentication on page load
 */
window.addEventListener('load', async () => {
    console.log('Page loaded, initializing auth...');
    await checkAuth();
});

// Export functions for global use
window.handleLogin = handleLogin;
window.logout = logout;
window.showMainApp = showMainApp;
window.showLogin = showLogin;