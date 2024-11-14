import React, { createContext, useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));

  const login = (token, role) => {
    localStorage.setItem('token', token);
    localStorage.setItem('role', role);
    setIsAuthenticated(true);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const RequireAuth = ({ children, adminOnly = false }) => {
  const { isAuthenticated } = useContext(AuthContext);
  const navigate = useNavigate();
  const role = localStorage.getItem('role');

  if (!isAuthenticated) {
    navigate('/login');
    return null;
  }

  if (adminOnly && role !== 'admin') {
    return <div>Unauthorized access</div>;
  }

  return children;
};
