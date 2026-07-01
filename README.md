# 🌍 VoyageOS – AI-Powered Travel Planning Assistant

VoyageOS is an AI-powered travel assistant that simplifies travel planning by combining itinerary generation, destination recommendations, travel knowledge, and personalized trip management into a single conversational application.

Instead of searching across multiple websites, users can interact with VoyageOS to generate complete travel plans, receive destination recommendations, ask travel-related questions, and download their itinerary as a PDF.

---

## ✨ Key Features

### 🧳 AI Trip Planning
- Personalized travel itinerary generation
- Budget-based trip planning
- Solo, family, honeymoon & group trips
- Day-wise travel schedule
- Smart budget allocation

### 🏨 Smart Recommendations
- Hotel recommendations
- Tourist attractions
- Transport suggestions
- Weather-based travel advice
- Local tips & safety precautions

### 📚 Travel Knowledge Assistant
Ask questions related to:
- Visa requirements
- Passport information
- Airport procedures
- Customs regulations
- Immigration guidance
- Packing suggestions
- Travel documents
- Travel insurance

Powered using **Retrieval-Augmented Generation (RAG)** with travel documents.

### 📄 Additional Features
- PDF itinerary generation
- Conversation memory
- Session history
- Follow-up recommendations
- Budget modification & itinerary regeneration

---

# 🏗️ System Architecture

```
                User
                  │
          Streamlit Frontend
                  │
       VoyageOS Assistant
          │             │
   Trip Planner      Travel Knowledge
          │             │
      AI Planner     RAG Pipeline
          │             │
     Tool Execution   ChromaDB
          │
     Current Trip
          │
    PDF Generator
          │
      SQLite Memory
```

---

# 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.12 |
| Frontend | Streamlit |
| AI Framework | LangChain |
| LLM | Groq (Llama 3.1) |
| Vector Database | ChromaDB |
| Embeddings | Sentence Transformers |
| Database | SQLite |
| PDF Generation | FPDF2 |
| APIs | Geoapify, Open-Meteo, DuckDuckGo Search |
| Version Control | Git & GitHub |

---

# 📂 Project Structure

```
VoyageOS
│
├── agent/              # AI assistant logic
├── frontend/           # Streamlit application
├── tools/              # Hotel, Weather, Places, Budget, Transport
├── services/           # External API services
├── rag/                # RAG pipeline
├── memory/             # Conversation & session memory
├── database/           # SQLite & ChromaDB
├── downloads/          # Generated PDFs
├── data/               # Travel knowledge PDFs
├── requirements.txt
└── README.md
```

---

# 🚀 How It Works

1. User provides trip details.
2. Planner collects missing information.
3. APIs fetch:
   - Hotels
   - Attractions
   - Weather
   - Transport
4. AI generates a personalized itinerary.
5. Current trip is stored for follow-up interactions.
6. A downloadable PDF itinerary is generated.

For travel knowledge queries, VoyageOS retrieves relevant information from its document knowledge base before generating responses.

---

# 🎥 Project Demo

Watch the complete demo here:

**📹 Demo Video**  
🔗 **https://drive.google.com/file/d/1eZtaHdI25wWTZtj_vcic_ExdUgxTshZy/view?usp=drive_link**

---

# 🔮 Future Enhancements

- Flight booking integration
- Interactive maps
- Multi-language support
- Cost optimization
- Personalized travel recommendations
- Mobile application
- Docker & cloud deployment
- Advanced workflow orchestration

---

# 👨‍💻 Developer

**Mayur Gacche**
**Swapnaj Gharat**

---

⭐ *If you found this project interesting, consider giving the repository a star!*
