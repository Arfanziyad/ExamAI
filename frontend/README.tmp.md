# Frontend (Test Evaluation)

This folder contains the React + Vite + TypeScript frontend for the Test Evaluation project.

Quick start (Windows PowerShell)

1. Install dependencies

   npm install

2. Start backend and frontend together

   npm run start:all

   This runs `start-dev.ps1` which opens two PowerShell windows and runs the backend (using `python -m uvicorn main:app --reload --port 8000`) and the frontend dev server (`vite`).

If your backend isn't started by the script, start it manually from the `../backend` folder.

Notes

- The frontend expects the backend at http://localhost:8000.
- If you change backend models, update `src/types/index.ts` to match.
- Restart the TypeScript server in your editor if imports appear unresolved.

Troubleshooting

- Ensure Python and uvicorn are installed for the backend.
- Ensure Node.js and npm are installed for the frontend.
- If `start:all` fails, run frontend and backend manually in separate terminals.
