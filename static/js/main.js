  
// Global variables
let currentJobId = null;

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
});

function initializeEventListeners() {
    // Resume form submission
    const resumeForm = document.getElementById('resumeForm');
    if (resumeForm) {
        resumeForm.addEventListener('submit', handleResumeUpload);
    }

    // Job form submission
    const jobForm = document.getElementById('jobForm');
    if (jobForm) {
        jobForm.addEventListener('submit', handleJobDescription);
    }

    // File input change
    const fileInput = document.getElementById('resumeFile');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }

    // Download button
    const downloadBtn = document.getElementById('downloadBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadResults);
    }
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        const fileName = file.name;
        const fileSize = (file.size / 1024 / 1024).toFixed(2);
        
        // Update UI to show selected file
        const uploadArea = event.target.closest('.border-dashed');
        const icon = uploadArea.querySelector('i');
        const text = uploadArea.querySelector('span');
        
        icon.className = 'fas fa-file-alt text-4xl text-blue-500';
        text.textContent = `${fileName} (${fileSize} MB)`;
    }
}

async function handleResumeUpload(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const loadingSpinner = document.getElementById('loadingSpinner');
    
    try {
        showLoading(true);
        
        const response = await fetch('/upload_resume', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayResumeResults(result.parsed_data);
            showNotification('Resume uploaded and parsed successfully!', 'success');
        } else {
            showNotification('Error: ' + result.error, 'error');
        }
        
    } catch (error) {
        showNotification('Error uploading resume: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function handleJobDescription(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const jobData = {
        title: formData.get('title'),
        company: formData.get('company'),
        description: formData.get('description'),
        required_experience: parseInt(formData.get('required_experience')) || 0,
        education_requirements: []
    };
    
    try {
        showLoading(true);
        
        const response = await fetch('/upload_job_description', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(jobData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentJobId = result.job_id;
            displayJobResults(result.extracted_skills);
            showNotification('Job description saved successfully!', 'success');
            
            // Automatically match candidates
            await matchCandidates(result.job_id);
        } else {
            showNotification('Error: ' + result.error, 'error');
        }
        
    } catch (error) {
        showNotification('Error saving job description: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function matchCandidates(jobId) {
    try {
        showLoading(true);
        
        const response = await fetch(`/match_candidates/${jobId}`);
        const result = await response.json();
        
        if (result.success) {
            displayMatchResults(result.matches, result.job);
            showNotification('Candidates matched successfully!', 'success');
        } else {
            showNotification('Error matching candidates: ' + result.error, 'error');
        }
        
    } catch (error) {
        showNotification('Error matching candidates: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function displayResumeResults(parsedData) {
    const resultsDiv = document.getElementById('resumeResults');
    const infoDiv = document.getElementById('parsedInfo');
    
    let html = `
        <div class="space-y-3">
            <div class="flex items-center space-x-2">
                <i class="fas fa-envelope text-blue-500"></i>
                <span><strong>Email:</strong> ${parsedData.contact_info.email || 'Not found'}</span>
            </div>
            <div class="flex items-center space-x-2">
                <i class="fas fa-phone text-green-500"></i>
                <span><strong>Phone:</strong> ${parsedData.contact_info.phone || 'Not found'}</span>
            </div>
            <div class="flex items-center space-x-2">
                <i class="fas fa-map-marker-alt text-red-500"></i>
                <span><strong>Location:</strong> ${parsedData.contact_info.location || 'Not found'}</span>
            </div>
            <div class="flex items-center space-x-2">
                <i class="fas fa-calendar text-purple-500"></i>
                <span><strong>Experience:</strong> ${parsedData.experience_years} years</span>
            </div>
        </div>
        
        <div class="mt-4">
            <h4 class="font-semibold mb-2">Extracted Skills:</h4>
            <div class="flex flex-wrap gap-2">
    `;
    
    // Display skills by category
    for (const [category, skills] of Object.entries(parsedData.skills)) {
        if (skills.length > 0) {
            skills.forEach(skill => {
                html += `<span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">${skill}</span>`;
            });
        }
    }
    
    html += `</div></div>`;
    
    infoDiv.innerHTML = html;
    resultsDiv.classList.remove('hidden');
}

function displayJobResults(extractedSkills) {
    const resultsDiv = document.getElementById('jobResults');
    const skillsDiv = document.getElementById('extractedSkills');
    
    let html = '<div class="flex flex-wrap gap-2">';
    extractedSkills.forEach(skill => {
        html += `<span class="px-2 py-1 bg-green-100 text-green-800 rounded-full text-sm">${skill}</span>`;
    });
    html += '</div>';
    
    skillsDiv.innerHTML = html;
    resultsDiv.classList.remove('hidden');
}

function displayMatchResults(matches, job) {
    const matchSection = document.getElementById('matchSection');
    const resultsDiv = document.getElementById('matchResults');
    
    let html = `
        <div class="mb-6 p-4 bg-blue-50 rounded-lg">
            <h3 class="text-lg font-semibold text-blue-800">
                ${job.title} at ${job.company}
            </h3>
            <p class="text-blue-600">Found ${matches.length} candidates</p>
        </div>
    `;
    
    if (matches.length === 0) {
        html += `
            <div class="text-center py-12">
                <i class="fas fa-users-slash text-6xl text-gray-300 mb-4"></i>
                <p class="text-gray-500">No candidates found. Upload some resumes first!</p>
            </div>
        `;
    } else {
        html += '<div class="space-y-4">';
        
        matches.forEach((match, index) => {
            const candidate = match.candidate;
            const result = match.match_result;
            
            const scoreColor = result.overall_score >= 80 ? 'green' : 
                             result.overall_score >= 60 ? 'yellow' : 'red';
            
            html += `
                <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div class="flex justify-between items-start mb-3">
                        <div>
                            <h4 class="text-lg font-semibold text-gray-800">${candidate.name}</h4>
                            <p class="text-gray-600">${candidate.email || 'No email'}</p>
                            <p class="text-sm text-gray-500">${candidate.location || 'Location not specified'}</p>
                        </div>
                        <div class="text-right">
                            <div class="text-2xl font-bold text-${scoreColor}-600 mb-1">
                                ${result.overall_score}%
                            </div>
                            <div class="text-sm text-gray-500">Overall Match</div>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                        <div class="text-center">
                            <div class="text-lg font-semibold text-blue-600">${result.skill_match.score * 100}%</div>
                            <div class="text-xs text-gray-500">Skills</div>
                        </div>
                        <div class="text-center">
                            <div class="text-lg font-semibold text-purple-600">${result.semantic_score}%</div>
                            <div class="text-xs text-gray-500">Semantic</div>
                        </div>
                        <div class="text-center">
                            <div class="text-lg font-semibold text-orange-600">${result.experience_score}%</div>
                            <div class="text-xs text-gray-500">Experience</div>
                        </div>
                        <div class="text-center">
                            <div class="text-lg font-semibold text-teal-600">${result.education_score}%</div>
                            <div class="text-xs text-gray-500">Education</div>
                        </div>
                    </div>
                    
                    <div class="border-t pt-3">
                        <div class="grid md:grid-cols-2 gap-4">
                            <div>
                                <h5 class="font-semibold text-green-700 mb-2">Matched Skills:</h5>
                                <div class="flex flex-wrap gap-1">
            `;
            
            result.skill_match.matched_skills.forEach(skill => {
                html += `<span class="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">${skill}</span>`;
            });
            
            html += `
                                </div>
                            </div>
                            <div>
                                <h5 class="font-semibold text-red-700 mb-2">Missing Skills:</h5>
                                <div class="flex flex-wrap gap-1">
            `;
            
            result.skill_match.missing_skills.forEach(skill => {
                html += `<span class="px-2 py-1 bg-red-100 text-red-700 rounded text-xs">${skill}</span>`;
            });
            
            html += `
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
    }
    
    resultsDiv.innerHTML = html;
    matchSection.classList.remove('hidden');
}

function downloadResults() {
    if (currentJobId) {
        window.location.href = `/download_results/${currentJobId}`;
    } else {
        showNotification('No job selected for download', 'error');
    }
}

function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        if (show) {
            spinner.classList.remove('hidden');
        } else {
            spinner.classList.add('hidden');
        }
    }
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-4 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
    }`;
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'} mr-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}