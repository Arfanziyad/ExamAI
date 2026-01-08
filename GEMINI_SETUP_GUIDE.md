# 🚀 Gemini Hybrid Evaluation Setup Guide

## Overview
Your evaluation system now uses a **hybrid approach** combining:
- **Transformer-based evaluation** (fast, free, always runs)
- **Google Gemini LLM** (nuanced, contextual understanding)

## Quick Start (5 minutes)

### Step 1: Get Your Free Gemini API Key

1. Go to **https://aistudio.google.com/app/apikey**
2. Sign in with your Google account
3. Click **"Get API key"** or **"Create API key"**
4. Copy your API key

### Step 2: Install Required Package

```bash
cd backend
pip install google-generativeai
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### Step 3: Set Your API Key

**Option A: Environment Variable (Recommended)**
```bash
# Windows PowerShell
$env:GEMINI_API_KEY="your_api_key_here"

# Windows CMD
set GEMINI_API_KEY=your_api_key_here

# Linux/Mac
export GEMINI_API_KEY="your_api_key_here"
```

**Option B: Create .env File**
```bash
# Create .env file in backend folder
cp .env.example .env

# Edit .env and add your key:
GEMINI_API_KEY=your_actual_api_key_here
```

### Step 4: Restart Your Server

```bash
cd backend
python flask_server.py
```

You should see in the logs:
```
INFO - Gemini evaluator initialized successfully with gemini-1.5-flash
INFO - Hybrid mode: True, Gemini available: True
```

## How Hybrid Evaluation Works

### Evaluation Flow:

```
Student Answer
    ↓
┌─────────────────────────────────────┐
│  1. Transformer Evaluation (Fast)   │
│     - Semantic similarity            │
│     - Keyword matching               │
│     - Structure analysis             │
│     - Always runs (fallback)         │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  2. Gemini LLM Evaluation (Smart)   │
│     - Deep contextual understanding  │
│     - Nuanced reasoning              │
│     - Detailed feedback              │
│     - Partial credit awareness       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  3. Intelligent Combination          │
│     - 60% Gemini + 40% Transformer   │
│     - Uses Gemini's detailed feedback│
│     - Falls back if Gemini fails     │
└─────────────────────────────────────┘
    ↓
Final Score + Rich Feedback
```

### What You Get:

**Enhanced Feedback Includes:**
- ✓ **Strengths**: What the student did well
- ✗ **Weaknesses**: Areas needing improvement
- • **Missing Points**: Key concepts not covered
- 📊 **Detailed Scores**: Breakdown by criteria
  - Conceptual understanding
  - Accuracy
  - Completeness
  - Clarity

## Configuration Options

Edit `backend/services/evaluator_service.py`:

```python
class EvaluatorService:
    def __init__(self):
        # ... other code ...
        
        # Hybrid evaluation settings
        self.use_hybrid = True          # Enable/disable hybrid mode
        self.gemini_weight = 0.6        # 60% Gemini, 40% Transformer
        self.confidence_threshold = 0.7 # When to prefer Gemini
```

### Weight Configurations:

| Gemini Weight | Use Case |
|---------------|----------|
| 0.0 | Transformer only (no LLM) |
| 0.3 | Transformer-focused, LLM assists |
| 0.5 | Equal balance |
| **0.6** | **LLM-focused (recommended)** |
| 0.8 | Heavy LLM reliance |
| 1.0 | Pure LLM (no transformer) |

## Free Tier Limits

**Gemini 1.5 Flash (Free):**
- ✅ 15 requests per minute
- ✅ 1 million tokens per day
- ✅ No credit card required

**Typical Usage:**
- 1 evaluation ≈ 500-1000 tokens
- **~1000-2000 evaluations per day FREE**
- More than enough for testing and small classes

## Cost (If You Exceed Free Tier)

**Gemini 1.5 Flash Pricing:**
- $0.075 per 1M input tokens
- $0.30 per 1M output tokens

**Real-World Cost:**
- Per evaluation: ~$0.0001-0.0003 (0.01-0.03 cents)
- 100 evaluations: ~$0.01-0.03 (1-3 cents)
- 1000 evaluations: ~$0.10-0.30 (10-30 cents)

**Extremely affordable!** 💰

## Troubleshooting

### "Gemini evaluator disabled: No API key provided"

**Solution:**
```bash
# Set environment variable
export GEMINI_API_KEY="your_key_here"

# Or create .env file
echo "GEMINI_API_KEY=your_key_here" > .env
```

### "Gemini not available, using transformer-only evaluation"

**Check:**
1. Is `google-generativeai` installed?
   ```bash
   pip install google-generativeai
   ```

2. Is your API key set?
   ```bash
   echo $GEMINI_API_KEY  # Should show your key
   ```

3. Is the package imported correctly?
   - Server logs should show: `Gemini evaluator initialized successfully`

### "Rate limit exceeded"

**Solutions:**
- Wait 1 minute (free tier: 15 requests/minute)
- Reduce evaluation frequency
- Upgrade to paid tier (very cheap)

### System Still Works Without Gemini

**No worries!** The system automatically falls back to transformer-based evaluation if:
- No API key is set
- Gemini package not installed
- API rate limit exceeded
- Network error

Your evaluations will always complete! 🎯

## Testing Hybrid Evaluation

1. **Submit a test answer** via Smart Submit
2. **Check the results page** - you should see richer feedback
3. **Check server logs** for:
   ```
   INFO - Running hybrid evaluation with Gemini
   INFO - Hybrid evaluation: Transformer=7, Gemini=8, Combined=8
   ```

## Benefits You'll Notice

### Before (Transformer Only):
```
Score: 7/10
Feedback: "Good understanding but missing some key concepts"
```

### After (Hybrid with Gemini):
```
Score: 8/10
Feedback: "Good answer showing solid grasp of concepts.

✓ Strengths: Clear explanation of main principles, good use of examples
✗ Areas for improvement: Could elaborate more on edge cases
• Missing points: Discussion of alternative approaches, mention of limitations

Detailed Analysis:
• Conceptual Understanding: 85%
• Accuracy: 90%
• Completeness: 75%
• Clarity: 80%"
```

## Summary

✅ **Easy Setup**: 5 minutes to get API key and configure
✅ **Free Tier**: Generous limits for testing and small classes
✅ **Fallback Safe**: Always works even if Gemini unavailable
✅ **Better Feedback**: Students get detailed, actionable insights
✅ **Flexible**: Adjust weights or disable anytime
✅ **Cost-Effective**: Pennies per evaluation

**Ready to enhance your grading? Set your API key and restart the server!** 🚀
