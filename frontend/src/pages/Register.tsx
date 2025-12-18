import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import styles from './Login.module.css';

const Register: React.FC = () => {
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
    });
    const [errors, setErrors] = useState<{ [key: string]: string }>({});
    const [loading, setLoading] = useState(false);

    const { register } = useAuth();
    const navigate = useNavigate();

    const validateForm = () => {
        const newErrors: { [key: string]: string } = {};

        if (formData.username.length < 3) {
            newErrors.username = 'Username must be at least 3 characters';
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.email)) {
            newErrors.email = 'Please enter a valid email address';
        }

        if (formData.password.length < 6) {
            newErrors.password = 'Password must be at least 6 characters';
        }

        if (formData.password !== formData.confirmPassword) {
            newErrors.confirmPassword = 'Passwords do not match';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const getPasswordStrength = (password: string) => {
        if (password.length < 6) return 0;
        if (password.length < 8) return 1;
        if (password.length >= 8 && /[A-Z]/.test(password) && /[0-9]/.test(password)) return 3;
        return 2;
    };

    const passwordStrength = getPasswordStrength(formData.password);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        setLoading(true);

        try {
            await register(formData.username, formData.email, formData.password);
            navigate('/dashboard');
        } catch (err: any) {
            setErrors({
                submit: err.response?.data?.detail || 'Registration failed. Please try again.'
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.authPage}>
            {/* Left Panel - Branding */}
            <div className={styles.authPanel}>
                <div className={styles.authBranding}>
                    <div className={styles.authLogo}>
                        <svg viewBox="0 0 24 24" fill="currentColor">
                            <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        <span className={styles.authLogoText}>AI Decision Intelligence</span>
                    </div>

                    <h1 className={styles.authTagline}>
                        Start your data-driven journey today
                    </h1>
                    <p className={styles.authDescription}>
                        Join thousands of data professionals using AI to make better decisions faster.
                        No credit card required.
                    </p>
                </div>

                <div className={styles.authFeatures}>
                    <div className={styles.authFeature}>
                        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Free forever for individual use</span>
                    </div>
                    <div className={styles.authFeature}>
                        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>No credit card required</span>
                    </div>
                    <div className={styles.authFeature}>
                        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Enterprise-grade security</span>
                    </div>
                    <div className={styles.authFeature}>
                        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Setup in under 2 minutes</span>
                    </div>
                </div>
            </div>

            {/* Right Panel - Form */}
            <div className={styles.authForm}>
                <div className={styles.authFormContent}>
                    <Link to="/" className={styles.backLink}>
                        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                        </svg>
                        Back to Home
                    </Link>

                    <div className={styles.formHeader}>
                        <h2 className={styles.formTitle}>Create your account</h2>
                        <p className={styles.formSubtitle}>
                            Get started with AI-powered data analysis in minutes
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className={styles.form}>
                        {errors.submit && (
                            <div className={styles.error}>
                                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                {errors.submit}
                            </div>
                        )}

                        <div className={styles.formGroup}>
                            <label className={styles.label} htmlFor="username">
                                Username
                            </label>
                            <input
                                id="username"
                                type="text"
                                className={styles.input}
                                placeholder="Choose a username"
                                value={formData.username}
                                onChange={(e) => {
                                    setFormData({ ...formData, username: e.target.value });
                                    if (errors.username) {
                                        const newErrors = { ...errors };
                                        delete newErrors.username;
                                        setErrors(newErrors);
                                    }
                                }}
                                required
                                disabled={loading}
                                autoComplete="username"
                            />
                            {errors.username && (
                                <span className={styles.error}>{errors.username}</span>
                            )}
                        </div>

                        <div className={styles.formGroup}>
                            <label className={styles.label} htmlFor="email">
                                Email Address
                            </label>
                            <input
                                id="email"
                                type="email"
                                className={styles.input}
                                placeholder="your.email@company.com"
                                value={formData.email}
                                onChange={(e) => {
                                    setFormData({ ...formData, email: e.target.value });
                                    if (errors.email) {
                                        const newErrors = { ...errors };
                                        delete newErrors.email;
                                        setErrors(newErrors);
                                    }
                                }}
                                required
                                disabled={loading}
                                autoComplete="email"
                            />
                            {errors.email && (
                                <span className={styles.error}>{errors.email}</span>
                            )}
                        </div>

                        <div className={styles.formGroup}>
                            <label className={styles.label} htmlFor="password">
                                Password
                            </label>
                            <input
                                id="password"
                                type="password"
                                className={styles.input}
                                placeholder="Create a strong password"
                                value={formData.password}
                                onChange={(e) => {
                                    setFormData({ ...formData, password: e.target.value });
                                    if (errors.password) {
                                        const newErrors = { ...errors };
                                        delete newErrors.password;
                                        setErrors(newErrors);
                                    }
                                }}
                                required
                                disabled={loading}
                                autoComplete="new-password"
                            />
                            {formData.password && (
                                <div className={styles.passwordStrength}>
                                    <div className={`${styles.strengthBar} ${passwordStrength >= 1 ? styles.weak : ''}`}></div>
                                    <div className={`${styles.strengthBar} ${passwordStrength >= 2 ? styles.medium : ''}`}></div>
                                    <div className={`${styles.strengthBar} ${passwordStrength >= 3 ? styles.strong : ''}`}></div>
                                </div>
                            )}
                            {errors.password && (
                                <span className={styles.error}>{errors.password}</span>
                            )}
                        </div>

                        <div className={styles.formGroup}>
                            <label className={styles.label} htmlFor="confirmPassword">
                                Confirm Password
                            </label>
                            <input
                                id="confirmPassword"
                                type="password"
                                className={styles.input}
                                placeholder="Re-enter your password"
                                value={formData.confirmPassword}
                                onChange={(e) => {
                                    setFormData({ ...formData, confirmPassword: e.target.value });
                                    if (errors.confirmPassword) {
                                        const newErrors = { ...errors };
                                        delete newErrors.confirmPassword;
                                        setErrors(newErrors);
                                    }
                                }}
                                required
                                disabled={loading}
                                autoComplete="new-password"
                            />
                            {errors.confirmPassword && (
                                <span className={styles.error}>{errors.confirmPassword}</span>
                            )}
                        </div>

                        <button
                            type="submit"
                            className={styles.submitButton}
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <svg className="animate-spin" fill="none" viewBox="0 0 24 24" width="20" height="20">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Creating account...
                                </>
                            ) : (
                                'Create Account'
                            )}
                        </button>
                    </form>

                    <div className={styles.formFooter}>
                        Already have an account?{' '}
                        <Link to="/login">Sign in</Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Register;
