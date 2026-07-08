# AI-First CRM HCP Module — Log Interaction Screen

This project is an AI-first CRM module for Healthcare Professional (HCP) management, designed with a premium split-screen layout. The **left side** features a structured medical sales logging form, and the **right side** hosts a conversational **AI Assistant** driven by **LangGraph** and **LangChain**.

The AI Assistant processes natural language prompts and translates them into structured form actions using 6 dedicated tools. The form and the assistant's context are kept in sync in real-time via a **Redux Toolkit** state container.

---

## 🌟 Tech Stack & Features

- **Frontend**: React (Vite + TypeScript) with Redux Toolkit for state management, styling in custom Vanilla CSS (supporting custom scrollbars, premium dark/light glassmorphic glow, and slide/fade transitions), and Lucide Icons.
- **Backend**: Python 3 with FastAPI for RESTful APIs and LangGraph for the conversational agent flow.
- **Database**: SQLite by default (configured via SQLAlchemy to support MySQL and PostgreSQL out of the box).
- **AI Agent**: Built with LangGraph, utilizing LangChain's `ChatGroq` model integration to call the `gemma2-9b-it` (or `llama-3.3-70b-versatile`) LLM on Groq.
- **Font Family**: Google Inter.

---

## 🛠️ The Six (6) LangGraph Tools

The LangGraph agent utilizes 6 custom tools to manage HCP interactions:

1. **`log_interaction_details`**: Extracts date, time, attendees, topics discussed, sentiment, outcomes, follow-up actions, materials shared, and samples distributed from conversation history to automatically fill/pre-populate the CRM form.
2. **`edit_interaction_details`**: Allows targeted, field-by-field corrections. If the user tells the assistant, *"Change the sentiment to Neutral"* or *"The doctor name was Dr. Sarah Jenkins, not Dr. Smith"*, the agent calls this tool to update the specific Redux form state.
3. **`get_hcp_profile`**: Fetches the doctor's specialty, hospital, contact information, clinical preferences, and the history of their 3 most recent visits.
4. **`suggest_follow_up`**: Generates clinical follow-up schedules and specific next steps based on the discussion topics and sentiment.
5. **`fetch_product_materials`**: Searches the sales repository for brochures, clinical trials, product brief sheets, and sample kits matching a keyword.
6. **`email_materials_to_hcp`**: Simulates sending the selected clinical literature directly to the HCP's registered email, creating an outgoing dispatch record in the database.

---

## 🚀 How to Set Up and Run

### 1. Prerequisite
Ensure you have **Python 3.9+** and **Node.js 18+** installed.

### 2. Backend Setup
1. Open a terminal in the `backend/` directory:
   ```bash
   cd backend
   ```
2. Install the Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure the environment variables. Open the [backend/.env](file:///i:/Temp/Persnal/AI-First%20CRM%20HCP%20Module/backend/.env) file:
   - Paste your **Groq API Key** into the `GROQ_API_KEY` parameter:
     ```env
     GROQ_API_KEY=gsk_your_actual_key_here
     ```
   - (Optional) Configure the `DATABASE_URL` to connect to a PostgreSQL or MySQL server:
     ```env
     # DATABASE_URL=mysql+pymysql://user:password@localhost/hcp_crm
     ```
4. Start the FastAPI server:
   ```bash
   python main.py
   ```
   > [!NOTE]
   > On server startup, the database is automatically created (SQLite) and seeded with mock HCPs, brochures, past interactions, and sample kits.

### 3. Frontend Setup
1. Open a second terminal in the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install the Node packages:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to the local URL (usually `http://localhost:5173`).

---

## 🧪 Verification & Usage Flows

Click on the suggestion chips in the chat screen or type natural language inputs to test the LangGraph tools:

1. **Log Interaction**:
   - *Prompt*: *"Yesterday I met Dr. Sarah Jenkins. We talked about Prodo-X trials. The sentiment was positive."*
   - *Result*: The left form is automatically populated with:
     - HCP: Dr. Sarah Jenkins (selected)
     - Type: Meeting
     - Sentiment: Positive
     - Date: [Yesterday's Date]
     - Topics: "Prodo-X trials"
2. **Edit Form Fields**:
   - *Prompt*: *"Actually, change the interaction type to Call and set the time to 2:30 PM."*
   - *Result*: The left form updates dynamically.
3. **Lookup Profile**:
   - *Prompt*: *"Show me Dr. Jenkins' preferences."*
   - *Result*: The assistant lists her contact number, clinic, specialty, clinical preferences, and past visit logs.
4. **Product Search**:
   - *Prompt*: *"Search for brochures related to Prodo."*
   - *Result*: The assistant returns lists of matched pdf briefs and trial summaries.
5. **Generate Actions**:
   - *Prompt*: *"Suggest follow-up activities."*
   - *Result*: Next steps and outcome textareas are populated automatically.
6. **Email dispatch**:
   - *Prompt*: *"Email the Dosage Brochure to the doctor."*
   - *Result*: Simulates sending, logs entry to database, and reports successful dispatch to the doctor's email.
