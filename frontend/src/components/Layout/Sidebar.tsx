import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
    LayoutDashboard, Database, Cpu, BarChart3,
    LineChart, MessageSquare, PanelLeftClose,
    PanelLeft, LogOut, Sparkles
} from 'lucide-react';
import styles from './Sidebar.module.css';

interface NavItem {
    path: string;
    icon: React.ReactNode;
    label: string;
    badge?: string;
}

interface SidebarProps {
    collapsed: boolean;
    onToggle: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const mainNavItems: NavItem[] = [
        { path: '/dashboard', icon: <LayoutDashboard size={18} />, label: 'Dashboard' },
        { path: '/dataset-overview', icon: <Database size={18} />, label: 'Datasets' },
    ];

    const analyticsNavItems: NavItem[] = [
        { path: '/model-performance', icon: <Cpu size={18} />, label: 'Models' },
        { path: '/feature-importance', icon: <BarChart3 size={18} />, label: 'Feature Importance' },
        { path: '/visual-insights', icon: <LineChart size={18} />, label: 'Visual Insights' },
    ];

    const toolsNavItems: NavItem[] = [
        { path: '/copilot', icon: <MessageSquare size={18} />, label: 'AI Copilot', badge: 'AI' },
    ];

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const userInitials = user?.username
        ? user.username.slice(0, 2).toUpperCase()
        : 'U';

    const renderNavItem = (item: NavItem) => (
        <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.active : ''}`
            }
            title={collapsed ? item.label : undefined}
        >
            <span className={styles.navIcon}>{item.icon}</span>
            <span className={styles.navLabel}>{item.label}</span>
            {item.badge && <span className={styles.itemBadge}>{item.badge}</span>}
        </NavLink>
    );

    return (
        <aside className={`${styles.sidebar} ${collapsed ? styles.collapsed : ''}`}>
            {/* Header */}
            <div className={styles.header}>
                <div className={styles.logo}>
                    <div className={styles.logoIcon}>
                        <Sparkles size={14} className={styles.sparkleIcon} />
                    </div>
                    {!collapsed && (
                        <div className={styles.brandGroup}>
                            <span className={styles.logoText}>Decisera</span>
                            <span className={styles.logoBadge}>Intelligence</span>
                        </div>
                    )}
                </div>
                <button
                    className={styles.collapseButton}
                    onClick={onToggle}
                    aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                >
                    {collapsed ? <PanelLeft size={14} /> : <PanelLeftClose size={14} />}
                </button>
            </div>

            {/* Navigation */}
            <nav className={styles.nav}>
                <div className={styles.navSection}>
                    {!collapsed && <div className={styles.sectionTitle}>Overview</div>}
                    {mainNavItems.map(renderNavItem)}
                </div>

                <div className={styles.navSection}>
                    {!collapsed && <div className={styles.sectionTitle}>Analytics</div>}
                    {analyticsNavItems.map(renderNavItem)}
                </div>

                <div className={styles.navSection}>
                    {!collapsed && <div className={styles.sectionTitle}>Tools</div>}
                    {toolsNavItems.map(renderNavItem)}
                </div>
            </nav>

            {/* Footer */}
            <div className={styles.footer}>
                {collapsed ? (
                    <button
                        className={styles.collapsedLogoutBtn}
                        onClick={handleLogout}
                        title="Sign out"
                        aria-label="Sign out"
                    >
                        <LogOut size={16} />
                    </button>
                ) : (
                    <div className={styles.footerContent}>
                        <div className={styles.userInfo}>
                            <div className={styles.avatar}>{userInitials}</div>
                            <div className={styles.userDetails}>
                                <div className={styles.userName}>{user?.username || 'User'}</div>
                                <div className={styles.userStatus}>Active</div>
                            </div>
                        </div>
                        <button
                            className={styles.logoutIconBtn}
                            onClick={handleLogout}
                            title="Sign out"
                            aria-label="Sign out"
                        >
                            <LogOut size={14} />
                        </button>
                    </div>
                )}
            </div>
        </aside>
    );
};

export default Sidebar;
