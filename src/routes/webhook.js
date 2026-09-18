const express = require('express');

const router = express.Router();

const SLACK_WEBHOOK_URL = process.env.SLACK_WEBHOOK_URL;
const SENDGRID_API_KEY = process.env.SENDGRID_API_KEY;

async function notifySlack(message) {
  if (!SLACK_WEBHOOK_URL) {
    throw new Error('SLACK_WEBHOOK_URL is not configured');
  }

  const response = await fetch(SLACK_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: message }),
  });
  return response.ok;
}

async function sendEmail(to, subject, body) {
  if (!SENDGRID_API_KEY) {
    throw new Error('SENDGRID_API_KEY is not configured');
  }

  const response = await fetch('https://api.sendgrid.com/v3/mail/send', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${SENDGRID_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      personalizations: [{ to: [{ email: to }] }],
      from: { email: 'alerts@demo.example.com' },
      subject,
      content: [{ type: 'text/plain', value: body }],
    }),
  });
  return response.status;
}

router.post('/notify', async (req, res) => {
  const { message, email } = req.body;

  try {
    if (message) {
      await notifySlack(message);
    }
    if (email) {
      await sendEmail(email, 'Demo notification', message || 'Hello from secret-scan-demo');
    }
    res.json({ queued: true });
  } catch (err) {
    res.status(500).json({ error: 'Notification failed' });
  }
});

module.exports = router;
