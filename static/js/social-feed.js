// Social Media Style Civic Platform JavaScript

class CivicSocialFeed {
    constructor() {
        this.currentFilter = 'all';
        this.posts = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadPosts();
        this.setupLocationServices();
    }

    bindEvents() {
        // Feed filter buttons
        document.querySelectorAll('input[name="feedFilter"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.currentFilter = e.target.id;
                this.loadPosts();
            });
        });

        // Modal events
        document.addEventListener('DOMContentLoaded', () => {
            this.reportModal = new bootstrap.Modal(document.getElementById('reportModal'));
            this.imageModal = new bootstrap.Modal(document.getElementById('imageModal'));
        });
    }

    async loadPosts() {
        try {
            const endpoint = this.getEndpointForFilter(this.currentFilter);
            const response = await fetch(endpoint, {
                headers: this.getAuthHeaders()
            });

            if (response.ok) {
                const posts = await response.json();
                this.renderPosts(posts);
            }
        } catch (error) {
            console.error('Error loading posts:', error);
            this.showNotification('Error loading posts', 'error');
        }
    }

    getEndpointForFilter(filter) {
        const endpoints = {
            'all': '/social/feed/newest',
            'trending': '/social/feed/trending',
            'nearby': '/social/feed/nearby?latitude=40.7128&longitude=-74.0060',
            'following': '/social/feed/newest' // Placeholder
        };
        return endpoints[filter] || endpoints['all'];
    }

    renderPosts(posts) {
        const container = document.getElementById('posts-container');
        if (!container) return;

        container.innerHTML = posts.map(post => this.createPostHTML(post)).join('');
        this.bindPostEvents();
    }

    createPostHTML(post) {
        const timeAgo = this.getTimeAgo(new Date(post.created_at));
        const statusClass = `status-${post.status.replace(' ', '_').toLowerCase()}`;
        
        return `
            <div class="card mb-4 post-card fade-in" data-post-id="${post.id}">
                <div class="card-body">
                    <!-- Post Header -->
                    <div class="d-flex align-items-center mb-3">
                        <div class="profile-avatar me-3">
                            <i class="fas fa-user-circle fa-2x text-primary"></i>
                        </div>
                        <div class="flex-grow-1">
                            <h6 class="mb-0">${post.reporter_name || 'Anonymous'}</h6>
                            <small class="text-muted">
                                <i class="fas fa-clock me-1"></i>${timeAgo}
                                <span class="mx-2">•</span>
                                <i class="fas fa-map-marker-alt me-1"></i>${post.address || 'Location not specified'}
                            </small>
                        </div>
                        <div class="dropdown">
                            <button class="btn btn-sm btn-outline-secondary" data-bs-toggle="dropdown">
                                <i class="fas fa-ellipsis-h"></i>
                            </button>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="#" onclick="reportPost(${post.id})">
                                    <i class="fas fa-flag me-2"></i>Report
                                </a></li>
                                <li><a class="dropdown-item" href="#" onclick="savePost(${post.id})">
                                    <i class="fas fa-bookmark me-2"></i>Save
                                </a></li>
                                <li><a class="dropdown-item" href="#" onclick="sharePost(${post.id})">
                                    <i class="fas fa-share me-2"></i>Share
                                </a></li>
                            </ul>
                        </div>
                    </div>

                    <!-- Post Content -->
                    <div class="post-content mb-3">
                        <h5 class="post-title">${post.title}</h5>
                        <p class="post-description">${post.description}</p>
                        
                        <!-- Category and Status Tags -->
                        <div class="mb-3">
                            <span class="badge bg-secondary me-2">
                                <i class="fas fa-tag me-1"></i>${this.formatCategory(post.category)}
                            </span>
                            <span class="badge ${statusClass} me-2">
                                ${this.formatStatus(post.status)}
                            </span>
                            ${post.priority === 'urgent' ? '<span class="badge bg-danger"><i class="fas fa-exclamation-triangle me-1"></i>Urgent</span>' : ''}
                            ${post.priority === 'high' ? '<span class="badge bg-warning"><i class="fas fa-exclamation me-1"></i>High Priority</span>' : ''}
                        </div>

                        <!-- Post Image -->
                        ${post.photo_urls ? `
                        <div class="post-image mb-3">
                            <img src="${post.photo_urls}" 
                                 class="img-fluid rounded hover-lift" 
                                 alt="Issue photo"
                                 style="max-height: 400px; width: 100%; object-fit: cover; cursor: pointer;"
                                 onclick="openImageModal('${post.photo_urls}')">
                        </div>
                        ` : ''}
                    </div>

                    <!-- Engagement Stats -->
                    <div class="engagement-stats mb-3">
                        <div class="d-flex justify-content-between text-muted small">
                            <span>
                                <i class="fas fa-thumbs-up text-primary me-1"></i>${post.upvotes || 0} people find this important
                            </span>
                            <span>
                                <i class="fas fa-comment text-info me-1"></i>${post.comments_count || 0} comments
                                <span class="mx-2">•</span>
                                <i class="fas fa-check text-success me-1"></i>${post.confirmations || 0} confirmations
                            </span>
                        </div>
                    </div>

                    <!-- Action Buttons -->
                    <div class="post-actions">
                        <div class="btn-group w-100" role="group">
                            <button class="btn btn-outline-primary btn-sm upvote-btn ${post.user_voted ? 'active' : ''}" 
                                    onclick="toggleUpvote(${post.id})">
                                <i class="fas fa-thumbs-up me-1"></i>Important (${post.upvotes || 0})
                            </button>
                            <button class="btn btn-outline-info btn-sm" onclick="toggleComments(${post.id})">
                                <i class="fas fa-comment me-1"></i>Comment
                            </button>
                            <button class="btn btn-outline-success btn-sm" onclick="sharePost(${post.id})">
                                <i class="fas fa-share me-1"></i>Share
                            </button>
                            <button class="btn btn-outline-warning btn-sm ${post.user_confirmed ? 'active' : ''}" 
                                    onclick="confirmIssue(${post.id})">
                                <i class="fas fa-check me-1"></i>Me Too! (${post.confirmations || 0})
                            </button>
                        </div>
                    </div>

                    <!-- Comments Section -->
                    <div class="comments-section mt-3 d-none" id="comments-${post.id}">
                        <hr>
                        <div class="comment-input mb-3">
                            <div class="d-flex">
                                <div class="profile-avatar me-2">
                                    <i class="fas fa-user-circle fa-lg text-primary"></i>
                                </div>
                                <div class="flex-grow-1">
                                    <textarea class="form-control" rows="2" placeholder="Write a comment..." 
                                              id="comment-text-${post.id}"></textarea>
                                    <div class="d-flex justify-content-end mt-2">
                                        <button class="btn btn-primary btn-sm" onclick="postComment(${post.id})">
                                            <i class="fas fa-paper-plane me-1"></i>Post
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="comments-list" id="comments-list-${post.id}">
                            <!-- Comments will be loaded here -->
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    bindPostEvents() {
        // Add any additional event bindings for posts
    }

    formatCategory(category) {
        const categoryMap = {
            'road_maintenance': '🛣️ Road Maintenance',
            'streetlight': '💡 Streetlight',
            'sanitation': '🗑️ Sanitation',
            'water_supply': '💧 Water Supply',
            'electricity': '⚡ Electricity',
            'traffic': '🚦 Traffic',
            'parks': '🌳 Parks',
            'other': '📋 Other'
        };
        return categoryMap[category] || category.replace('_', ' ').toUpperCase();
    }

    formatStatus(status) {
        return status.replace('_', ' ').toUpperCase();
    }

    getTimeAgo(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
        if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
        
        return date.toLocaleDateString();
    }

    getAuthHeaders() {
        const token = localStorage.getItem('access_token');
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }

    setupLocationServices() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.userLocation = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    };
                },
                (error) => console.log('Location access denied')
            );
        }
    }

    showNotification(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }
}

// Global functions for post interactions
async function toggleUpvote(postId) {
    try {
        const response = await fetch(`/social/issues/${postId}/vote`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...civicFeed.getAuthHeaders()
            },
            body: JSON.stringify({ vote_type: 'upvote' })
        });

        if (response.ok) {
            const button = document.querySelector(`[data-post-id="${postId}"] .upvote-btn`);
            button.classList.toggle('active');
            civicFeed.loadPosts(); // Refresh to get updated counts
        } else if (response.status === 401) {
            civicFeed.showNotification('Please login to vote', 'warning');
        }
    } catch (error) {
        console.error('Error voting:', error);
        civicFeed.showNotification('Error voting on post', 'error');
    }
}

async function confirmIssue(postId) {
    try {
        const response = await fetch(`/social/issues/${postId}/vote`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...civicFeed.getAuthHeaders()
            },
            body: JSON.stringify({ vote_type: 'confirm' })
        });

        if (response.ok) {
            const button = document.querySelector(`[data-post-id="${postId}"] .btn-outline-warning`);
            button.classList.toggle('active');
            civicFeed.loadPosts();
        } else if (response.status === 401) {
            civicFeed.showNotification('Please login to confirm', 'warning');
        }
    } catch (error) {
        console.error('Error confirming:', error);
        civicFeed.showNotification('Error confirming issue', 'error');
    }
}

function toggleComments(postId) {
    const commentsSection = document.getElementById(`comments-${postId}`);
    if (commentsSection.classList.contains('d-none')) {
        commentsSection.classList.remove('d-none');
        loadComments(postId);
    } else {
        commentsSection.classList.add('d-none');
    }
}

async function loadComments(postId) {
    try {
        const response = await fetch(`/social/issues/${postId}/comments`, {
            headers: civicFeed.getAuthHeaders()
        });

        if (response.ok) {
            const comments = await response.json();
            renderComments(postId, comments);
        }
    } catch (error) {
        console.error('Error loading comments:', error);
    }
}

function renderComments(postId, comments) {
    const commentsList = document.getElementById(`comments-list-${postId}`);
    commentsList.innerHTML = comments.map(comment => `
        <div class="comment-item">
            <div class="d-flex">
                <div class="profile-avatar me-2">
                    <i class="fas fa-user-circle text-primary"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="comment-author">${comment.user_name}</div>
                    <div class="comment-text">${comment.comment}</div>
                    <div class="comment-time">${civicFeed.getTimeAgo(new Date(comment.created_at))}</div>
                </div>
            </div>
        </div>
    `).join('');
}

async function postComment(postId) {
    const textarea = document.getElementById(`comment-text-${postId}`);
    const comment = textarea.value.trim();
    
    if (!comment) return;

    try {
        const response = await fetch(`/social/issues/${postId}/comment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...civicFeed.getAuthHeaders()
            },
            body: JSON.stringify({ comment })
        });

        if (response.ok) {
            textarea.value = '';
            loadComments(postId);
            civicFeed.showNotification('Comment posted!', 'success');
        } else if (response.status === 401) {
            civicFeed.showNotification('Please login to comment', 'warning');
        }
    } catch (error) {
        console.error('Error posting comment:', error);
        civicFeed.showNotification('Error posting comment', 'error');
    }
}

function sharePost(postId) {
    if (navigator.share) {
        navigator.share({
            title: 'Civic Issue Report',
            text: 'Check out this community issue report',
            url: `${window.location.origin}/issue/${postId}`
        });
    } else {
        // Fallback: copy to clipboard
        const url = `${window.location.origin}/issue/${postId}`;
        navigator.clipboard.writeText(url).then(() => {
            civicFeed.showNotification('Link copied to clipboard!', 'success');
        });
    }
}

function openReportModal() {
    const modal = new bootstrap.Modal(document.getElementById('reportModal'));
    modal.show();
}

function openImageModal(imageSrc) {
    const modal = new bootstrap.Modal(document.getElementById('imageModal'));
    document.getElementById('modalImage').src = imageSrc;
    modal.show();
}

function getCurrentLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
            document.getElementById('latitude').value = position.coords.latitude;
            document.getElementById('longitude').value = position.coords.longitude;
            
            // Reverse geocode to get address
            fetch(`https://api.opencagedata.com/geocode/v1/json?q=${position.coords.latitude}+${position.coords.longitude}&key=YOUR_API_KEY`)
                .then(response => response.json())
                .then(data => {
                    if (data.results && data.results[0]) {
                        document.querySelector('input[name="address"]').value = data.results[0].formatted;
                    }
                })
                .catch(error => console.log('Geocoding error:', error));
                
            civicFeed.showNotification('Location captured!', 'success');
        }, (error) => {
            civicFeed.showNotification('Could not get location', 'error');
        });
    }
}

async function submitReport() {
    const form = document.getElementById('reportForm');
    const formData = new FormData(form);
    
    // Add location data
    if (civicFeed.userLocation) {
        formData.append('latitude', civicFeed.userLocation.latitude);
        formData.append('longitude', civicFeed.userLocation.longitude);
    }

    try {
        const response = await fetch('/issues/with-photo', {
            method: 'POST',
            headers: civicFeed.getAuthHeaders(),
            body: formData
        });

        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('reportModal'));
            modal.hide();
            form.reset();
            civicFeed.loadPosts();
            civicFeed.showNotification('Issue reported successfully!', 'success');
        } else if (response.status === 401) {
            civicFeed.showNotification('Please login to report issues', 'warning');
        } else {
            civicFeed.showNotification('Error reporting issue', 'error');
        }
    } catch (error) {
        console.error('Error submitting report:', error);
        civicFeed.showNotification('Error submitting report', 'error');
    }
}

function loadMorePosts() {
    // Implement pagination
    civicFeed.showNotification('Loading more posts...', 'info');
    // Add pagination logic here
}

// Initialize the social feed
let civicFeed;
document.addEventListener('DOMContentLoaded', () => {
    civicFeed = new CivicSocialFeed();
});