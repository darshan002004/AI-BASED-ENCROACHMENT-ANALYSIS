import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('encrowatch_user');
    try {
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  });
  const [token, setToken] = useState(() => localStorage.getItem('encrowatch_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const storedToken = localStorage.getItem('encrowatch_token');
      if (storedToken) {
        try {
          const res = await authAPI.getMe();
          if (res.data && res.data.role) {
            setUser(res.data);
            localStorage.setItem('encrowatch_user', JSON.stringify(res.data));
          } else {
            throw new Error('User profile missing role');
          }
        } catch (err) {
          console.warn('Session expired or invalid, resetting authentication state');
          localStorage.removeItem('encrowatch_token');
          localStorage.removeItem('encrowatch_user');
          setToken(null);
          setUser(null);
        }
      } else {
        // Unauthenticated visitor: do not auto-login to any role
        setUser(null);
        setToken(null);
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email, password) => {
    const res = await authAPI.login({ email, password });
    const { access_token, user: userData } = res.data;
    if (!userData || !userData.role) {
      throw new Error('Authenticated user record does not specify an authorized role');
    }
    localStorage.setItem('encrowatch_token', access_token);
    localStorage.setItem('encrowatch_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const register = async (userData) => {
    const res = await authAPI.register(userData);
    const { access_token, user: userProfile } = res.data;
    localStorage.setItem('encrowatch_token', access_token);
    localStorage.setItem('encrowatch_user', JSON.stringify(userProfile));
    setToken(access_token);
    setUser(userProfile);
    return userProfile;
  };

  const registerOfficer = async (officerData) => {
    const res = await authAPI.registerOfficer(officerData);
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('encrowatch_token');
    localStorage.removeItem('encrowatch_user');
    setToken(null);
    setUser(null);
  };

  const demoSwitch = async (targetRole) => {
    try {
      const res = await authAPI.demoSwitch(targetRole);
      const { access_token, user: userData } = res.data;
      if (!userData || !userData.role) {
        throw new Error('Demo switch returned invalid user data');
      }
      localStorage.setItem('encrowatch_token', access_token);
      localStorage.setItem('encrowatch_user', JSON.stringify(userData));
      setToken(access_token);
      setUser(userData);
      return userData;
    } catch (err) {
      console.error('Demo switch failed:', err);
      throw err;
    }
  };

  const userRole = user?.role ? String(user.role).toLowerCase() : null;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role: userRole,
        isAuthenticated: !!token && !!userRole,
        loading,
        login,
        register,
        registerOfficer,
        logout,
        demoSwitch,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
