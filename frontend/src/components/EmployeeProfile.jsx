import React, { useEffect, useState } from 'react';

const EmployeeProfile = () => {
  const [profile, setProfile] = useState({
    name: '',
    clockInStatus: '',
    jobSchedule: '',
    attendance: [],
    leaveDays: 0,
    warnings: [],
    skills: [],
  });

  useEffect(() => {
    const token = localStorage.getItem('token');
    fetch('http://localhost:9988/employee/profile', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(response => response.json())
      .then(data => setProfile(data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div>
      <h1>Employee Profile</h1>
      <p>Name: {profile.name}</p>
      <p>Clock-In Status: {profile.clockInStatus}</p>
      <p>Job Schedule: {profile.jobSchedule}</p>

      <h2>Attendance</h2>
      <ul>
        {profile.attendance.map((day, index) => (
          <li key={index}>{day}</li>
        ))}
      </ul>

      <h2>Leave Days</h2>
      <p>{profile.leaveDays} days remaining</p>

      <h2>Warnings</h2>
      <ul>
        {profile.warnings.map((warning, index) => (
          <li key={index}>{warning}</li>
        ))}
      </ul>

      <h2>Skills</h2>
      <ul>
        {profile.skills.map((skill, index) => (
          <li key={index}>{skill}</li>
        ))}
      </ul>
    </div>
  );
};

export default EmployeeProfile;
