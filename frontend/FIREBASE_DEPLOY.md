# Kraken Audit — Firebase Hosting Deployment Guide
Deploy the Kraken frontend dashboard on Google Firebase alongside the Gemini API.

## Prerequisites
- A Google account with Firebase access
- Node.js 18+ installed locally
- The Kraken repo cloned

## Step 1: Install Firebase CLI
```bash
npm install -g firebase-tools
```

## Step 2: Log in to Google
```bash
firebase login
```
This opens a browser — authenticate with the Google account tied to your Gemini API key.

## Step 3: Initialize Firebase in the Frontend Directory
```bash
cd kraken_audit/frontend
firebase init hosting
```
During the interactive prompts:
- **Select an existing project** → Create a new project (e.g., `kraken-audit`)
  or select one you already created at https://console.firebase.google.com
- **Public directory** → `static` (matches our firebase.json)
- **Configure as a single-page app** → Yes (rewrites all routes to index.html)
- **Set up automatic builds with GitHub** → No (we trigger manually)
- **File index.html already exists** → Keep it (do not overwrite)

## Step 4: Set Backend URL
The SPA reads the API base from a query parameter. When deploying, customers access:
```
https://kraken-audit.web.app/?api=https://your-backend-server:8080
```
For local dev during rehearsals:
```
http://localhost:8080/?api=http://localhost:8080
```

Alternatively, hardcode the API URL in `static/index.html` by editing the `API` constant before deploy:
```js
const API = 'https://your-backend-server:8080';
```

## Step 5: Deploy to Firebase
```bash
cd kraken_audit/frontend
firebase deploy --only hosting
```
After a few seconds you'll see:
```
✔  Deploy complete!
Project Console: https://console.firebase.google.com/project/kraken-audit/overview
Hosting URL: https://kraken-audit.web.app
```

## Step 6: Verify
Open the Hosting URL. You should see the Kraken Audit dashboard.
Append `?api=https://your-api-server:8080` to connect to your backend.

## Architecture Overview
```
┌─────────────────────────────────────────────────┐
│  🌐 Firebase Hosting                            │
│  https://kraken-audit.web.app                   │
│                                                  │
│  static/index.html  ← SPA dashboard             │
│  static/app.js      ← API calls + drag-drop     │
│                                                  │
│  Rewrites: all routes → index.html              │
└──────────────┬──────────────────────────────────┘
               │  CORS requests
               ▼
┌─────────────────────────────────────────────────┐
│  🖥️ FastAPI Backend                             │
│  http://your-server:8080                        │
│                                                  │
│  /api/dashboard    → Live stats from ChromaDB   │
│  /api/invoices     → Invoice table w/ status    │
│  /api/reports/*    → PDF audit report download   │
│  /api/upload       → Queue invoice for audit     │
└─────────────────────────────────────────────────┘
```

## Local Dev (No Firebase)
The backend doubles as a static file server for local rehearsals:
```bash
cd kraken_audit/frontend
bash run.sh
# → http://localhost:8080 serves both API + static SPA
```

## Teardown
```bash
firebase hosting:disable
```