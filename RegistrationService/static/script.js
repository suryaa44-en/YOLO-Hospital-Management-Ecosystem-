document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('register-form');
    const appointmentForm = document.getElementById('appointment-form');
    const statusForm = document.getElementById('status-form');
    const responseArea = document.getElementById('response-area');
    const notificationArea = document.getElementById('notification-area');

    const showNotification = (message, type) => {
        notificationArea.textContent = message;
        notificationArea.className = `notification ${type}`;
        notificationArea.style.display = 'block';
        setTimeout(() => {
            notificationArea.style.display = 'none';
        }, 5000);
    };

    registerForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const patient = {
            first_name: document.getElementById('first_name').value,
            last_name: document.getElementById('last_name').value,
            dob: document.getElementById('dob').value,
            contact_number: document.getElementById('contact_number').value,
            address: document.getElementById('address').value,
        };

        try {
            const response = await fetch('/api/v1/patients/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(patient),
            });
            const result = await response.json();
            responseArea.textContent = JSON.stringify(result, null, 2);

            if (response.ok) {
                showNotification('Patient registered successfully!', 'success');
                document.getElementById('patient_id').value = result.id;
                registerForm.reset();
            } else {
                showNotification(`Error: ${result.detail || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            showNotification(`Network Error: ${error.message}`, 'error');
            responseArea.textContent = `Error: ${error.message}`;
        }
    });

    appointmentForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const appointment = {
            patient_id: document.getElementById('patient_id').value,
            doctor_id: document.getElementById('doctor_id').value,
            appointment_time: document.getElementById('appointment_time').value,
            status: document.getElementById('status').value,
        };

        try {
            const response = await fetch('/api/v1/appointments/book', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(appointment),
            });
            const result = await response.json();
            responseArea.textContent = JSON.stringify(result, null, 2);

            if (response.ok) {
                showNotification('Appointment booked successfully!', 'success');
                appointmentForm.reset();
            } else {
                showNotification(`Error: ${result.detail || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            showNotification(`Network Error: ${error.message}`, 'error');
            responseArea.textContent = `Error: ${error.message}`;
        }
    });

    statusForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const appointmentId = document.getElementById('appointment_id_check').value;

        if (!appointmentId) {
            showNotification('Please enter an Appointment ID.', 'error');
            return;
        }

        try {
            const response = await fetch(`/api/v1/appointments/${appointmentId}`);
            const result = await response.json();
            responseArea.textContent = JSON.stringify(result, null, 2);

            if (response.ok) {
                showNotification(`Status for ${result.id}: ${result.status}`, 'success');
                statusForm.reset();
            } else {
                showNotification(`Error: ${result.detail || 'Appointment not found'}`, 'error');
            }
        } catch (error) {
            showNotification(`Network Error: ${error.message}`, 'error');
            responseArea.textContent = `Error: ${error.message}`;
        }
    });
});