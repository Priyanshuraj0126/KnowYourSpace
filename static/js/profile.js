// Profile Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize profile page
    initializeProfile();
    
    // Set up tab functionality
    setupTabs();
    
    // Set up form submissions
    setupForms();
    
    // Log page visit activity
    logActivity('page_visit', { page: 'profile' });
});

// Global variables
let currentProfile = null;
let currentStats = null;

// Initialize profile page
async function initializeProfile() {
    try {
        // Load profile data
        await loadProfileData();
        
        // Load profile stats
        await loadProfileStats();
        
        // Load initial tab content
        await loadTabContent('overview');
        
    } catch (error) {
        console.error('Failed to initialize profile:', error);
        showError('Failed to load profile data. Please refresh the page.');
    }
}

// Load profile data from API
async function loadProfileData() {
    try {
        const response = await fetch('/api/profile?user_id=default_user');
        const data = await response.json();
        
        if (data.success) {
            currentProfile = data.profile;
            if (data.preferences && !currentProfile.preferences) {
                currentProfile.preferences = data.preferences;
            }
            displayProfileData();
        } else {
            throw new Error(data.error || 'Failed to load profile');
        }
    } catch (error) {
        console.error('Error loading profile:', error);
        throw error;
    }
}

// Load profile stats from API
async function loadProfileStats() {
    try {
        const response = await fetch('/api/profile/stats?user_id=default_user');
        const data = await response.json();
        
        if (data.success) {
            currentStats = data.stats;
            displayProfileStats();
        } else {
            throw new Error(data.error || 'Failed to load stats');
        }
    } catch (error) {
        console.error('Error loading stats:', error);
        throw error;
    }
}

// Display profile data in UI
function displayProfileData() {
    if (!currentProfile) return;
    
    // Update profile header
    document.getElementById('profile-username').textContent = currentProfile.username;
    document.getElementById('profile-email').textContent = currentProfile.email;
    document.getElementById('profile-location').textContent = currentProfile.location;
    
    const memberDate = new Date(currentProfile.member_since);
    document.getElementById('profile-member-since').textContent = `Member since ${memberDate.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long' 
    })}`;
    
    // Update form fields
    document.getElementById('edit-username').value = currentProfile.username;
    document.getElementById('edit-email').value = currentProfile.email;
    document.getElementById('edit-location').value = currentProfile.location;
    
    // Update settings
    if (currentProfile.preferences) {
        const themeSelect = document.getElementById('theme-select');
        const unitsSelect = document.getElementById('units-select');
        const notificationsToggle = document.getElementById('notifications-toggle');
        
        if (themeSelect) themeSelect.value = currentProfile.preferences.theme || 'dark';
        if (unitsSelect) unitsSelect.value = currentProfile.preferences.units || 'metric';
        if (notificationsToggle) notificationsToggle.checked = currentProfile.preferences.notifications || false;
    }
}

// Display profile stats in UI
function displayProfileStats() {
    if (!currentStats) return;
    
    // Update stat cards
    document.getElementById('stats-explored').textContent = currentStats.space_objects_explored;
    document.getElementById('stats-events').textContent = currentStats.events_tracked;
    document.getElementById('stats-ai-questions').textContent = currentStats.ai_questions_asked;
    document.getElementById('stats-favorites').textContent = currentStats.total_favorites;
    
    // Update quick stats
    document.getElementById('member-days').textContent = `${currentStats.member_days} days`;
    document.getElementById('pages-visited').textContent = currentStats.pages_visited;
    document.getElementById('total-searches').textContent = currentStats.total_searches;
}

// Set up tab functionality
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;
            
            // Update active tab button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Update active tab pane
            tabPanes.forEach(pane => pane.classList.remove('active'));
            document.getElementById(`${targetTab}-tab`).classList.add('active');
            
            // Load tab content
            loadTabContent(targetTab);
        });
    });
}

// Load content for specific tab
async function loadTabContent(tabName) {
    try {
        switch (tabName) {
            case 'overview':
                await loadOverviewContent();
                break;
            case 'favorites':
                await loadFavoritesContent();
                break;
            case 'activity':
                await loadActivityContent();
                break;
            case 'achievements':
                await loadAchievementsContent();
                break;
            case 'search-history':
                await loadSearchHistoryContent();
                break;
        }
    } catch (error) {
        console.error(`Error loading ${tabName} content:`, error);
        showError(`Failed to load ${tabName} content. Please try again.`);
    }
}

// Load overview tab content
async function loadOverviewContent() {
    try {
        // Load recent activities
        const response = await fetch('/api/profile/activity?user_id=default_user&limit=5');
        const data = await response.json();
        
        if (data.success) {
            displayRecentActivities(data.activities);
        }
    } catch (error) {
        console.error('Error loading overview content:', error);
    }
}

// Load favorites tab content
async function loadFavoritesContent() {
    try {
        const response = await fetch('/api/profile/favorites?user_id=default_user');
        const data = await response.json();
        
        if (data.success) {
            displayFavorites(data.favorites);
        }
    } catch (error) {
        console.error('Error loading favorites:', error);
        showError('Failed to load favorites. Please try again.');
    }
}

// Load activity tab content
async function loadActivityContent() {
    try {
        const response = await fetch('/api/profile/activity?user_id=default_user&limit=50');
        const data = await response.json();
        
        if (data.success) {
            displayActivities(data.activities);
        }
    } catch (error) {
        console.error('Error loading activities:', error);
        showError('Failed to load activities. Please try again.');
    }
}

// Load achievements tab content
async function loadAchievementsContent() {
    try {
        const response = await fetch('/api/profile/achievements?user_id=default_user');
        const data = await response.json();
        
        if (data.success) {
            displayAchievements(data.achievements);
            document.getElementById('achievements-count').textContent = data.achievements.length;
            document.getElementById('total-achievements').textContent = '5'; // Total possible achievements
        }
    } catch (error) {
        console.error('Error loading achievements:', error);
        showError('Failed to load achievements. Please try again.');
    }
}

// Load search history tab content
async function loadSearchHistoryContent() {
    try {
        const response = await fetch('/api/profile/search-history?user_id=default_user&limit=50');
        const data = await response.json();
        
        if (data.success) {
            displaySearchHistory(data.searches);
        }
    } catch (error) {
        console.error('Error loading search history:', error);
        showError('Failed to load search history. Please try again.');
    }
}

// Display recent activities
function displayRecentActivities(activities) {
    const container = document.getElementById('recent-activities');
    
    if (!activities || activities.length === 0) {
        container.innerHTML = '<p class="no-data">No recent activity</p>';
        return;
    }
    
    const activitiesHTML = activities.map(activity => {
        const timestamp = new Date(activity.timestamp);
        const timeAgo = getTimeAgo(timestamp);
        
        return `
            <div class="activity-item">
                <div class="activity-icon">
                    <i class="fas ${getActivityIcon(activity.type)}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-text">${getActivityText(activity)}</div>
                    <div class="activity-time">${timeAgo}</div>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = activitiesHTML;
}

// Display favorites
function displayFavorites(favorites) {
    const container = document.getElementById('favorites-grid');
    
    if (!favorites || favorites.length === 0) {
        container.innerHTML = '<p class="no-data">No favorites yet. Start exploring to add some!</p>';
        return;
    }
    
    const favoritesHTML = favorites.map(favorite => {
        const addedDate = new Date(favorite.added_at);
        
        return `
            <div class="favorite-item">
                <div class="favorite-header">
                    <h4>${favorite.title || 'Untitled'}</h4>
                    <button class="remove-favorite-btn" onclick="removeFavorite('${favorite.id}')">
                        <i class="fas fa-heart-broken"></i>
                    </button>
                </div>
                <div class="favorite-type">${getFavoriteTypeLabel(favorite.type)}</div>
                <div class="favorite-description">${favorite.description || 'No description'}</div>
                <div class="favorite-date">Added ${addedDate.toLocaleDateString()}</div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = favoritesHTML;
}

// Display activities
function displayActivities(activities) {
    const container = document.getElementById('activity-timeline');
    
    if (!activities || activities.length === 0) {
        container.innerHTML = '<p class="no-data">No activities yet</p>';
        return;
    }
    
    const activitiesHTML = activities.map(activity => {
        const timestamp = new Date(activity.timestamp);
        const timeAgo = getTimeAgo(timestamp);
        
        return `
            <div class="timeline-item" data-type="${activity.type}">
                <div class="timeline-icon">
                    <i class="fas ${getActivityIcon(activity.type)}"></i>
                </div>
                <div class="timeline-content">
                    <div class="timeline-text">${getActivityText(activity)}</div>
                    <div class="timeline-time">${timestamp.toLocaleString()}</div>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = activitiesHTML;
}

// Display achievements
function displayAchievements(achievements) {
    const container = document.getElementById('achievements-grid');
    
    if (!achievements || achievements.length === 0) {
        container.innerHTML = '<p class="no-data">No achievements unlocked yet. Keep exploring to earn them!</p>';
        return;
    }
    
    const achievementsHTML = achievements.map(achievement => {
        const unlockedDate = new Date(achievement.unlocked_at);
        
        return `
            <div class="achievement-item unlocked">
                <div class="achievement-icon">
                    <i class="${achievement.icon}"></i>
                </div>
                <div class="achievement-content">
                    <h4>${achievement.name}</h4>
                    <p>${achievement.description}</p>
                    <div class="achievement-date">Unlocked ${unlockedDate.toLocaleDateString()}</div>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = achievementsHTML;
}

// Display search history
function displaySearchHistory(searches) {
    const container = document.getElementById('search-history-list');
    
    if (!searches || searches.length === 0) {
        container.innerHTML = '<p class="no-data">No search history yet</p>';
        return;
    }
    
    const searchesHTML = searches.map(search => {
        const timestamp = new Date(search.timestamp);
        const timeAgo = getTimeAgo(timestamp);
        
        return `
            <div class="search-history-item">
                <div class="search-query">${search.query}</div>
                <div class="search-meta">
                    <span class="search-type">${search.search_type}</span>
                    <span class="search-time">${timeAgo}</span>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = searchesHTML;
}

// Filter activities by type
function filterActivities() {
    const filterValue = document.getElementById('activity-filter').value;
    const timelineItems = document.querySelectorAll('.timeline-item');
    
    timelineItems.forEach(item => {
        if (filterValue === 'all' || item.dataset.type === filterValue) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// Set up form submissions
function setupForms() {
    // Edit profile form
    const editProfileForm = document.getElementById('edit-profile-form');
    if (editProfileForm) {
        editProfileForm.addEventListener('submit', handleEditProfile);
    }
    
    // Add favorite form
    const addFavoriteForm = document.getElementById('add-favorite-form');
    if (addFavoriteForm) {
        addFavoriteForm.addEventListener('submit', handleAddFavorite);
    }
}

// Handle edit profile form submission
async function handleEditProfile(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const updateData = {
        user_id: 'default_user',
        username: formData.get('username'),
        email: formData.get('email'),
        location: formData.get('location')
    };
    
    try {
        const response = await fetch('/api/profile/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updateData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Reload profile data
            await loadProfileData();
            closeEditModal();
            showSuccess('Profile updated successfully!');
        } else {
            throw new Error(data.error || 'Failed to update profile');
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        showError('Failed to update profile. Please try again.');
    }
}

// Handle add favorite form submission
async function handleAddFavorite(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const favoriteData = {
        user_id: 'default_user',
        item: {
            id: `fav_${Date.now()}`,
            title: formData.get('title'),
            type: formData.get('type'),
            description: formData.get('description')
        }
    };
    
    try {
        const response = await fetch('/api/profile/favorites/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(favoriteData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Reload favorites
            await loadFavoritesContent();
            closeAddFavoriteModal();
            showSuccess('Added to favorites!');
            
            // Reset form
            event.target.reset();
        } else {
            throw new Error(data.error || 'Failed to add favorite');
        }
    } catch (error) {
        console.error('Error adding favorite:', error);
        showError('Failed to add favorite. Please try again.');
    }
}

// Remove favorite
async function removeFavorite(itemId) {
    try {
        const response = await fetch('/api/profile/favorites/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: 'default_user',
                item_id: itemId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Reload favorites
            await loadFavoritesContent();
            showSuccess('Removed from favorites');
        } else {
            throw new Error(data.error || 'Failed to remove favorite');
        }
    } catch (error) {
        console.error('Error removing favorite:', error);
        showError('Failed to remove favorite. Please try again.');
    }
}

// Clear search history
async function clearSearchHistory() {
    if (!confirm('Are you sure you want to clear your search history? This action cannot be undone.')) {
        return;
    }
    
    try {
        // In a real app, you'd have an API endpoint to clear history
        // For now, we'll just reload the current user's data
        await loadSearchHistoryContent();
        showSuccess('Search history cleared');
    } catch (error) {
        console.error('Error clearing search history:', error);
        showError('Failed to clear search history. Please try again.');
    }
}

// Update user setting
async function updateSetting(setting, value) {
    try {
        const response = await fetch('/api/profile/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: 'default_user',
                preferences: {
                    [setting]: value
                }
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('Setting updated successfully!');
        } else {
            throw new Error(data.error || 'Failed to update setting');
        }
    } catch (error) {
        console.error('Error updating setting:', error);
        showError('Failed to update setting. Please try again.');
    }
}

// Modal functions
function openEditModal() {
    document.getElementById('edit-profile-modal').style.display = 'flex';
}

function closeEditModal() {
    document.getElementById('edit-profile-modal').style.display = 'none';
}

function openAddFavoriteModal() {
    document.getElementById('add-favorite-modal').style.display = 'flex';
}

function closeAddFavoriteModal() {
    document.getElementById('add-favorite-modal').style.display = 'none';
}

function openSettingsModal() {
    document.getElementById('settings-modal').style.display = 'flex';
}

function closeSettingsModal() {
    document.getElementById('settings-modal').style.display = 'none';
}

// Close modals when clicking outside
window.addEventListener('click', function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});

// Utility functions
function getTimeAgo(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)}d ago`;
    return date.toLocaleDateString();
}

function getActivityIcon(activityType) {
    const iconMap = {
        'page_visit': 'fa-eye',
        'ai_search': 'fa-brain',
        'event_view': 'fa-calendar-star',
        'object_explore': 'fa-rocket',
        'favorite_added': 'fa-heart',
        'achievement_unlocked': 'fa-trophy'
    };
    return iconMap[activityType] || 'fa-circle';
}

function getActivityText(activity) {
    const textMap = {
        'page_visit': `Visited ${activity.details.page || 'a page'}`,
        'ai_search': `Asked AI: "${activity.details.query || 'a question'}"`,
        'event_view': `Viewed ${activity.details.event || 'an astronomical event'}`,
        'object_explore': `Explored ${activity.details.object || 'a space object'}`,
        'favorite_added': `Added ${activity.details.item || 'an item'} to favorites`,
        'achievement_unlocked': `Unlocked achievement: ${activity.details.achievement || 'Unknown'}`
    };
    return textMap[activity.type] || 'Performed an action';
}

function getFavoriteTypeLabel(type) {
    const labelMap = {
        'space_object': 'Space Object',
        'event': 'Astronomical Event',
        'discovery': 'Discovery',
        'mission': 'Space Mission'
    };
    return labelMap[type] || type;
}

// Log user activity
async function logActivity(activityType, details = {}) {
    try {
        await fetch('/api/profile/activity/log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: 'default_user',
                type: activityType,
                details: details
            })
        });
    } catch (error) {
        console.error('Error logging activity:', error);
    }
}

// Show success message
function showSuccess(message) {
    // You can implement a toast notification system here
    alert(message); // Simple alert for now
}

// Show error message
function showError(message) {
    // You can implement a toast notification system here
    alert('Error: ' + message); // Simple alert for now
}
