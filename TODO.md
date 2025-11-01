# TravelMate AI - Implementation TODO List

**Hackathon:** Next-Generation Conversational Travel Insurance Distribution  
**Team:** Ancileo × MSIG  
**Architecture:** Enterprise-grade microservices with MCP  

---

## 🎯 Overview: 5 Blocks → 6 Phases

| Block | Phase | Status | Priority |
|-------|-------|--------|----------|
| Block 1 | Phase 1: Foundation | ✅ Complete | 🔥 Critical |
| Block 2 | Phase 2: MCP Layer | ✅ Complete | 🔥 Critical |
| Block 3 | Phase 3: Document Intelligence | ⏭️ Skipped | 🔥 Critical |
| Block 4 | Phase 4: Purchase Flow | ⚠️ Not Started | 🔥 Critical |
| Block 5 | Phase 5: Claims Intelligence | ⚠️ Not Started | 💡 Differentiator |
| -- | Phase 6: Polish & Demo | ⚠️ Not Started | 🎯 Final |

**Legend:**
- ✅ Completed
- 🚧 In Progress
- ⚠️ Not Started
- 🔥 Critical Path
- 💡 Innovation Differentiator
- 🎯 Demo Ready

---

## 📅 Phase 1: Foundation (BLOCK 1) - Day 1 Morning (4 hours)

**Objective:** Transform 3 policy PDFs into 4-layer taxonomy with dual-access pattern

### 1.1 Policy Data Extraction

- [x] **Task 1.1.1:** Read all 3 policy PDF documents
  - [x] Extract text from `Scootsurance QSR022206_updated.pdf` - 90,988 chars
  - [x] Extract text from `TravelEasy Policy QTD032212.pdf` - 170,550 chars
  - [x] Extract text from `TravelEasy Pre-Ex Policy QTD032212-PX.pdf` - 146,134 chars
  - **Tool:** Python `pdfplumber`
  - **Time:** 30 min ✅
  - **Owner:** AI Assistant

- [x] **Task 1.1.2:** Parse extracted text into structured format
  - [x] Identify sections, subsections, hierarchies
  - [x] Extract tables (coverage limits, benefits)
  - [x] Handle dual-column formats
  - **Time:** 1 hour ✅
  - **Owner:** AI Assistant

### 1.2 Taxonomy Mapping

- [x] **Task 1.2.1:** Load taxonomy template
  - [x] Read `Taxonomy/Taxonomy_Hackathon.json`
  - [x] Understand 4-layer structure
  - [x] Review taxonomy documentation PDF
  - **Time:** 15 min ✅
  - **Owner:** AI Assistant

- [x] **Task 1.2.2:** Map Scootsurance to taxonomy Layer 1 (General Conditions)
  - [x] Extract age eligibility (min/max)
  - [x] Extract residency requirements
  - [x] Extract trip duration limits
  - [x] Extract pre-existing condition rules
  - [x] Extract high-risk activity exclusions
  - [x] Extract destination restrictions
  - **Time:** 45 min ✅ (Using Groq llama-3.3-70b-versatile)
  - **Owner:** AI Assistant

- [x] **Task 1.2.3:** Map Scootsurance to taxonomy Layer 2 (Benefits Structure)
  - [x] Extract medical coverage limits (36 benefits extracted)
  - [x] Extract trip cancellation limits
  - [x] Extract baggage coverage limits
  - [x] Extract travel delay benefits
  - [x] Extract personal accident coverage
  - [x] Identify sub-limits for each benefit
  - **Time:** 45 min ✅
  - **Owner:** AI Assistant

- [x] **Task 1.2.4:** Map Scootsurance to taxonomy Layer 3 (Benefit Conditions)
  - [x] Extract eligibility per benefit
  - [x] Extract waiting periods
  - [x] Extract documentation requirements
  - [x] Extract benefit-specific exclusions
  - **Time:** 30 min ✅
  - **Owner:** AI Assistant

- [x] **Task 1.2.5:** Map Scootsurance to taxonomy Layer 4 (Operational)
  - [x] Extract deductibles/co-pays
  - [x] Extract claim procedures
  - [x] Extract time limits for claims
  - [x] Extract provider networks (if any)
  - **Time:** 20 min ✅
  - **Owner:** AI Assistant

- [x] **Task 1.2.6:** Repeat mapping for TravelEasy Standard
  - [x] Layer 1: General Conditions
  - [x] Layer 2: Benefits Structure (7 benefits)
  - [x] Layer 3: Benefit Conditions
  - [x] Layer 4: Operational
  - **Time:** 1 hour ✅
  - **Owner:** AI Assistant

- [x] **Task 1.2.7:** Repeat mapping for TravelEasy Pre-Ex
  - [x] Layer 1: General Conditions (focus on pre-existing rules)
  - [x] Layer 2: Benefits Structure (8 benefits)
  - [x] Layer 3: Benefit Conditions
  - [x] Layer 4: Operational
  - **Time:** 1 hour ✅
  - **Owner:** AI Assistant

### 1.3 Data Storage

- [x] **Task 1.3.1:** Create database for policies
  - [x] Database: SQLite (`travelmate.db`)
  - [x] Tables: policies, general_conditions, benefits, operational_details, claims
  - [x] Proper indexes and foreign keys configured
  - **Time:** 15 min ✅
  - **Owner:** AI Assistant

- [x] **Task 1.3.2:** Store normalized taxonomy data
  - [x] Insert Scootsurance with all 4 layers (36 benefits)
  - [x] Insert TravelEasy Standard with all 4 layers (7 benefits)
  - [x] Insert TravelEasy Pre-Ex with all 4 layers (8 benefits)
  - **Time:** 15 min ✅
  - **Owner:** AI Assistant

- [x] **Task 1.3.3:** Store raw policy text (dual-access requirement)
  - [x] Store original PDF text alongside normalized data
  - [x] Create mapping between normalized fields and original text sections
  - [x] Add source citations for traceability
  - **Time:** 20 min ✅
  - **Owner:** AI Assistant

### 1.4 Validation

- [x] **Task 1.4.1:** Validate completeness
  - [x] Check all required taxonomy fields populated
  - [x] Verify no missing critical data (limits, exclusions)
  - [x] Boolean validation for coverage availability
  - **Time:** 20 min ✅
  - **Owner:** AI Assistant

- [x] **Task 1.4.2:** Build dual-access data retrieval functions
  - [x] SQLAlchemy ORM provides structured data access
  - [x] Raw text stored in `original_text` field
  - [x] Test both access patterns work correctly
  - **Time:** 30 min ✅
  - **Owner:** AI Assistant

**Phase 1 Total Time:** ~4 hours ✅ COMPLETED  
**Phase 1 Completion Criteria:** ✅ 3 policies in SQLite with 4-layer taxonomy + raw text (51 benefits total)

---

## 📅 Phase 2: MCP Layer (BLOCK 2) - Day 1 Afternoon (6 hours) ✅ COMPLETE

**Objective:** Build MCP server with Tools/Resources/Prompts layers + query classification

### 2.1 MCP Server Setup

- [x] **Task 2.1.1:** Initialize MCP Python project
  - [x] Create project structure: `backend-mcp/`
  - [x] Install dependencies: `mcp`, `groq`, `fastapi`, `pydantic`, `sqlalchemy`
  - [x] Create `requirements.txt`
  - [x] Set up virtual environment
  - **Time:** 20 min ✅
  - **Owner:** AI Assistant

- [x] **Task 2.1.2:** Configure MCP server
  - [x] Create `app/main.py` with FastAPI
  - [x] Set up MCP protocol handlers in `app/mcp/server.py`
  - [x] Configure Groq API integration
  - [x] Add environment variables (API keys, database config)
  - **Time:** 30 min ✅
  - **Owner:** AI Assistant

### 2.2 Resources Layer

- [x] **Task 2.2.1:** Implement Normalized Policy Resource
  - [x] Resource: `normalized_policies` in `app/mcp/resources.py`
  - [x] Reads from SQLite structured data
  - [x] Returns PolicySchema JSON for algorithmic processing
  - [x] Tested: 3 policies with 51 total benefits retrieved
  - **Time:** 30 min ✅
  - **Owner:** AI Assistant

- [x] **Task 2.2.2:** Implement Original Document Resource
  - [x] Resource: `original_policy_text`
  - [x] Reads from SQLite raw text fields (90K+ chars per policy)
  - [x] Returns full-fidelity policy language with section extraction
  - [x] Tested: Retrieved 90,988 chars from Scootsurance
  - **Time:** 25 min ✅
  - **Owner:** AI Assistant

- [x] **Task 2.2.3:** Implement User Session Resource
  - [x] Resource: `user_session`
  - [x] Store conversation context in-memory (can be Redis later)
  - [x] Preserve extracted trip data, preferences, history
  - [x] Tested: Session creation and retrieval working
  - **Time:** 20 min ✅
  - **Owner:** AI Assistant

- [x] **Task 2.2.4:** Implement Taxonomy Schema Resource
  - [x] Resource: `taxonomy_schema`
  - [x] Load 4-layer taxonomy structure for reference
  - [x] Provide field definitions and descriptions
  - [x] Tested: All 4 layers accessible
  - **Time:** 15 min ✅
  - **Owner:** AI Assistant

### 2.3 Tools Layer - Comparison Queries

- [x] **Task 2.3.1:** Build `compare_policies` tool
  - [x] Input: `policy_ids[]`, `comparison_criteria[]`, `user_context`
  - [x] Access: Normalized policy resource via PolicyComparisonService
  - [x] Output: Side-by-side feature matrix with 47 benefit categories
  - [x] Test: Compared all 3 policies successfully
  - **Time:** 1.5 hours ✅
  - **Owner:** AI Assistant

- [x] **Task 2.3.2:** Implement multi-dimensional comparison logic
  - [x] Benefit-by-benefit analysis (medical, cancellation, baggage)
  - [x] Limit comparison (absolute, sub-limits handling)
  - [x] Exclusion analysis (pre-existing, activities, destinations)
  - [x] Recommendation generation with rationale
  - **Time:** 45 min ✅
  - **Owner:** AI Assistant

### 2.4 Tools Layer - Explanation Queries

- [x] **Task 2.4.1:** Build `answer_policy_question` tool
  - [x] Input: `question`, `policy_id` (optional), `include_citations`
  - [x] Access: Original policy text + normalized context via QuestionAnsweringService
  - [x] Output: Detailed answer with exact policy language (1753-2385 chars)
  - [x] Test: "What is the maximum coverage for emergency medical expenses?" - 90% confidence
  - [x] Groq LLM integration: llama-3.3-70b-versatile model
  - **Time:** 1.5 hours ✅
  - **Owner:** AI Assistant

- [x] **Task 2.4.2:** Implement citation system
  - [x] Link answers to original policy sections
  - [x] Extract policy names mentioned in answers
  - [x] Return citations with policy document references
  - [x] Confidence scoring (0.6-0.9 range)
  - **Time:** 30 min ✅
  - **Owner:** AI Assistant

### 2.5 Tools Layer - Eligibility & Scenario Queries

- [x] **Task 2.5.1:** Build `check_eligibility` tool
  - [x] Input: `user_profile` (age, health, destination, trip_duration)
  - [x] Access: Layer 1 (General Conditions) via EligibilityService
  - [x] Output: Eligible products with qualifying conditions + warnings
  - [x] Test: 2 travelers, 14-day USA trip - correctly identified eligible policies
  - [x] Real logic: age checks, duration checks, pre-existing conditions
  - **Time:** 1 hour ✅
  - **Owner:** AI Assistant

- [x] **Task 2.5.2:** Build `analyze_scenario` tool
  - [x] Input: `scenario_description` (e.g., "break leg skiing in Japan")
  - [x] Access: Multiple benefits and exclusions (Layers 2+3)
  - [x] Output: Step-by-step coverage analysis with LLM intelligence
  - [x] Reuses question answering service for scenario analysis
  - **Time:** 45 min ✅
  - **Owner:** AI Assistant

### 2.6 Quote Generation

- [x] **Task 2.6.1:** Build `get_quote` tool
  - [x] Input: `trip_details`, `policy_ids` (optional)
  - [x] Access: Policies + eligibility + pricing logic via QuoteService
  - [x] Output: Quote with premiums ($291-$2912 SGD), recommendations
  - [x] Real pricing logic: base rate, age factors, destination risk, activities
  - [x] Test: Japan 16-day trip with skiing - quotes generated successfully
  - **Time:** 2 hours ✅
  - **Owner:** AI Assistant

### 2.7 Prompts Layer

- [x] **Task 2.7.1:** Create comparison prompt templates
  - [x] Structured format for product comparison in `app/mcp/prompts.py`
  - [x] Clear differentiation and value assessment
  - [x] User-friendly language (avoid jargon)
  - [x] Test: Comparison prompt generated correctly
  - **Time:** 30 min ✅
  - **Owner:** AI Assistant

- [x] **Task 2.7.2:** Create explanation prompt templates
  - [x] Natural language generation guides
  - [x] Legal precision with clarity
  - [x] Include citations and references
  - [x] 7 prompt types: greeting, comparison, explanation, recommendation, eligibility, quote, error
  - **Time:** 30 min ✅
  - **Owner:** AI Assistant

### 2.8 FastAPI Application

- [x] **Task 2.8.1:** Build REST API endpoints
  - [x] `/health`: Health check
  - [x] `/`: API information
  - [x] `/mcp`: Generic MCP protocol endpoint
  - [x] `/compare`: Policy comparison
  - [x] `/ask`: Question answering
  - [x] `/eligibility`: Eligibility checking
  - [x] `/scenario`: Scenario analysis
  - [x] `/quote`: Quote generation
  - [x] `/policies`: List all policies
  - [x] `/policies/{policy_id}`: Get policy details
  - **Time:** 1.5 hours ✅
  - **Owner:** AI Assistant

### 2.9 Testing & Validation

- [x] **Task 2.9.1:** Comprehensive testing
  - [x] Test script: `scripts/test_mcp_server.py`
  - [x] 7/7 tests passed ✅
  - [x] Resources layer: 3 policies retrieved
  - [x] Eligibility: Real checks working
  - [x] Question answering: Groq LLM integration working
  - [x] Policy comparison: 47 benefit categories
  - [x] Quote generation: Real premiums calculated
  - [x] Prompt templates: All 7 types functional
  - [x] MCP protocol: Full request/response cycle
  - **Time:** 2 hours ✅
  - **Owner:** AI Assistant

**Phase 2 Total Time:** ~10 hours (more than estimated due to comprehensive implementation) ✅ COMPLETED  
**Phase 2 Completion Criteria:** ✅ MCP server with 8 tools, 4 resources, 7 prompt templates, FastAPI REST API, ALL TESTS PASSING

---

## 📅 Phase 3: Intelligent Data Collection (BLOCK 3) - Day 2 Morning (5.5 hours)

**Objective:** Revolutionary zero-form data collection using Agentic AI + Real-time Intelligence  
**Status:** ✅ Redesigned - Multiple intelligent entry points replacing traditional forms  
**Innovation:** 20 minutes → 30 seconds | 70% → <10% abandonment rate

### 3.1 Conversational Data Extraction (Primary UX)

- [ ] **Task 3.1.1:** Build conversational context manager
  - [ ] Extend existing MCP user session resource
  - [ ] Track extracted trip details through conversation
  - [ ] Handle multi-turn dialogue state
  - [ ] Validate completeness before quote generation
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 3.1.2:** Implement natural language trip extraction
  - [ ] Parse destination from casual input ("going to Japan")
  - [ ] Extract dates (relative: "next month", absolute: "Dec 20")
  - [ ] Identify travelers ("with my wife" → 2 travelers)
  - [ ] Detect activities ("skiing" → high-risk activity)
  - [ ] Uses existing Groq LLM for understanding
  - **Time:** 45 min
  - **Owner:** [Assign]

- [ ] **Task 3.1.3:** Create guided conversation flow
  - [ ] Smart follow-up questions (only ask what's missing)
  - [ ] Conversational validation (confirm extracted details)
  - [ ] Handle ambiguity ("this weekend" → ask which)
  - [ ] Test with 5+ different conversation styles
  - **Time:** 45 min
  - **Owner:** [Assign]

### 3.2 Tavily Real-Time Intelligence Integration 🔥 NEW!

- [ ] **Task 3.2.1:** Set up Tavily Search API
  - [ ] Sign up at https://www.tavily.com (1,000 free credits/month)
  - [ ] Install: `pip install tavily-python`
  - [ ] Configure API key in `.env`
  - [ ] Test basic search functionality
  - **Time:** 10 min
  - **Owner:** [Assign]

- [ ] **Task 3.2.2:** Build real-time destination intelligence tool
  - [ ] New MCP tool: `get_destination_intelligence`
  - [ ] Tavily search: Travel advisories, visa requirements, health alerts
  - [ ] Extract: Insurance requirements, vaccination needs, risk factors
  - [ ] Cache results (1 hour TTL) for performance
  - [ ] Test with: Japan, Bali, USA, Thailand destinations
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 3.2.3:** Build proactive risk intelligence tool
  - [ ] New MCP tool: `analyze_real_time_risks`
  - [ ] Tavily search: Current conditions, weather, health outbreaks
  - [ ] Combine with Phase 5 historical claims data
  - [ ] Generate risk alerts with citations
  - [ ] Test: "Japan ski trip December" → flu outbreak + snow conditions
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 3.2.4:** Implement intelligent upselling logic
  - [ ] Use Tavily data to justify coverage upgrades
  - [ ] Example: "Hospital costs up 20% this year" → upgrade medical
  - [ ] Include source citations from Tavily
  - [ ] A/B test messaging effectiveness
  - **Time:** 20 min
  - **Owner:** [Assign]

### 3.3 Gmail/Email Integration

- [ ] **Task 3.3.1:** Set up Gmail API OAuth
  - [ ] Create Google Cloud project
  - [ ] Enable Gmail API
  - [ ] Configure OAuth consent screen
  - [ ] Implement OAuth flow in backend
  - [ ] Test with personal Gmail account
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 3.3.2:** Build email scanning MCP tool
  - [ ] New MCP tool: `scan_gmail_for_bookings`
  - [ ] Search for: "booking confirmed", "itinerary", "reservation"
  - [ ] Filter by date (last 30 days, next 90 days)
  - [ ] Return list of potential trips
  - [ ] Test with real booking emails
  - **Time:** 45 min
  - **Owner:** [Assign]

- [ ] **Task 3.3.3:** Implement booking confirmation parser
  - [ ] Pattern matching for airlines (Singapore Airlines, ANA, etc.)
  - [ ] Pattern matching for hotels (Booking.com, Airbnb, etc.)
  - [ ] Extract: Destination, dates, travelers, booking cost
  - [ ] Use Groq LLM for intelligent extraction when patterns fail
  - [ ] Test with 10+ different booking email formats
  - **Time:** 1 hour
  - **Owner:** [Assign]

### 3.4 Document Upload + Vision AI

- [ ] **Task 3.4.1:** Build document upload endpoint
  - [ ] FastAPI endpoint: POST `/upload-document`
  - [ ] Support: PDF, JPG, PNG (max 10MB)
  - [ ] Temporary storage (in-memory or /tmp)
  - [ ] Return upload ID for processing
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 3.4.2:** Integrate Claude Vision API for OCR
  - [ ] Use existing Anthropic API credentials
  - [ ] Claude Vision model for image/PDF analysis
  - [ ] Extract all visible text and structured data
  - [ ] Confidence scoring for extracted fields
  - [ ] Test with sample flight confirmations
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 3.4.3:** Build intelligent document parser
  - [ ] New MCP tool: `extract_trip_from_document`
  - [ ] Identify document type (flight/hotel/visa)
  - [ ] Extract: Names, dates, destinations, costs
  - [ ] Validate extracted data (dates logical, etc.)
  - [ ] Handle errors gracefully (ask user for clarification)
  - [ ] Test with 10+ different document formats
  - **Time:** 45 min
  - **Owner:** [Assign]

### 3.5 Integration with Existing MCP Tools

- [ ] **Task 3.5.1:** Connect conversational extraction to quote flow
  - [ ] Map extracted data to TripDetailsSchema
  - [ ] Automatically call `check_eligibility` when data complete
  - [ ] Seamlessly transition to `get_quote`
  - [ ] No explicit "submit" - feels conversational
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 3.5.2:** Enhance quote service with Tavily intelligence
  - [ ] Inject Tavily insights into quote response
  - [ ] Show real-time risk factors alongside pricing
  - [ ] Include source citations for credibility
  - [ ] Test: Quote should include "Based on current conditions..."
  - **Time:** 15 min
  - **Owner:** [Assign]

### 3.6 Testing & Validation

- [ ] **Task 3.6.1:** Test conversational extraction
  - [ ] Test 5+ different conversation styles
  - [ ] Measure: Time to complete extraction
  - [ ] Target: <2 minutes for full trip details
  - [ ] Validate: All required fields captured
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 3.6.2:** Test Tavily intelligence integration
  - [ ] Test with 5+ destinations (Japan, Bali, USA, Thailand, Europe)
  - [ ] Verify: Real-time data is relevant and accurate
  - [ ] Validate: Citations are included
  - [ ] Measure: API response time (<2s)
  - **Time:** 15 min
  - **Owner:** [Assign]

- [ ] **Task 3.6.3:** Test Gmail scanning
  - [ ] Test with real inbox (10+ booking emails)
  - [ ] Measure: Accuracy of trip identification
  - [ ] Validate: Correct data extraction
  - [ ] Target: 90%+ accuracy
  - **Time:** 15 min
  - **Owner:** [Assign]

- [ ] **Task 3.6.4:** Test document upload flow
  - [ ] Test with 10+ different document formats
  - [ ] Flight confirmations, hotel bookings, screenshots
  - [ ] Measure: Extraction accuracy per field
  - [ ] Target: 95%+ for critical fields (dates, destination)
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 3.6.5:** End-to-end integration test
  - [ ] Test all 3 entry points → quote generation
  - [ ] Conversational: "Going to Japan skiing" → quote
  - [ ] Gmail: Scan → select trip → quote
  - [ ] Upload: Drop PDF → quote
  - [ ] Measure: Total time for each path
  - [ ] Target: <2 minutes for any path
  - **Time:** 30 min
  - **Owner:** [Assign]

**Phase 3 Total Time:** ~5.5 hours  
**Phase 3 Completion Criteria:** 
✅ 3 working entry points (Chat, Gmail, Upload)
✅ Tavily real-time intelligence integrated
✅ <2 minute quote generation from any entry point
✅ Zero traditional forms
✅ 95%+ extraction accuracy
✅ Real-time risk intelligence with citations

---

## 📅 Phase 4: Purchase Flow (BLOCK 4) - Day 2 Morning (3 hours)

**Objective:** Complete in-conversation purchase using existing Stripe integration

### 4.1 Payment System Integration

- [ ] **Task 4.1.1:** Review existing payment infrastructure
  - [ ] Check `Payments/` folder components
  - [ ] Review `stripe_webhook.py` (webhook handler)
  - [ ] Review `test_payment_flow.py` (reference implementation)
  - [ ] Verify DynamoDB table `lea-payments-local` exists
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 4.1.2:** Start payment services
  - [ ] Run `docker-compose up` in `Payments/` folder
  - [ ] Verify DynamoDB Local running on port 8000
  - [ ] Verify DynamoDB Admin UI on port 8010
  - [ ] Verify Stripe webhook on port 8086
  - [ ] Verify payment pages on port 8085
  - **Time:** 15 min
  - **Owner:** [Assign]

### 4.2 Purchase MCP Tool

- [ ] **Task 4.2.1:** Build `purchase_policy` MCP tool
  - [ ] Input: `quote_id`, `user_id`, `payment_method`
  - [ ] Output: `checkout_url`, `payment_intent_id`, `expires_at`
  - [ ] Adapts code from `test_payment_flow.py`
  - **Time:** 1 hour
  - **Owner:** [Assign]

- [ ] **Task 4.2.2:** Implement payment record creation
  - [ ] Create payment record in DynamoDB
  - [ ] Fields: payment_intent_id, user_id, quote_id, status=pending, amount, currency
  - [ ] Generate unique payment_intent_id
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 4.2.3:** Implement Stripe checkout session
  - [ ] Create Stripe checkout session
  - [ ] Set success_url and cancel_url
  - [ ] Include metadata: user_id, quote_id
  - [ ] Return checkout URL to user
  - **Time:** 20 min
  - **Owner:** [Assign]

### 4.3 Payment Status Monitoring

- [ ] **Task 4.3.1:** Build `check_payment_status` MCP tool
  - [ ] Input: `payment_intent_id`
  - [ ] Query: DynamoDB for current status
  - [ ] Output: `status`, `policy_number`, `updated_at`
  - [ ] Polls for webhook updates
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 4.3.2:** Test webhook processing
  - [ ] Simulate successful payment
  - [ ] Verify webhook updates DynamoDB status
  - [ ] Verify status changes: pending → completed
  - [ ] Test failure scenarios
  - **Time:** 20 min
  - **Owner:** [Assign]

### 4.4 Policy Issuance Integration

- [ ] **Task 4.4.1:** Integrate with MSIG policy issuance API
  - [ ] Review API documentation
  - [ ] Build API client for policy issuance
  - [ ] Input: quote_id, payment_confirmation
  - [ ] Output: policy_number, policy_document_url
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 4.4.2:** Implement policy delivery
  - [ ] Store policy_number in DynamoDB payment record
  - [ ] Return policy details in conversation
  - [ ] Provide policy document download link
  - **Time:** 15 min
  - **Owner:** [Assign]

### 4.5 Conversation Integration

- [ ] **Task 4.5.1:** Test end-to-end purchase flow
  - [ ] Accept quote in conversation
  - [ ] Call purchase_policy tool → get checkout URL
  - [ ] User completes payment (test mode)
  - [ ] Webhook updates status
  - [ ] Policy issued and confirmed in chat
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 4.5.2:** Implement error handling
  - [ ] Payment declined → clear error + retry option
  - [ ] Checkout expired → regenerate session
  - [ ] API failures → graceful degradation
  - [ ] User guidance through issues
  - **Time:** 20 min
  - **Owner:** [Assign]

**Phase 4 Total Time:** ~3 hours  
**Phase 4 Completion Criteria:** ✅ Quote acceptance → payment → policy issuance within conversation

---

## 📅 Phase 5: Claims Intelligence (BLOCK 5) - Day 2 Afternoon (4 hours)

**Objective:** Use historical claims data for predictive recommendations (DIFFERENTIATOR)

### 5.1 Claims Data Extraction

- [ ] **Task 5.1.1:** Read claims database PDF
  - [ ] Extract text from `Claims_Data_DB.pdf`
  - [ ] Identify data structure (tables, patterns)
  - [ ] Parse into structured format (CSV or JSON)
  - **Time:** 1 hour
  - **Owner:** [Assign]

- [ ] **Task 5.1.2:** Store claims data
  - [ ] Create S3 bucket for processed claims data
  - [ ] Store as Parquet files for fast querying
  - [ ] Or: Load into DynamoDB claims table
  - [ ] Or: SQLite for analytics
  - **Time:** 20 min
  - **Owner:** [Assign]

### 5.2 Risk Scoring Engine

- [ ] **Task 5.2.1:** Build `analyze_trip_risk` MCP tool
  - [ ] Input: `trip_details` (destination, activities, duration, age)
  - [ ] Output: `RiskAnalysis` with scores and recommendations
  - **Time:** 1 hour
  - **Owner:** [Assign]

- [ ] **Task 5.2.2:** Implement destination risk analysis
  - [ ] Query claims data by destination
  - [ ] Calculate claim frequency rate
  - [ ] Calculate average claim amount
  - [ ] Example: "73% of Japan winter travelers make claims, avg $32K"
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 5.2.3:** Implement activity risk analysis
  - [ ] Query claims data by activity (skiing, scuba, hiking)
  - [ ] Calculate activity-specific claim rates
  - [ ] Example: "Skiing claims 4x higher than general travel"
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 5.2.4:** Implement age-based risk analysis
  - [ ] Query claims data by traveler age groups
  - [ ] Calculate age-specific claim rates
  - [ ] Example: "Travelers 65+ have 2x medical claim rate"
  - **Time:** 20 min
  - **Owner:** [Assign]

### 5.3 Product Tier Recommendations

- [ ] **Task 5.3.1:** Build recommendation logic
  - [ ] Analyze risk score against product tiers
  - [ ] Match historical claims to coverage limits
  - [ ] Example: "80% of claims at this destination exceed Bronze limit"
  - **Time:** 45 min
  - **Owner:** [Assign]

- [ ] **Task 5.3.2:** Generate data-driven narratives
  - [ ] "Customers with similar trips average $X in claims"
  - [ ] "Silver Plan covers 98% of claims for this destination"
  - [ ] "Bronze Plan risky: 15% of claims exceeded $20K limit"
  - **Time:** 30 min
  - **Owner:** [Assign]

### 5.4 Integration with Quotation

- [ ] **Task 5.4.1:** Enhance `get_quote` tool with risk analysis
  - [ ] Call `analyze_trip_risk` during quote generation
  - [ ] Return quote + risk analysis + recommendation
  - [ ] Show specific product tier guidance
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 5.4.2:** Test claims-driven recommendations
  - [ ] Test: Japan skiing trip → Silver recommended
  - [ ] Test: Thailand beach trip → Bronze sufficient
  - [ ] Test: Pre-existing condition → Pre-Ex plan required
  - [ ] Verify rationale includes claims data
  - **Time:** 20 min
  - **Owner:** [Assign]

**Phase 5 Total Time:** ~4 hours  
**Phase 5 Completion Criteria:** ✅ Claims data integrated → risk scoring → data-driven recommendations with narratives

---

## 📅 Phase 6: Polish & Demo (Final) - Day 2 Evening + Day 3 (8 hours)

**Objective:** Web UI, end-to-end testing, demo preparation

### 6.1 Web Chat Interface

- [ ] **Task 6.1.1:** Set up Next.js project
  - [ ] Create `travelmate-ui/` folder
  - [ ] Initialize Next.js 14 with TypeScript
  - [ ] Install dependencies: shadcn/ui, Tailwind, Zustand
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 6.1.2:** Build chat interface
  - [ ] Chat message list (user + assistant)
  - [ ] Message input with file upload
  - [ ] Typing indicators
  - [ ] Real-time updates
  - **Time:** 2 hours
  - **Owner:** [Assign]

- [ ] **Task 6.1.3:** Connect to MCP backend
  - [ ] API client for MCP server
  - [ ] Handle streaming responses
  - [ ] Display tool calls (loading states)
  - **Time:** 1 hour
  - **Owner:** [Assign]

- [ ] **Task 6.1.4:** Implement document upload UI
  - [ ] Drag-and-drop file upload
  - [ ] Preview uploaded documents
  - [ ] Show extraction results
  - **Time:** 1 hour
  - **Owner:** [Assign]

- [ ] **Task 6.1.5:** Build comparison visualization
  - [ ] Side-by-side policy comparison table
  - [ ] Highlight differences
  - [ ] Visual coverage limits chart
  - **Time:** 1 hour
  - **Owner:** [Assign]

### 6.2 End-to-End Testing

- [ ] **Task 6.2.1:** Test full user journey - Scenario 1
  - [ ] User: "I'm planning a ski trip to Japan"
  - [ ] Upload: Flight confirmation
  - [ ] Extract: Trip details automatically
  - [ ] Compare: Scootsurance vs TravelEasy
  - [ ] Risk analysis: "73% of travelers make claims, avg $32K"
  - [ ] Recommend: Silver plan
  - [ ] Quote: $89 for both travelers
  - [ ] Purchase: Complete payment
  - [ ] Confirm: Policy issued
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 6.2.2:** Test full user journey - Scenario 2
  - [ ] User: "Thailand beach vacation with pre-existing condition"
  - [ ] Upload: Hotel booking + flight
  - [ ] Extract: Trip details
  - [ ] Eligibility: Flag pre-existing condition
  - [ ] Recommend: TravelEasy Pre-Ex plan
  - [ ] Quote: With pre-ex coverage
  - [ ] Purchase: Complete
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 6.2.3:** Test edge cases
  - [ ] Invalid document upload
  - [ ] Incomplete extraction
  - [ ] Payment failure
  - [ ] API timeouts
  - [ ] Conflicting trip dates
  - **Time:** 30 min
  - **Owner:** [Assign]

### 6.3 Performance Optimization

- [ ] **Task 6.3.1:** Optimize API response times
  - [ ] Target: P95 < 1.5s for conversational queries
  - [ ] Target: <3s for document extraction
  - [ ] Target: <500ms for policy comparisons
  - [ ] Add caching where appropriate
  - **Time:** 1 hour
  - **Owner:** [Assign]

- [ ] **Task 6.3.2:** Add loading states & error handling
  - [ ] Graceful degradation on failures
  - [ ] Clear error messages to user
  - [ ] Retry mechanisms
  - **Time:** 30 min
  - **Owner:** [Assign]

### 6.4 Demo Preparation

- [ ] **Task 6.4.1:** Prepare demo script
  - [ ] Scenario 1: Japan skiing (claims intelligence highlight)
  - [ ] Scenario 2: Pre-existing condition handling
  - [ ] Scenario 3: Complex multi-city trip
  - [ ] Show all 5 blocks in action
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 6.4.2:** Prepare demo data
  - [ ] Sample flight confirmations
  - [ ] Sample hotel bookings
  - [ ] Test payment cards (Stripe test mode)
  - [ ] Pre-populate some data if needed
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 6.4.3:** Record demo video (backup)
  - [ ] Screen recording of full journey
  - [ ] Voiceover explaining each step
  - [ ] Highlight innovation points
  - **Time:** 1 hour
  - **Owner:** [Assign]

- [ ] **Task 6.4.4:** Prepare presentation slides
  - [ ] Architecture overview
  - [ ] 5 blocks implementation
  - [ ] Technical highlights (MCP, claims intelligence)
  - [ ] Live demo transition
  - **Time:** 1 hour
  - **Owner:** [Assign]

### 6.5 Documentation

- [ ] **Task 6.5.1:** Update README
  - [ ] Project overview
  - [ ] Setup instructions
  - [ ] Architecture diagram
  - [ ] API documentation
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 6.5.2:** Code comments & cleanup
  - [ ] Add docstrings to all functions
  - [ ] Remove debug code
  - [ ] Clean up unused imports
  - **Time:** 30 min
  - **Owner:** [Assign]

**Phase 6 Total Time:** ~8 hours  
**Phase 6 Completion Criteria:** ✅ Beautiful UI + Full demo ready + All 5 blocks working end-to-end

---

## 📊 Progress Tracking

### Overall Completion

```
Phase 1: Foundation               [████████████████████] 100% ✅
Phase 2: MCP Layer                [████████████████████] 100% ✅
Phase 3: Intelligent Data Collect [                    ] 0% 
Phase 4: Purchase Flow            [                    ] 0%
Phase 5: Claims Intelligence      [                    ] 0%
Phase 6: Polish & Demo            [                    ] 0%
----------------------------------------
Total Progress:                   [████████░░░░░░░░░░░░] 40%
```

### Time Budget

| Phase | Estimated | Actual | Status |
|-------|-----------|--------|--------|
| Phase 1 | 4h | 4h | ✅ Complete |
| Phase 2 | 6h | -- | 🚧 In Progress |
| Phase 3 | 4h | 0h | ⏭️ Skipped |
| Phase 4 | 3h | -- | ⚠️ Not Started |
| Phase 5 | 4h | -- | ⚠️ Not Started |
| Phase 6 | 8h | -- | ⚠️ Not Started |
| **Total** | **29h** | **4h** | **20% Complete** |

---

## 🎯 Critical Success Factors

### Must-Have (Minimum Viable Demo)
- ✅ 3 policies normalized in 4-layer taxonomy *(BLOCK 1)* **COMPLETE**
- ✅ MCP server with comparison + FAQ tools *(BLOCK 2)* **COMPLETE**
- [ ] Zero-form intelligent data collection *(BLOCK 3)* **NEXT** - Chat, Gmail, Upload
- [ ] Complete purchase flow *(BLOCK 4)*

### Differentiators (Competitive Advantage)
- [ ] Claims data intelligence *(BLOCK 5)* **TODO**
- ✅ Data-driven recommendations with real pricing logic **COMPLETE**
- ✅ Dual-access pattern (normalized + raw text) **COMPLETE**
- [ ] Beautiful, responsive UI *(Phase 6)* **TODO**

### Demo Requirements
- ✅ End-to-end working demo (upload → quote → purchase)
- ✅ Show all 5 blocks in action
- ✅ <2 minute purchase time (vs 20 min traditional)
- ✅ Impressive "wow" moments (auto-extraction, claims insights)

---

## 📝 Notes & Decisions

### Technical Decisions
- **Database:** SQLite (for hackathon simplicity) ✅
- **LLM:** Groq API with llama-3.3-70b-versatile model ✅
- **Document Processing:** Claude Vision API for OCR - Phase 3
- **Real-Time Intelligence:** Tavily Search API (1,000 free credits/month) - Phase 3 🔥 NEW!
- **Email Integration:** Gmail API OAuth - Phase 3
- **Payment:** Stripe (already integrated!) - Phase 4 next
- **Frontend:** Next.js 14 + shadcn/ui (Phase 6) or Claude Desktop MCP
- **Backend:** FastAPI for MCP server ✅ COMPLETE
- **PDF Processing:** pdfplumber for text extraction ✅
- **MCP Protocol:** Custom implementation with 8 tools, 4 resources ✅
- **Testing:** Comprehensive test suite - 7/7 tests passing ✅

### Known Limitations
- Claims data extraction from PDF may be time-consuming (Phase 5)
- External API (MSIG quote/policy) documentation needs review
- Stripe webhook testing requires ngrok or similar for local dev

### Risk Mitigation
- Payment system already working (biggest risk mitigated!)
- Start with 1 policy if PDF extraction is slow, scale to 3 later
- Focus on working demo over perfect code
- Prepare backup demo video in case live demo fails

---

## 🚀 Next Steps

**Immediate Action Items:**
1. [x] Review this TODO with team ✅
2. [x] Assign owners to each phase ✅
3. [x] Set up development environment ✅
4. [x] Phase 1: Policy extraction ✅
5. [x] Phase 2: Build MCP server ✅
6. [ ] Phase 3: Intelligent Data Collection 🎯 NEXT
   - [ ] Conversational extraction (reuses Phase 2)
   - [ ] Tavily API integration (real-time intelligence) 🔥
   - [ ] Gmail scanning (OAuth + parsing)
   - [ ] Document upload (Claude Vision OCR)

**Daily Stand-ups:**
- Morning: Review yesterday's progress, assign today's tasks
- Evening: Demo current state, identify blockers

**Demo Rehearsal:**
- Day 2 evening: First full run-through
- Day 3 morning: Final polish
- Day 3 afternoon: Demo ready!

---

**Let's build something amazing! 🎉**

