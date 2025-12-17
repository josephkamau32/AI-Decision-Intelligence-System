import React from 'react';
import styles from './Card.module.css';

interface CardProps {
    children: React.ReactNode;
    className?: string;
    variant?: 'default' | 'glass' | 'gradient';
    hoverable?: boolean;
    onClick?: () => void;
}

const Card: React.FC<CardProps> = ({
    children,
    className = '',
    variant = 'default',
    hoverable = false,
    onClick
}) => {
    const classes = [
        styles.card,
        styles[variant],
        hoverable && styles.hoverable,
        onClick && styles.clickable,
        className
    ].filter(Boolean).join(' ');

    return (
        <div className={classes} onClick={onClick}>
            {children}
        </div>
    );
};

export default Card;
