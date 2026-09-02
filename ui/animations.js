// Intersection Observer for Scroll Animations
document.addEventListener('DOMContentLoaded', () => {
  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
  };

  const observer = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Select all elements that need to animate
  const elementsToAnimate = document.querySelectorAll('.reveal-up, .reveal-left');
  elementsToAnimate.forEach(el => observer.observe(el));
});
