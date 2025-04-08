document.addEventListener('DOMContentLoaded', function() {
    // Mobile navigation toggle
    const navToggle = document.querySelector('.navbar-toggle');
    const navMenu = document.querySelector('.navbar-menu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }
    
    // Add current year to footer
    const yearElement = document.querySelector('.footer-bottom');
    if (yearElement) {
        const year = new Date().getFullYear();
        yearElement.innerHTML = yearElement.innerHTML.replace('{{ now.year }}', year);
    }
}); 