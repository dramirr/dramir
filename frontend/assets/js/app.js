// ===================================
// COMPLETE app.js with Beautiful Score Range Filter
// ===================================

let uploadMode = 'single';
let currentPositions = [];
let currentResumes = [];
let currentCandidates = [];
let activePollingIntervals = new Map();

// ✅ NEW: Global filter state for Results tab
let resultsFilters = {
    position_id: '',
    status: 'all',
    score_min: 0,
    score_max: 100,
    urgency: 50  // 0-100, where higher = lower score threshold (more urgent = accept lower scores)
};

// ===================================
// 1. TAB MANAGEMENT
// ===================================
function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(tabName).classList.add('active');
    
    if (tabName === 'dashboard') loadDashboard();
    if (tabName === 'results') {
        loadPositions(); // Ensure positions are loaded for filter
        loadResults();
    }
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
        
        // Update upload position select
        const uploadSelect = document.getElementById('positionSelect');
        if (uploadSelect) {
            uploadSelect.innerHTML = '<option value="">Select position...</option>';
            data.positions.forEach(pos => {
                const option = document.createElement('option');
                option.value = pos.id;
                option.textContent = pos.title;
                uploadSelect.appendChild(option);
            });
        }
        
        // ✅ FIXED: Update results filter position select
        const filterSelect = document.getElementById('filterPosition');
        if (filterSelect) {
            filterSelect.innerHTML = '<option value="">All Positions</option>';
            data.positions.forEach(pos => {
                const option = document.createElement('option');
                option.value = pos.id;
                option.textContent = pos.title;
                filterSelect.appendChild(option);
            });
        }
        
    } catch (error) {
        console.error('Failed to load positions:', error);
        showNotification('Failed to load positions', 'error');
    }
}

// ===================================
// 4. RESUME STATUS POLLING (FIXED)
// ===================================
async function pollResumeStatus(resumeId, onComplete) {
    if (activePollingIntervals.has(resumeId)) {
        console.log(`Already polling resume ${resumeId}`);
        return;
    }

    const maxAttempts = 60;
    let attempts = 0;
    
    console.log(`Starting to poll status for resume ${resumeId}`);
    
    const pollInterval = setInterval(async () => {
        try {
            attempts++;
            
            const data = await api.getResumeStatus(resumeId);
            console.log(`Resume ${resumeId} status (attempt ${attempts}):`, data.processing_status);
            
            updateStatusDisplay(resumeId, data.processing_status);
            
            if (data.processing_status === 'completed' || data.processing_status === 'failed') {
                clearInterval(pollInterval);
                activePollingIntervals.delete(resumeId);
                
                console.log(`Resume ${resumeId} processing finished with status: ${data.processing_status}`);
                
                if (onComplete) {
                    onComplete(data, data.processing_status);
                }
                
                await loadResults();
                await loadDashboard();
                
                if (data.processing_status === 'completed') {
                    showNotification('✅ Resume processing completed!', 'success');
                    
                    if (data.score) {
                        displayCompletedResult(resumeId, data);
                    }
                } else {
                    showNotification('❌ Resume processing failed', 'error');
                }
            }
            
            if (attempts >= maxAttempts) {
                clearInterval(pollInterval);
                activePollingIntervals.delete(resumeId);
                showNotification('⏱️ Processing is taking longer than expected', 'warning');
            }
            
        } catch (error) {
            console.error('Polling error:', error);
            
            if (error.message && (error.message.includes('401') || error.message.includes('Unauthorized'))) {
                clearInterval(pollInterval);
                activePollingIntervals.delete(resumeId);
                showNotification('⚠️ Authentication error. Please login again.', 'error');
                
                if (typeof logout === 'function') {
                    logout();
                }
                return;
            }
            
            if (attempts >= maxAttempts) {
                clearInterval(pollInterval);
                activePollingIntervals.delete(resumeId);
            }
        }
    }, 5000);
    
    activePollingIntervals.set(resumeId, pollInterval);
}

function updateStatusDisplay(resumeId, status) {
    const statusElement = document.getElementById(`status-${resumeId}`);
    if (!statusElement) return;
    
    const statusMessages = {
        'pending': 'Pending...',
        'processing': '⏳ Processing...',
        'completed': '✅ Completed',
        'failed': '❌ Failed'
    };
    
    statusElement.textContent = statusMessages[status] || status;
    
    const colors = {
        'pending': '#ffc107',
        'processing': '#17a2b8',
        'completed': '#28a745',
        'failed': '#dc3545'
    };
    
    statusElement.style.color = colors[status] || 'inherit';
}

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
        
        statusDiv.innerHTML = '<div class="alert alert-success">✅ Resume uploaded successfully!</div>';
        
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
        
        pollResumeStatus(resumeInfo.id, (statusData, finalStatus) => {
            console.log(`Resume ${resumeInfo.id} processing complete:`, finalStatus);
            
            const spinner = resultDiv.querySelector('.processing-spinner');
            if (spinner) {
                spinner.style.display = 'none';
            }
            
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
        
        fileInput.value = '';
        
    } catch (error) {
        console.error('Upload error:', error);
        statusDiv.innerHTML = `<div class="alert alert-error">❌ ${error.message}</div>`;
    }
}

// ===================================
// 6. LOAD DASHBOARD
// ===================================
async function loadDashboard() {
    try {
        const data = await api.getResumes();
        const resumes = data.resumes || [];
        
        const stats = {
            total: resumes.length,
            completed: resumes.filter(r => r.processing_status === 'completed').length,
            processing: resumes.filter(r => r.processing_status === 'processing').length,
            qualified: resumes.filter(r => r.score && r.score.status === 'Qualified').length,
            rejected: resumes.filter(r => r.score && r.score.status === 'Rejected').length
        };
        
        const avgScore = resumes.length > 0 
            ? resumes.filter(r => r.score).reduce((sum, r) => sum + r.score.percentage, 0) / Math.max(resumes.filter(r => r.score).length, 1)
            : 0;
        
        const statsContainer = document.getElementById('statsContainer');
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div class="stat-card">
                    <div class="stat-value">${stats.total}</div>
                    <div class="stat-label">📊 Total Resumes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.qualified}</div>
                    <div class="stat-label">✅ Qualified</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.rejected}</div>
                    <div class="stat-label">❌ Rejected</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${avgScore.toFixed(1)}%</div>
                    <div class="stat-label">📈 Avg Score</div>
                </div>
            `;
        }
        
        const recentDiv = document.getElementById('recentApplications');
        if (recentDiv) {
            recentDiv.innerHTML = '<h3>Recent Applications</h3>';
            resumes.slice(0, 5).forEach(resume => {
                recentDiv.innerHTML += `
                    <div class="recent-item">
                        <strong>${resume.candidate?.full_name || 'Processing...'}</strong>
                        <span class="status-${resume.processing_status}">${resume.processing_status}</span>
                        <small>${new Date(resume.uploaded_at).toLocaleDateString()}</small>
                    </div>
                `;
            });
        }
        
    } catch (error) {
        console.error('Failed to load dashboard:', error);
        showNotification('Failed to load dashboard', 'error');
    }
}

// ===================================
// 7. LOAD RESULTS WITH FILTERS
// ===================================
async function loadResults() {
    try {
        // Build filter object
        const filters = {};
        
        // ✅ FIXED: Get position filter
        const positionSelect = document.getElementById('filterPosition');
        if (positionSelect && positionSelect.value) {
            filters.position_id = positionSelect.value;
            resultsFilters.position_id = positionSelect.value;
        }
        
        // ✅ FIXED: Get status filter (THIS WAS MISSING!)
        const statusSelect = document.getElementById('filterStatus');
        if (statusSelect && statusSelect.value && statusSelect.value !== 'all') {
            filters.status = statusSelect.value;
            resultsFilters.status = statusSelect.value;
        }
        
        // ✅ NEW: Add score range filters
        filters.score_min = resultsFilters.score_min;
        filters.score_max = resultsFilters.score_max;
        
        console.log('Filters being applied:', filters);
        
        const data = await api.getResumes(filters);
        let resumes = data.resumes || [];
        
        // ✅ Filter by score range on frontend (if backend doesn't support it)
        resumes = resumes.filter(resume => {
            if (!resume.score) return true; // Include processing resumes
            return resume.score.percentage >= filters.score_min && 
                   resume.score.percentage <= filters.score_max;
        });
        
        currentResumes = resumes;
        
        const tableDiv = document.getElementById('resultsTable');
        if (!tableDiv) return;
        
        if (currentResumes.length === 0) {
            tableDiv.innerHTML = '<p style="padding: 20px; text-align: center; color: var(--text-secondary);">No resumes found matching the filters</p>';
            return;
        }
        
        let tableHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Candidate</th>
                        <th>Position</th>
                        <th>Score</th>
                        <th>Status</th>
                        <th>Date</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        currentResumes.forEach(resume => {
            const scoreDisplay = resume.score 
                ? `<span class="score-badge ${resume.score.status}">${resume.score.percentage.toFixed(1)}%</span>`
                : '<span class="score-badge pending">Pending</span>';
            
            tableHTML += `
                <tr>
                    <td>${resume.candidate?.full_name || 'Processing...'}</td>
                    <td>${resume.position?.title || 'N/A'}</td>
                    <td>${scoreDisplay}</td>
                    <td>
                        <span class="status-badge status-${resume.processing_status}">
                            ${resume.processing_status}
                        </span>
                    </td>
                    <td>${new Date(resume.uploaded_at).toLocaleDateString()}</td>
                    <td>
                        <button class="btn-sm btn-primary" onclick="viewResumeDetails(${resume.id})">View</button>
                    </td>
                </tr>
            `;
            
            if (resume.processing_status === 'processing' && !activePollingIntervals.has(resume.id)) {
                pollResumeStatus(resume.id);
            }
        });
        
        tableHTML += '</tbody></table>';
        tableDiv.innerHTML = tableHTML;
        
    } catch (error) {
        console.error('Failed to load results:', error);
        showNotification('Failed to load results', 'error');
    }
}

// ===================================
// 8. ✅ NEW: SCORE RANGE FILTER WITH URGENCY SLIDER
// ===================================
function initializeScoreRangeFilter() {
    const filterContainer = document.getElementById('scoreRangeFilterContainer');
    if (!filterContainer) return;
    
    filterContainer.innerHTML = `
        <div class="score-range-filter">
            <div class="filter-header">
                <h3>🎯 Score Range Filter</h3>
                <p class="filter-subtitle">Adjust urgency level or set custom score range</p>
            </div>
            
            <!-- Urgency Slider Section -->
            <div class="urgency-section">
                <div class="urgency-header">
                    <label>⚡ Urgency Level</label>
                    <span class="urgency-value" id="urgencyValue">Medium</span>
                </div>
                <div class="urgency-slider-container">
                    <div class="urgency-label">Low</div>
                    <input 
                        type="range" 
                        id="urgencySlider" 
                        min="0" 
                        max="100" 
                        value="50"
                        class="urgency-slider"
                        oninput="updateUrgencyFilter()"
                    >
                    <div class="urgency-label">High</div>
                </div>
                <div class="urgency-description" id="urgencyDescription">
                    Medium urgency: Accept candidates with 40-100% score
                </div>
                
                <!-- Visual indicator of current range -->
                <div class="score-range-display">
                    <div class="range-bar">
                        <div class="range-fill" id="rangeFill"></div>
                    </div>
                    <div class="range-labels">
                        <span>0%</span>
                        <span id="currentMinScore">40</span>% - <span id="currentMaxScore">100</span>%
                        <span>100%</span>
                    </div>
                </div>
            </div>
            
            <!-- OR Divider -->
            <div class="filter-divider">
                <span>OR</span>
            </div>
            
            <!-- Manual Score Range Section -->
            <div class="manual-range-section">
                <label class="manual-label">
                    <input type="checkbox" id="manualRangeToggle" onchange="toggleManualRange()">
                    Set Custom Score Range
                </label>
                
                <div class="manual-inputs" id="manualInputs" style="display: none;">
                    <div class="range-input-group">
                        <label>Minimum Score</label>
                        <div class="input-with-unit">
                            <input 
                                type="range" 
                                id="minScoreSlider" 
                                min="0" 
                                max="100" 
                                value="40"
                                class="score-slider"
                                oninput="updateManualRange()"
                            >
                            <input 
                                type="number" 
                                id="minScoreInput" 
                                min="0" 
                                max="100" 
                                value="40"
                                class="score-input"
                                onchange="updateManualRange()"
                            >
                            <span class="unit">%</span>
                        </div>
                    </div>
                    
                    <div class="range-input-group">
                        <label>Maximum Score</label>
                        <div class="input-with-unit">
                            <input 
                                type="range" 
                                id="maxScoreSlider" 
                                min="0" 
                                max="100" 
                                value="100"
                                class="score-slider"
                                oninput="updateManualRange()"
                            >
                            <input 
                                type="number" 
                                id="maxScoreInput" 
                                min="0" 
                                max="100" 
                                value="100"
                                class="score-input"
                                onchange="updateManualRange()"
                            >
                            <span class="unit">%</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="filter-actions">
                <button class="btn-primary" onclick="applyScoreFilter()">
                    <span>✓</span> Apply Filter
                </button>
                <button class="btn-secondary" onclick="resetScoreFilter()">
                    <span>↻</span> Reset
                </button>
            </div>
        </div>
    `;
    
    // Initialize urgency slider
    updateUrgencyFilter();
}

function updateUrgencyFilter() {
    const slider = document.getElementById('urgencySlider');
    const urgency = parseInt(slider.value);
    resultsFilters.urgency = urgency;
    
    // Calculate score range based on urgency
    // Low urgency (0): Accept 75-100
    // Medium urgency (50): Accept 40-100
    // High urgency (100): Accept 0-100
    const minScore = Math.max(0, 75 - (urgency * 0.75));
    const maxScore = 100;
    
    resultsFilters.score_min = Math.round(minScore);
    resultsFilters.score_max = maxScore;
    
    // Update display
    const urgencyValue = document.getElementById('urgencyValue');
    const urgencyDescription = document.getElementById('urgencyDescription');
    
    if (urgency < 30) {
        urgencyValue.textContent = 'Low (Strict)';
        urgencyDescription.textContent = '⬆️ Low urgency: Only accept high-quality candidates (75%+)';
    } else if (urgency < 70) {
        urgencyValue.textContent = 'Medium (Balanced)';
        urgencyDescription.textContent = '⚖️ Medium urgency: Accept candidates with 40%+ score';
    } else {
        urgencyValue.textContent = 'High (Flexible)';
        urgencyDescription.textContent = '⬇️ High urgency: Accept all candidates regardless of score';
    }
    
    // Update range display
    document.getElementById('currentMinScore').textContent = Math.round(minScore);
    document.getElementById('currentMaxScore').textContent = maxScore;
    
    const rangeFill = document.getElementById('rangeFill');
    if (rangeFill) {
        rangeFill.style.left = (minScore) + '%';
        rangeFill.style.right = (100 - maxScore) + '%';
    }
    
    // Disable manual inputs when using urgency
    const manualToggle = document.getElementById('manualRangeToggle');
    if (manualToggle) {
        manualToggle.checked = false;
        document.getElementById('manualInputs').style.display = 'none';
    }
}

function toggleManualRange() {
    const manualInputs = document.getElementById('manualInputs');
    const toggle = document.getElementById('manualRangeToggle');
    
    manualInputs.style.display = toggle.checked ? 'grid' : 'none';
    
    if (toggle.checked) {
        // Reset urgency slider
        document.getElementById('urgencySlider').value = 50;
        updateUrgencyFilter();
    }
}

function updateManualRange() {
    const minInput = document.getElementById('minScoreInput');
    const maxInput = document.getElementById('maxScoreInput');
    const minSlider = document.getElementById('minScoreSlider');
    const maxSlider = document.getElementById('maxScoreSlider');
    
    let minVal = parseInt(minInput.value);
    let maxVal = parseInt(maxInput.value);
    
    // Sync slider and input
    minSlider.value = minVal;
    maxSlider.value = maxVal;
    
    // Ensure min < max
    if (minVal > maxVal) {
        minVal = maxVal;
        minInput.value = minVal;
        minSlider.value = minVal;
    }
    
    resultsFilters.score_min = minVal;
    resultsFilters.score_max = maxVal;
}

function applyScoreFilter() {
    console.log('Applying score filter:', resultsFilters);
    loadResults();
    showNotification(`✅ Filter applied: ${resultsFilters.score_min}% - ${resultsFilters.score_max}%`, 'success');
}

function resetScoreFilter() {
    resultsFilters.score_min = 0;
    resultsFilters.score_max = 100;
    resultsFilters.urgency = 50;
    
    document.getElementById('urgencySlider').value = 50;
    document.getElementById('minScoreInput').value = 40;
    document.getElementById('maxScoreInput').value = 100;
    document.getElementById('minScoreSlider').value = 40;
    document.getElementById('maxScoreSlider').value = 100;
    document.getElementById('manualRangeToggle').checked = false;
    document.getElementById('manualInputs').style.display = 'none';
    
    updateUrgencyFilter();
    loadResults();
    showNotification('✓ Filter reset', 'success');
}

// ===================================
// 9. ✅ FIXED: FILTER RESULTS (NOW INCLUDES STATUS)
// ===================================
async function filterResults() {
    console.log('Filter results called');
    loadResults();
}

// ===================================
// 10. VIEW RESUME DETAILS WITH POPUP
// ===================================
async function viewResumeDetails(resumeId) {
    try {
        const data = await api.getResume(resumeId);
        
        if (!data.success) {
            throw new Error(data.message || 'Failed to load resume details');
        }
        
        showScorePopup(data);
        
    } catch (error) {
        console.error('Failed to load resume details:', error);
        showNotification('Failed to load resume details', 'error');
    }
}

function showScorePopup(data) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
        animation: fadeIn 0.3s;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: var(--bg-medium, #1e293b);
        border-radius: 16px;
        padding: 30px;
        max-width: 900px;
        max-height: 90vh;
        overflow-y: auto;
        position: relative;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        animation: slideUp 0.3s;
    `;
    
    let content = `
        <button onclick="this.closest('.modal-overlay').remove()" style="position: absolute; top: 15px; right: 20px; background: none; border: none; font-size: 28px; cursor: pointer; color: var(--text-secondary); line-height: 1;">×</button>
        
        <h2 style="margin: 0 0 20px 0; color: var(--primary, #3b82f6);">📊 Resume Analysis</h2>
        
        <div style="background: var(--bg-dark, #0f172a); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
            <h3 style="margin: 0 0 15px 0;">👤 ${data.candidate?.full_name || 'N/A'}</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div>
                    <strong>Position:</strong> ${data.position?.title || 'N/A'}
                </div>
                <div>
                    <strong>Phone:</strong> ${data.candidate?.phone || 'N/A'}
                </div>
                <div>
                    <strong>Email:</strong> ${data.candidate?.email || 'N/A'}
                </div>
                <div>
                    <strong>Upload Date:</strong> ${new Date(data.resume.uploaded_at).toLocaleDateString()}
                </div>
            </div>
        </div>
    `;
    
    if (data.score) {
        const statusClass = data.score.status === 'Qualified' ? 'success' : 'error';
        const statusColor = data.score.status === 'Qualified' ? '#10b981' : '#ef4444';
        
        content += `
            <div style="background: var(--bg-dark, #0f172a); padding: 25px; border-radius: 12px; margin-bottom: 20px; text-align: center;">
                <h3 style="margin: 0 0 20px 0;">📈 Overall Score</h3>
                <div style="display: flex; justify-content: center; align-items: center; gap: 30px; flex-wrap: wrap;">
                    <div style="width: 120px; height: 120px; border-radius: 50%; border: 5px solid ${statusColor}; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                        <div style="font-size: 32px; font-weight: bold; color: ${statusColor};">
                            ${data.score.percentage.toFixed(1)}%
                        </div>
                        <div style="font-size: 12px; color: var(--text-secondary);">
                            ${data.score.total_score.toFixed(1)} / ${data.score.max_possible_score.toFixed(1)}
                        </div>
                    </div>
                    <div style="text-align: left;">
                        <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: ${statusColor}; font-weight: bold;">${data.score.status.toUpperCase()}</span></p>
                        <p style="margin: 5px 0; max-width: 400px; line-height: 1.5;">${data.score.overall_assessment || ''}</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    if (data.individual_scores && data.individual_scores.length > 0) {
        content += `
            <div style="background: var(--bg-dark, #0f172a); padding: 25px; border-radius: 12px;">
                <h3 style="margin: 0 0 20px 0;">🎯 Detailed Scoring</h3>
                <div style="display: grid; gap: 12px;">
        `;
        
        const categories = {
            'core': [],
            'supplementary': [],
            'other': []
        };
        
        data.individual_scores.forEach(score => {
            const category = score.category || 'other';
            if (categories[category]) {
                categories[category].push(score);
            } else {
                categories.other.push(score);
            }
        });
        
        Object.entries(categories).forEach(([cat, scores]) => {
            if (scores.length === 0) return;
            
            const categoryName = cat === 'core' ? 'Core Criteria' : cat === 'supplementary' ? 'Supplementary' : 'Other';
            
            content += `<h4 style="margin: 20px 0 10px 0; color: var(--text-secondary);">${categoryName}</h4>`;
            
            scores.forEach(score => {
                const percentage = score.max_points > 0 ? (score.awarded_points / score.max_points * 100) : 0;
                const barColor = percentage >= 80 ? '#10b981' : percentage >= 50 ? '#f59e0b' : '#ef4444';
                
                content += `
                    <div style="background: var(--bg-medium, #1e293b); padding: 15px; border-radius: 8px; border-left: 4px solid ${barColor};">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <strong style="font-size: 15px;">${score.criterion_name || 'N/A'}</strong>
                            <span style="font-weight: bold; color: ${barColor};">
                                ${score.awarded_points.toFixed(1)} / ${score.max_points.toFixed(1)}
                                <span style="font-size: 13px; margin-left: 5px;">(${percentage.toFixed(0)}%)</span>
                            </span>
                        </div>
                        <div style="background: var(--bg-dark, #0f172a); height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 8px;">
                            <div style="width: ${percentage}%; height: 100%; background: ${barColor}; transition: width 0.3s;"></div>
                        </div>
                        ${score.extracted_value ? `<p style="margin: 5px 0; font-size: 13px;"><strong>Extracted Value:</strong> ${score.extracted_value}</p>` : ''}
                        ${score.reasoning ? `<p style="margin: 5px 0; font-size: 13px; color: var(--text-secondary);">${score.reasoning}</p>` : ''}
                    </div>
                `;
            });
        });
        
        content += `
                </div>
            </div>
        `;
    }
    
    modalContent.innerHTML = content;
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes slideUp {
            from { transform: translateY(50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
}

// ===================================
// 11. LOAD CANDIDATES
// ===================================
async function loadCandidates() {
    try {
        const data = await api.getCandidates();
        currentCandidates = data.candidates || [];
        
        const candidatesList = document.getElementById('candidatesList');
        if (!candidatesList) return;
        
        candidatesList.innerHTML = '';
        
        if (currentCandidates.length === 0) {
            candidatesList.innerHTML = '<p>No candidates found</p>';
            return;
        }
        
        currentCandidates.forEach(candidate => {
            const card = document.createElement('div');
            card.className = 'candidate-card';
            card.innerHTML = `
                <h3>${candidate.full_name}</h3>
                <p>📞 ${candidate.phone || 'N/A'}</p>
                <p>📧 ${candidate.email || 'N/A'}</p>
                <p>📊 ${candidate.total_submissions} submission(s)</p>
                <button class="btn-sm btn-primary" onclick="viewCandidateDetails(${candidate.id})">View Details</button>
            `;
            candidatesList.appendChild(card);
        });
        
    } catch (error) {
        console.error('Failed to load candidates:', error);
        showNotification('Failed to load candidates', 'error');
    }
}

// ===================================
// 12. LOAD POSITIONS LIST
// ===================================
async function loadPositionsList() {
    try {
        const data = await api.getPositions();
        currentPositions = data.positions || [];
        
        const positionsList = document.getElementById('positionsList');
        if (!positionsList) return;
        
        positionsList.innerHTML = '';
        
        if (currentPositions.length === 0) {
            positionsList.innerHTML = '<p>No positions found</p>';
            return;
        }
        
        currentPositions.forEach(position => {
            const card = document.createElement('div');
            card.className = 'position-card';
            card.innerHTML = `
                <h3>${position.title}</h3>
                <p>${position.description || 'No description'}</p>
                <p><strong>Threshold:</strong> ${position.threshold_percentage}%</p>
                <p><strong>Status:</strong> ${position.is_active ? '✅ Active' : '❌ Inactive'}</p>
                <button class="btn-sm btn-primary" onclick="viewPositionDetails(${position.id})">View Details</button>
            `;
            positionsList.appendChild(card);
        });
        
    } catch (error) {
        console.error('Failed to load positions:', error);
        showNotification('Failed to load positions', 'error');
    }
}

// ===================================
// OTHER FUNCTIONS
// ===================================
async function viewCandidateDetails(candidateId) {
    try {
        const candidate = await api.getCandidate(candidateId);
        
        alert(`Candidate Details:\n
            Name: ${candidate.full_name}
            Phone: ${candidate.phone || 'N/A'}
            Email: ${candidate.email || 'N/A'}
            Total Submissions: ${candidate.total_submissions}
        `);
        
    } catch (error) {
        console.error('Failed to load candidate details:', error);
        showNotification('Failed to load candidate details', 'error');
    }
}

async function viewPositionDetails(positionId) {
    try {
        const position = await api.getPosition(positionId);
        
        alert(`Position Details:\n
            Title: ${position.title}
            Description: ${position.description || 'N/A'}
            Threshold: ${position.threshold_percentage}%
            Criteria Count: ${position.criteria?.length || 0}
        `);
        
    } catch (error) {
        console.error('Failed to load position details:', error);
        showNotification('Failed to load position details', 'error');
    }
}

async function searchCandidates() {
    const searchInput = document.getElementById('searchCandidate');
    const query = searchInput?.value || '';
    
    if (query.length < 2) {
        loadCandidates();
        return;
    }
    
    try {
        const data = await api.searchCandidates(query);
        currentCandidates = data.candidates || [];
        
        const candidatesList = document.getElementById('candidatesList');
        if (!candidatesList) return;
        
        candidatesList.innerHTML = '';
        
        if (currentCandidates.length === 0) {
            candidatesList.innerHTML = '<p>No candidates found</p>';
            return;
        }
        
        currentCandidates.forEach(candidate => {
            const card = document.createElement('div');
            card.className = 'candidate-card';
            card.innerHTML = `
                <h3>${candidate.full_name}</h3>
                <p>📞 ${candidate.phone || 'N/A'}</p>
                <p>📧 ${candidate.email || 'N/A'}</p>
                <p>📊 ${candidate.total_submissions} submission(s)</p>
                <button class="btn-sm btn-primary" onclick="viewCandidateDetails(${candidate.id})">View Details</button>
            `;
            candidatesList.appendChild(card);
        });
        
    } catch (error) {
        console.error('Search error:', error);
        showNotification('Search failed', 'error');
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 9999;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// ===================================
// INITIALIZATION
// ===================================
document.addEventListener('DOMContentLoaded', async () => {
    console.log('App.js: DOM loaded');
    
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const fileName = e.target.files[0]?.name || 'No file selected';
            const fileNameDisplay = document.getElementById('fileName');
            if (fileNameDisplay) {
                fileNameDisplay.textContent = fileName;
            }
        });
    }
    
    const filesInput = document.getElementById('filesInput');
    if (filesInput) {
        filesInput.addEventListener('change', (e) => {
            const count = e.target.files.length;
            const fileCountDisplay = document.getElementById('fileCount');
            if (fileCountDisplay) {
                fileCountDisplay.textContent = `${count} file(s) selected`;
            }
        });
    }
    
    window.addEventListener('beforeunload', () => {
        cleanupPolling();
    });
});

// ===================================
// EXPORT FUNCTIONS
// ===================================
window.switchTab = switchTab;
window.setUploadMode = setUploadMode;
window.uploadResume = uploadResume;
window.bulkUploadResumes = bulkUploadResumes;
window.loadResults = loadResults;
window.loadDashboard = loadDashboard;
window.loadCandidates = loadCandidates;
window.loadPositionsList = loadPositionsList;
window.loadPositions = loadPositions;
window.viewResumeDetails = viewResumeDetails;
window.viewCandidateDetails = viewCandidateDetails;
window.viewPositionDetails = viewPositionDetails;
window.searchCandidates = searchCandidates;
window.filterResults = filterResults;
window.pollResumeStatus = pollResumeStatus;
window.initializeScoreRangeFilter = initializeScoreRangeFilter;
window.updateUrgencyFilter = updateUrgencyFilter;
window.toggleManualRange = toggleManualRange;
window.updateManualRange = updateManualRange;
window.applyScoreFilter = applyScoreFilter;
window.resetScoreFilter = resetScoreFilter;