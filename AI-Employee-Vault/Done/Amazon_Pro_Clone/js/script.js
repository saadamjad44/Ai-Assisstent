// Cart functionality
let cart = [];
let cartCount = 0;

// Update cart count display
function updateCartCount() {
    const cartBadge = document.querySelector('.cart-badge');
    if (cartBadge) {
        cartBadge.textContent = cartCount;
        cartBadge.style.display = cartCount > 0 ? 'flex' : 'none';
    }
}

// Add to cart functionality
function addToCart(productElement) {
    cartCount++;
    updateCartCount();
    
    // Visual feedback
    const button = productElement.querySelector('.add-to-cart-btn');
    const originalText = button.textContent;
    button.textContent = 'Added!';
    
    setTimeout(() => {
        button.textContent = originalText;
    }, 1000);
}

// Search functionality
function setupSearch() {
    const searchInput = document.querySelector('.search-input');
    const searchButton = document.querySelector('.search-button');
    
    if (searchInput && searchButton) {
        searchButton.addEventListener('click', performSearch);
        
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
}

function performSearch() {
    const searchTerm = document.querySelector('.search-input').value.trim();
    if (searchTerm) {
        alert(`Searching for: ${searchTerm}`);
        // In a real implementation, this would redirect to search results
    }
}

// Initialize product cards with event listeners
function initializeProductCards() {
    const productCards = document.querySelectorAll('.product-card');
    
    productCards.forEach(card => {
        const addToCartBtn = card.querySelector('.add-to-cart-btn');
        if (addToCartBtn) {
            addToCartBtn.addEventListener('click', () => {
                addToCart(card);
            });
        }
    });
}

// Initialize category cards
function initializeCategoryCards() {
    const categoryCards = document.querySelectorAll('.category-card');
    
    categoryCards.forEach(card => {
        const shopNowBtn = card.querySelector('.shop-now-btn');
        if (shopNowBtn) {
            shopNowBtn.addEventListener('click', function(e) {
                e.preventDefault();
                const category = card.querySelector('h3').textContent;
                alert(`Navigating to ${category} category`);
            });
        }
    });
}

// CTA button functionality
function setupCTAButton() {
    const ctaButton = document.querySelector('.cta-button');
    if (ctaButton) {
        ctaButton.addEventListener('click', function() {
            alert('Exploring featured deals!');
        });
    }
}

// Sub-navigation functionality
function setupSubNavigation() {
    const subNavLinks = document.querySelectorAll('.sub-nav-link');
    
    subNavLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.textContent.trim();
            alert(`Navigating to ${section}`);
        });
    });
}

// Handle window resize for responsive adjustments
function handleResize() {
    // Any responsive-specific JavaScript can go here
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    updateCartCount(); // Initialize cart count
    setupSearch();
    initializeProductCards();
    initializeCategoryCards();
    setupCTAButton();
    setupSubNavigation();
    
    // Set up resize handler
    window.addEventListener('resize', handleResize);
});

// Smooth scrolling for anchor links
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

// Dropdown functionality for mobile
function setupMobileDropdown() {
    const menuToggle = document.createElement('div');
    menuToggle.className = 'mobile-menu-toggle';
    menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
    menuToggle.style.display = 'none';
    
    // Add mobile menu toggle logic if needed
}

// Form validation for search
function validateSearchForm() {
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            // Trim whitespace and validate input
            this.value = this.value.trimStart();
        });
    }
}
