// Wait for the DOM to be fully loaded before running scripts
document.addEventListener('DOMContentLoaded', () => {
    
    // SECTION: Stats Counter Animation
    // This part finds all elements with the 'counter' class and animates them
    const counters = document.querySelectorAll('.counter');
    
    counters.forEach(counter => {
        // Get the target number from the 'data-target' attribute
        const target = +counter.getAttribute('data-target');
        // Set an increment value for smooth animation (1% of target per step)
        const increment = target / 100;
        
        // Function to update the number recursively
        const updateCounter = () => {
            const count = +counter.innerText;
            // If the current count is less than target, keep adding
            if (count < target) {
                counter.innerText = Math.ceil(count + increment);
                // Run again after 20 milliseconds
                setTimeout(updateCounter, 20);
            } else {
                // Once target is reached, set it exactly
                counter.innerText = target;
            }
        };
        // Start the animation
        updateCounter();
    });

    // SECTION: Mobile Sidebar Toggle
    // Handles opening the sidebar on smaller screens
    const toggleBtn = document.querySelector('.sidebar-toggle-btn');
    if(toggleBtn) {
        toggleBtn.addEventListener('click', (e) => {
            // Prevent the click from bubbling up to the document
            e.stopPropagation();
            // Toggle the 'sidebar-toggled' class on the body
            document.body.classList.toggle('sidebar-toggled');
        });
    }

    // SECTION: Click Outside to Close
    // Closes the sidebar when clicking anywhere else on the screen (Mobile only)
    document.addEventListener('click', (e) => {
        // Detect if screen width is mobile and sidebar is open
        if (window.innerWidth <= 992 && 
            document.body.classList.contains('sidebar-toggled') && 
            !e.target.closest('#sidebar') && 
            !e.target.closest('.sidebar-toggle-btn')) {
            // Close the sidebar
            document.body.classList.remove('sidebar-toggled');
        }
    });
});
