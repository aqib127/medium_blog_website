import React, { useState, useRef, useEffect } from 'react';
import '../styles/chatbot.css';
import { endpoints } from '../config/api';   // ✅ IMPORT THIS

export default function Chatbot({ onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(scrollToBottom, [messages]);

  const refreshAccessToken = async () => {
    const refresh = localStorage.getItem('refresh');
    if (!refresh) throw new Error('No refresh token');
    // ✅ FIXED: Use endpoints.refresh
    const res = await fetch(endpoints.refresh, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) {
      localStorage.removeItem('access');
      localStorage.removeItem('refresh');
      throw new Error('Refresh failed – please log in again.');
    }
    const data = await res.json();
    localStorage.setItem('access', data.access);
    if (data.refresh) {
      localStorage.setItem('refresh', data.refresh);
    }
    return data.access;
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      let token = localStorage.getItem('access');
      if (!token) throw new Error('No access token');

      // ✅ FIXED: Use endpoints.chatbot
      let response = await fetch(endpoints.chatbot, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ message: input }),
      });

      if (response.status === 401) {
        try {
          token = await refreshAccessToken();
          // ✅ FIXED: Use endpoints.chatbot
          response = await fetch(endpoints.chatbot, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({ message: input }),
          });
        } catch (refreshError) {
          throw new Error(refreshError.message);
        }
      }

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`HTTP ${response.status}: ${text}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';
      let buffer = '';

      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(5).trim();
              const data = JSON.parse(jsonStr);
              if (data.type === 'chunk') {
                assistantMessage += data.content;
                setMessages(prev => {
                  const newMessages = [...prev];
                  newMessages[newMessages.length - 1] = {
                    role: 'assistant',
                    content: assistantMessage,
                  };
                  return newMessages;
                });
              } else if (data.type === 'error') {
                throw new Error(data.error);
              }
            } catch (err) {
              console.warn('Parse error:', err, 'line:', line);
            }
          }
        }
      }
    } catch (error) {
      console.error('Chatbot error:', error);
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: error.message || 'Sorry, an error occurred.' },
      ]);
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
            <p>Hello! Ask me about articles, authors, tags, and more.</p>
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
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}