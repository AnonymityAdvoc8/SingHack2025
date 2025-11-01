# TravelMate AI - Quick Start Guide

## ✅ Phase 1 Complete - What's Been Built

### 1. **Project Structure Created**
```
backend-mcp/
├── app/
│   ├── config.py             # Configuration management
│   ├── database.py           # SQLite database setup
│   ├── models/               # Database models (policies, claims)
│   └── utils/                # PDF extraction, taxonomy mapping
├── scripts/
│   ├── init_database.py      # Initialize database
│   └── extract_policies.py   # Extract all 3 policies (Phase 1)
├── requirements.txt          # Python dependencies
└── setup.sh                  # Setup script
```

### 2. **Dependencies Installed** ✅
- FastAPI, Uvicorn (web framework)
- MCP 1.20.0 (Model Context Protocol)
- Groq (LLM for taxonomy mapping)
- SQLAlchemy (database ORM)
- pdfplumber (PDF extraction)
- Stripe (payment integration)
- And more...

### 3. **Database Models Created** ✅
- **Policy**: Main policy metadata
- **GeneralCondition**: Layer 1 (age, residency, trip requirements)
- **Benefit**: Layer 2 & 3 (coverage limits, conditions)
- **OperationalDetail**: Layer 4 (deductibles, claims procedures)
- **Claim**: Historical claims data (for Phase 5)

---

## 🔧 **Next Steps: Complete Phase 1**

### Step 1: Add Your API Keys

Create a `.env` file in the `backend-mcp/` directory:

```bash
cd backend-mcp
nano .env  # or use any text editor
```

Add this content (replace with your actual keys):

```bash
# REQUIRED: Groq API Key
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx

# REQUIRED for Phase 4: Stripe Keys  
STRIPE_API_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxx

# Optional: MSIG API (if you have it)
MSIG_API_KEY=your_msig_key_here

# These are fine as-is
DATABASE_URL=sqlite:///./travelmate.db
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### Step 2: Initialize Database

```bash
cd backend-mcp
source venv/bin/activate
python scripts/init_database.py
```

Expected output:
```
✅ Database initialized successfully!
📊 Tables created: policies, general_conditions, benefits, operational_details, claims
```

### Step 3: Extract All 3 Policies (PHASE 1)

This will:
- Extract text from all 3 PDFs
- Map to 4-layer taxonomy using Groq
- Store in SQLite with dual-access pattern

```bash
python scripts/extract_policies.py
```

**⏱️ Expected time:** 3-5 minutes (Groq API calls)

Expected output:
```
🚀 TravelMate AI - Phase 1: Policy Extraction
📄 Processing Policy 1/3: Scootsurance
   ✅ Extracted 45,123 characters
   ✅ Taxonomy mapping complete
   ✅ Policy stored

📄 Processing Policy 2/3: TravelEasy Standard
   ✅ Extracted 38,456 characters
   ✅ Taxonomy mapping complete
   ✅ Policy stored

📄 Processing Policy 3/3: TravelEasy Pre-Existing
   ✅ Extracted 42,789 characters
   ✅ Taxonomy mapping complete
   ✅ Policy stored

🎉 Phase 1 Complete!
```

---

## 📍 Where You Are Now

| Phase | Status | Description |
|-------|--------|-------------|
| ✅ Phase 1 Setup | **READY** | Structure created, dependencies installed |
| ⏳ Phase 1 Execution | **NEXT** | Run `extract_policies.py` |
| ⚠️ Phase 2 | Pending | Build MCP server |
| ⚠️ Phase 4 | Pending | Payment integration |
| ⚠️ Phase 5 | Pending | Claims intelligence |
| ⚠️ Phase 6 | Pending | UI & Demo |

---

## 🚨 Troubleshooting

### If you don't have Groq API key:
1. Go to: https://console.groq.com
2. Sign up / Log in
3. Create an API key
4. Copy it to your `.env` file

### If you don't have Stripe keys yet:
- Don't worry! We only need them for Phase 4 (payment integration)
- For now, just put placeholder values to pass validation
- Example: `STRIPE_API_KEY=sk_test_placeholder`

### If database errors occur:
```bash
# Delete and recreate database
rm travelmate.db
python scripts/init_database.py
```

---

## 🎯 What Happens Next

Once Phase 1 extraction completes, you'll have:

1. ✅ **3 policies in SQLite database**
   - Scootsurance
   - TravelEasy Standard
   - TravelEasy Pre-Ex

2. ✅ **4-layer taxonomy mapping**
   - Layer 1: General Conditions (eligibility, trip requirements)
   - Layer 2: Benefits Structure (coverage limits)
   - Layer 3: Benefit Conditions (requirements, exclusions)
   - Layer 4: Operational (deductibles, claims)

3. ✅ **Dual-access pattern**
   - Normalized data for algorithmic processing
   - Raw policy text for citations

Then we move to **Phase 2: Build MCP Server** with:
- Resources layer (policy data access)
- Tools layer (compare, answer questions, check eligibility)
- Prompts layer (conversational templates)

---

**Ready to proceed? Run the extraction script once you've added your Groq API key!** 🚀

