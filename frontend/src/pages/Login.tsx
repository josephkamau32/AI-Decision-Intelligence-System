import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Sparkles, Info, ArrowLeft, Loader2 } from 'lucide-react';
import styles from './Login.module.css';

const Login: React.FC = () => {
    const [formData, setFormData] = useState({ username: '', password: '' });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await login(formData.username, formData.password);
            navigate('/dashboard');
        } catch (err: any) {
            setError(err.message || 'Invalid credentials. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.authPage}>
            {/* Left Panel */}
            <div className={styles.authPanel}>
                <div className={styles.panelContent}>
                    <Link to="/" className={styles.panelLogo}>
                        <div className={styles.logoMark}><Sparkles size={16} /></div>
                        <span className={styles.logoText}>Decisera</span>
                    </Link>

                    <div className={styles.panelHero}>
                        <h1 className={styles.panelTitle}>Transform data into decisions with AI</h1>
                        <p className={styles.panelDesc}>
                            Upload any dataset. Get insights, forecasts, and explanations automatically.
                        </p>
                    </div>

                    <div className={styles.panelStats}>
                        <div className={styles.panelStat}>
                            <span className={styles.statValue}>12+</span>
                            <span className={styles.statLabel}>AutoML Algorithms</span>
                        </div>
                        <div className={styles.panelStatDivider} />
                        <div className={styles.panelStat}>
                            <span className={styles.statValue}>Real-time</span>
                            <span className={styles.statLabel}>SHAP Explanations</span>
                        </div>
                        <div className={styles.panelStatDivider} />
                        <div className={styles.panelStat}>
                            <span className={styles.statValue}>NLP</span>
                            <span className={styles.statLabel}>Data Queries</span>
                        </div>
                    </div>
                </div>
                <div className={styles.panelPattern} />
            </div>

            {/* Right Panel - Form */}
            <div className={styles.authForm}>
                <div className={styles.formContainer}>
                    <Link to="/" className={styles.backLink}>
                        <ArrowLeft size={14} />
                        Back to Home
                    </Link>

                    <div className={styles.formHeader}>
                        <h2 className={styles.formTitle}>Welcome back</h2>
                        <p className={styles.formSubtitle}>Sign in to your account to continue</p>
                    </div>

                    {/* Demo Credentials */}
                    <div className={styles.demoBanner}>
                        <Info size={16} className={styles.demoIcon} />
                        <div>
                            <div className={styles.demoLabel}>Demo Account</div>
                            <div className={styles.demoCreds}>
                                Register a new account to try the platform
                            </div>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className={styles.form}>
                        {error && (
                            <div className={styles.errorBanner}>
                                {error}
                            </div>
                        )}

                        <div className={styles.field}>
                            <label className={styles.label} htmlFor="username">Username</label>
                            <input
                                id="username"
                                type="text"
                                className={styles.input}
                                placeholder="Enter your username"
                                value={formData.username}
                                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                                required
                                disabled={loading}
                                autoComplete="username"
                            />
                        </div>

                        <div className={styles.field}>
                            <label className={styles.label} htmlFor="password">Password</label>
                            <input
                                id="password"
                                type="password"
                                className={styles.input}
                                placeholder="Enter your password"
                                value={formData.password}
                                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                required
                                disabled={loading}
                                autoComplete="current-password"
                            />
                        </div>

                        <button type="submit" className={styles.submitBtn} disabled={loading}>
                            {loading ? (
                                <>
                                    <Loader2 size={16} className={styles.spinIcon} />
                                    Signing in...
                                </>
                            ) : 'Sign In'}
                        </button>
                    </form>

                    <p className={styles.formFooter}>
                        Don't have an account? <Link to="/register">Create one</Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Login;
