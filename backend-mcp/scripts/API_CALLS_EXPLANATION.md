# Test Scripts - API Calls Explanation

**Question:** Do the test scripts make real API calls?  
**Short Answer:** Only **1 out of 5** test scripts makes real API calls

---

## 📊 API Call Breakdown

### ✅ Tests WITHOUT API Calls (Fast, Free)

| Test Script | API Calls | Speed | Cost |
|------------|-----------|-------|------|
| **test_emotional_intelligence.py** | ❌ None | ~2 sec | FREE |
| **test_proactive_intelligence.py** | ❌ None | ~2 sec | FREE |
| **test_gmail_agent.py** | ❌ None (mock) | ~3 sec | FREE |
| **test_flight_agent.py** | ❌ None (mock) | ~3 sec | FREE |

**Total:** 4/5 tests are FREE and FAST

---

### ⚠️ Test WITH API Calls (Slower, Uses Credits)

| Test Script | API Calls Made | Speed | Cost per Run |
|------------|----------------|-------|--------------|
| **test_personality_integration.py** | ✅ YES | ~30-60 sec | ~$0.01-0.02 |

**What API calls it makes:**

1. **Groq LLM API** (6-12 calls per test run)
   - Conversational extraction
   - Question answering
   - Intent detection
   - **Cost:** ~$0.005-0.01 per run

2. **Tavily API** (2-6 calls per test run)
   - Destination intelligence
   - Risk analysis
   - Medical cost intelligence
   - **Cost:** ~$0.005-0.01 per run

3. **PostgreSQL Database** (Several queries)
   - Claims analytics
   - Policy retrieval
   - **Cost:** FREE (your database)

**Total Cost:** ~$0.01-0.02 per full test run (very cheap!)

---

## 🛠️ How to Control API Calls

### Option 1: Skip API Tests (Free, Fast)

```bash
cd backend-mcp

# Set environment variable to skip API-calling tests
export SKIP_API_CALLS=1

# Run tests (will skip test_personality_integration.py)
python scripts/test_all_new_features.py
```

**Result:**
- Tests 1-4 run normally (10 seconds, FREE)
- Test 5 skips (no API calls, FREE)
- Total time: ~10 seconds

---

### Option 2: Run All Tests Including API (Real Validation)

```bash
cd backend-mcp

# Make sure API keys are set
echo $GROQ_API_KEY   # Should show your key
echo $TAVILY_API_KEY # Should show your key

# Run tests (includes API calls)
python scripts/test_all_new_features.py
```

**Result:**
- Tests 1-4 run normally (10 seconds, FREE)
- Test 5 makes real API calls (30-60 seconds, ~$0.01-0.02)
- Total time: ~40-70 seconds

---

## 💰 Cost Analysis

### Per Test Run
| Component | Calls | Cost per Call | Total |
|-----------|-------|---------------|-------|
| **Groq LLM** | 6-12 | ~$0.0008 | ~$0.005-0.01 |
| **Tavily** | 2-6 | ~$0.002 | ~$0.004-0.012 |
| **PostgreSQL** | Several | FREE | $0 |
| **TOTAL** | | | **~$0.01-0.02** |

### For 10 Test Runs
- **Without API skip:** ~$0.10-0.20
- **With API skip:** $0 (FREE)

---

## 🎯 Recommendation

### For Development/Debugging
**Use:** `SKIP_API_CALLS=1` (free and fast)

```bash
export SKIP_API_CALLS=1
python scripts/test_all_new_features.py
# Tests the logic, no API costs
```

### Before Demo/Presentation
**Use:** Full tests (validate real integration)

```bash
unset SKIP_API_CALLS
python scripts/test_personality_integration.py
# Validates actual LLM responses work
```

### What Each Validates

**Tests 1-4 (No API):**
- ✅ Emotion detection logic
- ✅ Proactive insight generation
- ✅ Gmail parsing patterns
- ✅ Flight data extraction
- ✅ Service logic and structure

**Test 5 (With API):**
- ✅ Real Groq LLM responses
- ✅ Real Tavily intelligence
- ✅ Full orchestration flow
- ✅ End-to-end integration

---

## 🚀 Best Practice

**During Development:**
```bash
# Run fast tests frequently (no cost)
export SKIP_API_CALLS=1
python scripts/test_all_new_features.py

# Only run full integration tests when needed
unset SKIP_API_CALLS
python scripts/test_personality_integration.py
```

**Before Demo:**
```bash
# Validate everything works with real APIs
unset SKIP_API_CALLS
python scripts/test_all_new_features.py

# Expected: All tests pass
# Cost: ~$0.02
# Time: ~60 seconds
```

---

## 📋 What Each Test Actually Does

### test_emotional_intelligence.py (NO API CALLS)
```python
# Pure Python logic testing
service = EmotionalIntelligenceService()
context = service.detect_emotion("This is confusing")
# No external API needed - just pattern matching
```

### test_proactive_intelligence.py (NO API CALLS)
```python
# Tests insight generation logic
service = ProactiveIntelligenceService()
insights = service.generate_insights(trip_data, claims_data)
# No external API needed - generates from input data
```

### test_gmail_agent.py (NO API CALLS)
```python
# Uses mock data
agent = GmailAgent()
bookings = await agent.search_for_bookings()
# Returns MOCK_BOOKINGS (no real Gmail API call)
```

### test_flight_agent.py (NO API CALLS)
```python
# Uses mock flight database
agent = FlightAPIAgent()
booking = await agent.lookup_booking("ABC123")
# Returns MOCK_BOOKINGS["ABC123"] (no real airline API)
```

### test_personality_integration.py (YES - API CALLS)
```python
# Calls full orchestration service
orchestrator = ConversationOrchestrator(db)
response = orchestrator.handle_message("I need insurance for Japan")
# This triggers:
# - Groq LLM (conversational extraction)
# - Tavily API (destination intelligence)
# - PostgreSQL (claims data)
```

---

## ✅ Summary

**API Calls in Tests:**
- **4 tests:** NO API calls (mock data, logic testing only)
- **1 test:** YES API calls (full integration validation)
- **Control:** Use `SKIP_API_CALLS=1` to avoid costs
- **Cost:** ~$0.01-0.02 per full run (very cheap!)
- **Time:** ~10 sec without API, ~60 sec with API

**Recommendation:**
- Use `SKIP_API_CALLS=1` during development (FREE, FAST)
- Run full tests before demo to validate (CHEAP, 60 sec)

---

## 🚀 Quick Reference

```bash
# Fast, free tests (skip API)
export SKIP_API_CALLS=1
python scripts/test_all_new_features.py

# Full validation (with API)
unset SKIP_API_CALLS  
python scripts/test_all_new_features.py

# Or just run the free tests individually
python scripts/test_emotional_intelligence.py  # FREE
python scripts/test_proactive_intelligence.py  # FREE
python scripts/test_gmail_agent.py             # FREE
python scripts/test_flight_agent.py            # FREE
```

---

*Last Updated: November 1, 2025*  
*Purpose: Clarify which tests make API calls and how to control them*

