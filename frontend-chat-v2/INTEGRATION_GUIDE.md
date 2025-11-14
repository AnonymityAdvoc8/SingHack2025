# Backend Integration Guide - Frontend Chat V2

This guide explains how the frontend-chat-v2 integrates with the backend-mcp API.

## Overview

The frontend now communicates with the backend API for:
- **Conversational AI**: Real-time chat with intelligent orchestration
- **Gmail Integration**: OAuth-based email scanning for trip details
- **Policy Recommendations**: AI-powered insurance policy matching
- **Session Management**: Persistent conversation state across page reloads

## Architecture

```
┌─────────────────┐         HTTP/REST        ┌──────────────────┐
│  Frontend v2    │ ◄──────────────────────► │   Backend MCP    │
│  (Next.js)      │                          │   (FastAPI)      │
└─────────────────┘                          └──────────────────┘
        │                                              │
        │                                              │
   localStorage                                  PostgreSQL
  (Session State)                              (Claims Data)
```

## Key Files

### API Client Layer
- `lib/api-client.ts` - Centralized API communication
- `lib/types.ts` - TypeScript type definitions
- `lib/session.ts` - Session & state management

### Components
- `components/chat-interface.tsx` - Main chat UI with backend integration
- `components/gmail-integration.tsx` - Gmail OAuth flow
- `components/insurance-comparison.tsx` - Dynamic policy display

## API Endpoints Used

### Chat & Recommendations
```typescript
POST /ask
Body: {
  question: string,
  session_id: string,
  context?: object
}
Response: {
  success: boolean,
  answer: string,
  trip_details?: object,
  policy_recommendations?: array
}
```

### Gmail Integration
```typescript
GET /gmail/authorize?session_id={sessionId}
Response: {
  authorization_url: string,
  session_id: string
}

GET /gmail/status?session_id={sessionId}
Response: {
  authorized: boolean,
  bookings: array
}
```

### Policy Data
```typescript
GET /policies
Response: {
  total_policies: number,
  policies: array
}

GET /policies/{policy_id}
Response: Policy details object
```

## Setup Instructions

### 1. Environment Configuration

Create `.env.local` in the frontend-chat-v2 directory:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8080
```

### 2. Install Dependencies

```bash
cd frontend-chat-v2
npm install
```

### 3. Start the Backend

```bash
cd ../backend-mcp
source venv/bin/activate
uvicorn app.main:app --reload --port 8080
```

### 4. Start the Frontend

```bash
cd ../frontend-chat-v2
npm run dev
```

The frontend will be available at http://localhost:3000

## Features

### 1. Intelligent Chat
- Real-time AI responses from backend orchestration service
- Automatic trip detail extraction
- Context-aware policy recommendations
- Session persistence across page reloads

### 2. Gmail Integration
- OAuth 2.0 popup flow
- Automatic booking extraction
- Support for multiple booking types (flights, hotels, etc.)
- Real-time status checking

### 3. Insurance Comparison
- Dynamic policy loading from backend
- Real benefit data from policy database
- Smart recommendations based on trip details
- Coverage scoring and reasoning

### 4. Session Management
- Automatic session ID generation
- localStorage persistence
- Message history preservation
- Trip details caching

## Usage Examples

### Basic Chat Flow

```typescript
// User sends message
const response = await apiClient.sendMessage(
  "I'm traveling to Japan for 2 weeks",
  { trip_details: currentTripDetails }
)

// Response includes:
// - AI answer
// - Extracted trip details
// - Policy recommendations (if applicable)
```

### Gmail OAuth Flow

```typescript
// 1. Get authorization URL
const authData = await apiClient.getGmailAuthUrl()

// 2. Open popup window
window.open(authData.authorization_url, ...)

// 3. Poll for completion
const status = await apiClient.checkGmailStatus()

// 4. Display extracted bookings
if (status.bookings) {
  // Show booking details
}
```

### Policy Comparison

```typescript
// Option 1: Get from AI recommendations
<InsuranceComparison 
  recommendations={aiResponse.policy_recommendations}
  tripDetails={aiResponse.trip_details}
/>

// Option 2: Load default policies
<InsuranceComparison />
// Component will auto-fetch policies
```

## Session State Management

The frontend maintains session state in localStorage:

```typescript
{
  sessionId: "session_123...",
  messages: [...],
  tripDetails: {...},
  gmailAuthorized: boolean,
  lastUpdated: timestamp
}
```

This ensures:
- Conversations persist across page reloads
- Trip details are maintained
- Gmail authorization status is remembered

## Error Handling

The integration includes comprehensive error handling:

1. **Network Errors**: Graceful fallback messages
2. **API Errors**: User-friendly error displays
3. **OAuth Failures**: Clear authorization status
4. **Timeout Handling**: Automatic cleanup for long-running operations

## Testing the Integration

### 1. Health Check

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "TravelMate AI",
  "version": "1.0.0"
}
```

### 2. Chat Test

Visit http://localhost:3000 and:
1. Type: "I'm traveling to Paris next month"
2. Verify AI response appears
3. Check browser console for no errors
4. Verify session ID in localStorage

### 3. Gmail Integration Test

1. Click "Connect to Gmail" action
2. Verify OAuth popup opens
3. Authorize with Google account
4. Check that bookings are displayed

### 4. Policy Comparison Test

1. Ask: "Show me insurance options"
2. Verify policy cards appear
3. Check that benefits are loaded
4. Confirm data matches backend policies

## Troubleshooting

### Frontend can't connect to backend
- Check that backend is running on port 8080
- Verify `NEXT_PUBLIC_API_URL` in `.env.local`
- Check browser console for CORS errors

### Gmail OAuth fails
- Verify Google OAuth credentials in backend `.env`
- Check that redirect URI is configured: `http://localhost:8080/oauth/callback`
- Ensure popup wasn't blocked by browser

### Policies not loading
- Verify database is initialized
- Check backend logs for errors
- Confirm `/policies` endpoint returns data

### Session not persisting
- Check browser localStorage is enabled
- Verify no errors in browser console
- Clear localStorage and try again

## Production Considerations

Before deploying to production:

1. **Update API URL**: Set production backend URL
2. **Enable HTTPS**: OAuth requires secure connections
3. **Configure CORS**: Restrict to production domains
4. **Add Rate Limiting**: Protect API endpoints
5. **Error Tracking**: Add Sentry or similar
6. **Session Security**: Add encryption for sensitive data

## Next Steps

- [ ] Add payment integration
- [ ] Implement file upload for booking confirmations
- [ ] Add real-time policy pricing
- [ ] Implement chat history export
- [ ] Add multi-language support

