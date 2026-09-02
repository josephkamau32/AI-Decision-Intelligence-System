import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useTheme } from '../../context/ThemeProvider';
import { Sun, Moon, CheckCircle2 } from 'lucide-react';
import styles from './Layout.module.css';
import Sidebar from './Sidebar';

interface LayoutProps {
    children: React.ReactNode;
}

const getBreadcrumb = (pathname: string): { section: string; title: string } => {
    switch (pathname) {
        case '/dashboard':
            return { section: 'Overview', title: 'Dashboard' };
        case '/dataset-overview':
            return { section: 'Data Management', title: 'Datasets' };
        case '/model-performance':
            return { section: 'Machine Learning', title: 'Model Performance' };
        case '/feature-importance':
            return { section: 'Explainability', title: 'Feature Importance' };
        case '/visual-insights':
            return { section: 'Analytics', title: 'Visual Insights' };
        case '/copilot':
            return { section: 'Intelligence', title: 'AI Copilot' };
        default:
            return { section: 'Decisera', title: 'Analytics' };
    }
};

const Layout: React.FC<LayoutProps> = ({ children }) => {
    const { theme, toggleTheme } = useTheme();
    const [collapsed, setCollapsed] = useState(false);
    const location = useLocation();
    const breadcrumb = getBreadcrumb(location.pathname);

    return (
        <div className={styles.layout}>
            <Sidebar
                collapsed={collapsed}
                onToggle={() => setCollapsed(!collapsed)}
            />

            <div className={`${styles.main} ${collapsed ? styles.mainCollapsed : ''}`}>
                <header className={styles.header}>
                    <div className={styles.headerContent}>
                        {/* Dynamic Breadcrumbs */}
                        <div className={styles.breadcrumb}>
                            <span className={styles.breadcrumbSection}>{breadcrumb.section}</span>
                            <span className={styles.breadcrumbDivider}>/</span>
                            <span className={styles.breadcrumbTitle}>{breadcrumb.title}</span>
                        </div>

                        <div className={styles.headerActions}>
                            {/* System Status Pill */}
                            <div className={styles.statusPill}>
                                <CheckCircle2 size={12} className={styles.statusIcon} />
                                <span>Engine Active</span>
                            </div>

                            {/* Theme Toggle Button */}
                            <button
                                className={styles.themeToggle}
                                onClick={toggleTheme}
                                aria-label="Toggle theme"
                                title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
                            >
                                {theme === 'light' ? (
                                    <Moon size={15} />
                                ) : (
                                    <Sun size={15} />
                                )}
                            </button>
                        </div>
                    </div>
                </header>

                <main className={styles.content}>
                    {children}
                </main>
            </div>
        </div>
    );
};

export default Layout;
