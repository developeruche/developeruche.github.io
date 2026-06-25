/**
 * Synthetic Health - Scroll Animations
 * Uses IntersectionObserver to trigger fade-in and slide-up effects
 * as elements scroll into the viewport, mirroring the Seed.com interaction style.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Select all elements with animation classes
    const animatedElements = document.querySelectorAll('.slide-up, .fade-in');

    // Configuration for the IntersectionObserver
    const observerOptions = {
        root: null, // Use the viewport as the root
        rootMargin: '0px 0px -100px 0px', // Trigger slightly before the element is fully in view
        threshold: 0.1 // Trigger when 10% of the element is visible
    };

    // Callback function executed when an intersection is observed
    const observerCallback = (entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Add the 'is-visible' class to trigger CSS transitions
                entry.target.classList.add('is-visible');
                // Unobserve the element so the animation only happens once
                observer.unobserve(entry.target);
            }
        });
    };

    // Instantiate the observer
    const observer = new IntersectionObserver(observerCallback, observerOptions);

    // Observe each animated element
    animatedElements.forEach(element => {
        observer.observe(element);
    });
});
