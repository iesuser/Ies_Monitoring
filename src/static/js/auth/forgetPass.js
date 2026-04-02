function openResetPasswordModal() {
    const resetPasswordModal = new bootstrap.Modal(document.getElementById('resetPasswordModal'));
    resetPasswordModal.show(); // Show the modal
}

function sendEmail(event) {
    event.preventDefault();

    const modalEmail = document.getElementById('modalEmail').value;

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
            showAlert('alertPlaceholder', 'success', data.message || ' გთხოვთ შეამოწმოთ ელ.ფოსტა, ვერიფიკაციის ლინკი გამოგზავნილია.');
            // Close the modal 
                closeModal('resetPasswordModal');
        } else {
            showAlert('forgetAlertDiv', 'danger', data.error || ' გაუმართავი ელ.ფოსტა.');

        }
    })
    .catch(error => {
        console.error('Error:', error);
        btn.disabled = false;
    });
}

document.getElementById('modalResetPassword').onsubmit = sendEmail;
document.addEventListener('DOMContentLoaded', function() {

    if (message == 'invalid'){
        showAlert('alertPlaceholder', 'danger', 'პაროლის აღდგენის ლინკი არასწორია.');
    }else if (message == 'expired'){
        showAlert('alertPlaceholder', 'danger', 'პაროლის აღდგენის ლინკს გაუვიდა ვადა.');
    }

} )