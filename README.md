
# DataPilot-AI 🚀

**An AI-Powered Data Analytics Platform**

DataPilot-AI is a Python-based data analytics application that allows users to upload CSV files, inspect data quality, clean datasets, explore statistical summaries, and ask questions about uploaded data using natural language.

The application combines a FastAPI backend, a browser-based frontend, PostgreSQL storage, and a Gemini-powered SQL assistant.

## ✨ Features

### 1. CSV Upload and Profiling
- Upload CSV files through the web interface.
- Validate file format, encoding, and data content.
- Generate data profiling summaries.
- Enforce a 5 MB upload limit on the relevant upload endpoints.

### 2. Data Cleaning
- Remove duplicate rows.
- Fill missing numerical values using median imputation.
- Fill missing categorical or text values using mode imputation.
- Review before-and-after cleaning statistics.
- Download cleaned CSV data.

### 3. Data Validation
- Identify missing and invalid values.
- Validate age-related data when applicable.
- Review validation results through the API and frontend.

### 4. Exploratory Data Analysis
- Generate numerical summaries.
- Inspect categorical value frequencies.
- Explore relationships between numerical variables.
- View charts and correlation visualizations.

### 5. PostgreSQL Integration
- Store uploaded datasets as PostgreSQL tables.
- Maintain a registry of uploaded datasets.
- Retrieve registered datasets and their metadata.
- Select a dataset for subsequent SQL analysis.

### 6. AI-Powered SQL Assistant
- Ask questions about a selected dataset in natural language.
- Generate SQL using Gemini through LangChain integration.
- Use deterministic fallback queries for supported questions.
- Validate generated queries before execution.
- Restrict query access to the selected registered dataset.
- Return query results as structured data for the frontend.

## 🧰 Technology Stack

- **Language:** Python 3.12
- **Backend:** FastAPI, Uvicorn
- **Data Processing:** Pandas, NumPy
- **Database:** PostgreSQL
- **AI Integration:** Google Gemini, LangChain Google GenAI
- **SQL Validation:** SQLGlot
- **Configuration:** Pydantic Settings, python-dotenv
- **Testing:** pytest
- **Frontend:** HTML, CSS, JavaScript

LangGraph packages are listed in the project dependencies. Multi-agent orchestration has not yet been verified as an implemented feature.

## 📁 Project Structure

```text
DataPilot-AI/
├── app/
│   ├── core/
│   ├── database/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── data/
├── docs/
├── frontend/
│   └── index.html
├── scripts/
├── tests/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## ⚙️ Prerequisites

Install or prepare the following:

- Python 3.12
- PostgreSQL
- Git (optional, for version control)
- A Google Gemini API key for AI-powered SQL generation

## 🚀 Installation and Setup

### 1. Clone the repository

After the project is published on GitHub:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd DataPilot-AI
```

Alternatively, use your existing local project directory.

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Create the PostgreSQL database

Create a PostgreSQL database named `datapilot_db` using your PostgreSQL installation.

For example, using `psql`:

```sql
CREATE DATABASE datapilot_db;
```

Configure the connection string using your actual PostgreSQL username, password, host, port, and database name.

### 5. Configure environment variables

Create a local `.env` file based on `.env.example`:

```powershell
Copy-Item .env.example .env
```

Set the appropriate values in `.env`:

```dotenv
GOOGLE_API_KEY=your_google_gemini_api_key
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/datapilot_db
APP_NAME=DataPilot-AI
APP_ENV=development
DEBUG=true
```

Replace the example credentials with your own values.

**Never commit `.env` or expose API keys, passwords, or database credentials.** The `.env` file should remain local.

### 6. Start the backend

From the project root, with the virtual environment activated:

```powershell
python -m uvicorn app.main:app --reload
```

The backend should be available at:

- Application: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs
- Application health: http://127.0.0.1:8000/health
- Database health: http://127.0.0.1:8000/db-health

### 7. Start the frontend

Open a second PowerShell terminal, navigate to the project root, and activate the virtual environment if needed.

Run:

```powershell
python -m http.server 5500 --directory frontend
```

Open the frontend at:

http://127.0.0.1:5500/index.html

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Application welcome and status |
| GET | `/health` | Application health check |
| GET | `/db-health` | Database health check |
| GET | `/profile-sample` | Profile the configured sample CSV |
| POST | `/upload-csv` | Upload and profile a CSV |
| POST | `/clean-csv` | Clean a CSV and return a downloadable file |
| POST | `/cleaning-summary` | Generate cleaning statistics |
| POST | `/validate-csv` | Validate CSV data |
| POST | `/eda` | Generate EDA summaries |
| POST | `/store-csv` | Store a CSV in PostgreSQL |
| GET | `/datasets` | List registered datasets |
| POST | `/query-data` | Ask a question about a selected dataset |

Upload endpoints expect CSV files using multipart form data. The SQL assistant expects a question and a selected dataset name.

## 🧪 Testing

Run the automated test suite from the project root:

```powershell
python -m pytest -v
```

Latest recorded result during development:

**59 tests passed.**

Run the tests again after making changes to verify the current codebase.

## 🔐 Security Notes

- Keep API keys and database credentials in `.env`.
- Do not commit `.env`, `.venv`, or generated cache files.
- Use `.env.example` to document required configuration keys without real credentials.
- The SQL assistant validates generated SQL and restricts queries to the selected registered dataset.
- Review security, database permissions, and deployment settings before exposing the application publicly.

## 🛠️ Project Status

Core CSV processing, cleaning, validation, EDA, PostgreSQL integration, and natural-language SQL features have been implemented and tested.

Final end-to-end verification, documentation review, and deployment readiness checks remain part of the project completion process.

## 📌 Future Improvements

- Verify and implement multi-agent orchestration where needed.
- Add more analytical workflows and supported natural-language queries.
- Improve deployment automation and production configuration.
- Add further integration tests and user-facing error handling.
- Enhance reporting and data export capabilities.

## 👨‍💻 Development

This project is being developed as an AI and Data Science portfolio project.

Contributions, suggestions, and constructive feedback are welcome.


