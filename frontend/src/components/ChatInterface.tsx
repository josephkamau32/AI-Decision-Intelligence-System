import React, { useState } from 'react';
import { askCopilot } from '../services/copilotService';

interface Message {
  text: string;
  sender: 'user' | 'bot';
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMessage: Message = { text: input, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    try {
      const answer = await askCopilot(input);
      const botMessage: Message = { text: answer, sender: 'bot' };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage: Message = { text: 'Sorry, I couldn\'t process that.', sender: 'bot' };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <div style={{ height: '400px', overflowY: 'scroll', border: '1px solid #ccc', padding: '10px' }}>
        {messages.map((msg, index) => (
          <div key={index} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left' }}>
            <p style={{ display: 'inline-block', padding: '8px', background: msg.sender === 'user' ? '#007bff' : '#f1f1f1', color: msg.sender === 'user' ? 'white' : 'black', borderRadius: '10px' }}>
              {msg.text}
            </p>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', marginTop: '10px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          style={{ flex: 1, padding: '8px' }}
          placeholder="Ask a question about your data..."
        />
        <button onClick={handleSend} style={{ padding: '8px 16px' }}>Send</button>
      </div>
    </div>
  );
};

export default ChatInterface;