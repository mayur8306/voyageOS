# VoyageOS - AI Travel Assistant

VoyageOS is a comprehensive AI-powered travel assistant that combines intelligent trip planning with travel knowledge management. It uses advanced RAG (Retrieval-Augmented Generation) technology to answer travel-related questions from uploaded documents while maintaining conversational context throughout user interactions.

## Features

### 🏠 Trip Planning
- **Intelligent Itinerary Generation**: Creates complete travel itineraries with hotels, attractions, transport, and budget
- **Multi-Step Conversation**: Collects trip details naturally through conversation (origin, destination, budget, duration, travelers, trip type)
- **Smart Tool Integration**: Uses Geoapify for hotels/places, DuckDuckGo for transport, Open-Meteo for weather
- **Budget Management**: Calculates and optimizes trip budgets with feasibility analysis
- **PDF Export**: Generates professional PDF itineraries

### 📚 Travel Knowledge Assistant
- **RAG-Powered Q&A**: Answers questions from uploaded travel documents (visas, passports, customs, etc.)
- **Source Citations**: Always cites document sources for transparency
- **General Travel Knowledge**: Answers travel questions using LLM when documents don't contain the answer
- **Document Management**: Automatically loads and indexes all PDFs from the data directory

### 🕘 Conversation Memory
- **SQLite Database**: Stores all conversations and trip history
- **Session Management**: Tracks multiple conversation sessions
- **Trip History**: Saves complete trip data for future reference
- **Follow-up Support**: Modifies previous trips without re-entering all details

### 🧠 State Management
- **Context Awareness**: Remembers what it was doing (collecting details, itinerary ready, modifying)
- **Smart Routing**: Never interrupts an active planning session
- **Follow-up Detection**: Understands questions like "Which hotel is best?" or "Replace Day 2"
- **Seamless Transitions**: Switches between planning, RAG, and general knowledge naturally
- 
video link 
**https://drive.google.com/file/d/1eZtaHdI25wWTZtj_vcic_ExdUgxTshZy/view?usp=drive_link**

## Architecture

```
VoyageOS/
├── agent/                    # AI Agent Layer
│   ├── travel_agent.py      # Existing trip planner (unchanged)
│   ├── voyageos_assistant.py # Main orchestrator with state management
│   ├── intent_detector.py   # Intent classification
│   ├── planner.py           # Trip planning logic
│   ├── tool_manager.py      # Tool execution
│   └── prompts.py           # System prompts
│
├── rag/                      # RAG System
│   ├── loader.py            # PDF document loader
│   ├── splitter.py          # Text chunking
│   ├── embeddings.py        # Sentence-transformers embeddings
│   ├── vector_store.py      # ChromaDB storage
│   ├── retriever.py         # Document retrieval
│   ├── rag_pipeline.py      # Complete RAG pipeline
│   └── prompts.py           # RAG-specific prompts
│
├── memory/                   # Memory System
│   ├── database.py          # SQLite setup
│   └── history.py           # Conversation & trip history
│
├── tools/                    # External Tools
│   ├── weather_tool.py      # Open-Meteo
│   ├── hotel_tool.py        # Geoapify
│   ├── places_tool.py       # Geoapify
│   ├── transport_tool.py    # DuckDuckGo
│   └── budget_tool.py       # Custom budget calculator
│
├── services/                 # Service Layer
│   ├── geoapify_service.py  # Geoapify API
│   ├── transport_service.py # Transport API
│   └── weather_service.py   # Weather API
│
├── frontend/                 # Streamlit UI
│   └── app.py               # Multi-page interface
│
├── backend/                  # FastAPI Backend
│   └── api.py               # REST API endpoints
│
├── database/                 # Data Storage
│   ├── voyageos.db          # SQLite (auto-created)
│   └── chromadb/            # ChromaDB (auto-created)
│
├── data/                     # Travel Documents (PDFs)
│   ├── *.pdf                # Upload your travel docs here
│
└── utils/                    # Utilities
    ├── config.py
    ├── formatters.py
    ├── http_client.py
    └── pdf_generator.py
```

## Technology Stack

- **LLM**: Groq (Llama 3.1 8B)
- **Orchestration**: LangChain & LangGraph
- **RAG**: ChromaDB + Sentence-Transformers
- **Database**: SQLite (conversations & trips)
- **Frontend**: Streamlit
- **Backend**: FastAPI
- **APIs**: Geoapify, DuckDuckGo, Open-Meteo
- **PDF Processing**: PyPDF2
- **PDF Generation**: fpdf2

## Installation

### Prerequisites
- Python 3.8+
- Groq API key
- Geoapify API key

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd voyageOS
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
# Create .env file
GROQ_API_KEY=your_groq_api_key
GEOAPIFY_API_KEY=your_geoapify_api_key
```

4. **Add travel documents**
```bash
# Place PDF files in the data/ directory
cp your_travel_docs/*.pdf data/
```

5. **Run the application**

**Streamlit Frontend:**
```bash
cd frontend
streamlit run app.py
```

**FastAPI Backend:**
```bash
cd backend
uvicorn main:app --reload
```

## Usage

### Trip Planning

**Example 1: Basic Trip Planning**
```
User: Plan a trip to Rajasthan for 3 days
Assistant: Which city will you be travelling from?
User: Mumbai
Assistant: Great! What is your approximate budget?
User: 25000
Assistant: How many people are travelling?
User: 2
Assistant: What type of trip? (Family/Solo/Friends/Honeymoon)
User: Friends
Assistant: [Generates complete itinerary with hotels, places, transport, budget]
```

**Example 2: Follow-up Questions**
```
User: Which hotel would you recommend?
Assistant: [Recommends from previous itinerary - no API calls]

User: Replace Day 2 with adventure activities
Assistant: [Modifies only Day 2 of existing itinerary]

User: Increase budget to 40000
Assistant: [Recalculates budget and regenerates itinerary]
```

### Travel Knowledge

**Example 1: Document-Based Questions**
```
User: What documents are required for Schengen visa?
Assistant: Based on the travel documents:
- Valid passport with 6 months validity
- Schengen visa application form
- Travel insurance (minimum €30,000)
- Flight reservations
- Hotel bookings

Sources:
- Travellers_Guide_2026.pdf, Page 45
- Formalities of International Travel.pdf, Page 12
```

**Example 2: General Travel Questions**
```
User: What is jet lag?
Assistant: Jet lag is a temporary sleep disorder that occurs when your body's internal clock is out of sync with your destination's time zone. It typically occurs when traveling across 2+ time zones. To minimize it, stay hydrated, avoid alcohol, and adjust your sleep schedule before traveling.
```

## State Management

VoyageOS uses a state machine to maintain conversation context:

### States
1. **IDLE**: Assistant is waiting for new input
2. **COLLECTING_TRIP**: Gathering trip details from user
3. **ITINERARY_READY**: Trip generated, ready for follow-ups
4. **MODIFYING_TRIP**: Processing trip modifications

### State Flow
```
IDLE → COLLECTING_TRIP → ITINERARY_READY → MODIFYING_TRIP → ITINERARY_READY
                    ↓                                      ↓
                    └──────────────────────────────────────┘
```

### Key Behaviors
- **Active planner protection**: Intent detection never interrupts trip collection
- **Automatic state transitions**: Moves to next state when trip is complete
- **Follow-up detection**: Recognizes modification requests
- **Context preservation**: Remembers all trip details throughout conversation

## API Endpoints

### Chat
```http
POST /chat
{
  "message": "Plan a trip to Goa",
  "session_id": "optional-session-id"
}
```

### Sessions
```http
GET /sessions                    # Get recent sessions
GET /sessions/{id}/history       # Get conversation history
GET /sessions/{id}/trips         # Get trip history
```

### RAG
```http
GET /rag/sources                 # List available documents
POST /rag/reload                 # Force reload documents
```

### Health
```http
GET /health                      # System health check
GET /                            # API status
```

## Database Schema

### conversation_history
- `id` - Primary key
- `session_id` - Session identifier
- `user_message` - User's message
- `assistant_message` - Assistant's response
- `timestamp` - Message timestamp

### trip_history
- `id` - Primary key
- `session_id` - Session identifier
- `origin` - Trip origin
- `destination` - Trip destination
- `budget` - Trip budget
- `duration` - Trip duration (days)
- `travelers` - Number of travelers
- `trip_type` - Family/Solo/Friends/Honeymoon
- `weather_json` - Weather data (JSON)
- `transport_json` - Transport options (JSON)
- `hotels_json` - Hotel recommendations (JSON)
- `places_json` - Attractions (JSON)
- `budget_json` - Budget breakdown (JSON)
- `generated_itinerary` - Complete itinerary text
- `created_at` - Trip creation timestamp

## Configuration

### Environment Variables
```env
# Required
GROQ_API_KEY=your_groq_api_key
GEOAPIFY_API_KEY=your_geoapify_api_key

# Optional
LOG_LEVEL=INFO
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### RAG Settings
- **Chunk Size**: 1000 characters (configurable in `rag/splitter.py`)
- **Chunk Overlap**: 200 characters
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Similarity Metric**: Cosine
- **Max Context**: 3000 characters

## Travel Domain Restriction

VoyageOS only answers travel-related questions:

**Allowed Topics:**
- Trip planning and itineraries
- Hotels, flights, transport
- Visas, passports, immigration
- Customs and travel regulations
- Travel insurance
- Airports and procedures
- Destinations and attractions
- Weather and climate
- Currency and money exchange
- Packing and safety
- Local culture and etiquette

**Blocked Topics:**
- Programming, math, politics
- Assignments and homework
- Non-travel technical questions
- Personal advice unrelated to travel

## Production Readiness

### Code Quality
- ✅ Type hints throughout
- ✅ Docstrings on all classes/methods
- ✅ Comprehensive logging
- ✅ Exception handling
- ✅ No debug prints
- ✅ No placeholder code
- ✅ Clean architecture
- ✅ Modular design

### Performance
- ✅ Efficient SQLite queries with indexes
- ✅ ChromaDB persistent storage
- ✅ Lazy RAG initialization
- ✅ Connection pooling
- ✅ Error recovery

### Scalability
- ✅ Modular component design
- ✅ Easy to add new tools
- ✅ Pluggable RAG system
- ✅ Extensible intent detection
- ✅ API-first architecture

## Example Conversations

### Scenario 1: Complete Trip Planning
```
User: Plan a trip to Japan for 7 days
Assistant: Which city will you be travelling from?
User: Delhi
Assistant: What is your approximate budget?
User: 80000
Assistant: How many people are travelling?
User: 2
Assistant: What type of trip? (Family/Solo/Friends/Honeymoon)
User: Honeymoon
Assistant: [Generates complete 7-day Japan itinerary]
```

### Scenario 2: Follow-up Modification
```
User: Which hotel do you recommend?
Assistant: Based on your honeymoon trip to Japan, I recommend...
[No API calls - uses stored trip data]

User: Replace Day 3 with more cultural activities
Assistant: [Modifies Day 3 and returns updated itinerary]
```

### Scenario 3: Travel Knowledge
```
User: What are the visa requirements for Thailand?
Assistant: [Searches PDFs and provides answer with sources]
```

### Scenario 4: General Travel Question
```
User: What is jet lag and how do I prevent it?
Assistant: [Answers using general travel knowledge]
```

### Scenario 5: Off-Topic Question
```
User: Solve this Python programming problem
Assistant: I specialize in travel assistance. Please ask me about trip planning, visas, passports, destinations, or other travel-related topics.
```

## Contributing

This is a capstone project. For issues or questions, please contact the development team.

## License

[Your License Here]

## Acknowledgments

- **Groq** - LLM inference
- **Geoapify** - Places and geocoding APIs
- **DuckDuckGo** - Transport search
- **Open-Meteo** - Weather data
- **ChromaDB** - Vector database
- **Sentence-Transformers** - Embeddings
- **LangChain** - LLM orchestration
- **Streamlit** - Frontend framework
- **FastAPI** - Backend framework
