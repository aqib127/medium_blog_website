import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { confirmNewsletter } from '../services/newsletterService';
import '../styles/newsletter.css';

export default function NewsletterConfirm() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('loading');
  const [message, setMessage] = useState('');

  const token = searchParams.get('token');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('No confirmation token provided.');
      return;
    }

    confirmNewsletter(token)
      .then((data) => {
        setStatus('success');
        setMessage(data.message || 'Subscription confirmed!');
      })
      .catch((err) => {
        setStatus('error');
        setMessage(err.message || 'Confirmation failed.');
      });
  }, [token]);

  return (
    <div className="newsletter-page">
      <div className={`newsletter-status-card newsletter-status-${status}`}>
        {status === 'loading' && (
          <>
            <div className="newsletter-spinner" />
            <h2>Confirming...</h2>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="newsletter-success-icon">✓</div>
            <h2>You're subscribed!</h2>
            <p>{message}</p>
            <p className="newsletter-hint">
              You'll now receive our latest articles.
            </p>
            <button
              className="newsletter-btn"
              onClick={() => navigate('/')}
            >
              Go to Home
            </button>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="newsletter-error-icon">✕</div>
            <h2>Confirmation failed</h2>
            <p>{message}</p>
            <p className="newsletter-hint">
              The link may have expired. Try subscribing again.
            </p>
            <button
              className="newsletter-btn"
              onClick={() => navigate('/')}
            >
              Go to Home
            </button>
          </>
        )}
      </div>
    </div>
  );
}
