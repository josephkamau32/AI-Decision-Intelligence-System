import React, { useEffect, useState } from 'react';
import { subscribeBackendWarming } from '../../services/api';
import styles from './ServerWarmingBanner.module.css';

interface ServerWarmingBannerProps {
    forceShow?: boolean;
}

const ServerWarmingBanner: React.FC<ServerWarmingBannerProps> = ({ forceShow = false }) => {
    const [isWarming, setIsWarming] = useState(false);

    useEffect(() => {
        const unsubscribe = subscribeBackendWarming((warming) => {
            setIsWarming(warming);
        });
        return unsubscribe;
    }, []);

    if (!isWarming && !forceShow) {
        return null;
    }

    return (
        <div className={styles.banner} role="status" aria-live="polite">
            <span className={styles.pulseDot} />
            <div className={styles.text}>
                <span className={styles.highlight}>Waking up backend</span> — Render free-tier instance is spinning up from sleep (~50s cold start). Your request will complete automatically...
            </div>
        </div>
    );
};

export default ServerWarmingBanner;
