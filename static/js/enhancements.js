// KnowYourSpace - Enhanced JavaScript
// Adds amazing interactive animations and effects

class EnhancedUI {
    constructor() {
        this.init();
    }

    init() {
        this.setupParallaxEffects();
        this.setupScrollAnimations();
        this.setupHoverEffects();
        this.setupTypingEffect();
        this.setupParticleSystem();
        this.setupSmoothScrolling();
        this.setupLoadingAnimations();
        this.setupInteractiveCards();
    }

    setupParallaxEffects() {
        // Parallax effect for hero section
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const parallaxElements = document.querySelectorAll('.hero, .planet-orbit');
            
            parallaxElements.forEach(element => {
                const speed = element.dataset.speed || 0.5;
                element.style.transform = `translateY(${scrolled * speed}px)`;
            });
        });
    }

    setupScrollAnimations() {
        // Enhanced scroll-triggered animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    
                    // Add staggered animation classes
                    if (element.classList.contains('stats-grid')) {
                        this.animateStaggeredChildren(element.children, 'fade-in-up', 100);
                    } else if (element.classList.contains('planets-grid')) {
                        this.animateStaggeredChildren(element.children, 'slide-in-left', 150);
                    } else if (element.classList.contains('events-grid')) {
                        this.animateStaggeredChildren(element.children, 'slide-in-right', 150);
                    } else {
                        element.classList.add('fade-in');
                    }
                    
                    observer.unobserve(element);
                }
            });
        }, observerOptions);

        // Observe elements for animation
        const animateElements = document.querySelectorAll('.card, .stat-card, .planet-card, .event-card, .weather-card, .stats-grid, .planets-grid, .events-grid');
        animateElements.forEach(el => observer.observe(el));
    }

    animateStaggeredChildren(children, animationClass, delay) {
        Array.from(children).forEach((child, index) => {
            setTimeout(() => {
                child.classList.add(animationClass);
            }, index * delay);
        });
    }

    setupHoverEffects() {
        // Enhanced hover effects for cards
        const cards = document.querySelectorAll('.card, .apod-card, .stat-card, .planet-card, .event-card, .weather-card');
        
        cards.forEach(card => {
            card.addEventListener('mouseenter', (e) => {
                this.addHoverEffect(card);
            });
            
            card.addEventListener('mouseleave', (e) => {
                this.removeHoverEffect(card);
            });
        });

        // Enhanced button hover effects
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(btn => {
            btn.addEventListener('mouseenter', (e) => {
                this.addButtonHoverEffect(btn);
            });
            
            btn.addEventListener('mouseleave', (e) => {
                this.removeButtonHoverEffect(btn);
            });
        });
    }

    addHoverEffect(card) {
        card.style.transform = 'translateY(-8px) scale(1.02)';
        card.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.3)';
        
        // Add floating animation
        card.classList.add('float');
        
        // Add glow effect
        card.style.borderColor = 'rgba(6, 182, 212, 0.5)';
        card.style.boxShadow = '0 0 30px rgba(6, 182, 212, 0.3)';
    }

    removeHoverEffect(card) {
        card.style.transform = '';
        card.style.boxShadow = '';
        card.classList.remove('float');
        card.style.borderColor = '';
        card.style.boxShadow = '';
    }

    addButtonHoverEffect(btn) {
        btn.style.transform = 'translateY(-3px) scale(1.02)';
        btn.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.3)';
        
        // Add pulse effect
        btn.classList.add('pulse');
    }

    removeButtonHoverEffect(btn) {
        btn.style.transform = '';
        btn.style.boxShadow = '';
        btn.classList.remove('pulse');
    }

    setupTypingEffect() {
        // Typing effect for hero title
        const heroTitle = document.querySelector('.hero-title');
        if (heroTitle) {
            const text = heroTitle.textContent;
            heroTitle.textContent = '';
            heroTitle.style.borderRight = '2px solid #06b6d4';
            
            let i = 0;
            const typeWriter = () => {
                if (i < text.length) {
                    heroTitle.textContent += text.charAt(i);
                    i++;
                    setTimeout(typeWriter, 100);
                } else {
                    // Remove cursor after typing is complete
                    setTimeout(() => {
                        heroTitle.style.borderRight = 'none';
                    }, 1000);
                }
            };
            
            // Start typing effect after a delay
            setTimeout(typeWriter, 1000);
        }
    }

    setupParticleSystem() {
        // Create floating particles in the background
        const hero = document.querySelector('.hero');
        if (hero) {
            for (let i = 0; i < 20; i++) {
                this.createParticle(hero);
            }
        }
    }

    createParticle(container) {
        const particle = document.createElement('div');
        particle.className = 'floating-particle';
        particle.style.cssText = `
            position: absolute;
            width: 2px;
            height: 2px;
            background: rgba(6, 182, 212, 0.6);
            border-radius: 50%;
            pointer-events: none;
            animation: float 6s ease-in-out infinite;
            animation-delay: ${Math.random() * 6}s;
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
        `;
        
        container.appendChild(particle);
    }

    setupSmoothScrolling() {
        // Enhanced smooth scrolling with easing
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    setupLoadingAnimations() {
        // Enhanced loading animations
        const loadingElements = document.querySelectorAll('.spinner, .loading');
        
        loadingElements.forEach(element => {
            // Add shimmer effect
            element.classList.add('shimmer');
            
            // Add pulse effect
            element.classList.add('pulse');
        });
    }

    setupInteractiveCards() {
        // Make cards more interactive
        const cards = document.querySelectorAll('.card, .apod-card, .stat-card, .planet-card, .event-card, .weather-card');
        
        cards.forEach(card => {
            // Add tilt effect on mouse move
            card.addEventListener('mousemove', (e) => {
                this.addTiltEffect(card, e);
            });
            
            // Reset tilt on mouse leave
            card.addEventListener('mouseleave', (e) => {
                this.resetTiltEffect(card);
            });
            
            // Add click ripple effect
            card.addEventListener('click', (e) => {
                this.addRippleEffect(card, e);
            });
        });
    }

    addTiltEffect(card, event) {
        const rect = card.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 10;
        const rotateY = (centerX - x) / 10;
        
        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
    }

    resetTiltEffect(card) {
        card.style.transform = '';
    }

    addRippleEffect(card, event) {
        const ripple = document.createElement('span');
        const rect = card.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: radial-gradient(circle, rgba(6, 182, 212, 0.3) 0%, transparent 70%);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s ease-out;
            pointer-events: none;
        `;
        
        card.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    // Utility method to add CSS animations
    static addAnimation(element, animationName, duration = '0.6s') {
        element.style.animation = `${animationName} ${duration} ease-out`;
    }

    // Utility method to remove animations
    static removeAnimation(element) {
        element.style.animation = '';
    }

    // Method to create floating elements
    static createFloatingElement(container, className = 'floating-element') {
        const element = document.createElement('div');
        element.className = className;
        element.style.cssText = `
            position: absolute;
            width: 4px;
            height: 4px;
            background: rgba(6, 182, 212, 0.4);
            border-radius: 50%;
            pointer-events: none;
            animation: float 8s ease-in-out infinite;
            animation-delay: ${Math.random() * 8}s;
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
        `;
        
        container.appendChild(element);
        return element;
    }
}

// Enhanced notification system
class EnhancedNotifications {
    static show(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `enhanced-notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close">&times;</button>
        `;
        
        // Add enhanced styling
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            padding: 16px 20px;
            color: white;
            z-index: 10000;
            transform: translateX(400px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Close button functionality
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            this.hide(notification);
        });
        
        // Auto hide
        setTimeout(() => {
            this.hide(notification);
        }, duration);
    }

    static hide(notification) {
        notification.style.transform = 'translateX(400px)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    static getIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
}

// Initialize enhanced UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize enhanced UI
    window.enhancedUI = new EnhancedUI();
    
    // Add enhanced notification system to global scope
    window.showNotification = EnhancedNotifications.show;
    
    // Add some floating particles to the page
    setTimeout(() => {
        const containers = document.querySelectorAll('.hero, .main-content');
        containers.forEach(container => {
            for (let i = 0; i < 5; i++) {
                EnhancedUI.createFloatingElement(container);
            }
        });
    }, 2000);
});

// Add CSS for enhanced notifications
const enhancedStyles = document.createElement('style');
enhancedStyles.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .enhanced-notification {
        font-family: 'Roboto', sans-serif;
        font-size: 14px;
        line-height: 1.4;
    }
    
    .enhanced-notification .notification-content {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .enhanced-notification i {
        font-size: 18px;
        color: #06b6d4;
    }
    
    .enhanced-notification .notification-close {
        background: none;
        border: none;
        color: rgba(255, 255, 255, 0.6);
        font-size: 20px;
        cursor: pointer;
        padding: 0;
        margin-left: 16px;
        transition: color 0.3s ease;
    }
    
    .enhanced-notification .notification-close:hover {
        color: white;
    }
    
    .notification-success i { color: #10b981; }
    .notification-error i { color: #ef4444; }
    .notification-warning i { color: #f59e0b; }
    .notification-info i { color: #06b6d4; }
`;

document.head.appendChild(enhancedStyles);
