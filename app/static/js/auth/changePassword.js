function submitChangePassword(event) {
    event.preventDefault();

    const currentPassword = document.getElementById('currentPassword').value;
    const password = document.getElementById('password').value;
    const retypePassword = document.getElementById('retypePassword').value;
    const accessToken = localStorage.getItem('access_token');

    if (!accessToken) {
        showAlert('alertPlaceholder', 'danger', 'Please sign in first.');
        return;
    }

    fetch('/api/auth/change_password', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
            current_password: currentPassword,
            password: password,
            retype_password: retypePassword
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            showAlert('alertPlaceholder', 'success', data.message || 'Password changed successfully.');
            setTimeout(() => {
                clearSessionData();
            }, 1000);
        } else {
            showAlert('alertPlaceholder', 'danger', data.error || 'Failed to change password.');
        }
    })
    .catch(() => {
        showAlert('alertPlaceholder', 'danger', 'Request failed while changing password.');
    });
}

document.getElementById('changePasswordForm').onsubmit = submitChangePassword;
window.initPasswordToggle?.({
    fieldId: 'currentPassword',
    toggleId: 'toggleCurrentPassword',
    imageId: 'toggleCurrentPasswordImg'
});
window.initPasswordToggle?.({
    fieldId: 'password',
    toggleId: 'toggleNewPassword',
    imageId: 'toggleNewPasswordImg'
});
window.initPasswordToggle?.({
    fieldId: 'retypePassword',
    toggleId: 'toggleRetypePassword',
    imageId: 'toggleRetypePasswordImg'
});