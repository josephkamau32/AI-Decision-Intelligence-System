import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
    id: string;
    username: string;
    email: string;
    role: string;
    is_active: boolean;
    created_at: string;
}

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (username: string, password: string) => Promise<void>;
    register: (username: string, email: string, password: string) => Promise<void>;
    logout: () => void;
    getToken: () => string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

interface AuthProviderProps {
    children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

    // Check for existing token on mount
    useEffect(() => {
        const token = localStorage.getItem('auth_token');
        if (token) {
            // Verify token and get user data
            fetchCurrentUser(token);
        } else {
            setIsLoading(false);
        }
    }, []);

    const fetchCurrentUser = async (token: string) => {
        try {
            const response = await fetch(`${API_URL}/api/v1/users/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
            } else {
                // Token is invalid, clear it
                localStorage.removeItem('auth_token');
                setUser(null);
            }
        } catch (error) {
            console.error('Failed to fetch user:', error);
            localStorage.removeItem('auth_token');
            setUser(null);
        } finally {
            setIsLoading(false);
        }
    };

    const parseErrorMessage = (data: any, defaultMsg: string): string => {
        if (!data) return defaultMsg;
        if (data.error && typeof data.error.message === 'string') {
            return data.error.message;
        }
        if (typeof data.detail === 'string') {
            return data.detail;
        }
        if (Array.isArray(data.detail) && data.detail.length > 0) {
            const msgs = data.detail.map((d: any) => d.msg || JSON.stringify(d)).join('; ');
            return msgs || defaultMsg;
        }
        if (typeof data.message === 'string') {
            return data.message;
        }
        return defaultMsg;
    };

    const login = async (username: string, password: string) => {
        try {
            const response = await fetch(`${API_URL}/api/v1/users/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });

            if (!response.ok) {
                let errorMsg = 'Login failed';
                try {
                    const errorData = await response.json();
                    errorMsg = parseErrorMessage(errorData, 'Login failed');
                } catch {
                    errorMsg = response.statusText || 'Login failed';
                }
                throw new Error(errorMsg);
            }

            const data = await response.json();
            const { access_token } = data;

            // Store token
            localStorage.setItem('auth_token', access_token);

            // Fetch user data
            await fetchCurrentUser(access_token);
        } catch (error) {
            throw error;
        }
    };

    const register = async (username: string, email: string, password: string) => {
        try {
            const response = await fetch(`${API_URL}/api/v1/users/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username,
                    email,
                    password,
                    role: 'user',
                }),
            });

            if (!response.ok) {
                let errorMsg = 'Registration failed';
                try {
                    const errorData = await response.json();
                    errorMsg = parseErrorMessage(errorData, 'Registration failed');
                } catch {
                    errorMsg = response.statusText || 'Registration failed';
                }
                throw new Error(errorMsg);
            }

            // Auto-login after registration
            await login(username, password);
        } catch (error) {
            throw error;
        }
    };

    const logout = () => {
        localStorage.removeItem('auth_token');
        setUser(null);
    };

    const getToken = () => {
        return localStorage.getItem('auth_token');
    };

    const value: AuthContextType = {
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        getToken,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
