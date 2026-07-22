// Open the modal for editing a User record
async function openUserModal() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        showAlert('alertPlaceholder', 'danger', 'Session has expired. Please sign in again.');
        clearSessionData();
        return;
    }

    const emailText = document.getElementById('user_email');
    const roleText = document.getElementById('user_role');
    const accountsButton = document.getElementById('accountsButton');

    try {
        // Use centralized request helper so refresh-token flow is applied automatically.
        const data = await makeApiRequest('/api/user', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!data || data.error) {
            showAlert('alertPlaceholder', 'danger', data?.error || 'An error occurred while fetching data.');
            return;
        }

        document.getElementById('userUUID').value = data.uuid;
        document.getElementById('user_name').value = data.name;
        document.getElementById('user_lastname').value = data.lastname;
        emailText.textContent = data.email;
        roleText.textContent = data.role_name;

        if (accountsButton) {
            accountsButton.style.display = data.role_name === 'Admin' ? 'block' : 'none';
        }

        const modal = new bootstrap.Modal(document.getElementById('UserModal'));
        modal.show();
    } catch (error) {
        console.error('Error fetching data:', error);
        showAlert('alertPlaceholder', 'danger', 'An error occurred while fetching data.');
    }
}

// Redirect to the accounts page
function redirectToAccounts() {
    window.location.href = '/accounts';
}

function submitUserForm(event) {
    event.preventDefault();

    const formData = new FormData(document.getElementById('UserForm'));
    const UUIDField = document.getElementById('userUUID').value;

    const token = localStorage.getItem('access_token');

    // makeApiRequest is in the globalAccessControl.js
    makeApiRequest(`/api/user/${UUIDField}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    })
    .then(data => {
        if (data.error) {
            closeModal('UserModal')
            showAlert('alertPlaceholder', 'danger', data.error || 'An error occurred while updating data.');
        } else {
            window.location.reload(); // Reload the page to reflect changes
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function changePassword(){
    window.location.href = '/change_password';
}