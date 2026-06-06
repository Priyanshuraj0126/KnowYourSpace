// KnowYourSpace - Dashboard JavaScript
// Handles dashboard functionality: APOD, planets, events, weather, and stats

class Dashboard {
    constructor() {
        this.init();
    }

    init() {
        this.loadAPOD();
        this.loadPlanets();
        this.loadEvents();
        this.loadWeather();
        this.loadStats();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Refresh buttons and interactive elements
        const refreshButtons = document.querySelectorAll('.refresh-btn');
        refreshButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const section = btn.closest('section');
                if (section.classList.contains('apod-section')) {
                    this.loadAPOD();
                } else if (section.classList.contains('weather-section')) {
                    this.loadWeather();
                }
            });
        });

        // Planet card interactions
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('favorite-btn')) {
                this.toggleFavorite(e.target);
            }
        });
    }

    async loadAPOD() {
        const apodCard = document.getElementById('apod-card');
        if (!apodCard) return;

        try {
            const data = await KnowYourSpace.apiCall('/api/apod');
            this.displayAPOD(data, apodCard);
        } catch (error) {
            this.showAPODError(apodCard);
        }
    }

    displayAPOD(data, container) {
        const apodContent = `
            <div class="apod-content">
                <div class="apod-image-container">
                    <img src="${data.url}" alt="${data.title}" class="apod-image" loading="lazy">
                </div>
                <div class="apod-info">
                    <h3>${data.title}</h3>
                    <p>${data.explanation}</p>
                    <div class="apod-meta">
                        <span>${data.date}</span>
                        <span>${data.copyright || 'NASA'}</span>
                        <span>${data.media_type}</span>
                    </div>
                    <div class="apod-actions">
                        <button class="btn btn-outline favorite-btn" data-type="apod" data-id="${data.date}">
                            <i class="fas fa-heart"></i> Add to Favorites
                        </button>
                        <a href="${data.hdurl || data.url}" target="_blank" class="btn btn-primary">
                            <i class="fas fa-external-link-alt"></i> View Full Size
                        </a>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = apodContent;
        container.classList.add('fade-in');
    }

    showAPODError(container) {
        container.innerHTML = `
            <div class="apod-error">
                <i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: var(--error-color); margin-bottom: var(--spacing-md);"></i>
                <h3>Unable to Load APOD</h3>
                <p>We couldn't load today's Astronomy Picture of the Day. Please try again later.</p>
                <button class="btn btn-primary refresh-btn">
                    <i class="fas fa-redo"></i> Try Again
                </button>
            </div>
        `;
    }

    async loadPlanets() {
        const planetsGrid = document.getElementById('planets-grid');
        if (!planetsGrid) return;

        try {
            const planets = await KnowYourSpace.apiCall('/api/planets');
            this.displayPlanets(planets, planetsGrid);
        } catch (error) {
            this.showPlanetsError(planetsGrid);
        }
    }

    displayPlanets(planets, container) {
        const planetCards = Object.entries(planets).map(([key, planet]) => `
            <div class="planet-card" data-planet="${key}">
                <div class="planet-header">
                    <div class="planet-icon ${key}">
                        <i class="fas fa-globe"></i>
                    </div>
                    <div class="planet-info">
                        <h3>${planet.name}</h3>
                        <span class="planet-type">${planet.type}</span>
                    </div>
                </div>
                <div class="planet-details">
                    <div class="planet-detail">
                        <div class="planet-detail-label">Distance from Sun</div>
                        <div class="planet-detail-value">${planet.distance_from_sun}</div>
                    </div>
                    <div class="planet-detail">
                        <div class="planet-detail-label">Orbital Period</div>
                        <div class="planet-detail-value">${planet.orbital_period}</div>
                    </div>
                    <div class="planet-detail">
                        <div class="planet-detail-label">Surface Temp</div>
                        <div class="planet-detail-value">${planet.surface_temp}</div>
                    </div>
                    <div class="planet-detail">
                        <div class="planet-detail-label">Type</div>
                        <div class="planet-detail-value">${planet.type}</div>
                    </div>
                </div>
                <p class="planet-description">${planet.description}</p>
                <div class="planet-actions">
                    <button class="btn btn-outline favorite-btn" data-type="planet" data-id="${key}">
                        <i class="fas fa-heart"></i> Add to Favorites
                    </button>
                    <a href="/explore?planet=${key}" class="btn btn-primary">
                        <i class="fas fa-search"></i> Learn More
                    </a>
                </div>
            </div>
        `).join('');

        container.innerHTML = planetCards;
        
        // Add animation to each card
        const cards = container.querySelectorAll('.planet-card');
        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
            card.classList.add('fade-in');
        });
    }

    showPlanetsError(container) {
        container.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: var(--error-color); margin-bottom: var(--spacing-md);"></i>
                <h3>Unable to Load Planets</h3>
                <p>We couldn't load the planet information. Please try again later.</p>
            </div>
        `;
    }

    async loadEvents() {
        const eventsGrid = document.getElementById('events-grid');
        if (!eventsGrid) return;

        try {
            const events = await KnowYourSpace.apiCall('/api/astronomical-events');
            this.displayEvents(events, eventsGrid);
        } catch (error) {
            this.showEventsError(eventsGrid);
        }
    }

    displayEvents(events, container) {
        const eventCards = events.map(event => `
            <div class="event-card">
                <div class="event-header">
                    <div class="event-title">
                        <h3>${event.name}</h3>
                        <span class="event-type ${event.type}">${event.type.replace('_', ' ')}</span>
                    </div>
                    <div class="event-date">${KnowYourSpace.formatDate(event.date)}</div>
                </div>
                <p class="event-description">${event.description}</p>
                <div class="event-viewing">
                    <div class="event-viewing-label">Best Viewing</div>
                    <div class="event-viewing-info">${event.best_viewing}</div>
                </div>
                <div class="event-actions" style="margin-top: var(--spacing-lg);">
                    <button class="btn btn-outline favorite-btn" data-type="event" data-id="${event.name}">
                        <i class="fas fa-heart"></i> Add to Favorites
                    </button>
                    <button class="btn btn-primary" onclick="this.setReminder('${event.name}', '${event.date}')">
                        <i class="fas fa-bell"></i> Set Reminder
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = eventCards;
        
        // Add animation to each card
        const cards = container.querySelectorAll('.event-card');
        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
            card.classList.add('fade-in');
        });
    }

    showEventsError(container) {
        container.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: var(--error-color); margin-bottom: var(--spacing-md);"></i>
                <h3>Unable to Load Events</h3>
                <p>We couldn't load the astronomical events. Please try again later.</p>
            </div>
        `;
    }

    async loadWeather() {
        const weatherCard = document.getElementById('weather-card');
        if (!weatherCard) return;

        try {
            // Get user's location or use default
            const position = await this.getCurrentPosition();
            const weather = await KnowYourSpace.apiCall(`/api/weather?lat=${position.lat}&lon=${position.lon}`);
            this.displayWeather(weather, weatherCard);
        } catch (error) {
            // Use default coordinates if location access fails
            try {
                const weather = await KnowYourSpace.apiCall('/api/weather');
                this.displayWeather(weather, weatherCard);
            } catch (fallbackError) {
                this.showWeatherError(weatherCard);
            }
        }
    }

    getCurrentPosition() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation not supported'));
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve({
                        lat: position.coords.latitude,
                        lon: position.coords.longitude
                    });
                },
                (error) => {
                    reject(error);
                },
                { timeout: 10000, enableHighAccuracy: false }
            );
        });
    }

    displayWeather(data, container) {
        const current = data.hourly;
        const daily = data.daily;
        
        // Get current hour index
        const now = new Date();
        const currentHour = now.getHours();
        const currentIndex = currentHour;

        const weatherContent = `
            <div class="weather-content">
                <div class="weather-current">
                    <div class="weather-icon">
                        <i class="fas fa-${this.getWeatherIcon(current.visibility[currentIndex], current.cloud_cover[currentIndex])}"></i>
                    </div>
                    <div class="weather-temp">${Math.round(current.temperature_2m[currentIndex])}°C</div>
                    <div class="weather-description">${this.getWeatherDescription(current.visibility[currentIndex], current.cloud_cover[currentIndex])}</div>
                    <div class="weather-details">
                        <div class="weather-detail">
                            <div class="weather-detail-label">Humidity</div>
                            <div class="weather-detail-value">${Math.round(current.relative_humidity_2m[currentIndex])}%</div>
                        </div>
                        <div class="weather-detail">
                            <div class="weather-detail-label">Visibility</div>
                            <div class="weather-detail-value">${Math.round(current.visibility[currentIndex] / 1000)} km</div>
                        </div>
                        <div class="weather-detail">
                            <div class="weather-detail-label">Cloud Cover</div>
                            <div class="weather-detail-value">${Math.round(current.cloud_cover[currentIndex])}%</div>
                        </div>
                        <div class="weather-detail">
                            <div class="weather-detail-label">Precipitation</div>
                            <div class="weather-detail-value">${Math.round(daily.precipitation_probability_max[0])}%</div>
                        </div>
                    </div>
                </div>
                <div class="weather-forecast">
                    <h4 style="margin-bottom: var(--spacing-md); color: var(--space-white);">3-Day Forecast</h4>
                    ${this.generateForecastItems(daily)}
                </div>
            </div>
        `;

        container.innerHTML = weatherContent;
        container.classList.add('fade-in');
    }

    getWeatherIcon(visibility, cloudCover) {
        if (visibility < 5000) return 'cloud-fog';
        if (cloudCover > 80) return 'cloud';
        if (cloudCover > 50) return 'cloud-sun';
        return 'sun';
    }

    getWeatherDescription(visibility, cloudCover) {
        if (visibility < 5000) return 'Poor visibility - not ideal for stargazing';
        if (cloudCover > 80) return 'Very cloudy - limited stargazing';
        if (cloudCover > 50) return 'Partly cloudy - moderate stargazing';
        return 'Clear skies - excellent for stargazing!';
    }

    generateForecastItems(daily) {
        const days = ['Today', 'Tomorrow', 'Day After'];
        return days.map((day, index) => `
            <div class="forecast-item">
                <div class="forecast-day">${day}</div>
                <div class="forecast-temp">
                    ${Math.round(daily.temperature_2m_max[index])}° / ${Math.round(daily.temperature_2m_min[index])}°
                </div>
                <div class="forecast-icon">
                    <i class="fas fa-${daily.precipitation_probability_max[index] > 50 ? 'cloud-rain' : 'sun'}"></i>
                </div>
            </div>
        `).join('');
    }

    showWeatherError(container) {
        container.innerHTML = `
            <div class="weather-error">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: var(--error-color); margin-bottom: var(--spacing-md);"></i>
                <h3>Unable to Load Weather</h3>
                <p>We couldn't load the weather information. Please try again later.</p>
                <button class="btn btn-primary refresh-btn">
                    <i class="fas fa-redo"></i> Try Again
                </button>
            </div>
        `;
    }

    async loadStats() {
        try {
            // Load NEO count
            const neos = await KnowYourSpace.apiCall('/api/neos');
            const neoCount = neos.element_count || 0;
            this.updateStat('neo-count', neoCount);

            // Load events count
            const events = await KnowYourSpace.apiCall('/api/astronomical-events');
            this.updateStat('event-count', events.length);

        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    updateStat(statId, value) {
        const statElement = document.getElementById(statId);
        if (statElement) {
            statElement.textContent = KnowYourSpace.formatNumber(value);
        }
    }

    async toggleFavorite(button) {
        const type = button.dataset.type;
        const id = button.dataset.id;
        
        try {
            if (button.classList.contains('favorited')) {
                // Remove from favorites
                await KnowYourSpace.apiCall(`/api/user/favorites?id=${id}`, { method: 'DELETE' });
                button.classList.remove('favorited');
                button.innerHTML = '<i class="fas fa-heart"></i> Add to Favorites';
                KnowYourSpace.showNotification('Removed from favorites', 'success');
            } else {
                // Add to favorites
                await KnowYourSpace.apiCall('/api/user/favorites', {
                    method: 'POST',
                    body: JSON.stringify({ type, id, name: id })
                });
                button.classList.add('favorited');
                button.innerHTML = '<i class="fas fa-heart"></i> Favorited';
                KnowYourSpace.showNotification('Added to favorites', 'success');
            }
        } catch (error) {
            KnowYourSpace.showNotification('Unable to update favorites', 'error');
        }
    }

    setReminder(eventName, eventDate) {
        if ('Notification' in window && Notification.permission === 'granted') {
            // Calculate time until event
            const eventTime = new Date(eventDate);
            const now = new Date();
            const timeUntil = eventTime.getTime() - now.getTime();
            
            if (timeUntil > 0) {
                // Set notification for 1 hour before event
                const reminderTime = timeUntil - (60 * 60 * 1000);
                
                setTimeout(() => {
                    new Notification('Astronomical Event Reminder', {
                        body: `${eventName} is happening in 1 hour!`,
                        icon: '/static/images/notification-icon.png'
                    });
                }, reminderTime);
                
                KnowYourSpace.showNotification('Reminder set for 1 hour before the event', 'success');
            } else {
                KnowYourSpace.showNotification('This event has already passed', 'info');
            }
        } else if ('Notification' in window && Notification.permission !== 'denied') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    this.setReminder(eventName, eventDate);
                }
            });
        } else {
            KnowYourSpace.showNotification('Please enable notifications to set reminders', 'info');
        }
    }

    // Utility methods
    static formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.main-content')) {
        window.dashboard = new Dashboard();
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Dashboard;
}
