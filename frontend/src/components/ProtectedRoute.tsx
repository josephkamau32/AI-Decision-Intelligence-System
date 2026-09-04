import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Spinner from './ui/Spinner';

interface ProtectedRouteProps {
    children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
    const { isAuthenticated, isLoading } = useAuth();
    const [isDelayed, setIsDelayed] = useState(false);

    useEffect(() => {
        let timer: NodeJS.Timeout;
        if (isLoading) {
            timer = setTimeout(() => {
                setIsDelayed(true);
            }, 3000);
        }
        return () => {
            if (timer) clearTimeout(timer);
        };
    }, [isLoading]);

    if (isLoading) {
        return (
            <div style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100vh',
                gap: '16px',
                padding: '24px',
                textAlign: 'center',
                background: 'var(--bg-primary, #09090b)',
                color: 'var(--text-secondary, #a1a1aa)'
            }}>
                <Spinner size="lg" />
                <p style={{ fontSize: '1rem', fontWeight: 500, margin: 0, color: 'var(--text-primary, #f4f4f5)' }}>
                    {isDelayed ? 'Waking up the backend service...' : 'Verifying session...'}
                </p>
                {isDelayed && (
                    <p style={{ fontSize: '0.85rem', maxWidth: '420px', margin: 0, opacity: 0.85 }}>
                        Render free-tier instances sleep when idle. Booting up can take up to ~50 seconds on initial visit.
                    </p>
                )}
            </div>
        );
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
};

export default ProtectedRoute;
