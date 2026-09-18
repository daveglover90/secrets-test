require('dotenv').config();

const express = require('express');
const { S3Client, ListBucketsCommand } = require('@aws-sdk/client-s3');
const webhookRouter = require('./routes/webhook');

const app = express();
app.disable('x-powered-by');
app.use(express.json());

const s3 = new S3Client({
  region: process.env.AWS_REGION || 'us-east-1',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  },
});

function buildDbConnectionString() {
  const url = process.env.DATABASE_URL;
  if (!url) {
    throw new Error('DATABASE_URL is required');
  }
  return url;
}

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', app: 'secret-scan-demo' });
});

app.get('/config-check', (_req, res) => {
  res.json({
    databaseConfigured: Boolean(buildDbConnectionString()),
    stripeConfigured: Boolean(process.env.STRIPE_SECRET_KEY),
    jwtConfigured: Boolean(process.env.JWT_SECRET),
  });
});

app.get('/aws/ping', async (_req, res) => {
  try {
    const result = await s3.send(new ListBucketsCommand({}));
    res.json({ bucketCount: result.Buckets?.length ?? 0 });
  } catch (err) {
    res.status(502).json({ error: 'AWS call failed (expected with demo credentials)' });
  }
});

app.use('/webhooks', webhookRouter);

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`secret-scan-demo listening on http://localhost:${port}`);
});
