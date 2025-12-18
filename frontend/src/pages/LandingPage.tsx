import React from 'react';
import { Link } from 'react-router-dom';
import styles from './LandingPage.module.css';

const LandingPage: React.FC = () => {
    return (
        <div className={styles.landingPage}>
            {/* Header/Navigation */}
            <header className={styles.header}>
                <div className={styles.headerContainer}>
                    <div className={styles.logo}>
                        <svg viewBox="0 0 24 24" fill="currentColor" className={styles.logoIcon}>
                            <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        <span className={styles.logoText}>AI Decision Intelligence</span>
                    </div>
                    <nav className={styles.nav}>
                        <Link to="/login" className={styles.navLink}>Sign In</Link>
                        <Link to="/register" className={styles.navButtonPrimary}>Get Started Free</Link>
                    </nav>
                </div>
            </header>

            {/* Hero Section */}
            <section className={styles.hero}>
                <div className={styles.heroContainer}>
                    <div className={styles.heroContent}>
                        <h1 className={styles.heroTitle}>
                            Turn Raw Data into <span className={styles.gradient}>Decisions with AI</span>
                        </h1>
                        <p className={styles.heroSubtitle}>
                            Upload any dataset. Get insights, forecasts, and explanations — automatically.
                            No coding required.
                        </p>
                        <div className={styles.heroCTA}>
                            <Link to="/register" className={styles.ctaPrimary}>
                                Get Started Free
                                <svg className={styles.ctaIcon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                </svg>
                            </Link>
                            <Link to="/login" className={styles.ctaSecondary}>
                                View Demo
                                <svg className={styles.ctaIcon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </Link>
                        </div>
                    </div>
                    <div className={styles.heroImage}>
                        <div className={styles.heroImagePlaceholder}>
                            <svg viewBox="0 0 400 300" fill="none">
                                <rect width="400" height="300" rx="12" fill="url(#heroGradient)" />
                                <defs>
                                    <linearGradient id="heroGradient" x1="0" y1="0" x2="400" y2="300">
                                        <stop offset="0%" stopColor="#4f46e5" />
                                        <stop offset="100%" stopColor="#14b8a6" />
                                    </linearGradient>
                                </defs>
                                {/* Analytics visualization icons */}
                                <circle cx="100" cy="80" r="30" fill="white" opacity="0.2" />
                                <circle cx="300" cy="120" r="40" fill="white" opacity="0.25" />
                                <circle cx="200" cy="200" r="35" fill="white" opacity="0.3" />
                            </svg>
                        </div>
                    </div>
                </div>
            </section>

            {/* How It Works */}
            <section className={styles.howItWorks}>
                <div className={styles.container}>
                    <h2 className={styles.sectionTitle}>How It Works</h2>
                    <p className={styles.sectionSubtitle}>Four simple steps to data-driven decisions</p>

                    <div className={styles.stepsGrid}>
                        <div className={styles.step}>
                            <div className={styles.stepNumber}>1</div>
                            <div className={styles.stepIcon}>
                                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                </svg>
                            </div>
                            <h3 className={styles.stepTitle}>Upload Data</h3>
                            <p className={styles.stepDescription}>
                                Drop your CSV, Excel, or Parquet files. We handle the rest.
                            </p>
                        </div>

                        <div className={styles.step}>
                            <div className={styles.stepNumber}>2</div>
                            <div className={styles.stepIcon}>
                                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                                </svg>
                            </div>
                            <h3 className={styles.stepTitle}>AI Analyzes & Trains Models</h3>
                            <p className={styles.stepDescription}>
                                AutoML selects the best algorithms and trains models automatically.
                            </p>
                        </div>

                        <div className={styles.step}>
                            <div className={styles.stepNumber}>3</div>
                            <div className={styles.stepIcon}>
                                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                                </svg>
                            </div>
                            <h3 className={styles.stepTitle}>Ask Questions in Plain English</h3>
                            <p className={styles.stepDescription}>
                                Our AI Copilot understands your business questions naturally.
                            </p>
                        </div>

                        <div className={styles.step}>
                            <div className={styles.stepNumber}>4</div>
                            <div className={styles.stepIcon}>
                                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                                </svg>
                            </div>
                            <h3 className={styles.stepTitle}>Visualize & Act</h3>
                            <p className={styles.stepDescription}>
                                Interactive dashboards reveal insights. Export or share results instantly.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Key Features */}
            <section className={styles.features}>
                <div className={styles.container}>
                    <h2 className={styles.sectionTitle}>Enterprise-Grade Capabilities</h2>
                    <p className={styles.sectionSubtitle}>Everything you need for data-driven decision making</p>

                    <div className={styles.featuresGrid}>
                        <div className={styles.feature}>
                            <div className={styles.featureIcon}>
                                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                                </svg>
                            </div>
                            <h3 className={styles.featureTitle}>Automated Data Profiling</h3>
                            <p className={styles.featureDescription}>
                                Instant insights into data quality, distributions, and anomalies. No manual analysis.
                            </p>
                        </div>

                        <div className={styles.feature}>
                            <div className={styles.featureIcon}>
                                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                            </div>
                            <h3 className={styles.featureTitle}>AutoML & Forecasting</h3>
                            <p className={styles.featureDescription}>
                                Train 12+ models simultaneously. Prophet & LSTM for time-series predictions.
                            </p>
                        </div>

                        <div className={styles.feature}>
                            <div className={styles.featureIcon}>
                                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                                </svg>
                            </div>
                            <h3 className={styles.featureTitle}>AI Copilot for Insights</h3>
                            <p className={styles.featureDescription}>
                                Chat with your data. Ask complex questions in natural language.
                            </p>
                        </div>

                        <div className={styles.feature}>
                            <div className={styles.featureIcon}>
                                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                </svg>
                            </div>
                            <h3 className={styles.featureTitle}>Explainable AI (SHAP)</h3>
                            <p className={styles.featureDescription}>
                                Understand why models make predictions. Trust through transparency.
                            </p>
                        </div>

                        <div className={styles.feature}>
                            <div className={styles.featureIcon}>
                                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                </svg>
                            </div>
                            <h3 className={styles.featureTitle}>Enterprise MLOps</h3>
                            <p className={styles.featureDescription}>
                                MLflow tracking, Prometheus monitoring, automated retraining, and drift detection.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Who It's For */}
            <section className={styles.whoItsFor}>
                <div className={styles.container}>
                    <h2 className={styles.sectionTitle}>Built for Teams</h2>
                    <p className={styles.sectionSubtitle}>Trusted by data professionals across industries</p>

                    <div className={styles.audienceGrid}>
                        <div className={styles.audienceCard}>
                            <div className={styles.audienceIcon}>👨‍💼</div>
                            <h3 className={styles.audienceTitle}>Data Analysts</h3>
                            <p className={styles.audienceDescription}>
                                Automate repetitive analysis. Focus on strategic insights.
                            </p>
                        </div>

                        <div className={styles.audienceCard}>
                            <div className={styles.audienceIcon}>📊</div>
                            <h3 className={styles.audienceTitle}>Product Managers</h3>
                            <p className={styles.audienceDescription}>
                                Make data-backed decisions faster. No SQL required.
                            </p>
                        </div>

                        <div className={styles.audienceCard}>
                            <div className={styles.audienceIcon}>💼</div>
                            <h3 className={styles.audienceTitle}>Business Leaders</h3>
                            <p className={styles.audienceDescription}>
                                Get actionable insights in seconds. Not hours.
                            </p>
                        </div>

                        <div className={styles.audienceCard}>
                            <div className={styles.audienceIcon}>🤖</div>
                            <h3 className={styles.audienceTitle}>AI Engineers</h3>
                            <p className={styles.audienceDescription}>
                                Deploy models faster. Monitor performance in production.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Tech Stack */}
            <section className={styles.techStack}>
                <div className={styles.container}>
                    <h2 className={styles.sectionTitle}>Powered by Industry-Leading Technology</h2>
                    <div className={styles.techBadges}>
                        <div className={styles.techBadge}>FastAPI</div>
                        <div className={styles.techBadge}>MLflow</div>
                        <div className={styles.techBadge}>PyTorch</div>
                        <div className={styles.techBadge}>XGBoost</div>
                        <div className={styles.techBadge}>LightGBM</div>
                        <div className={styles.techBadge}>Prophet</div>
                        <div className={styles.techBadge}>OpenAI</div>
                        <div className={styles.techBadge}>Prometheus</div>
                    </div>
                </div>
            </section>

            {/* Final CTA */}
            <section className={styles.finalCTA}>
                <div className={styles.ctaContainer}>
                    <h2 className={styles.ctaTitle}>Start Making Data-Driven Decisions Today</h2>
                    <p className={styles.ctaSubtitle}>
                        Join teams using AI to transform raw data into actionable insights
                    </p>
                    <Link to="/register" className={styles.ctaButton}>
                        Get Started Free
                        <svg className={styles.ctaIcon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                    </Link>
                </div>
            </section>

            {/* Footer */}
            <footer className={styles.footer}>
                <div className={styles.footerContainer}>
                    <div className={styles.footerContent}>
                        <div className={styles.footerLogo}>
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                            <span>AI Decision Intelligence</span>
                        </div>
                        <p className={styles.footerText}>
                            Transform data into decisions with enterprise-grade AI
                        </p>
                    </div>
                    <div className={styles.footerLinks}>
                        <Link to="/login">Sign In</Link>
                        <Link to="/register">Get Started</Link>
                    </div>
                </div>
                <div className={styles.footerBottom}>
                    <p>© 2025 AI Decision Intelligence. All rights reserved.</p>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
