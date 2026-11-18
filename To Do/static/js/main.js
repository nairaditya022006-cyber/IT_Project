// Client-side validation and interactive UI logic

// Confirm task deletion
function confirmDelete() {
    return confirm("Are you sure you want to delete this task? This action cannot be undone.");
}

// Validate registration form passwords
function validateRegistration() {
    const password = document.getElementById('password').value;
    const confirm_password = document.getElementById('confirm_password').value;
    const error_msg = document.getElementById('password_error');
    
    if (password !== confirm_password) {
        error_msg.style.display = 'block';
        return false;
    }
    
    error_msg.style.display = 'none';
    return true;
}

// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.style.display = 'none';
            }, 300); // Wait for transition
        }, 5000);
    });
});
