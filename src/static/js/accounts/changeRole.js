async function fetchRoles() {
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch('/api/roles', {
            method: 'GET',
            headers: {
                'accept': 'application/json',
                'Authorization': `Bearer ${token}`,  // Add your JWT token here
            }
        });

        if (!response.ok) throw new Error('Failed to fetch data');

        const data = await response.json();
        populateRolesTable(data);
    } catch (error) {
        console.error('Error:', error);
    }
}

function populateRolesTable(roles) {
    const roleSelect = document.getElementById('roleSelect');
    roleSelect.innerHTML = '';
    
    roles.forEach(role => {
        const option = document.createElement('option');
        option.value = role.id;  // Use the role ID as the value
        option.textContent = role.name;  // Use the role name as the displayed text
        roleSelect.appendChild(option);
    });
}

function changeRole(userUUID) {
    const changeRoleModal = new bootstrap.Modal(document.getElementById('changeRoleModal'));
    fetchRoles();
    // Show the modal after roles are fetched
    changeRoleModal.show();

    // Handle role changes on form submission
    const form = document.getElementById('changeRoleForm');
    form.onsubmit = function (event) {
        event.preventDefault();
        const token = localStorage.getItem('access_token');
        const newRoleId = document.getElementById('roleSelect').value;
        
        // Data to be sent
        const data = {
            role_id: newRoleId
        };

        // Send PUT request to update role
        makeApiRequest(`/api/accounts/${userUUID}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,  // Include the JWT token
            },
            body: JSON.stringify(data)
        })
        .then(data => {
            if (data.error) {
                closeModal('UserModal')
                showAlert('alertPlaceholder', 'danger', data.error || ' გაუმართავი როლის ცვლილება.');
            } else {
                window.location.reload(); // Reload the page to reflect changes
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });

        // Call API to update role here
        changeRoleModal.hide();
    };
}