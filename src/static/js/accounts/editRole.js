// Function to open modal and populate form with role data
function populateEditRoleModal(roleId) {
    const token = localStorage.getItem('access_token');

    fetch(`/api/roles/${roleId}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(role => {
        // Populate form fields
        document.getElementById('editRoleId').value = roleId;
        document.getElementById('editRoleName').value = role.name;
        document.getElementById('editIsAdmin').checked = role.is_admin;
        document.getElementById('editCanUsers').checked = role.can_users;
        document.getElementById('editCanShakemap').checked = role.can_shakemap;

        // Show the modal
        const editRoleModal = new bootstrap.Modal(document.getElementById('editRoleModal'));
        editRoleModal.show();
    })
    .catch(error => console.error('Error fetching role data:', error));
}

// Event listener for form submission
document.getElementById('editRoleForm').onsubmit = function (event) {
    event.preventDefault();
    submitEditRoleForm();
};

// Function to submit edited role data
function submitEditRoleForm() {
    const token = localStorage.getItem('access_token');
    const roleId = document.getElementById('editRoleId').value;
    const formData = new FormData(document.getElementById('editRoleForm'));

    const data = {
        name: formData.get('name'),
        is_admin: formData.get('is_admin') === 'on',
        can_users: formData.get('can_users') === 'on',
        can_shakemap: formData.get('can_shakemap') === 'on'
    };

    makeApiRequest(`/api/roles/${roleId}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(result => {
        if (result.message) {
            window.location.reload(); // Reload to reflect changes
        } else if (result.error) {
            showAlert('alertPlaceholder', 'danger', result.error || 'როლის განახლების შეცდომა');
        }
    })
    .catch(error => console.error('Error updating role:', error));
}