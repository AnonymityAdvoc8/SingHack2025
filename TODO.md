# TravelMate AI - Implementation TODO List

**Hackathon:** Next-Generation Conversational Travel Insurance Distribution  
**Team:** Ancileo × MSIG  
**Architecture:** Enterprise-grade microservices with MCP  

---

## 🎯 Overview: 5 Blocks → 6 Phases

| Block | Phase | Status | Priority |
|-------|-------|--------|----------|
| Block 1 | Phase 1: Foundation | ⚠️ Not Started | 🔥 Critical |
| Block 2 | Phase 2: MCP Layer | ⚠️ Not Started | 🔥 Critical |
| Block 3 | Phase 3: Document Intelligence | ⚠️ Not Started | 🔥 Critical |
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

- [ ] **Task 1.1.1:** Read all 3 policy PDF documents
  - [ ] Extract text from `Scootsurance QSR022206_updated.pdf`
  - [ ] Extract text from `TravelEasy Policy QTD032212.pdf`
  - [ ] Extract text from `TravelEasy Pre-Ex Policy QTD032212-PX.pdf`
  - **Tool:** Python `pdfplumber` or Claude API with PDF input
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 1.1.2:** Parse extracted text into structured format
  - [ ] Identify sections, subsections, hierarchies
  - [ ] Extract tables (coverage limits, benefits)
  - [ ] Handle dual-column formats
  - **Time:** 1 hour
  - **Owner:** [Assign]

### 1.2 Taxonomy Mapping

- [ ] **Task 1.2.1:** Load taxonomy template
  - [ ] Read `Taxonomy/Taxonomy_Hackathon.json`
  - [ ] Understand 4-layer structure
  - [ ] Review taxonomy documentation PDF
  - **Time:** 15 min
  - **Owner:** [Assign]

- [ ] **Task 1.2.2:** Map Scootsurance to taxonomy Layer 1 (General Conditions)
  - [ ] Extract age eligibility (min/max)
  - [ ] Extract residency requirements
  - [ ] Extract trip duration limits
  - [ ] Extract pre-existing condition rules
  - [ ] Extract high-risk activity exclusions
  - [ ] Extract destination restrictions
  - **Time:** 45 min
  - **Owner:** [Assign]

- [ ] **Task 1.2.3:** Map Scootsurance to taxonomy Layer 2 (Benefits Structure)
  - [ ] Extract medical coverage limits
  - [ ] Extract trip cancellation limits
  - [ ] Extract baggage coverage limits
  - [ ] Extract travel delay benefits
  - [ ] Extract personal accident coverage
  - [ ] Identify sub-limits for each benefit
  - **Time:** 45 min
  - **Owner:** [Assign]

- [ ] **Task 1.2.4:** Map Scootsurance to taxonomy Layer 3 (Benefit Conditions)
  - [ ] Extract eligibility per benefit
  - [ ] Extract waiting periods
  - [ ] Extract documentation requirements
  - [ ] Extract benefit-specific exclusions
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 1.2.5:** Map Scootsurance to taxonomy Layer 4 (Operational)
  - [ ] Extract deductibles/co-pays
  - [ ] Extract claim procedures
  - [ ] Extract time limits for claims
  - [ ] Extract provider networks (if any)
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 1.2.6:** Repeat mapping for TravelEasy Standard
  - [ ] Layer 1: General Conditions
  - [ ] Layer 2: Benefits Structure
  - [ ] Layer 3: Benefit Conditions
  - [ ] Layer 4: Operational
  - **Time:** 1 hour
  - **Owner:** [Assign]

- [ ] **Task 1.2.7:** Repeat mapping for TravelEasy Pre-Ex
  - [ ] Layer 1: General Conditions (focus on pre-existing rules)
  - [ ] Layer 2: Benefits Structure
  - [ ] Layer 3: Benefit Conditions
  - [ ] Layer 4: Operational
  - **Time:** 1 hour
  - **Owner:** [Assign]

### 1.3 Data Storage

- [ ] **Task 1.3.1:** Create DynamoDB table for policies
  - [ ] Table name: `travel-insurance-policies`
  - [ ] Partition key: `policy_id`
  - [ ] Sort key: `version`
  - [ ] Configure on-demand capacity
  - **Time:** 15 min
  - **Owner:** [Assign]

- [ ] **Task 1.3.2:** Store normalized taxonomy data
  - [ ] Insert Scootsurance with all 4 layers
  - [ ] Insert TravelEasy Standard with all 4 layers
  - [ ] Insert TravelEasy Pre-Ex with all 4 layers
  - **Time:** 15 min
  - **Owner:** [Assign]

- [ ] **Task 1.3.3:** Store raw policy text (dual-access requirement)
  - [ ] Store original PDF text alongside normalized data
  - [ ] Create mapping between normalized fields and original text sections
  - [ ] Add source citations for traceability
  - **Time:** 20 min
  - **Owner:** [Assign]

### 1.4 Validation

- [ ] **Task 1.4.1:** Validate completeness
  - [ ] Check all required taxonomy fields populated
  - [ ] Verify no missing critical data (limits, exclusions)
  - [ ] Boolean validation for coverage availability
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 1.4.2:** Build dual-access data retrieval functions
  - [ ] Function: `get_normalized_policy(policy_id)` → Returns structured data
  - [ ] Function: `get_original_policy_text(policy_id, section)` → Returns raw text
  - [ ] Test both access patterns work correctly
  - **Time:** 30 min
  - **Owner:** [Assign]

**Phase 1 Total Time:** ~4 hours  
**Phase 1 Completion Criteria:** ✅ 3 policies in DynamoDB with 4-layer taxonomy + raw text

---

## 📅 Phase 2: MCP Layer (BLOCK 2) - Day 1 Afternoon (6 hours)

**Objective:** Build MCP server with Tools/Resources/Prompts layers + query classification

### 2.1 MCP Server Setup

- [ ] **Task 2.1.1:** Initialize MCP Python project
  - [ ] Create project structure: `mcp-server/`
  - [ ] Install dependencies: `anthropic`, `mcp`, `boto3`, `fastapi`
  - [ ] Create `requirements.txt`
  - [ ] Set up virtual environment
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 2.1.2:** Configure MCP server
  - [ ] Create `server.py` with FastAPI
  - [ ] Set up MCP protocol handlers
  - [ ] Configure Claude API integration
  - [ ] Add environment variables (API keys, AWS credentials)
  - **Time:** 30 min
  - **Owner:** [Assign]

### 2.2 Resources Layer

- [ ] **Task 2.2.1:** Implement Normalized Policy Resource
  - [ ] Resource: `normalized_policies`
  - [ ] Reads from DynamoDB structured data
  - [ ] Returns JSON for algorithmic processing
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 2.2.2:** Implement Original Document Resource
  - [ ] Resource: `original_policy_text`
  - [ ] Reads from DynamoDB raw text fields
  - [ ] Returns full-fidelity policy language
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 2.2.3:** Implement User Session Resource
  - [ ] Resource: `user_session`
  - [ ] Store conversation context in Redis/DynamoDB
  - [ ] Preserve extracted trip data, preferences, history
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 2.2.4:** Implement Taxonomy Schema Resource
  - [ ] Resource: `taxonomy_schema`
  - [ ] Load taxonomy structure for reference
  - [ ] Provide field definitions and descriptions
  - **Time:** 15 min
  - **Owner:** [Assign]

### 2.3 Tools Layer - Comparison Queries

- [ ] **Task 2.3.1:** Build `compare_policies` tool
  - [ ] Input: `policy_ids[]`, `comparison_criteria[]`, `user_context`
  - [ ] Access: Normalized policy resource
  - [ ] Output: Side-by-side feature matrix
  - [ ] Test: Compare Scootsurance vs TravelEasy on medical coverage
  - **Time:** 1 hour
  - **Owner:** [Assign]

- [ ] **Task 2.3.2:** Implement multi-dimensional comparison logic
  - [ ] Benefit-by-benefit analysis (medical, cancellation, baggage)
  - [ ] Limit comparison (absolute, sub-limits)
  - [ ] Exclusion analysis
  - [ ] Value assessment (coverage per dollar)
  - **Time:** 45 min
  - **Owner:** [Assign]

### 2.4 Tools Layer - Explanation Queries

- [ ] **Task 2.4.1:** Build `answer_policy_question` tool
  - [ ] Input: `question`, `policy_id` (optional), `include_citations`
  - [ ] Access: Original policy text resource + normalized context
  - [ ] Output: Detailed answer with exact policy language
  - [ ] Test: "What exactly is covered under medical expenses?"
  - **Time:** 1 hour
  - **Owner:** [Assign]

- [ ] **Task 2.4.2:** Implement citation system
  - [ ] Link answers to original policy sections
  - [ ] Include page numbers or section references
  - [ ] Flag areas of uncertainty for human review
  - **Time:** 30 min
  - **Owner:** [Assign]

### 2.5 Tools Layer - Eligibility & Scenario Queries

- [ ] **Task 2.5.1:** Build `check_eligibility` tool
  - [ ] Input: `user_profile` (age, health, destination, trip_duration)
  - [ ] Access: Layer 1 (General Conditions) of taxonomy
  - [ ] Output: Eligible products with qualifying conditions
  - [ ] Test: "Am I covered for pre-existing conditions?"
  - **Time:** 45 min
  - **Owner:** [Assign]

- [ ] **Task 2.5.2:** Build `analyze_scenario` tool
  - [ ] Input: `scenario_description` (e.g., "break leg skiing in Japan")
  - [ ] Access: Multiple benefits and exclusions (Layers 2+3)
  - [ ] Output: Step-by-step coverage analysis
  - [ ] Test: "What happens if I miss my flight due to traffic?"
  - **Time:** 1 hour
  - **Owner:** [Assign]

### 2.6 Query Classification System

- [ ] **Task 2.6.1:** Implement query classifier
  - [ ] Classify as: comparison / explanation / eligibility / scenario
  - [ ] Route to appropriate tool
  - [ ] Use Claude for natural language understanding
  - **Time:** 45 min
  - **Owner:** [Assign]

- [ ] **Task 2.6.2:** Test query classification
  - [ ] "Which plan is better?" → comparison
  - [ ] "What is covered?" → explanation
  - [ ] "Am I eligible?" → eligibility
  - [ ] "What if I get sick?" → scenario
  - **Time:** 20 min
  - **Owner:** [Assign]

### 2.7 Prompts Layer

- [ ] **Task 2.7.1:** Create comparison prompt templates
  - [ ] Structured format for product comparison
  - [ ] Clear differentiation and value assessment
  - [ ] User-friendly language (avoid jargon)
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 2.7.2:** Create explanation prompt templates
  - [ ] Natural language generation guides
  - [ ] Legal precision with clarity
  - [ ] Include citations and references
  - **Time:** 20 min
  - **Owner:** [Assign]

**Phase 2 Total Time:** ~6 hours  
**Phase 2 Completion Criteria:** ✅ MCP server with 4 tools, 4 resources, prompts, query classification

---

## 📅 Phase 3: Document Intelligence (BLOCK 3) - Day 1 Evening (4 hours)

**Objective:** Auto-extract trip details from documents with 95%+ accuracy

### 3.1 Lambda Function Setup

- [ ] **Task 3.1.1:** Create Lambda function for document extraction
  - [ ] Function name: `travelmate-document-extraction`
  - [ ] Runtime: Python 3.11
  - [ ] Timeout: 30 seconds
  - [ ] Memory: 1024 MB
  - **Time:** 15 min
  - **Owner:** [Assign]

- [ ] **Task 3.1.2:** Configure S3 bucket for document uploads
  - [ ] Bucket name: `travelmate-documents-dev`
  - [ ] Enable CORS for upload UI
  - [ ] Set lifecycle: Delete after 30 days
  - [ ] Configure encryption (AES-256)
  - **Time:** 15 min
  - **Owner:** [Assign]

### 3.2 Document Extraction Tool

- [ ] **Task 3.2.1:** Build `extract_trip_details` MCP tool
  - [ ] Input: `document_url`, `document_type` (auto/flight/hotel/visa)
  - [ ] Uses: Claude Vision API for image/PDF parsing
  - [ ] Output: Structured TripDetails JSON
  - **Time:** 1 hour
  - **Owner:** [Assign]

- [ ] **Task 3.2.2:** Implement multi-format handling
  - [ ] Support: PDF confirmations
  - [ ] Support: Mobile screenshots (JPG, PNG)
  - [ ] Support: Email attachments
  - [ ] Support: Physical document photos
  - **Time:** 30 min
  - **Owner:** [Assign]

### 3.3 Data Extraction Logic

- [ ] **Task 3.3.1:** Extract traveler details
  - [ ] Names (first, last)
  - [ ] Ages / Date of birth
  - [ ] Passport numbers (if present)
  - [ ] Confidence scoring for each field
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 3.3.2:** Extract trip framework
  - [ ] Departure date, return date
  - [ ] Origin, destination cities
  - [ ] Layovers / multi-city itinerary
  - [ ] Trip duration calculation
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 3.3.3:** Extract investment indicators
  - [ ] Ticket cost
  - [ ] Cabin class (economy/business/first)
  - [ ] Hotel costs (if present)
  - [ ] Total trip investment
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 3.3.4:** Extract activities & risk factors
  - [ ] Adventure activities mentioned
  - [ ] Special equipment (ski, scuba)
  - [ ] Event tickets / cruises
  - **Time:** 20 min
  - **Owner:** [Assign]

### 3.4 Validation & Quality Control

- [ ] **Task 3.4.1:** Implement logical consistency checks
  - [ ] Departure date < Return date
  - [ ] Trip duration reasonable (1-365 days)
  - [ ] Names consistent across documents
  - [ ] Destinations geographically valid
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 3.4.2:** Cross-document verification
  - [ ] Compare flight dates with hotel dates
  - [ ] Verify name consistency across bookings
  - [ ] Flag inconsistencies for human review
  - **Time:** 20 min
  - **Owner:** [Assign]

- [ ] **Task 3.4.3:** Test extraction accuracy
  - [ ] Test with 10+ sample documents
  - [ ] Measure accuracy per field type
  - [ ] Target: 95%+ accuracy for critical fields
  - [ ] Document failure cases
  - **Time:** 45 min
  - **Owner:** [Assign]

### 3.5 Quotation Integration

- [ ] **Task 3.5.1:** Integrate with MSIG quote API
  - [ ] Review `Travel Insurance API Documentation.pdf`
  - [ ] Extract API endpoints, authentication
  - [ ] Build API client wrapper
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 3.5.2:** Build `get_quote` MCP tool
  - [ ] Input: `trip_details` (from extraction), `product_id`
  - [ ] Call: MSIG quote API
  - [ ] Output: Quote with premium, coverage details
  - **Time:** 30 min
  - **Owner:** [Assign]

- [ ] **Task 3.5.3:** Test end-to-end: Document → Quote
  - [ ] Upload flight confirmation
  - [ ] Extract trip details
  - [ ] Generate quote automatically
  - [ ] Verify quote accuracy
  - [ ] Measure time: Target <3 seconds
  - **Time:** 20 min
  - **Owner:** [Assign]

**Phase 3 Total Time:** ~4 hours  
**Phase 3 Completion Criteria:** ✅ Document upload → extraction (95%+ accuracy) → auto-quote in <3s

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
Phase 1: Foundation               [                    ] 0%
Phase 2: MCP Layer                [                    ] 0%
Phase 3: Document Intelligence    [                    ] 0%
Phase 4: Purchase Flow            [                    ] 0%
Phase 5: Claims Intelligence      [                    ] 0%
Phase 6: Polish & Demo            [                    ] 0%
----------------------------------------
Total Progress:                   [                    ] 0%
```

### Time Budget

| Phase | Estimated | Actual | Status |
|-------|-----------|--------|--------|
| Phase 1 | 4h | -- | ⚠️ |
| Phase 2 | 6h | -- | ⚠️ |
| Phase 3 | 4h | -- | ⚠️ |
| Phase 4 | 3h | -- | ⚠️ |
| Phase 5 | 4h | -- | ⚠️ |
| Phase 6 | 8h | -- | ⚠️ |
| **Total** | **29h** | **--** | **--** |

---

## 🎯 Critical Success Factors

### Must-Have (Minimum Viable Demo)
- ✅ 3 policies normalized in 4-layer taxonomy *(BLOCK 1)*
- ✅ MCP server with comparison + FAQ tools *(BLOCK 2)*
- ✅ Document extraction with 95%+ accuracy *(BLOCK 3)*
- ✅ Complete purchase flow *(BLOCK 4)*

### Differentiators (Competitive Advantage)
- ✅ Claims data intelligence *(BLOCK 5)*
- ✅ Data-driven recommendations with narratives
- ✅ Dual-access pattern (normalized + raw text)
- ✅ Beautiful, responsive UI

### Demo Requirements
- ✅ End-to-end working demo (upload → quote → purchase)
- ✅ Show all 5 blocks in action
- ✅ <2 minute purchase time (vs 20 min traditional)
- ✅ Impressive "wow" moments (auto-extraction, claims insights)

---

## 📝 Notes & Decisions

### Technical Decisions
- **Database:** DynamoDB (already provided, single-digit ms latency)
- **Cache:** Redis (ElastiCache for session management)
- **Document Processing:** Lambda + Claude Vision
- **Payment:** Stripe (already integrated!)
- **Frontend:** Next.js 14 + shadcn/ui
- **Backend:** FastAPI for MCP server

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
1. [ ] Review this TODO with team
2. [ ] Assign owners to each phase
3. [ ] Set up development environment
4. [ ] Start Phase 1: Policy extraction

**Daily Stand-ups:**
- Morning: Review yesterday's progress, assign today's tasks
- Evening: Demo current state, identify blockers

**Demo Rehearsal:**
- Day 2 evening: First full run-through
- Day 3 morning: Final polish
- Day 3 afternoon: Demo ready!

---

**Let's build something amazing! 🎉**

