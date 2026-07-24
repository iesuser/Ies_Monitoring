function openResetPasswordModal() {
    const resetPasswordModal = new bootstrap.Modal(document.getElementById('resetPasswordModal'));
    resetPasswordModal.show(); // Show the modal
}

function sendEmail(event) {
    event.preventDefault();
    const i18n = window.I18n;

    const modalEmail = document.getElementById('modalEmail').value;
    const modalForm = document.getElementById('modalResetPassword');

    const formData = { email: modalEmail };
    const btn = document.getElementById('modalSubmit');
    const loadingMessage = document.getElementById('loadingMessage');
    btn.disabled = true;
    loadingMessage.style.display = 'block';

    fetch('/api/auth/request_reset_password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        btn.disabled = false;
        loadingMessage.style.display = 'none';
        if (data.message) {
            closeModal('resetPasswordModal');
            showAlert('alertPlaceholder', 'success', data.message || (i18n ? i18n.t('alerts.reset_check_email', 'Please check your email. Verification link has been sent.') : 'Please check your email. Verification link has been sent.'));
            modalForm.reset();
        } else {
            showAlert('alertPlaceholder', 'danger', data.error || (i18n ? i18n.t('alerts.invalid_email', 'Invalid email address.') : 'Invalid email address.'));

        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('alertPlaceholder', 'danger', i18n ? i18n.t('alerts.request_failed', 'Request failed. Please try again.') : 'Request failed. Please try again.');
        btn.disabled = false;
        loadingMessage.style.display = 'none';
    });
}

document.getElementById('modalResetPassword').onsubmit = sendEmail;
document.addEventListener('DOMContentLoaded', function() {
    const i18n = window.I18n;

    if (message == 'invalid'){
        showAlert('alertPlaceholder', 'danger', i18n ? i18n.t('alerts.reset_invalid', 'Password reset link is invalid.') : 'Password reset link is invalid.');
    }else if (message == 'expired'){
        showAlert('alertPlaceholder', 'danger', i18n ? i18n.t('alerts.reset_expired', 'Password reset link has expired.') : 'Password reset link has expired.');
    }

} )