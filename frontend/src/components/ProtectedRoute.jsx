// src/components/ProtectedRoute.jsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert, Loader2 } from 'lucide-react';

export default function ProtectedRoute({ children, allowedRoles }) {
    const { user, loading } = useAuth();
    const location = useLocation();

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100vh',
                background: 'var(--bg-main)',
                color: 'var(--text-primary)'
            }}>
                <Loader2 size={36} className="spin" color="var(--cyan)" />
                <p style={{ marginTop: 12, fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                    Authenticating security session...
                </p>
            </div>
        );
    }

    if (!user) {
        // Redirect to login page and keep compile history redirect route
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    if (allowedRoles && !allowedRoles.includes(user.role)) {
        return (
            <div className="page animate-fade-in" style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: '70vh',
                textAlign: 'center',
                padding: 40
            }}>
                <div className="card card-glow" style={{
                    maxWidth: 480,
                    background: 'var(--bg-card)',
                    padding: 32,
                    border: '1px solid var(--border)',
                    borderRadius: 12,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center'
                }}>
                    <ShieldAlert size={54} color="var(--red)" style={{ marginBottom: 16 }} />
                    <h2 style={{ fontSize: '1.4rem', color: 'var(--text-primary)', marginBottom: 8 }}>
                        Access Denied
                    </h2>
                    <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: 20 }}>
                        Your role <strong>{user.role}</strong> does not possess the permissions necessary to access this feature.
                        This endpoint is limited to: {allowedRoles.join(', ')}.
                    </p>
                    <Navigate to="/dashboard" replace />
                </div>
            </div>
        );
    }

    return children;
}
