import React, { useState } from 'react';
import { subscribeToNewsletter } from '../services/newsletterService';
import '../styles/newsletter.css';

export default function NewsletterSignup({ source = 'website', compact = false }) {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [status, setStatus] = useState('idle'); // idle | loading | success | error
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;

    setStatus('loading');
    setMessage('');

    try {
      const data = await subscribeToNewsletter(email.trim(), name.trim(), source);
      setStatus('success');
      setMessage(data.message || 'Check your email to confirm!');
      setEmail('');
      setName('');
    } catch (err) {
      setStatus('error');
      setMessage(err.message || 'Something went wrong. Try again.');
    }
  };

  if (compact) {
    return (
      <form className="newsletter-compact" onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="your@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={status === 'loading'}
          required
        />
        <button type="submit" disabled={status === 'loading'}>
          {status === 'loading' ? '...' : 'Subscribe'}
        </button>
        {message && (
          <div className={`newsletter-msg newsletter-msg-${status}`}>
            {message}
          </div>
        )}
      </form>
    );
  }

  return (
    <div className="newsletter-card">
      <div className="newsletter-header">
        <h3>📬 Subscribe to our newsletter</h3>
        <p>Get the latest articles delivered to your inbox.</p>
      </div>

      {status === 'success' ? (
        <div className="newsletter-success">
          <div className="newsletter-success-icon">✓</div>
          <p>{message}</p>
          <p className="newsletter-hint">
            Didn't receive the email? Check your spam folder.
          </p>
        </div>
      ) : (
        <form className="newsletter-form" onSubmit={handleSubmit}>
          <div className="newsletter-field">
            <label>Name (optional)</label>
            <input
              type="text"
              placeholder="Your name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={status === 'loading'}
            />
          </div>

          <div className="newsletter-field">
            <label>Email *</label>
            <input
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={status === 'loading'}
              required
            />
          </div>

          <button
            type="submit"
            className="newsletter-btn"
            disabled={status === 'loading' || !email.trim()}
          >
            {status === 'loading' ? 'Subscribing...' : 'Subscribe'}
          </button>

          {message && status === 'error' && (
            <div className="newsletter-msg newsletter-msg-error">
              {message}
            </div>
          )}

          <p className="newsletter-terms">
            We'll send you an email to confirm. No spam, unsubscribe anytime.
          </p>
        </form>
      )}
    </div>
  );
}
