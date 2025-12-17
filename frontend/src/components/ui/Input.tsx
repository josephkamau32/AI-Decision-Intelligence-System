import React, { InputHTMLAttributes, forwardRef } from 'react';
import styles from './Input.module.css';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
    helperText?: string;
    leftIcon?: React.ReactNode;
    rightIcon?: React.ReactNode;
    fullWidth?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
    ({
        label,
        error,
        helperText,
        leftIcon,
        rightIcon,
        fullWidth = false,
        className = '',
        ...props
    }, ref) => {
        const containerClasses = [
            styles.container,
            fullWidth && styles.fullWidth,
            className
        ].filter(Boolean).join(' ');

        const inputClasses = [
            styles.input,
            error && styles.error,
            leftIcon && styles.withLeftIcon,
            rightIcon && styles.withRightIcon
        ].filter(Boolean).join(' ');

        return (
            <div className={containerClasses}>
                {label && <label className={styles.label}>{label}</label>}
                <div className={styles.inputWrapper}>
                    {leftIcon && <span className={styles.iconLeft}>{leftIcon}</span>}
                    <input
                        ref={ref}
                        className={inputClasses}
                        {...props}
                    />
                    {rightIcon && <span className={styles.iconRight}>{rightIcon}</span>}
                </div>
                {error && <span className={styles.errorText}>{error}</span>}
                {!error && helperText && <span className={styles.helperText}>{helperText}</span>}
            </div>
        );
    }
);

Input.displayName = 'Input';

export default Input;
