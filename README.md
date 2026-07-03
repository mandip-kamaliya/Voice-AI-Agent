# Voice AI Agent for BrightBox Support

A voice AI agent that can handle real phone calls, answer questions using a knowledge base, and gracefully handle unknown queries.

## Architecture

```
Phone Call → Twilio → Gather (Speech Recognition) → Flask Server
                                                    ↓
                                            Retrieve Context (sentence-transformers)
                                                    ↓
                                            Generate Response (Gemini 2.5 Flash)
                                                    ↓
                                            Say (Text-to-Speech via Amazon Polly)
                                                    ↓
                                            Twilio → Phone
```

## Loom Video : https://www.loom.com/share/c9b43c84d7b8438c92f944d127bfa296

## Tech Stack

- **Telephony**: Twilio Voice (Gather/Say for speech recognition and text-to-speech)
- **LLM**: Google Gemini 2.5 Flash (for conversation generation)
- **STT**: Twilio's built-in speech recognition (powered by Google)
- **TTS**: Amazon Polly (via Twilio) for natural-sounding voice
- **Vector Database**: sentence-transformers with cosine similarity (local, pickle-based)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Backend**: Flask (webhooks)

## Setup Instructions

### 1. Prerequisites
- Python 3.9+
- Twilio account (free trial)
- Google Gemini API key

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

Required variables:
- `TWILIO_ACCOUNT_SID`: From Twilio Console
- `TWILIO_AUTH_TOKEN`: From Twilio Console
- `TWILIO_PHONE_NUMBER`: Your Twilio trial number
- `GEMINI_API_KEY`: From Google AI Studio (https://aistudio.google.com/app/apikey)

### 4. Set Up Twilio
1. Sign up at [twilio.com/try-twilio](https://twilio.com/try-twilio) (no credit card needed)
2. Verify your personal phone number in Twilio Console (required for trial accounts)
3. Note your Account SID, Auth Token, and phone number

### 5. Set Up Vector Database
```bash
python setup_vector_db.py
```
This will:
- Read the knowledge base from `knowledge_base.md`
- Chunk the documents
- Generate embeddings using sentence-transformers
- Store in a local pickle file (`vector_db.pkl`)

### 6. Run the Server
```bash
python voice_agent_simple.py
```
This starts the Flask server on port 5000.

### 7. Expose Your Server Locally
Since Twilio needs to reach your server, use ngrok:
```bash
ngrok http 5000
```

### 8. Configure Twilio Webhook
In Twilio Console:
1. Go to your phone number settings
2. Set "Voice" webhook to: `https://your-ngrok-url/twilio/voice`
3. Set method to POST

### 9. Test
Call your Twilio number from your verified phone number and try asking:
- "How much does the Family Box cost?"
- "How long does shipping take?"
- "Can I cancel my subscription?"

## Tool Choices & Reasoning

### Why Google Gemini over OpenAI?
- Free tier with generous limits (no quota issues)
- Fast response times with gemini-2.5-flash
- No billing setup required for testing
- Good quality for conversational AI

### Why Twilio Gather/Say over Media Streams/LiveKit?
- **Simplicity**: Much faster to implement (30 min vs 2-3 hours)
- **Reliability**: No WebSocket tunnel complexity or audio processing issues
- **Adequate for demo**: Meets all core requirements (real call + LLM + RAG + local vector DB)
- **No additional infrastructure**: No need for separate WebSocket server or SIP trunking
- **Note**: For production, I would migrate to Twilio Media Streams or LiveKit for lower latency (500ms-1s vs current 3-6s) and better voice quality

### Why Amazon Polly over Google TTS?
- More natural-sounding voice quality
- Better stability and less "cracking" audio
- Integrated with Twilio (no separate API setup needed)

### Why sentence-transformers over Chroma?
- No C++ compilation required (works on Windows without Visual Studio)
- Pre-built wheels available
- Simple pickle-based storage
- Good enough for small knowledge bases
- Easy to understand and debug

### Why Flask over FastAPI?
- Simpler for this use case
- Adequate performance for webhook handling
- More familiar to most developers

## What I'd Improve for Production

1. **Migrate to real-time streaming**: Use Twilio Media Streams or LiveKit for lower latency (500ms-1s vs current 3-6s)
2. **Add conversation persistence**: Store conversation history in a database for analytics and follow-up
3. **Implement proper error handling**: Add retry logic for API failures
4. **Add monitoring/logging**: Track call metrics, success rates, common queries
5. **Implement rate limiting**: Prevent abuse of the service
6. **Add authentication**: Secure the webhook endpoints
7. **Use a hosted vector DB**: For better performance and scalability (e.g., Pinecone, Weaviate)
8. **Add A/B testing**: Test different system prompts and responses

## Testing

Test questions from the knowledge base:
1. "How much does the Family Box cost?" → Should answer $34/month
2. "How long does shipping take?" → Should answer 3-5 business days US, 5-8 for Canada
3. "Can I cancel my subscription?" → Should explain the cancellation process

Test escalation:
1. "What's the status of order #12345?" → Should offer to connect to human
2. "I want to speak to a manager" → Should offer to connect to human


