function submitChangePassword(event) {
    event.preventDefault();

    const currentPassword = document.getElementById('currentPassword').value;
    const password = document.getElementById('password').value;
    const retypePassword = document.getElementById('retypePassword').value;
    const accessToken = localStorage.getItem('access_token');

    if (!accessToken) {
        showAlert('alertPlaceholder', 'danger', 'ჯერ ავტორიზაცია გაიარე.');
        return;
    }

    fetch('/api/change_password', {
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
            showAlert('alertPlaceholder', 'success', data.message || 'პაროლი წარმატებით შეიცვალა.');
            setTimeout(() => {
                clearSessionData();
            }, 1000);
        } else {
            showAlert('alertPlaceholder', 'danger', data.error || 'პაროლის შეცვლა ვერ მოხერხდა.');
        }
    })
    .catch(() => {
        showAlert('alertPlaceholder', 'danger', 'მოთხოვნა ჩავარდა პაროლის შეცვლისას.');
    });
}

document.getElementById('changePasswordForm').onsubmit = submitChangePassword;
