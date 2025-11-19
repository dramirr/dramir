// ===================================
// FIXED app.js for TalentRadar
// ===================================

let uploadMode = 'single';
let currentPositions = [];
let currentResumes = [];
let currentCandidates = [];
let activePollingIntervals = new Map();

// ===================================
// 1. TAB MANAGEMENT
// ===================================
function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(tabName).classList.add('active');
    
    if (tabName === 'dashboard') loadDashboard();
    if (tabName === 'results') loadResults();
    if (tabName === 'candidates') loadCandidates();
    if (tabName === 'positions') loadPositionsList();
}

// ===================================
// 2. UPLOAD MODE SWITCH
// ===================================
function setUploadMode(mode) {
    uploadMode = mode;
    
    document.querySelectorAll('.btn-group .btn-secondary').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    if (mode === 'single') {
        document.getElementById('singleUpload').style.display = 'block';
        document.getElementById('bulkUpload').style.display = 'none';
    } else {
        document.getElementById('singleUpload').style.display = 'none';
        document.getElementById('bulkUpload').style.display = 'block';
    }
}

// ===================================
// 3. LOAD POSITIONS
// ===================================
async function loadPositions() {
    try {
        const data = await api.getPositions();
        currentPositions = data.positions;
        
        const selects = document.querySelectorAll('#positionSelect, #filterPosition');
        selects.forEach(select => {
            select.innerHTML = '<option value="">Select position...</option>';
            data.positions.forEach(pos => {
                const option = document.createElement('option');
                option.value = pos.id;
                option.textContent = pos.title;
                select.appendChild(option);
            });
        });
    } catch (error) {
        console.error('Failed to load positions:', error);
    }
}

// ===================================
// 4. RESUME STATUS POLLING (FIXED)
// ===================================

/**
 * Poll resume status until processing is complete
 */
async function pollResumeStatus(resumeId, onComplete) {
    // Prevent duplicate polling
    if (activePollingIntervals.has(resumeId)) {
        console.log(`Already polling resume ${resumeId}`);
        return;
    }

    const maxAttempts = 60; // 5 minutes max (5s intervals)
    let attempts = 0;
    
    console.log(`Starting to poll status for resume ${resumeId}`);
    
    const pollInterval = setInterval(async () => {
        try {
            attempts++;
            
            // Get resume status
            const data = await api.getResumeStatus(resumeId);
            console.log(`Resume ${resumeId} status (attempt ${attempts}):`, data.processing_status);
            
            // Update UI if status element exists
            updateStatusDisplay(resumeId, data.processing_status);
            
            // Check if processing is complete
            if (data.processing_status === 'completed' || data.processing_status === 'failed') {
                clearInterval(pollInterval);
                activePollingIntervals.delete(resumeId);
                
                console.log(`Resume ${resumeId} processing finished with status: ${data.processing_status}`);
                
                // Call completion handler
                if (onComplete) {
                    onComplete(data, data.processing_status);
                }
                
                // Refresh lists
                await loadResults();
                await loadDashboard();
                
                // Show notification
                if (data.processing_status === 'completed') {
                    showNotification('✅ Resume processing completed!', 'success');
                    
                    // If we have score data, display it
                    if (data.score) {
                        displayCompletedResult(resumeId, data);
                    }
                } else {
                    showNotification('❌ Resume processing failed', 'error');
                }
            }
            
            // Stop polling after max attempts
            if (attempts >= maxAttempts) {
                clearInterval(pollInterval);
                activePollingIntervals.delete(resumeId);
                showNotification('⏱️ Processing is taking longer than expected', 'warning');
            }
            
        } catch (error) {
            console.error('Polling error:', error);
            
            // Stop polling on auth errors
            if (error.message && (error.message.includes('401') || error.message.includes('Unauthorized'))) {
                clearInterval(pollInterval);
                activePollingIntervals.delete(resumeId);
                showNotification('⚠️ Authentication error. Please login again.', 'error');
                return;
            }
            
            // Stop after max attempts
            if (attempts >= maxAttempts) {
                clearInterval(pollInterval);
                activePollingIntervals.delete(resumeId);
            }
        }
    }, 5000); // Poll every 5 seconds
    
    // Store interval ID
    activePollingIntervals.set(resumeId, pollInterval);
}

/**
 * Update status display in UI
 */
function updateStatusDisplay(resumeId, status) {
    const statusElement = document.getElementById(`status-${resumeId}`);
    if (!statusElement) return;
    
    const statusMessages = {
        'pending': 'Pending...',
        'processing': '⏳ Processing... This may take a moment.',
        'completed': '✅ Completed',
        'failed': '❌ Failed'
    };
    
    statusElement.textContent = statusMessages[status] || status;
    
    // Update color based on status
    const colors = {
        'pending': 'var(--warning, #ffc107)',
        'processing': 'var(--info, #17a2b8)',
        'completed': 'var(--success, #28a745)',
        'failed': 'var(--danger, #dc3545)'
    };
    
    statusElement.style.color = colors[status] || 'inherit';
}

/**
 * Display completed result
 */
function displayCompletedResult(resumeId, data) {
    const resultDiv = document.getElementById('uploadResult');
    if (!resultDiv) return;
    
    if (data.score) {
        resultDiv.innerHTML = `
            <div class="result-card">
                <h4>Processing Complete</h4>
                <div class="score-display">
                    <div class="score-circle ${data.score.status}">
                        ${data.score.percentage.toFixed(1)}%
                    </div>
                    <div class="score-details">
                        <p><strong>Score:</strong> ${data.score.total_score.toFixed(1)} / ${data.score.max_possible_score.toFixed(1)}</p>
                        <p><strong>Status:</strong> <span class="${data.score.status}">${data.score.status.toUpperCase()}</span></p>
                        ${data.score.overall_assessment ? `<p><strong>Assessment:</strong> ${data.score.overall_assessment}</p>` : ''}
                    </div>
                </div>
            </div>
        `;
    }
}

/**
 * Clean up all polling intervals
 */
function cleanupPolling() {
    activePollingIntervals.forEach((interval) => {
        clearInterval(interval);
    });
    activePollingIntervals.clear();
}

// ===================================
// 5. UPLOAD RESUME (FIXED)
// ===================================
async function uploadResume() {
    const fileInput = document.getElementById('fileInput');
    const positionId = document.getElementById('positionSelect').value;
    const statusDiv = document.getElementById('uploadStatus');
    const resultDiv = document.getElementById('uploadResult');
    
    // Validation
    if (!fileInput.files[0]) {
        statusDiv.innerHTML = '<div class="alert alert-error">Please select a file</div>';
        return;
    }
    
    if (!positionId) {
        statusDiv.innerHTML = '<div class="alert alert-error">Please select a position</div>';
        return;
    }
    
    statusDiv.innerHTML = '<div class="alert alert-warning">⏳ Uploading resume...</div>';
    resultDiv.innerHTML = '';
    
    try {
        const result = await api.uploadResume(fileInput.files[0], positionId);
        
        if (!result.success) {
            throw new Error(result.message || 'Upload failed');
        }
        
        // Show initial success
        statusDiv.innerHTML = '<div class="alert alert-success">✅ Resume uploaded successfully!</div>';
        
        // Display processing status card
        const resumeInfo = result.resume;
        const candidateInfo = result.candidate;
        
        resultDiv.innerHTML = `
            <div class="processing-card">
                <h4>Upload Successful</h4>
                <p><strong>Resume ID:</strong> ${resumeInfo.id}</p>
                <p><strong>Candidate:</strong> ${candidateInfo.full_name}</p>
                <p><strong>File:</strong> ${resumeInfo.filename}</p>
                <p><strong>Status:</strong> <span id="status-${resumeInfo.id}">${resumeInfo.processing_status}</span></p>
                <div class="processing-spinner">
                    <div class="spinner"></div>
                    <p>Processing resume... This may take a moment.</p>
                </div>
            </div>
        `;
        
        // Start polling for status updates
        pollResumeStatus(resumeInfo.id, (statusData, finalStatus) => {
            console.log(`Resume ${resumeInfo.id} processing complete:`, finalStatus);
            
            // Hide spinner
            const spinner = resultDiv.querySelector('.processing-spinner');
            if (spinner) {
                spinner.style.display = 'none';
            }
            
            // Update the result display
            if (finalStatus === 'completed' && statusData.score) {
                displayCompletedResult(resumeInfo.id, statusData);
            } else if (finalStatus === 'failed') {
                resultDiv.innerHTML += `
                    <div class="alert alert-error">
                        Processing failed. Please check the file and try again.
                    </div>
                `;
            }
        });
        
        // Clear file input
        fileInput.value = '';
        
    } catch (error) {
        console.error('Upload error:', error);
        statusDiv.innerHTML = `<div class="alert alert-error">❌ ${error.message}</div>`;
    }
}

// ===================================
// 6. BULK UPLOAD (FIXED)
// ===================================
async function bulkUpload() {
    const filesInput = document.getElementById('bulkFiles');
    const positionId = document.getElementById('positionSelect').value;
    const statusDiv = document.getElementById('uploadStatus');
    const resultDiv = document.getElementById('uploadResult');
    
    if (!filesInput.files.length) {
        statusDiv.innerHTML = '<div class="alert alert-error">Please select files</div>';
        return;
    }
    
    if (!positionId) {
        statusDiv.innerHTML = '<div class="alert alert-error">Please select a position</div>';
        return;
    }
    
    statusDiv.innerHTML = '<div class="alert alert-warning">⏳ Uploading files...</div>';
    resultDiv.innerHTML = '';
    
    try {
        const files = Array.from(filesInput.files);
        const result = await api.bulkUploadResumes(files, positionId);
        
        if (!result.success) {
            throw new Error(result.message || 'Bulk upload failed');
        }
        
        statusDiv.innerHTML = `<div class="alert alert-success">✅ ${result.total_uploaded} files uploaded successfully!</div>`;
        
        // Display results
        resultDiv.innerHTML = '<h4>Upload Results:</h4>';
        result.results.forEach(fileResult => {
            if (fileResult.success) {
                resultDiv.innerHTML += `
                    <div class="bulk-result-item success">
                        <p>✅ ${fileResult.filename} - Resume ID: ${fileResult.resume_id}</p>
                        <p>Status: <span id="status-${fileResult.resume_id}">processing</span></p>
                    </div>
                `;
                
                // Start polling for each uploaded file
                pollResumeStatus(fileResult.resume_id);
            } else {
                resultDiv.innerHTML += `
                    <div class="bulk-result-item error">
                        <p>❌ ${fileResult.filename} - ${fileResult.message}</p>
                    </div>
                `;
            }
        });
        
        // Clear file input
        filesInput.value = '';
        
    } catch (error) {
        console.error('Bulk upload error:', error);
        statusDiv.innerHTML = `<div class="alert alert-error">❌ ${error.message}</div>`;
    }
}

// ===================================
// 7. LOAD RESULTS
// ===================================
async function loadResults() {
    try {
        const filterPosition = document.getElementById('filterPosition')?.value;
        const filters = {};
        if (filterPosition) filters.position_id = filterPosition;
        
        const data = await api.getResumes(filters);
        currentResumes = data.resumes || [];
        
        const tbody = document.getElementById('resultsTableBody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (currentResumes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No resumes found</td></tr>';
            return;
        }
        
        currentResumes.forEach(resume => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${resume.candidate?.full_name || 'Processing...'}</td>
                <td>${resume.position?.title || 'N/A'}</td>
                <td>
                    ${resume.score ? 
                        `<span class="score-badge ${resume.score.status}">${resume.score.percentage.toFixed(1)}%</span>` : 
                        '<span class="score-badge pending">Pending</span>'
                    }
                </td>
                <td>
                    <span class="status-badge status-${resume.processing_status}">
                        ${resume.processing_status}
                    </span>
                </td>
                <td>${new Date(resume.uploaded_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-small" onclick="viewResumeDetails(${resume.id})">View</button>
                    ${resume.processing_status === 'processing' ? 
                        `<button class="btn btn-small" onclick="pollResumeStatus(${resume.id})">Check Status</button>` : 
                        ''
                    }
                </td>
            `;
            tbody.appendChild(row);
            
            // If resume is still processing, start polling
            if (resume.processing_status === 'processing' && !activePollingIntervals.has(resume.id)) {
                pollResumeStatus(resume.id);
            }
        });
        
    } catch (error) {
        console.error('Failed to load results:', error);
        showNotification('Failed to load results', 'error');
    }
}

// ===================================
// 8. DASHBOARD
// ===================================
async function loadDashboard() {
    try {
        const data = await api.getResumes();
        const resumes = data.resumes || [];
        
        // Calculate statistics
        const stats = {
            total: resumes.length,
            completed: resumes.filter(r => r.processing_status === 'completed').length,
            processing: resumes.filter(r => r.processing_status === 'processing').length,
            passed: resumes.filter(r => r.score && r.score.status === 'passed').length,
            failed: resumes.filter(r => r.score && r.score.status === 'failed').length
        };
        
        // Update dashboard stats
        document.getElementById('totalResumes').textContent = stats.total;
        document.getElementById('processedResumes').textContent = stats.completed;
        document.getElementById('processingResumes').textContent = stats.processing;
        document.getElementById('passedResumes').textContent = stats.passed;
        
        // Recent uploads
        const recentList = document.getElementById('recentUploads');
        if (recentList) {
            recentList.innerHTML = '';
            resumes.slice(0, 5).forEach(resume => {
                const item = document.createElement('div');
                item.className = 'recent-item';
                item.innerHTML = `
                    <strong>${resume.candidate?.full_name || 'Processing...'}</strong>
                    <span class="status-${resume.processing_status}">${resume.processing_status}</span>
                    <small>${new Date(resume.uploaded_at).toLocaleDateString()}</small>
                `;
                recentList.appendChild(item);
            });
        }
        
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

// ===================================
// 9. VIEW RESUME DETAILS
// ===================================
async function viewResumeDetails(resumeId) {
    try {
        const resume = await api.getResume(resumeId);
        
        if (!resume.success) {
            throw new Error(resume.message || 'Failed to load resume details');
        }
        
        // Create modal or navigate to details page
        alert(`Resume Details:\n
            Candidate: ${resume.candidate?.full_name || 'N/A'}
            Position: ${resume.position?.title || 'N/A'}
            Score: ${resume.score ? resume.score.percentage.toFixed(1) + '%' : 'Pending'}
            Status: ${resume.score?.status || 'Processing'}
        `);
        
        // TODO: Implement proper modal or details page
        
    } catch (error) {
        console.error('Failed to load resume details:', error);
        showNotification('Failed to load resume details', 'error');
    }
}

// ===================================
// 10. NOTIFICATIONS
// ===================================
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// ===================================
// 11. AUTHENTICATION CHECK
// ===================================
async function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login.html';
        return false;
    }
    
    try {
        const user = await api.getCurrentUser();
        document.getElementById('username').textContent = user.username;
        return true;
    } catch (error) {
        console.error('Auth check failed:', error);
        window.location.href = '/login.html';
        return false;
    }
}

// ===================================
// 12. LOGOUT
// ===================================
async function logout() {
    try {
        await api.logout();
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login.html';
}

// ===================================
// 13. INITIALIZATION
// ===================================
document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    const isAuthenticated = await checkAuth();
    if (!isAuthenticated) return;
    
    // Load initial data
    await loadPositions();
    await loadDashboard();
    
    // Setup file input listeners
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const fileName = e.target.files[0]?.name || 'No file selected';
            document.getElementById('fileName').textContent = fileName;
        });
    }
    
    const bulkFiles = document.getElementById('bulkFiles');
    if (bulkFiles) {
        bulkFiles.addEventListener('change', (e) => {
            const count = e.target.files.length;
            document.getElementById('fileCount').textContent = `${count} file(s) selected`;
        });
    }
    
    // Cleanup polling on page unload
    window.addEventListener('beforeunload', () => {
        cleanupPolling();
    });
});

// ===================================
// EXPORT FUNCTIONS FOR GLOBAL USE
// ===================================
window.switchTab = switchTab;
window.setUploadMode = setUploadMode;
window.uploadResume = uploadResume;
window.bulkUpload = bulkUpload;
window.loadResults = loadResults;
window.viewResumeDetails = viewResumeDetails;
window.logout = logout;
window.pollResumeStatus = pollResumeStatus;