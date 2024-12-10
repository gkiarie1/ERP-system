import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));

  const login = (token, role) => {
    localStorage.setItem('token', token);
    localStorage.setItem('role', role);
    console.log(token, role);
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

  useEffect(() => {
    // Redirect to login if the user is not authenticated
    if (!isAuthenticated) {
      navigate('/login');
    }
    // Redirect to unauthorized access page if the route is admin-only and the user is not an admin
    if (adminOnly && role !== 'admin') {
      navigate('/unauthorized'); 
    }
  }, [isAuthenticated, role, adminOnly, navigate]);

  // Render the children if authentication checks pass
  if (!isAuthenticated || (adminOnly && role !== 'admin')) {
    return null; // Render nothing until the navigation is complete
  }

  return children;
};
