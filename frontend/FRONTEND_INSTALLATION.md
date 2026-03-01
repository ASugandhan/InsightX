# Frontend Installation & Run Guide

This guide starts the InsightX frontend locally.

## Prerequisites

- Node.js 18+ (recommended)
- npm 9+
- Backend API running at `http://localhost:8000`

## Steps

1. Open terminal in project root.
2. Go to frontend folder:
   - `cd insightx/frontend`
3. Install packages:
   - `npm install`
4. Start development server:
   - `npm start`
   - or `npm run dev`
5. Open browser:
   - `http://localhost:3000`

## Build For Production

- `npm run build`

## Troubleshooting

- Port already used:
  - Stop existing app on `3000`, or accept alternate port when prompted.
- API not responding:
  - Ensure backend is running on `http://localhost:8000`.
- Dependency issues:
  - Delete `node_modules` and `package-lock.json`, then run `npm install` again.

## Useful Scripts

- `npm start` -> run dev server
