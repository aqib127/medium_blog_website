import React, { useState } from 'react';
import Chatbot from './Chatbot';
import '../styles/chatbot.css';

export default function ChatbotButton() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {!isOpen && (
        <button className="chatbot-toggle-btn" onClick={() => setIsOpen(true)}>
          💬
        </button>
      )}
      {isOpen && <Chatbot onClose={() => setIsOpen(false)} />}
    </>
  );
}