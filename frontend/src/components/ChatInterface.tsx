import React, { useState, useRef, useEffect } from 'react';
import { askCopilot } from '../services/copilotService';
import { useToast } from '../context/ToastProvider';
import Button from './ui/Button';
import styles from './ChatInterface.module.css';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  confidence?: number;  // AI response confidence (0-1)
  metadata?: Record<string, any>;  // Additional metadata
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { addToast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      text: input,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await askCopilot(input);
      const botMessage: Message = {
        id: `bot-${Date.now()}`,
        text: response.answer,
        sender: 'bot',
        timestamp: new Date(),
        confidence: response.confidence,
        metadata: response.metadata
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      addToast('Failed to get response from AI Copilot', 'error');
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        text: 'Sorry, I couldn\'t process that request. Please try again.',
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getConfidenceLevel = (confidence?: number): 'high' | 'medium' | 'low' | null => {
    if (!confidence) return null;
    if (confidence >= 0.8) return 'high';
    if (confidence >= 0.5) return 'medium';
    return 'low';
  };

  const getConfidenceLabel = (confidence?: number): string | null => {
    if (!confidence) return null;
    const level = getConfidenceLevel(confidence);
    const percentage = Math.round(confidence * 100);
    return `${percentage}% confidence (${level})`;
  };

  return (
    <div className={styles.container}>
      <div className={styles.messagesContainer}>
        {messages.length === 0 && (
          <div className={styles.empty}>
            <svg className={styles.emptyIcon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <p className={styles.emptyText}>Start a conversation with AI Copilot</p>
            <p className={styles.emptySubtext}>Ask questions about your datasets, models, or insights</p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`${styles.message} ${styles[msg.sender]}`}>
            <div className={styles.messageContent}>
              <div className={styles.messageAvatar}>
                {msg.sender === 'user' ? (
                  <svg fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6z" />
                  </svg>
                )}
              </div>
              <div className={styles.messageBody}>
                <p className={styles.messageText}>{msg.text}</p>
                <div className={styles.messageFooter}>
                  <span className={styles.messageTime}>{formatTime(msg.timestamp)}</span>
                  {msg.sender === 'bot' && msg.confidence !== undefined && (
                    <span
                      className={`${styles.confidenceBadge} ${styles[`confidence${getConfidenceLevel(msg.confidence)?.charAt(0).toUpperCase()}${getConfidenceLevel(msg.confidence)?.slice(1)}`]}`}
                      aria-label={getConfidenceLabel(msg.confidence) || undefined}
                      title={getConfidenceLabel(msg.confidence) || undefined}
                    >
                      {Math.round(msg.confidence * 100)}%
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className={`${styles.message} ${styles.bot}`}>
            <div className={styles.messageContent}>
              <div className={styles.messageAvatar}>
                <svg fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6z" />
                </svg>
              </div>
              <div className={styles.messageBody}>
                <div className={styles.typing}>
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className={styles.inputContainer}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question about your data..."
          className={styles.input}
          rows={1}
          disabled={loading}
          aria-label="Ask AI Copilot a question"
          aria-describedby="copilot-help-text"
        />
        <span id="copilot-help-text" className={styles.srOnly}>
          Type your question and press Enter or click Send to ask AI Copilot
        </span>
        <Button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          loading={loading}
          variant="primary"
          aria-label="Send message to AI Copilot"
        >
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ width: '20px', height: '20px' }} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </Button>
      </div>
    </div>
  );
};

export default ChatInterface;