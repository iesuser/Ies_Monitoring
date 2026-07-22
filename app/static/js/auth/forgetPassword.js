function openResetPasswordModal() {
    const resetPasswordModal = new bootstrap.Modal(document.getElementById('resetPasswordModal'));
    resetPasswordModal.show(); // Show the modal
}

function sendEmail(event) {
    event.preventDefault();

    const modalEmail = document.getElementById('modalEmail').value;
    const modalForm = document.getElementById('modalResetPassword');

    const formData = {
        modalEmail: modalEmail
    };
    const btn = document.getElementById('modalSubmit');
    btn.disabled = true;
    fetch('/api/request_reset_password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        btn.disabled = false;
        if (data.message) {
            closeModal('resetPasswordModal');
            showAlert('alertPlaceholder', 'success', data.message || 'Please check your email. Verification link has been sent.');
            modalForm.reset();
        } else {
            showAlert('alertPlaceholder', 'danger', data.error || 'Invalid email address.');

        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('alertPlaceholder', 'danger', 'Request failed. Please try again.');
        btn.disabled = false;
    });
}

document.getElementById('modalResetPassword').onsubmit = sendEmail;
document.addEventListener('DOMContentLoaded', function() {

    if (message == 'invalid'){
        showAlert('alertPlaceholder', 'danger', 'Password reset link is invalid.');
    }else if (message == 'expired'){
        showAlert('alertPlaceholder', 'danger', 'Password reset link has expired.');
    }

} )