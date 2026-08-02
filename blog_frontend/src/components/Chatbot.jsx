import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { endpoints } from '../config/api';
import '../styles/chatbot.css';

export default function Chatbot({ onClose }) {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const token = localStorage.getItem('access');
      const response = await fetch(endpoints.chatbot, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          message: input,
          history: messages.map(m => ({ role: m.role, content: m.content })),
        }),
      });

      if (!response.ok) throw new Error('Network response was not ok');
      const data = await response.json();

      setMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);
    } catch (error) {
      console.error('Chatbot error:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, an error occurred. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chatbot-window">
      <div className="chatbot-header">
        <span>AI Assistant</span>
        <button className="chatbot-close-btn" onClick={onClose}>×</button>
      </div>
      <div className="chatbot-messages">
        {messages.length === 0 && (
          <div className="chatbot-welcome">
            <p>Hello! I can answer questions about articles, authors, tags, and more.</p>
          </div>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} className={`chatbot-message ${msg.role}`}>
            <div className="message-content">{msg.content}</div>
          </div>
        ))}
        {loading && (
          <div className="chatbot-message assistant">
            <div className="message-content">Thinking...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form className="chatbot-input-form" onSubmit={sendMessage}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask something..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>Send</button>
      </form>
    </div>
  );
}