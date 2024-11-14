import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import EmployeeProfile from './components/EmployeeProfile';
import AdminDashboard from './components/AdminDashboard';
// import QRGenerator from './components/QRGenerator';
import Login from './components/Login';
import { AuthProvider, RequireAuth } from './components/AuthProvider';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/profile" element={<RequireAuth><EmployeeProfile /></RequireAuth>} />
          <Route path="/admin" element={<RequireAuth adminOnly={true}><AdminDashboard /></RequireAuth>} />
          {/* <Route path="/qr" element={<QRGenerator />} /> */}
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
