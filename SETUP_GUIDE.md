# ExamAI - Setup Guide

## Quick Start for New Users

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/Arfanziyad/ExamAI.git
cd ExamAI
```

### Step 2: Backend Setup

1. **Navigate to backend folder:**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment (optional but recommended):**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file:**
   Create a file named `.env` in the `backend` folder with the following content:
   ```
   OCR_API_KEY=your_api_key_here
   OCR_API_URL=https://www.handwritingocr.com/api/v3
   ```
   
   **Get your OCR API key from:** https://www.handwritingocr.com
   
   ⚠️ **Important:** Without a valid API key, OCR functionality won't work!

5. **Initialize the database:**
   ```bash
   python flask_server.py
   ```
   (This will automatically create the database tables on first run. You can press Ctrl+C to stop it after initialization)

### Step 3: Frontend Setup

1. **Navigate to frontend folder:**
   ```bash
   cd ../frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

### Step 4: Run the Application

**Option A: Run Both Servers Separately**

1. **Terminal 1 - Backend:**
   ```bash
   cd backend
   python flask_server.py
   ```
   Backend will run on: http://localhost:5000

2. **Terminal 2 - Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend will run on: http://localhost:5173

**Option B: Using PowerShell Script (Windows only)**
   ```bash
   cd frontend
   .\start-dev.ps1
   ```

### Step 5: Access the Application

Open your browser and navigate to:
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:5000

## File Structure

```
ExamAI/
├── backend/
│   ├── flask_server.py       # Main server file
│   ├── database.py           # Database configuration
│   ├── models.py             # Database models
│   ├── requirements.txt      # Python dependencies
│   ├── .env                  # Environment variables (YOU MUST CREATE THIS!)
│   ├── evaluators/           # Evaluation logic
│   ├── services/             # OCR, file handling, analytics
│   └── storage/              # File storage (auto-created)
├── frontend/
│   ├── src/
│   │   ├── pages/           # React pages
│   │   ├── components/      # React components
│   │   └── services/        # API calls
│   ├── package.json         # Node.js dependencies
│   └── vite.config.ts       # Vite configuration
└── README.md
```

## Required Files to Create

### 1. Backend `.env` File
**Location:** `backend/.env`

**Content:**
```
OCR_API_KEY=your_actual_api_key_here
OCR_API_URL=https://www.handwritingocr.com/api/v3
```

### 2. Storage Directories (Auto-created)
The following directories will be created automatically when you run the server:
- `backend/storage/uploads/`
- `backend/storage/processed/`
- `backend/storage/model_answers/`
- `backend/storage/question_papers/`
- `backend/storage/submissions/`

## Troubleshooting

### Backend Issues

**Error: "No module named 'flask'"**
- Solution: Install dependencies with `pip install -r requirements.txt`

**Error: "OCR processing failed"**
- Solution: Check your OCR_API_KEY in the `.env` file
- Get a valid key from https://www.handwritingocr.com

**Error: Database errors**
- Solution: Delete `app.db` and restart the server to recreate the database

### Frontend Issues

**Error: "Port 5173 is in use"**
- Solution: The frontend will automatically try port 5174. Use the URL shown in terminal.

**Error: "Failed to fetch"**
- Solution: Make sure the backend is running on port 5000
- Check that `src/services/api.ts` has `API_BASE_URL = 'http://localhost:5000'`

**Error: Dependencies installation fails**
- Solution: Delete `node_modules` and `package-lock.json`, then run `npm install` again

## Features

- ✅ Create question papers with OCR support
- ✅ Multiple question types (subjective, coding)
- ✅ Automatic handwriting OCR
- ✅ AI-powered evaluation
- ✅ Student submissions and grading
- ✅ Analytics and aggregated results

## Tech Stack

**Backend:**
- Python 3.8+
- Flask
- SQLAlchemy
- HandwritingOCR API

**Frontend:**
- React 18
- TypeScript
- Vite
- Tailwind CSS

## Support

For issues or questions, please open an issue on GitHub.
