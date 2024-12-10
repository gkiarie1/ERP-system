import React, { useEffect, useState, useRef } from "react";
import { io } from "socket.io-client";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

const AdminDashboard = () => {
  const socketRef = useRef();
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [showAddEmployeeForm, setShowAddEmployeeForm] = useState(false);
  const [newEmployee, setNewEmployee] = useState({
    name: "",
    email: "",
    role: "employee",
    password: "",
  });

  const [editingId, setEditingId] = useState(null);
  const [editedName, setEditedName] = useState("");

  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedShift, setSelectedShift] = useState("day");

  // Initialize socket connection
  if (!socketRef.current) {
    socketRef.current = io("http://localhost:9988", {
      query: { token: localStorage.getItem("token") },
    });
  }

  useEffect(() => {
    const socket = socketRef.current;
    const token = localStorage.getItem("token");

    // Fetch employee data
    fetch("http://localhost:9988/admin/dashboard", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((response) => response.json())
      .then((data) => {
        const sortedEmployees = data.attendance.sort((a, b) =>
          a.clock_in_status === "Clocked In" ? -1 : 1
        );
        setEmployees(sortedEmployees || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching employee data:", err);
        setLoading(false);
      });

    const handleClockIn = (data) => {
      setMessage(`${data.name} has clocked in.`);
    };

    const handleNewEmployee = (data) => {
      setEmployees((prev) => [
        ...prev,
        { ...data, clock_in_status: "Not Clocked In" },
      ]);
    };

    // Register socket event listeners
    socket.on("employee_clocked_in", handleClockIn);
    socket.on("employee_created", handleNewEmployee);

    // Clean up on unmount
    return () => {
      socket.off("employee_clocked_in", handleClockIn);
      socket.off("employee_created", handleNewEmployee);
      if (socket.connected) {
        socket.disconnect();
      }
    };
  }, [socketRef]);

  const handleEditField = (id, field, value) => {
    const token = localStorage.getItem("token");

    fetch(`http://localhost:9988/employee/${id}/edit`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ [field]: value }),
    })
      .then((response) => response.json())
      .then((data) => {
        setMessage(data.message);
        setEmployees((prev) =>
          prev.map((emp) => (emp.id === id ? { ...emp, [field]: value } : emp))
        );
        setEditingId(null); // Stop editing after save
        setEditedName(""); // Clear edited name
      })
      .catch((err) => console.error("Error editing employee:", err));
  };

  const handleAddEmployee = () => {
    const token = localStorage.getItem("token");
    fetch("http://localhost:9988/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(newEmployee),
    })
      .then((response) => response.json())
      .then((data) => {
        setMessage(data.message);
        alert("New employee added successfully!"); 
        setNewEmployee({ name: "", email: "", role: "employee", password: "" });
        setShowAddEmployeeForm(false);
      })
      .catch((err) => console.error("Error creating employee:", err));
  };

  const handleNameBlur = (id) => {
    if (editedName.trim() === "") return; // Do not submit empty names
    handleEditField(id, "name", editedName); // Submit the name change
  };

  return (
    <div className="dashboard-container">
      <h1 className="dashboard-title">Admin Dashboard</h1>

      <button
        className="add-employee-button"
        onClick={() => setShowAddEmployeeForm(true)}
      >
        Add New Employee
      </button>

      {loading ? (
        <p>Loading employees...</p>
      ) : (
        <div className="employee-list">
          <h2>Employees</h2>

          {/* Header Row */}
          <div className="employee-header-row">
            <div className="employee-header-cell">Name</div>
            <div className="employee-header-cell">Job Schedule</div>
            <div className="employee-header-cell">Clock-In Status</div>
            <div className="employee-header-cell">Attendance</div>
            <div className="employee-header-cell">Leave Days</div>
            <div className="employee-header-cell">Warnings</div>
            <div className="employee-header-cell">Skills</div>
          </div>

          {/* Employee Rows */}
          {employees.map((emp, index) => (
            <div
              key={emp.id}
              className={`employee-row ${
                index % 2 === 0 ? "even-row" : "odd-row"
              }`}
            >
              <div className="employee-cell employee-name">
                {editingId === emp.id ? (
                  <input
                    type="text"
                    value={editedName || emp.name}
                    onChange={(e) => setEditedName(e.target.value)}
                    onBlur={() => handleNameBlur(emp.id)} // Submit on blur
                    autoFocus
                  />
                ) : (
                  <span
                    onClick={() => {
                      setEditingId(emp.id);
                      setEditedName(emp.name);
                    }}
                  >
                    {emp.name}
                  </span>
                )}
              </div>
              <div className="employee-cell">
                <div>
                  <label>Select Date:</label>
                  <DatePicker
                    selected={selectedDate}
                    onChange={(date) => setSelectedDate(date)}
                    dateFormat="dd-mm-yyyy"
                  />
                </div>
                <div>
                  <label>Select Shift:</label>
                  <select
                    value={selectedShift}
                    onChange={(e) => setSelectedShift(e.target.value)}
                  >
                    <option value="day">Day Shift</option>
                    <option value="night">Night Shift</option>
                  </select>
                </div>
                <button
                  onClick={() => {
                    if (selectedDate) {
                      const formattedDate = selectedDate.toISOString().split("T")[0];
                      const jobSchedule = `${formattedDate} (${selectedShift})`;
                      handleEditField(emp.id, "job_schedule", jobSchedule);
                    } else {
                      alert("Please select a date.");
                    }
                  }}
                >
                  Save
                </button>
              </div>
              <div className="employee-cell">
                <strong>{emp.clock_in_status}</strong>
              </div>
              <div className="employee-cell">{emp.attendance || "N/A"}</div>
              <div className="employee-cell">
                <input
                  type="number"
                  value={emp.leave_days || 0}
                  onChange={(e) =>
                    handleEditField(emp.id, "leave_days", e.target.value)
                  }
                />
              </div>
              <div className="employee-cell">
                <input
                  type="text"
                  value={emp.warnings || ""}
                  onChange={(e) =>
                    handleEditField(emp.id, "warnings", e.target.value)
                  }
                />
              </div>
              <div className="employee-cell employee-skills">
                <input
                  type="text"
                  value={emp.skills || ""}
                  onChange={(e) =>
                    handleEditField(emp.id, "skills", e.target.value)
                  }
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {showAddEmployeeForm && (
        <div className="add-employee-form">
          <h2>Add New Employee</h2>
          <input
            type="text"
            placeholder="Employee Name"
            value={newEmployee.name}
            onChange={(e) =>
              setNewEmployee({ ...newEmployee, name: e.target.value })
            }
          />
          <input
            type="email"
            placeholder="Employee Email"
            value={newEmployee.email}
            onChange={(e) =>
              setNewEmployee({ ...newEmployee, email: e.target.value })
            }
          />
          <input
            type="password"
            placeholder="Password"
            value={newEmployee.password}
            onChange={(e) =>
              setNewEmployee({ ...newEmployee, password: e.target.value })
            }
          />
          <select
            value={newEmployee.role}
            onChange={(e) =>
              setNewEmployee({ ...newEmployee, role: e.target.value })
            }
          >
            <option value="employee">Employee</option>
            <option value="admin">Admin</option>
          </select>
          <button onClick={handleAddEmployee}>Add Employee</button>
          <button onClick={() => setShowAddEmployeeForm(false)}>Cancel</button>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
