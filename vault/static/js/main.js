// Simple file upload progress indicator
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.querySelector('input[type="file"]');
    const uploadButton = document.querySelector('button[type="submit"]');
    
    if (fileInput && uploadButton) {
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                uploadButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Preparing...';
                uploadButton.classList.add('uploading');
            }
        });
    }
    
    // Enable tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});