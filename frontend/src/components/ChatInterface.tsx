import React, { useState, useRef, useEffect } from 'react';
import { askCopilot } from '../services/copilotService';
import { useToast } from '../context/ToastProvider';
import { Sparkles, Send, User } from 'lucide-react';
import styles from './ChatInterface.module.css';

interface Message {
    id: string;
    text: string;
    sender: 'user' | 'bot';
    timestamp: Date;
    confidence?: number;
}

const SUGGESTED_PROMPTS = [
    'Summarize my dataset',
    'Which features matter most?',
    "What's my best model's accuracy?",
    'How many missing values?',
];

const ChatInterface: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const { addToast } = useToast();

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const sendMessage = async (text: string) => {
        if (!text.trim()) return;

        const userMessage: Message = {
            id: `user-${Date.now()}`,
            text: text.trim(),
            sender: 'user',
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const response = await askCopilot(text);
            const botMessage: Message = {
                id: `bot-${Date.now()}`,
                text: response.answer,
                sender: 'bot',
                timestamp: new Date(),
                confidence: response.confidence,
            };
            setMessages(prev => [...prev, botMessage]);
        } catch (err: any) {
            const status = err?.response?.status;
            const errorMsg =
                err?.response?.data?.error?.message ||
                err?.response?.data?.detail ||
                (typeof err?.response?.data?.error === 'string' ? err?.response?.data?.error : null) ||
                (status === 429
                    ? 'Rate limit exceeded (5 requests/minute). Please wait a moment before asking another question.'
                    : 'Sorry, I couldn\'t process that request. Please try again.');
            addToast(status === 429 ? 'Rate limit reached' : 'Failed to get response from AI Copilot', 'error');
            const errorMessage: Message = {
                id: `error-${Date.now()}`,
                text: errorMsg,
                sender: 'bot',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(input);
        }
    };

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const getConfidenceLabel = (c: number): string => {
        if (c >= 0.8) return 'High';
        if (c >= 0.5) return 'Medium';
        return 'Low';
    };

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.chatHeader}>
                <div className={styles.chatHeaderIcon}>
                    <Sparkles size={16} />
                </div>
                <div>
                    <h2 className={styles.chatTitle}>AI Copilot</h2>
                    <p className={styles.chatSubtitle}>Ask questions about your data in plain English</p>
                </div>
            </div>

            {/* Messages */}
            <div className={styles.messagesArea}>
                {messages.length === 0 && (
                    <div className={styles.emptyState}>
                        <div className={styles.emptyIcon}>
                            <Sparkles size={28} />
                        </div>
                        <h3 className={styles.emptyTitle}>Ask anything about your data</h3>
                        <p className={styles.emptyDesc}>
                            Get insights, summaries, and explanations from your datasets and models
                        </p>
                        <div className={styles.suggestions}>
                            {SUGGESTED_PROMPTS.map((prompt, i) => (
                                <button
                                    key={i}
                                    className={styles.suggestionChip}
                                    onClick={() => sendMessage(prompt)}
                                >
                                    {prompt}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {messages.map((msg) => (
                    <div key={msg.id} className={`${styles.message} ${styles[msg.sender]}`}>
                        <div className={styles.messageAvatar}>
                            {msg.sender === 'user' ? (
                                <User size={14} />
                            ) : (
                                <Sparkles size={14} />
                            )}
                        </div>
                        <div className={styles.messageBubble}>
                            <p className={styles.messageText}>{msg.text}</p>
                            <div className={styles.messageFooter}>
                                <span className={styles.messageTime}>{formatTime(msg.timestamp)}</span>
                                {msg.sender === 'bot' && msg.confidence !== undefined && (
                                    <span className={styles.confidencePill}>
                                        {Math.round(msg.confidence * 100)}% {getConfidenceLabel(msg.confidence)}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className={`${styles.message} ${styles.bot}`}>
                        <div className={styles.messageAvatar}>
                            <Sparkles size={14} />
                        </div>
                        <div className={styles.messageBubble}>
                            <div className={styles.typingIndicator}>
                                <div className={styles.shimmerBar} />
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className={styles.inputBar}>
                <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask a question about your data..."
                    className={styles.inputField}
                    rows={1}
                    disabled={loading}
                    aria-label="Ask AI Copilot a question"
                />
                <button
                    className={styles.sendBtn}
                    onClick={() => sendMessage(input)}
                    disabled={!input.trim() || loading}
                    aria-label="Send message"
                >
                    <Send size={16} />
                </button>
            </div>
        </div>
    );
};

export default ChatInterface;