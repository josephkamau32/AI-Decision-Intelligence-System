import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Sparkles, ArrowLeft, Loader2, Check, Circle } from 'lucide-react';
import styles from './Login.module.css';

interface PasswordValidation {
    minLength: boolean;
    hasUpper: boolean;
    hasLower: boolean;
    hasDigit: boolean;
    hasSpecial: boolean;
    isValid: boolean;
}

const checkPasswordRules = (pwd: string): PasswordValidation => {
    const minLength = pwd.length >= 8;
    const hasUpper = /[A-Z]/.test(pwd);
    const hasLower = /[a-z]/.test(pwd);
    const hasDigit = /\d/.test(pwd);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(pwd);
    const isValid = minLength && hasUpper && hasLower && hasDigit && hasSpecial;
    return { minLength, hasUpper, hasLower, hasDigit, hasSpecial, isValid };
};

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

    const pwdRules = checkPasswordRules(formData.password);

    const getPasswordStrength = (pwd: string): number => {
        if (!pwd) return 0;
        const rules = checkPasswordRules(pwd);
        const metCount = [rules.minLength, rules.hasUpper, rules.hasLower, rules.hasDigit, rules.hasSpecial].filter(Boolean).length;
        if (metCount <= 2) return 1;
        if (metCount <= 4) return 2;
        return 3;
    };

    const passwordStrength = getPasswordStrength(formData.password);

    const validateForm = () => {
        const newErrors: { [key: string]: string } = {};

        if (formData.username.length < 3) {
            newErrors.username = 'Username must be at least 3 characters';
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.email)) {
            newErrors.email = 'Please enter a valid email address';
        }

        const rules = checkPasswordRules(formData.password);
        if (!rules.isValid) {
            const missing: string[] = [];
            if (!rules.minLength) missing.push('at least 8 characters');
            if (!rules.hasUpper) missing.push('one uppercase letter');
            if (!rules.hasLower) missing.push('one lowercase letter');
            if (!rules.hasDigit) missing.push('one digit');
            if (!rules.hasSpecial) missing.push('one special character');
            newErrors.password = `Password must contain: ${missing.join(', ')}`;
        }

        if (formData.password !== formData.confirmPassword) {
            newErrors.confirmPassword = 'Passwords do not match';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateForm()) return;

        setLoading(true);
        try {
            await register(formData.username, formData.email, formData.password);
            navigate('/dashboard');
        } catch (err: any) {
            setErrors({
                submit: err.message || 'Registration failed. Please try again.'
            });
        } finally {
            setLoading(false);
        }
    };

    const ruleItems = [
        { met: pwdRules.minLength, label: 'At least 8 characters' },
        { met: pwdRules.hasUpper, label: 'One uppercase letter' },
        { met: pwdRules.hasLower, label: 'One lowercase letter' },
        { met: pwdRules.hasDigit, label: 'One digit' },
        { met: pwdRules.hasSpecial, label: 'One special character' },
    ];

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
                        <h1 className={styles.panelTitle}>Start making data-driven decisions today</h1>
                        <p className={styles.panelDesc}>
                            Create your account and start exploring your data with AI-powered insights in minutes.
                        </p>
                    </div>

                    <div className={styles.panelStats}>
                        <div className={styles.panelStat}>
                            <span className={styles.statValue}>Free</span>
                            <span className={styles.statLabel}>To Get Started</span>
                        </div>
                        <div className={styles.panelStatDivider} />
                        <div className={styles.panelStat}>
                            <span className={styles.statValue}>No Card</span>
                            <span className={styles.statLabel}>Required</span>
                        </div>
                        <div className={styles.panelStatDivider} />
                        <div className={styles.panelStat}>
                            <span className={styles.statValue}>Instant</span>
                            <span className={styles.statLabel}>Setup</span>
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
                        <h2 className={styles.formTitle}>Create your account</h2>
                        <p className={styles.formSubtitle}>Fill in your details to get started</p>
                    </div>

                    <form onSubmit={handleSubmit} className={styles.form}>
                        {errors.submit && (
                            <div className={styles.errorBanner}>{errors.submit}</div>
                        )}

                        <div className={styles.field}>
                            <label className={styles.label} htmlFor="reg-username">Username</label>
                            <input
                                id="reg-username"
                                type="text"
                                className={`${styles.input} ${errors.username ? styles.inputError : ''}`}
                                placeholder="Choose a username"
                                value={formData.username}
                                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                                required
                                disabled={loading}
                                autoComplete="username"
                            />
                            {errors.username && <span className={styles.errorBanner} style={{ padding: '6px 10px' }}>{errors.username}</span>}
                        </div>

                        <div className={styles.field}>
                            <label className={styles.label} htmlFor="reg-email">Email</label>
                            <input
                                id="reg-email"
                                type="email"
                                className={`${styles.input} ${errors.email ? styles.inputError : ''}`}
                                placeholder="your@email.com"
                                value={formData.email}
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                required
                                disabled={loading}
                                autoComplete="email"
                            />
                            {errors.email && <span className={styles.errorBanner} style={{ padding: '6px 10px' }}>{errors.email}</span>}
                        </div>

                        <div className={styles.field}>
                            <label className={styles.label} htmlFor="reg-password">Password</label>
                            <input
                                id="reg-password"
                                type="password"
                                className={`${styles.input} ${errors.password ? styles.inputError : ''}`}
                                placeholder="Create a strong password"
                                value={formData.password}
                                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                required
                                disabled={loading}
                                autoComplete="new-password"
                            />

                            {/* Strength Bar */}
                            {formData.password && (
                                <div className={styles.strengthBar}>
                                    <div className={`${styles.strengthSegment} ${passwordStrength >= 1 ? styles.strengthWeak : ''}`} />
                                    <div className={`${styles.strengthSegment} ${passwordStrength >= 2 ? styles.strengthMedium : ''}`} />
                                    <div className={`${styles.strengthSegment} ${passwordStrength >= 3 ? styles.strengthStrong : ''}`} />
                                </div>
                            )}

                            {/* Password Rules — Always visible */}
                            <div className={styles.passwordRules}>
                                {ruleItems.map((rule, i) => (
                                    <div key={i} className={`${styles.rule} ${rule.met ? styles.ruleMet : ''}`}>
                                        {rule.met
                                            ? <Check size={12} />
                                            : <Circle size={12} />
                                        }
                                        {rule.label}
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className={styles.field}>
                            <label className={styles.label} htmlFor="reg-confirm">Confirm Password</label>
                            <input
                                id="reg-confirm"
                                type="password"
                                className={`${styles.input} ${errors.confirmPassword ? styles.inputError : ''}`}
                                placeholder="Confirm your password"
                                value={formData.confirmPassword}
                                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                                required
                                disabled={loading}
                                autoComplete="new-password"
                            />
                            {errors.confirmPassword && <span className={styles.errorBanner} style={{ padding: '6px 10px' }}>{errors.confirmPassword}</span>}
                        </div>

                        <button type="submit" className={styles.submitBtn} disabled={loading}>
                            {loading ? (
                                <>
                                    <Loader2 size={16} className={styles.spinIcon} />
                                    Creating account...
                                </>
                            ) : 'Create Account'}
                        </button>
                    </form>

                    <p className={styles.formFooter}>
                        Already have an account? <Link to="/login">Sign in</Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Register;
