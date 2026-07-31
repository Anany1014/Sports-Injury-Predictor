// src/context/AuthContext.jsx
import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // Verification helper to check session validity on load
    const checkAuth = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/v1/auth/me', {
                headers: { 'Accept': 'application/json' },
                credentials: 'include',
            });
            if (res.ok) {
                const data = await res.json();
                setUser(data);
            } else {
                setUser(null);
            }
        } catch (err) {
            console.warn('Authentication status query failed:', err);
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        checkAuth();
    }, []);

    const login = async (username, password) => {
        const res = await fetch('http://localhost:8000/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password }),
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Login failed');
        }

        const userData = await res.json();
        setUser(userData);
        return userData;
    };

    const logout = async () => {
        try {
            await fetch('http://localhost:8000/api/v1/auth/logout', {
                method: 'POST',
                credentials: 'include',
            });
        } catch (err) {
            console.warn('Session logout API invocation encountered error:', err);
        } finally {
            setUser(null);
        }
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, logout, checkAuth }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);
