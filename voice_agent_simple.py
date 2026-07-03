"""
Simple Voice AI Agent using Twilio Gather/Say, Google Gemini, and sentence-transformers.
This uses Twilio's built-in speech recognition and text-to-speech - much simpler setup.
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather

load_dotenv()

class SimpleVoiceAgent:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Load vector database
        with open('vector_db.pkl', 'rb') as f:
            self.vector_db = pickle.load(f)
        
        # Load sentence transformer model
        self.embedding_model = SentenceTransformer(self.vector_db['model_name'])
        
        # Conversation history
        self.conversation_history = []
        
        # System prompt
        self.system_prompt = """You are a helpful customer support agent for BrightBox, a subscription box service. 
Your role is to answer customer questions based ONLY on the provided knowledge base context.

Rules:
1. Answer questions using the retrieved context from the knowledge base
2. If the answer is not in the context, politely say you don't have that information and offer to connect them to a human agent
3. Be friendly, professional, and concise
4. If the customer asks about specific order details, account information, or anything requiring access to their personal data, say you don't have access and offer to connect to a human
5. If the customer seems frustrated or angry, offer to connect them to a human agent
6. Keep responses conversational and natural for voice - avoid long paragraphs, use simple language

When you don't know the answer or need to escalate, say: "I don't have access to that information, but I can connect you with a human agent who can help you with that. Would you like me to do that?"

To end the call naturally, you can say: "Is there anything else I can help you with today?" or similar."""

    def retrieve_context(self, query: str, n_results: int = 3) -> str:
        """Retrieve relevant context from the vector database."""
        query_embedding = self.embedding_model.encode([query])[0]
        
        similarities = []
        for i, chunk_embedding in enumerate(self.vector_db['embeddings']):
            similarity = 1 - cosine(query_embedding, chunk_embedding)
            similarities.append((similarity, i))
        
        similarities.sort(reverse=True, key=lambda x: x[0])
        top_chunks = [self.vector_db['chunks'][i] for _, i in similarities[:n_results]]
        
        return "\n\n".join(top_chunks)

    def should_escalate(self, user_input: str) -> bool:
        """Check if the query should be escalated to a human."""
        escalation_keywords = [
            "order number", "my order", "account", "billing dispute",
            "exception", "special case", "angry", "frustrated", "complaint",
            "speak to manager", "talk to human", "real person"
        ]
        
        user_input_lower = user_input.lower()
        for keyword in escalation_keywords:
            if keyword in user_input_lower:
                return True
        return False

    def generate_response(self, user_input: str) -> str:
        """Generate a response using RAG."""
        if self.should_escalate(user_input):
            return "I don't have access to your specific account or order details, but I can connect you with a human agent who can help you with that. Would you like me to do that?"
        
        context = self.retrieve_context(user_input)
        
        prompt = f"""{self.system_prompt}

Knowledge Base Context:
{context}

Conversation history:
{self.format_history()}

User: {user_input}"""
        
        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=300,
            )
        )
        
        assistant_response = response.text
        
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": assistant_response})
        
        return assistant_response
    
    def format_history(self) -> str:
        """Format conversation history for the prompt."""
        if not self.conversation_history:
            return ""
        
        formatted = []
        for msg in self.conversation_history[-6:]:  # Last 3 turns
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                formatted.append(f"User: {content}")
            else:
                formatted.append(f"Assistant: {content}")
        
        return "\n".join(formatted)


# Flask app for Twilio webhooks
app = Flask(__name__)
agent = SimpleVoiceAgent()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return {"status": "healthy"}, 200

@app.route('/twilio/voice', methods=['POST'])
def handle_incoming_call():
    """Handle incoming Twilio voice calls using Gather and Say."""
    response = VoiceResponse()
    
    speech_result = request.values.get('SpeechResult', None)
    
    if speech_result:
        agent_response = agent.generate_response(speech_result)
        
        response.say(agent_response, voice='Polly.Joanna')
        
        gather = Gather(input='speech', action='/twilio/voice', method='POST', timeout=5, language='en-US')
        gather.say("Is there anything else I can help you with?", voice='Polly.Joanna')
        response.append(gather)
        
    else:
        greeting = "Thank you for calling BrightBox support. I'm your AI assistant. How can I help you today?"
        response.say(greeting, voice='Polly.Joanna')
        
        gather = Gather(input='speech', action='/twilio/voice', method='POST', timeout=5, language='en-US')
        response.append(gather)
        
        response.say("I didn't hear anything. Goodbye!")
        response.hangup()
    
    return Response(str(response), mimetype='application/xml')

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
