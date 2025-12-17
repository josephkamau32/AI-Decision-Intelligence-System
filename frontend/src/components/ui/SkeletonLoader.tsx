import React from 'react';
import styles from './SkeletonLoader.module.css';

interface SkeletonLoaderProps {
    variant?: 'text' | 'rect' | 'circle';
    width?: string | number;
    height?: string | number;
    count?: number;
    className?: string;
}

const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
    variant = 'text',
    width,
    height,
    count = 1,
    className = ''
}) => {
    const getStyle = () => {
        const style: React.CSSProperties = {};
        if (width) style.width = typeof width === 'number' ? `${width}px` : width;
        if (height) style.height = typeof height === 'number' ? `${height}px` : height;
        return style;
    };

    const skeletonClasses = [
        styles.skeleton,
        styles[variant],
        className
    ].filter(Boolean).join(' ');

    return (
        <>
            {Array.from({ length: count }).map((_, index) => (
                <div key={index} className={skeletonClasses} style={getStyle()} />
            ))}
        </>
    );
};

export default SkeletonLoader;
