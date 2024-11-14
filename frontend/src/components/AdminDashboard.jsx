import React, { useEffect, useState } from 'react';

const AdminDashboard = () => {
  const [attendance, setAttendance] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [newSkill, setNewSkill] = useState('');
  const [selectedEmployeeId, setSelectedEmployeeId] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    fetch('http://localhost:5000/admin/dashboard', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(response => response.json())
      .then(data => {
        setAttendance(data.attendance);
        setRecommendations(data.recommendations);
      })
      .catch(err => console.error(err));
  }, []);

  const handleAddSkill = () => {
    const token = localStorage.getItem('token');
    fetch(`http://localhost:5000/employee/${selectedEmployeeId}/add-skill`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ skill: newSkill }),
    })
      .then(response => response.json())
      .then(data => {
        alert(data.message);
        setNewSkill('');
      })
      .catch(err => console.error(err));
  };

  return (
    <div>
      <h1>Admin Dashboard</h1>
      <h2>Employee Attendance</h2>
      <ul>
        {attendance.map((emp, index) => (
          <li key={index}>{emp.name} - {emp.skills} - {emp.clock_in_status}</li>
        ))}
      </ul>

      <h2>Recommendations</h2>
      <ul>
        {recommendations.map((rec, index) => (
          <li key={index}>{rec.message}</li>
        ))}
      </ul>

      <h2>Add Skill</h2>
      <select onChange={(e) => setSelectedEmployeeId(e.target.value)}>
        <option value="">Select Employee</option>
        {attendance.map((emp) => (
          <option key={emp.id} value={emp.id}>
            {emp.name}
          </option>
        ))}
      </select>
      <input type="text" value={newSkill} onChange={(e) => setNewSkill(e.target.value)} placeholder="New Skill" />
      <button onClick={handleAddSkill}>Add Skill</button>
    </div>
  );
};

export default AdminDashboard;
