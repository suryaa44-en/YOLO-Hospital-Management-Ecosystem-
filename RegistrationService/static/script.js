document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('hms_token');
    const role = localStorage.getItem('hms_role');
    const username = localStorage.getItem('hms_username');
    
    if (!token) {
        window.location.href = '/';
        return;
    }
    
    // Redirect based on role
    if (role === 'NURSE') {
        window.location.href = '/vitals';
        return;
    } else if (role === 'DOCTOR') {
        window.location.href = '/queue';
        return;
    }

    // Update user info in header
    const userNameElement = document.getElementById('user-name');
    if (userNameElement) {
        userNameElement.textContent = `Welcome, ${username} (${role})`;
    }

    const registerForm = document.getElementById('register-form');
    const appointmentForm = document.getElementById('appointment-form');
    const statusForm = document.getElementById('status-form');
    const responseArea = document.getElementById('response-area');
    const notificationArea = document.getElementById('notification-area');
    const logoutBtn = document.getElementById('logout-btn');
    const navLinks = document.querySelectorAll('.nav-link');
    const contentSections = document.querySelectorAll('.content-section');
    const statsContainer = document.getElementById('stats-container');

    const { jsPDF } = window.jspdf;

    // Handle logout button (delegated event listener)
    document.addEventListener('click', (e) => {
        if (e.target.id === 'logout-btn') {
            localStorage.removeItem('hms_token');
            localStorage.removeItem('hms_role');
            localStorage.removeItem('hms_username');
            window.location.href = '/';
        }
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

    // Load dashboard statistics
    loadDashboardStats();
    loadPatients();

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
        
        // Validate required fields
        const firstName = document.getElementById('first_name').value.trim();
        const lastName = document.getElementById('last_name').value.trim();
        const dob = document.getElementById('dob').value;
        const contactNumber = document.getElementById('contact_number').value.trim();
        const address = document.getElementById('address').value.trim();
        
        if (!firstName || !lastName || !dob || !contactNumber || !address) {
            showNotification('Please fill in all required fields', 'error');
            return;
        }
        
        const patient = {
            first_name: firstName,
            last_name: lastName,
            dob: dob,
            contact_number: contactNumber,
            address: address,
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
                showNotification(`Patient registered successfully! Patient ID: ${result.patient_uid}`, 'success');
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

    async function loadDashboardStats() {
        try {
            const response = await authenticatedFetch('/api/v1/dashboard/stats');
            const stats = await response.json();
            
            if (response.ok) {
                statsContainer.innerHTML = `
                    <div class="stats-grid">
                        <div class="stat-card">
                            <h3>Total Patients</h3>
                            <p>${stats.total_patients}</p>
                        </div>
                        <div class="stat-card">
                            <h3>Today's Appointments</h3>
                            <p>${stats.today_appointments}</p>
                        </div>
                        <div class="stat-card">
                            <h3>Pending Queue</h3>
                            <p>${stats.pending_queue}</p>
                        </div>
                    </div>
                `;
            } else {
                statsContainer.innerHTML = '<p>Error loading statistics.</p>';
            }
        } catch (error) {
            statsContainer.innerHTML = '<p>Error loading statistics.</p>';
        }
    }

    async function loadPatients() {
        try {
            const response = await authenticatedFetch('/api/v1/patients');
            const patients = await response.json();
            
            if (response.ok) {
                const patientsContainer = document.getElementById('patients-container');
                if (patients.length === 0) {
                    patientsContainer.innerHTML = '<p>No patients registered yet.</p>';
                } else {
                    patientsContainer.innerHTML = `
                        <div class="patients-grid">
                            ${patients.map(patient => `
                                <div class="patient-card">
                                    <h3>${patient.first_name} ${patient.last_name}</h3>
                                    <p><strong>Patient ID:</strong> ${patient.patient_uid}</p>
                                    <p><strong>DOB:</strong> ${new Date(patient.dob).toLocaleDateString()}</p>
                                    <p><strong>Contact:</strong> ${patient.contact_number}</p>
                                    <p><strong>Address:</strong> ${patient.address}</p>
                                    <p><strong>Registered:</strong> ${new Date(patient.created_at).toLocaleString()}</p>
                                </div>
                            `).join('')}
                        </div>
                    `;
                }
            } else {
                document.getElementById('patients-container').innerHTML = '<p>Error loading patients.</p>';
            }
        } catch (error) {
            document.getElementById('patients-container').innerHTML = '<p>Error loading patients.</p>';
        }
    }
});