import React from 'react';
import ChatInterface from '../components/ChatInterface';
import styles from './CopilotChat.module.css';

const CopilotChat: React.FC = () => {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>AI Copilot</h1>
        <p className={styles.subtitle}>
          Ask questions about your datasets, models, and analytics in plain English
        </p>
      </div>
      <div className={styles.chatWrapper}>
        <ChatInterface />
      </div>
    </div>
  );
};

export default CopilotChat;