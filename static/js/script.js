// Main script for MurtiKart project
document.addEventListener('DOMContentLoaded', () => {
    console.log('MurtiKart Initialized Successfully');

    // MOBILE NAVIGATION SECTION
    // Handles the hamburger menu toggle for mobile devices
    const toggleBtns = document.querySelectorAll('.sidebar-toggle-btn');
    
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation(); // Stops the event from reaching the document click listener
            document.body.classList.toggle('sidebar-toggled');
        });
    });

    // CLICK-OUTSIDE DISMISSAL
    // Closes the sidebar if a user clicks outside the sidebar area on mobile
    document.addEventListener('click', (e) => {
        // Only trigger on mobile/tablet screens (up to 1024px) when sidebar is active
        if (window.innerWidth <= 1024 && 
            document.body.classList.contains('sidebar-toggled') && 
            !e.target.closest('#sidebar') && 
            !e.target.closest('.sidebar-toggle-btn')) {
            document.body.classList.remove('sidebar-toggled');
        }
    });
});
