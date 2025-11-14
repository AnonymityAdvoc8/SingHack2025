# TravelMate AI - Frontend Chat V2

Modern, conversational travel insurance platform built with Next.js and integrated with the TravelMate AI backend.

## 🚀 Quick Start

### Option 1: Use the Startup Script (Recommended)

From the project root:

```bash
./start-integrated-app.sh
```

This will start both backend and frontend automatically.

### Option 2: Manual Setup

1. **Setup Environment**

```bash
# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8080" > .env.local
```

2. **Install Dependencies**

```bash
npm install
```

3. **Start Backend** (in another terminal)

```bash
cd ../backend-mcp
source venv/bin/activate
uvicorn app.main:app --reload --port 8080
```

4. **Start Frontend**

```bash
npm run dev
```

5. **Open** [http://localhost:3000](http://localhost:3000)

## ✨ Features

### 🤖 Conversational AI
- Real-time chat with intelligent backend orchestration
- Automatic trip detail extraction
- Context-aware policy recommendations
- Multi-turn conversation support

### 📧 Gmail Integration
- OAuth 2.0 authentication
- Automatic booking extraction from emails
- Support for flights, hotels, car rentals
- Real-time status updates

### 🛡️ Smart Insurance Comparison
- Dynamic policy loading from backend
- Real benefit data from database
- AI-powered recommendations
- Coverage scoring and reasoning

### 💾 Session Management
- Persistent conversation state
- localStorage-based caching
- Cross-page reload support
- Trip details preservation

## 📁 Project Structure

```
frontend-chat-v2/
├── app/                    # Next.js app directory
│   ├── page.tsx           # Main page
│   ├── layout.tsx         # Root layout
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── chat-interface.tsx        # Main chat UI ✨
│   ├── gmail-integration.tsx     # Gmail OAuth ✨
│   ├── insurance-comparison.tsx  # Policy comparison ✨
│   ├── message-bubble.tsx
│   ├── payment-processor.tsx
│   ├── welcome-screen.tsx
│   └── ui/                # shadcn/ui components
├── lib/                   # Utilities
│   ├── api-client.ts     # Backend API client ✨
│   ├── types.ts          # TypeScript types ✨
│   ├── session.ts        # Session management ✨
│   └── utils.ts          # Utilities
└── INTEGRATION_GUIDE.md  # Detailed integration docs

✨ = Backend integrated
```

## 🔌 Backend Integration

This frontend integrates with the **backend-mcp** FastAPI server.

### API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `POST /ask` | Main chat endpoint |
| `GET /policies` | List all policies |
| `GET /policies/{id}` | Get policy details |
| `GET /gmail/authorize` | Start Gmail OAuth |
| `GET /gmail/status` | Check Gmail auth status |
| `GET /oauth/callback` | OAuth redirect handler |

See [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for detailed API documentation.

## 🧪 Testing

### Test the Integration

1. **Health Check**
```bash
curl http://localhost:8080/health
```

2. **Basic Chat Flow**
- Open http://localhost:3000
- Type: "I'm traveling to Tokyo for 10 days"
- Verify AI responds with trip detail questions
- Type: "Show me insurance options"
- Verify policy comparison appears

3. **Gmail Integration**
- Click "Connect to Gmail"
- Authorize with Google
- Verify bookings are extracted

## 🛠️ Built With

- **Next.js 16** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **Lucide React** - Icons
- **Backend** - FastAPI (../backend-mcp)

## 📚 Documentation

- [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) - Detailed integration docs
- [../INTEGRATION_COMPLETE.md](../INTEGRATION_COMPLETE.md) - Integration summary
- [Backend API Docs](http://localhost:8080/docs) - Interactive API docs (when running)

## 🔧 Development

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

### Build for Production

```bash
npm run build
npm start
```

### Lint Code

```bash
npm run lint
```

## 🌐 Environment Variables

Create `.env.local`:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8080
```

## 🤝 Contributing

This is a hackathon project for SingHack 2025.

## 📝 License

MIT

## 🙏 Acknowledgments

- Built for SingHack 2025
- Powered by MSIG travel insurance data
- Uses Groq for LLM inference
- Uses Tavily for real-time intelligence
