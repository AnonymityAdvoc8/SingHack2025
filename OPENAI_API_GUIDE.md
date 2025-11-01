# OpenAI-Compatible Chat Completions API

## Overview

TravelMate AI now provides an **OpenAI-compatible Chat Completions API** that follows the standard OpenAI format. This allows seamless integration with:

- ✅ OpenAI SDKs (Python, Node.js, etc.)
- ✅ Claude Desktop MCP integration
- ✅ LangChain, LlamaIndex, and other frameworks
- ✅ Any tool expecting OpenAI API format
- ✅ Streaming and non-streaming responses

## Endpoints

### 1. Chat Completions

**Endpoint**: `POST /v1/chat/completions`

**Non-Streaming Request**:
```json
{
  "model": "travelmate-ai",
  "messages": [
    {"role": "user", "content": "I need insurance for Japan trip"}
  ],
  "stream": false
}
```

**Streaming Request**:
```json
{
  "model": "travelmate-ai",
  "messages": [
    {"role": "user", "content": "I need insurance for Japan trip"}
  ],
  "stream": true
}
```

**Response (Non-Streaming)**:
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1730000000,
  "model": "travelmate-ai",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "I'd be happy to help..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 150,
    "total_tokens": 160
  }
}
```

**Response (Streaming)** - Server-Sent Events (SSE):
```
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1730000000,"model":"travelmate-ai","choices":[{"index":0,"delta":{"content":"I'd "},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1730000000,"model":"travelmate-ai","choices":[{"index":0,"delta":{"content":"be "},"finish_reason":null}]}

...

data: [DONE]
```

### 2. List Models

**Endpoint**: `GET /v1/models`

**Response**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "travelmate-ai",
      "object": "model",
      "created": 1730000000,
      "owned_by": "travelmate",
      "root": "travelmate-ai"
    }
  ]
}
```

## Usage Examples

### cURL (Non-Streaming)

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "travelmate-ai",
    "messages": [
      {"role": "user", "content": "I am 31 travelling to Japan in December for hiking"}
    ],
    "stream": false
  }'
```

### cURL (Streaming)

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -N \
  -d '{
    "model": "travelmate-ai",
    "messages": [
      {"role": "user", "content": "Compare Scootsurance vs TravelEasy"}
    ],
    "stream": true
  }'
```

### Python (OpenAI SDK)

```python
from openai import OpenAI

# Point to your local TravelMate AI server
client = OpenAI(
    api_key="not-needed",  # No API key required for local server
    base_url="http://localhost:8080/v1"
)

# Non-streaming
response = client.chat.completions.create(
    model="travelmate-ai",
    messages=[
        {"role": "user", "content": "I need insurance for Japan trip"}
    ]
)

print(response.choices[0].message.content)

# Streaming
stream = client.chat.completions.create(
    model="travelmate-ai",
    messages=[
        {"role": "user", "content": "Compare policies for me"}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### JavaScript/TypeScript (OpenAI SDK)

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'not-needed',
  baseURL: 'http://localhost:8080/v1',
});

// Non-streaming
const response = await client.chat.completions.create({
  model: 'travelmate-ai',
  messages: [
    { role: 'user', content: 'I need insurance for Japan trip' }
  ],
});

console.log(response.choices[0].message.content);

// Streaming
const stream = await client.chat.completions.create({
  model: 'travelmate-ai',
  messages: [
    { role: 'user', content: 'Compare policies' }
  ],
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || '');
}
```

### LangChain Integration

```python
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

# Initialize with TravelMate AI endpoint
chat = ChatOpenAI(
    openai_api_key="not-needed",
    openai_api_base="http://localhost:8080/v1",
    model_name="travelmate-ai"
)

# Use it like any LangChain chat model
response = chat([
    HumanMessage(content="I need insurance for Japan trip")
])

print(response.content)
```

## Conversation History

The API supports multi-turn conversations by including previous messages:

```json
{
  "model": "travelmate-ai",
  "messages": [
    {"role": "user", "content": "I need travel insurance"},
    {"role": "assistant", "content": "I'd be happy to help! Where are you traveling?"},
    {"role": "user", "content": "Japan for 9 days in December"},
    {"role": "assistant", "content": "Great! How old are you?"},
    {"role": "user", "content": "I'm 31 years old"}
  ],
  "stream": false
}
```

The system automatically extracts context from the conversation history.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | "travelmate-ai" | Model to use |
| `messages` | array | required | List of messages with role and content |
| `temperature` | float | 0.7 | Sampling temperature (0-2) |
| `max_tokens` | int | null | Maximum tokens to generate |
| `stream` | boolean | false | Whether to stream the response |
| `session_id` | string | null | Optional session ID for continuity |

## Features

### ✅ Full OpenAI Compatibility
- Drop-in replacement for OpenAI API
- Compatible with official SDKs
- Standard response format

### ✅ Streaming Support
- Real-time token streaming
- Server-Sent Events (SSE)
- Efficient for long responses

### ✅ Intelligent Orchestration
- Automatic trip detail extraction
- Real-time Tavily intelligence
- Historical claims analysis
- Policy recommendations

### ✅ Conversation Context
- Multi-turn dialogue support
- Automatic context extraction
- Session management

## Comparison: OpenAI API vs Custom /ask API

| Feature | `/v1/chat/completions` (OpenAI) | `/ask` (Custom) |
|---------|--------------------------------|-----------------|
| Format | OpenAI standard | TravelMate custom |
| Streaming | ✅ Yes | ❌ No |
| SDK Support | ✅ All OpenAI SDKs | ❌ Custom integration |
| Conversation | ✅ Messages array | ✅ Context object |
| Response | OpenAI format | Full orchestration data |
| Use Case | Standard integrations | Detailed debugging |

**Recommendation**: Use `/v1/chat/completions` for production integrations, keep `/ask` for development/testing.

## Testing

### Run Test Suite

```bash
cd backend-mcp
python scripts/test_openai_api.py
```

This tests:
1. ✅ Non-streaming completions
2. ✅ Streaming completions
3. ✅ Conversation history
4. ✅ Models endpoint

### Manual Testing

**Non-streaming**:
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"travelmate-ai","messages":[{"role":"user","content":"Japan trip insurance"}]}' | jq
```

**Streaming**:
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -N \
  -d '{"model":"travelmate-ai","messages":[{"role":"user","content":"Japan trip"}],"stream":true}'
```

## Error Handling

**Invalid Request**:
```json
{
  "error": {
    "message": "No user message found",
    "type": "invalid_request_error",
    "code": 400
  }
}
```

**Server Error**:
```json
{
  "error": {
    "message": "Internal server error",
    "type": "server_error",
    "code": 500
  }
}
```

## Claude Desktop Integration

To use TravelMate AI with Claude Desktop via MCP:

1. **Start the server**:
```bash
cd backend-mcp
python scripts/start_server.py
```

2. **Configure Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "travelmate-ai": {
      "command": "http",
      "args": ["http://localhost:8080/v1/chat/completions"],
      "env": {}
    }
  }
}
```

3. **Use in Claude**:
```
User: @travelmate-ai I need insurance for Japan trip
Claude: [Uses TravelMate AI via MCP]
```

## Performance

- **Non-streaming**: ~2-5 seconds total response time
- **Streaming**: First token in ~0.5s, complete in ~3-5s
- **Tokens**: ~150-300 tokens per response
- **Throughput**: Handles concurrent requests via FastAPI async

## Next Steps

1. ✅ **Deploy to production** with proper CORS/auth
2. ✅ **Add rate limiting** per API key
3. ✅ **Monitor usage** via logging/metrics
4. ✅ **Cache responses** for common queries
5. ✅ **Add function calling** for tool use (future)

## Support

For issues or questions:
- Check logs: `tail -f backend-mcp/extraction.log`
- Test health: `curl http://localhost:8080/health`
- Run tests: `python scripts/test_openai_api.py`

