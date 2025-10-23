document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('hms_token');
    if (!token) {
        window.location.href = '/';
        return;
    }

    const registerForm = document.getElementById('register-form');
    const appointmentForm = document.getElementById('appointment-form');
    const statusForm = document.getElementById('status-form');
    const responseArea = document.getElementById('response-area');
    const notificationArea = document.getElementById('notification-area');
    const logoutBtn = document.getElementById('logout-btn');
    const navLinks = document.querySelectorAll('.nav-link');
    const contentSections = document.querySelectorAll('.content-section');

    const { jsPDF } = window.jspdf;

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('hms_token');
        window.location.href = '/';
    });

    const activateSection = (targetId) => {
        contentSections.forEach((section) => {
            section.classList.toggle('active', section.id === targetId);
        });
    };

    const activateNavLink = (activeLink) => {
        navLinks.forEach((link) => {
            link.classList.toggle('active', link === activeLink);
        });
    };

    navLinks.forEach((link) => {
        link.addEventListener('click', () => {
            const targetId = link.getAttribute('data-target');
            activateSection(targetId);
            activateNavLink(link);
        });
    });

    activateSection('register-section');
    const defaultNavLink = document.querySelector('.nav-link[data-target="register-section"]');
    if (defaultNavLink) {
        activateNavLink(defaultNavLink);
    }

    const showNotification = (message, type) => {
        notificationArea.textContent = message;
        notificationArea.className = `notification ${type}`;
        notificationArea.style.display = 'block';
        setTimeout(() => {
            notificationArea.style.display = 'none';
        }, 5000);
    };

    const authenticatedFetch = async (url, options = {}) => {
        const headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        };
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401) {
            localStorage.removeItem('hms_token');
            window.location.href = '/';
        }
        return response;
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
            const response = await authenticatedFetch('/api/v1/patients/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(patient),
            });
            const result = await response.json();
            responseArea.textContent = JSON.stringify(result, null, 2);

            if (response.ok) {
                showNotification('Patient registered successfully!', 'success');
                document.getElementById('patient_uid').value = result.patient_uid;
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
            patient_uid: parseInt(document.getElementById('patient_uid').value),
            doctor_id: document.getElementById('doctor_id').value,
            appointment_time: document.getElementById('appointment_time').value,
            status: document.getElementById('status').value,
        };

        try {
            const response = await authenticatedFetch('/api/v1/appointments/book', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(appointment),
            });
            const result = await response.json();
            responseArea.textContent = JSON.stringify(result, null, 2);

            if (response.ok) {
                showNotification('Appointment booked successfully!', 'success');
                generateAndDownloadSlip(result);
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
            const response = await authenticatedFetch(`/api/v1/appointments/${appointmentId}`);
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

    function generateAndDownloadSlip(appointment) {
        const doc = new jsPDF();

        doc.setFontSize(22);
        doc.text("Appointment Slip", 105, 20, null, null, "center");

        doc.setFontSize(12);
        doc.text(`Appointment ID: ${appointment.id}`, 20, 40);
        doc.text(`Patient ID: ${appointment.patient_uid}`, 20, 50);
        doc.text(`Doctor ID: ${appointment.doctor_id}`, 20, 60);
        doc.text(`Time: ${new Date(appointment.appointment_time).toLocaleString()}`, 20, 70);
        doc.text(`Status: ${appointment.status}`, 20, 80);
        doc.text(`Queue Token: ${appointment.queue_token}`, 20, 90);

        doc.save(`appointment_${appointment.id}.pdf`);
    }
});