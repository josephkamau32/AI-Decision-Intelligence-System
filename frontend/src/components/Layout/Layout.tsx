import React from 'react';
import { useTheme } from '../../context/ThemeProvider';
import styles from './Layout.module.css';
import Sidebar from './Sidebar';

interface LayoutProps {
    children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
    const { theme, toggleTheme } = useTheme();

    return (
        <div className={styles.layout}>
            <Sidebar />

            <div className={styles.main}>
                <header className={styles.header}>
                    <div className={styles.headerContent}>
                        <div className={styles.breadcrumb}>
                            {/* Breadcrumb will be added dynamically */}
                        </div>

                        <div className={styles.headerActions}>
                            <button
                                className={styles.themeToggle}
                                onClick={toggleTheme}
                                aria-label="Toggle theme"
                                title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
                            >
                                {theme === 'light' ? (
                                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                                    </svg>
                                ) : (
                                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                                    </svg>
                                )}
                            </button>
                        </div>
                    </div>
                </header>

                <div className={styles.content}>
                    {children}
                </div>
            </div>
        </div>
    );
};

export default Layout;
