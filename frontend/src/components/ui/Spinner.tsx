import React from 'react';
import styles from './Spinner.module.css';

interface SpinnerProps {
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

const Spinner: React.FC<SpinnerProps> = ({ size = 'md', className = '' }) => {
    const classes = [styles.spinner, styles[size], className].filter(Boolean).join(' ');

    return (
        <div className={classes} role="status" aria-label="Loading">
            <svg viewBox="0 0 50 50">
                <circle className={styles.path} cx="25" cy="25" r="20" fill="none" strokeWidth="4" />
            </svg>
        </div>
    );
};

export default Spinner;
