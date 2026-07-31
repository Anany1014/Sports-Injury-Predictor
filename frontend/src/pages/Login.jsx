// src/pages/Login.jsx
import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Activity, ShieldCheck, UserCheck, Key, ShieldAlert } from 'lucide-react';
import './Login.css';

export default function Login() {
    const { login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    // Return route helper
    const from = location.state?.from?.pathname || '/dashboard';

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!username.trim() || !password.trim()) {
            setError('Please fill in check credentials');
            return;
        }

        try {
            setError(null);
            setLoading(true);
            await login(username.trim(), password.trim());
            navigate(from, { replace: true });
        } catch (err) {
            setError(err.message || 'Incorrect credentials');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            <div className="login-visual-glow" />

            <div className="login-card animate-fade-in">
                <div className="login-header">
                    <div className="login-logo">
                        <Activity className="pulse" size={28} />
                    </div>
                    <h1>Injury Predictor</h1>
                    <p>Secure Clinical Assessment Portal</p>
                </div>

                {error && (
                    <div className="login-error-banner animate-slide-up">
                        <ShieldAlert size={16} />
                        <span>{error}</span>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="form-group-login">
                        <label className="form-label-login">Username</label>
                        <div className="input-with-icon">
                            <UserCheck size={16} className="icon-field" />
                            <input
                                type="text"
                                className="input-login"
                                placeholder="Enter your username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                disabled={loading}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-group-login">
                        <label className="form-label-login">Password</label>
                        <div className="input-with-icon">
                            <Key size={16} className="icon-field" />
                            <input
                                type="password"
                                className="input-login"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                disabled={loading}
                                required
                            />
                        </div>
                    </div>

                    <button type="submit" className="btn-login" disabled={loading}>
                        {loading ? (
                            <span className="loader spin" />
                        ) : (
                            <>
                                <ShieldCheck size={16} />
                                <span>Initialize Secure Connection</span>
                            </>
                        )}
                    </button>
                </form>

                <div className="clinical-disclaimer">
                    <p>
                        Authorized medical staff and athlete administration connection only. HIPAA & GDPR compliance active.
                    </p>
                </div>
            </div>

            {/* Quick Access Sidebar for Testing */}
            <div className="clinical-accounts-widget card card-glow animate-fade-in">
                <h4>Dev Registry Simulator</h4>
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 12 }}>
                    Select credentials to pre-fill standard credentials:
                </p>
                <div className="credential-buttons">
                    <button onClick={() => { setUsername('alex'); setPassword('alex123'); }} className="btn-cred">
                        <strong>Athlete:</strong> alex / alex123
                    </button>
                    <button onClick={() => { setUsername('coach_dan'); setPassword('coach123'); }} className="btn-cred">
                        <strong>Coach:</strong> coach_dan / coach123
                    </button>
                    <button onClick={() => { setUsername('physio_sarah'); setPassword('physio123'); }} className="btn-cred">
                        <strong>Medical Staff:</strong> physio_sarah / physio123
                    </button>
                    <button onClick={() => { setUsername('admin'); setPassword('admin123'); }} className="btn-cred">
                        <strong>Admin:</strong> admin / admin123
                    </button>
                </div>
            </div>
        </div>
    );
}
