// Fake student data (like a mini database) - stored in localStorage for persistence
let students = JSON.parse(localStorage.getItem('students')) || [
    { rollno: '101', password: 'pass123', name: 'Amit', attendance: 'Present today', fees: 'Paid', results: '90%' },
    { rollno: '102', password: 'pass456', name: 'Priya', attendance: 'Absent today', fees: 'Unpaid', results: '85%' }
    // Add more students here if needed
];

// Fake teacher data
const teachers = [
    { email: 'teacher@school.com', password: 'teach123' }
    // Add more teachers if needed
];

// Function to save students back to localStorage after updates
function saveStudents() {
    localStorage.setItem('students', JSON.stringify(students));
}

// Student login function
function studentLogin() {
    const rollno = document.getElementById('rollno').value;
    const pass = document.getElementById('pass').value;
    const student = students.find(s => s.rollno === rollno && s.password === pass);
    
    if (student) {
        localStorage.setItem('currentStudent', JSON.stringify(student));
        window.location.href = 'student-dashboard.html';
    } else {
        document.getElementById('error').textContent = 'Wrong roll number or password';
    }
}

// Load student dashboard
function loadStudentDashboard() {
    // Reload students from localStorage in case teacher updated them
    students = JSON.parse(localStorage.getItem('students')) || students;
    
    const student = JSON.parse(localStorage.getItem('currentStudent'));
    if (!student) { 
        window.location.href = 'student-login.html'; 
        return; 
    }
    
    document.getElementById('name').textContent = student.name;
    document.getElementById('attendance').textContent = student.attendance;
    document.getElementById('fees').textContent = student.fees;
    document.getElementById('results').textContent = student.results;
}

// Teacher login function (similar to student)
function teacherLogin() {
    const email = document.getElementById('email').value;  // Assuming input ID 'email' in teacher-login.html
    const pass = document.getElementById('pass').value;
    const teacher = teachers.find(t => t.email === email && t.password === pass);
    
    if (teacher) {
        localStorage.setItem('currentTeacher', JSON.stringify(teacher));
        window.location.href = 'teacher-dashboard.html';
    } else {
        document.getElementById('error').textContent = 'Wrong email or password';
    }
}

// Load teacher dashboard - shows list of students with edit options
function loadTeacherDashboard() {
    const teacher = JSON.parse(localStorage.getItem('currentTeacher'));
    if (!teacher) { 
        window.location.href = 'teacher-login.html'; 
        return; 
    }
    
    const container = document.getElementById('student-list');  // Assuming a <div id="student-list"> in teacher-dashboard.html
    container.innerHTML = '';  // Clear previous content
    
    students.forEach((student, index) => {
        const studentDiv = document.createElement('div');
        studentDiv.innerHTML = `
            <p>Roll No: ${student.rollno} | Name: ${student.name} | Attendance: ${student.attendance}</p>
            <input id="new-attendance-${index}" placeholder="Update Attendance" type="text">
            <button onclick="updateAttendance(${index})">Update</button>
        `;
        container.appendChild(studentDiv);
    });
}

// Function to update attendance (called from button in teacher dashboard)
function updateAttendance(index) {
    const newAttendance = document.getElementById(`new-attendance-${index}`).value;
    if (newAttendance) {
        students[index].attendance = newAttendance;
        saveStudents();  // Save changes
        alert('Attendance updated!');  // Simple feedback
        loadTeacherDashboard();  // Refresh the list
    }
}
