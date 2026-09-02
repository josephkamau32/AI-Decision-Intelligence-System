import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
    Upload, Cpu, MessageSquare, BarChart3, Database,
    Zap, Shield, BrainCircuit, Users, LineChart,
    ArrowRight, Menu, X, Sparkles
} from 'lucide-react';
import styles from './LandingPage.module.css';

const LandingPage: React.FC = () => {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    const steps = [
        { icon: <Upload size={20} />, title: 'Upload Data', desc: 'Drop your CSV, Excel, or JSON files. We handle the rest.' },
        { icon: <Cpu size={20} />, title: 'AI Trains Models', desc: 'AutoML selects the best algorithms and trains models automatically.' },
        { icon: <MessageSquare size={20} />, title: 'Ask Questions', desc: 'Our AI Copilot understands your business questions naturally.' },
        { icon: <BarChart3 size={20} />, title: 'Visualize & Act', desc: 'Interactive dashboards reveal insights. Export or share instantly.' },
    ];

    const features = [
        { icon: <Database size={18} />, title: 'Automated Data Profiling', desc: 'Instant insights into data quality, distributions, and anomalies.' },
        { icon: <Zap size={18} />, title: 'AutoML & Forecasting', desc: 'Train 12+ models simultaneously. Prophet & LSTM for time-series.' },
        { icon: <MessageSquare size={18} />, title: 'AI Copilot for Insights', desc: 'Chat with your data. Ask complex questions in natural language.' },
        { icon: <BarChart3 size={18} />, title: 'Explainable AI (SHAP)', desc: 'Understand why models make predictions. Trust through transparency.' },
        { icon: <Shield size={18} />, title: 'Enterprise MLOps', desc: 'MLflow tracking, monitoring, automated retraining, and drift detection.' },
    ];

    const audiences = [
        { icon: <LineChart size={20} />, title: 'Data Analysts', desc: 'Automate repetitive analysis. Focus on strategic insights.' },
        { icon: <BarChart3 size={20} />, title: 'Product Managers', desc: 'Make data-backed decisions faster. No SQL required.' },
        { icon: <Users size={20} />, title: 'Business Leaders', desc: 'Get actionable insights in seconds. Not hours.' },
        { icon: <BrainCircuit size={20} />, title: 'AI Engineers', desc: 'Deploy models faster. Monitor performance in production.' },
    ];

    const techStack = ['FastAPI', 'MLflow', 'PyTorch', 'XGBoost', 'LightGBM', 'Prophet', 'OpenAI', 'Prometheus'];

    return (
        <div className={styles.page}>
            {/* Header */}
            <header className={styles.header}>
                <div className={styles.headerInner}>
                    <Link to="/" className={styles.logo}>
                        <div className={styles.logoMark}>
                            <Sparkles size={16} />
                        </div>
                        <span className={styles.logoText}>Decisera</span>
                    </Link>

                    <nav className={`${styles.nav} ${mobileMenuOpen ? styles.navOpen : ''}`}>
                        <Link to="/login" className={styles.navLink} onClick={() => setMobileMenuOpen(false)}>Sign In</Link>
                        <Link to="/register" className={styles.navCta} onClick={() => setMobileMenuOpen(false)}>Get Started Free</Link>
                    </nav>

                    <button
                        className={styles.menuToggle}
                        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                        aria-label="Toggle menu"
                    >
                        {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
                    </button>
                </div>
            </header>

            {/* Hero */}
            <section className={styles.hero}>
                <div className={styles.heroInner}>
                    <div className={styles.heroContent}>
                        <h1 className={styles.heroTitle}>
                            Turn Raw Data into{' '}
                            <span className={styles.heroGradient}>Decisions with AI</span>
                        </h1>
                        <p className={styles.heroSubtitle}>
                            Upload any dataset. Get insights, forecasts, and explanations — automatically. No coding required.
                        </p>
                        <div className={styles.heroCtas}>
                            <Link to="/register" className={styles.ctaPrimary}>
                                Get Started Free
                                <ArrowRight size={16} />
                            </Link>
                            <Link to="/login" className={styles.ctaOutline}>
                                Sign In
                            </Link>
                        </div>
                    </div>
                    <div className={styles.heroVisual}>
                        <img
                            src="/hero-dashboard.jpg"
                            alt="Decisera analytics dashboard"
                            className={styles.heroImage}
                        />
                        <div className={styles.heroGlow} />
                    </div>
                </div>
            </section>

            {/* How It Works */}
            <section className={styles.section}>
                <div className={styles.container}>
                    <h2 className={styles.sectionTitle}>How It Works</h2>
                    <p className={styles.sectionSubtitle}>Four simple steps to data-driven decisions</p>

                    <div className={styles.stepsRow}>
                        {steps.map((step, i) => (
                            <div key={i} className={styles.step}>
                                <div className={styles.stepNumber}>{i + 1}</div>
                                <div className={styles.stepIcon}>{step.icon}</div>
                                <h3 className={styles.stepTitle}>{step.title}</h3>
                                <p className={styles.stepDesc}>{step.desc}</p>
                                {i < steps.length - 1 && <div className={styles.stepConnector} />}
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Features */}
            <section className={`${styles.section} ${styles.sectionAlt}`}>
                <div className={styles.container}>
                    <h2 className={styles.sectionTitle}>Enterprise-Grade Capabilities</h2>
                    <p className={styles.sectionSubtitle}>Everything you need for data-driven decision making</p>

                    <div className={styles.featuresGrid}>
                        {features.map((feat, i) => (
                            <div key={i} className={styles.featureCard}>
                                <div className={styles.featureIcon}>{feat.icon}</div>
                                <h3 className={styles.featureTitle}>{feat.title}</h3>
                                <p className={styles.featureDesc}>{feat.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Built for Teams */}
            <section className={styles.section}>
                <div className={styles.container}>
                    <h2 className={styles.sectionTitle}>Built for Teams</h2>
                    <p className={styles.sectionSubtitle}>Trusted by data professionals across industries</p>

                    <div className={styles.audienceGrid}>
                        {audiences.map((aud, i) => (
                            <div key={i} className={styles.audienceCard}>
                                <div className={styles.audienceIcon}>{aud.icon}</div>
                                <h3 className={styles.audienceTitle}>{aud.title}</h3>
                                <p className={styles.audienceDesc}>{aud.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Tech Stack */}
            <section className={`${styles.section} ${styles.sectionAlt}`}>
                <div className={styles.container}>
                    <h2 className={styles.sectionTitle}>Powered by Industry-Leading Technology</h2>
                    <div className={styles.techList}>
                        {techStack.map((tech, i) => (
                            <React.Fragment key={i}>
                                <span className={styles.techItem}>{tech}</span>
                                {i < techStack.length - 1 && <span className={styles.techDot}>·</span>}
                            </React.Fragment>
                        ))}
                    </div>
                </div>
            </section>

            {/* Final CTA */}
            <section className={styles.finalCta}>
                <div className={styles.container}>
                    <h2 className={styles.ctaHeading}>Start Making Data-Driven Decisions Today</h2>
                    <p className={styles.ctaSubheading}>
                        Join teams using AI to transform raw data into actionable insights
                    </p>
                    <Link to="/register" className={styles.ctaPrimary}>
                        Get Started Free
                        <ArrowRight size={16} />
                    </Link>
                </div>
            </section>

            {/* Footer */}
            <footer className={styles.footer}>
                <div className={styles.footerInner}>
                    <div className={styles.footerBrand}>
                        <div className={styles.logoMark}><Sparkles size={14} /></div>
                        <span className={styles.footerLogoText}>Decisera</span>
                    </div>
                    <div className={styles.footerLinks}>
                        <Link to="/login">Sign In</Link>
                        <Link to="/register">Get Started</Link>
                    </div>
                    <p className={styles.copyright}>© {new Date().getFullYear()} Decisera. All rights reserved.</p>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
