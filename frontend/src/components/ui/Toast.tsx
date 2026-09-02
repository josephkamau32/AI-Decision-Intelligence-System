import React from 'react';
import { useToast } from '../../context/ToastProvider';
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from 'lucide-react';
import styles from './Toast.module.css';

const Toast: React.FC = () => {
    const { toasts, removeToast } = useToast();

    if (toasts.length === 0) return null;

    const getIcon = (type: string) => {
        switch (type) {
            case 'success':
                return <CheckCircle2 className={styles.icon} size={16} />;
            case 'error':
                return <XCircle className={styles.icon} size={16} />;
            case 'warning':
                return <AlertTriangle className={styles.icon} size={16} />;
            case 'info':
            default:
                return <Info className={styles.icon} size={16} />;
        }
    };

    return (
        <div className={styles.container}>
            {toasts.map((toast) => (
                <div
                    key={toast.id}
                    className={`${styles.toast} ${styles[toast.type]}`}
                    role="alert"
                >
                    <div className={styles.content}>
                        {getIcon(toast.type)}
                        <p className={styles.message}>{toast.message}</p>
                    </div>
                    <button
                        onClick={() => removeToast(toast.id)}
                        className={styles.closeButton}
                        aria-label="Close"
                    >
                        <X size={14} />
                    </button>
                </div>
            ))}
        </div>
    );
};

export default Toast;
