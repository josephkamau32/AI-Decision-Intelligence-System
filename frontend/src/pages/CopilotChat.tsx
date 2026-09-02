import React from 'react';
import ChatInterface from '../components/ChatInterface';
import styles from './CopilotChat.module.css';

const CopilotChat: React.FC = () => {
    return (
        <div className={styles.container}>
            <ChatInterface />
        </div>
    );
};

export default CopilotChat;