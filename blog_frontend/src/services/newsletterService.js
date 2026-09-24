// frontend/src/services/newsletterService.js
import { endpoints } from '../config/api';

export const subscribeToNewsletter = async (email, name = '', source = 'website') => {
  const res = await fetch(endpoints.newsletterSubscribe, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, name, source }),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || data.message || 'Subscription failed');
  }

  return data;
};

export const confirmNewsletter = async (token) => {
  const res = await fetch(endpoints.newsletterConfirm(token), {
    method: 'GET',
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || 'Confirmation failed');
  }

  return data;
};

export const unsubscribeFromNewsletter = async (email) => {
  const res = await fetch(endpoints.newsletterUnsubscribe, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || 'Unsubscribe failed');
  }

  return data;
};

export const getNewsletterStatus = async (email) => {
  const res = await fetch(endpoints.newsletterStatus(email));
  return res.json();
};
