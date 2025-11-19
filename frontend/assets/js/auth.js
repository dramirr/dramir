let currentUser = null;

async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');
    
    try {
        errorDiv.style.display = 'none';
        
        const result = await api.login(username, password);
        
        localStorage.setItem('access_token', result.access_token);
        localStorage.setItem('user', JSON.stringify(result.user));
        
        currentUser = result.user;
        
        showMainApp();
        
    } catch (error) {
        errorDiv.textContent = error.message;
        errorDiv.style.display = 'block';
    }
}

function showMainApp() {
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('mainApp').style.display = 'block';
    
    const userInfo = document.getElementById('userInfo');
    const userName = document.getElementById('userName');
    
    if (currentUser) {
        userName.textContent = currentUser.username;
        userInfo.style.display = 'flex';
    }
    
    updateStatus(true);
    
    loadPositions();
    loadDashboard();
}

function logout() {
    api.logout().catch(() => {});
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    
    currentUser = null;
    
    document.getElementById('mainApp').style.display = 'none';
    document.getElementById('loginSection').style.display = 'flex';
    
    updateStatus(false);
    
    document.getElementById('loginForm').reset();
}

function updateStatus(connected) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    
    if (connected) {
        statusDot.classList.add('active');
        statusText.textContent = 'Connected';
    } else {
        statusDot.classList.remove('active');
        statusText.textContent = 'Disconnected';
    }
}

function checkAuth() {
    const token = localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user');
    
    if (token && userStr) {
        try {
            currentUser = JSON.parse(userStr);
            
            api.getCurrentUser()
                .then(() => showMainApp())
                .catch(() => logout());
        } catch {
            logout();
        }
    }
}

window.addEventListener('load', checkAuth);