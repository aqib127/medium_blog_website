// frontend/src/services/chatbotService.js
import { endpoints } from '../config/api';

/**
 * Sends a message to the chatbot and handles Server-Sent Events (SSE) streaming.
 * 
 * @param {string} message - The user's message.
 * @param {string} token - The JWT access token.
 * @param {function} onChunk - Callback for each received chunk of data (e.g., update UI).
 * @param {function} onError - Callback for errors.
 * @param {function} onComplete - Callback when the stream ends.
 * @returns {AbortController} - An AbortController to cancel the request if needed.
 */
export const sendChatMessage = async (message, token, onChunk, onError, onComplete) => {
  const controller = new AbortController();
  const signal = controller.signal;

  const fetchStream = async () => {
    try {
      const response = await fetch(endpoints.chatbot, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ message }),
        signal,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          onComplete && onComplete();
          break;
        }

        // Decode the chunk
        const chunk = decoder.decode(value, { stream: true });
        
        // Process the chunk (assuming Server-Sent Events format "data: {...}\n\n")
        // or plain JSON chunks separated by newlines.
        // Adapt this parsing logic to match your Django backend's output format.
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonString = line.substring(6).trim();
            if (jsonString && jsonString !== '[DONE]') {
              try {
                const data = JSON.parse(jsonString);
                onChunk && onChunk(data);
              } catch (parseError) {
                // If it's not JSON, send the raw text
                onChunk && onChunk({ text: jsonString });
              }
            }
          } else if (line.trim()) {
            // Fallback: treat as raw text if not SSE format
            try {
              const data = JSON.parse(line.trim());
              onChunk && onChunk(data);
            } catch {
              // ignore non-JSON lines
            }
          }
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Chat request aborted.');
        return;
      }
      onError && onError(error.message || 'Failed to connect to chatbot.');
    }
  };

  fetchStream();
  return controller;
};