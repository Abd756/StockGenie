document.addEventListener('DOMContentLoaded', function() {
    // Check if preloader has been shown before
    const hasSeenPreloader = sessionStorage.getItem('preloaderShown');
    
    if (hasSeenPreloader) {
        // Hide preloader immediately if already shown
        document.getElementById('preloader').style.display = 'none';
        document.body.classList.add('preloader-done');
        return;
    }
    
    let progress = 0;
    const progressFill = document.querySelector('.progress-fill');
    const progressPercent = document.getElementById('progress-percent');
    const preloader = document.getElementById('preloader');
    
    // Simulate loading progress over 5 seconds
    const totalDuration = 5000; // 5 seconds
    const updateInterval = 50; // Update every 50ms
    const incrementsNeeded = totalDuration / updateInterval; // 100 increments
    const progressIncrement = 100 / incrementsNeeded; // Each increment value
    
    const interval = setInterval(() => {
        progress += progressIncrement;
        
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            
            // Complete the loading and fade out smoothly
            progressFill.style.width = '100%';
            progressPercent.textContent = '100%';
            
            // Wait a moment then start fade out
            setTimeout(() => {
                preloader.classList.add('fade-out');
                
                // Mark preloader as shown for this session
                sessionStorage.setItem('preloaderShown', 'true');
                
                // Show the content
                document.body.classList.add('preloader-done');
                
                // Remove from DOM after fade animation completes
                setTimeout(() => {
                    preloader.style.display = 'none';
                }, 500); // Wait for CSS transition to complete
            }, 300); // Brief pause at 100%
        } else {
            progressFill.style.width = progress + '%';
            progressPercent.textContent = Math.round(progress) + '%';
        }
    }, updateInterval);
});