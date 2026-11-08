# 🚀 DataPilot-AI

### Intelligent AI-Powered Data Analytics Studio

**Transform raw CSV data into meaningful insights using AI, Python, and PostgreSQL.**

DataPilot-AI is an AI-powered data analytics platform that simplifies the process of uploading, profiling, cleaning, validating, and analyzing datasets. It also allows users to interact with their stored data using natural language through a Gemini-powered SQL assistant.

🌐 **Live Application:** https://datapilot-ai-frontend-a123.onrender.com

⚙️ **Backend API:** https://datapilot-ai-anaw.onrender.com

📖 **API Documentation:** https://datapilot-ai-anaw.onrender.com/docs

---

## ✨ Key Features

### 1. 📂 CSV Upload & Data Profiling
- Upload CSV datasets through a browser-based interface.
- Automatically inspect dataset dimensions.
- Identify column names and data types.
- Detect missing values and duplicate records.
- Calculate a data quality score.
- Maximum supported upload size: 5 MB.

### 2. 🧹 Intelligent Data Cleaning
- Remove duplicate records.
- Handle missing numerical values using median imputation.
- Handle missing categorical and text values using mode imputation.
- Generate cleaning summaries.
- Download cleaned datasets as CSV files.

### 3. ✅ Data Validation
- Identify missing and suspicious values.
- Detect invalid or unexpected data.
- Generate validation reports.
- Highlight potential data quality issues.

### 4. 📊 Exploratory Data Analysis (EDA)
- Generate statistical summaries.
- Analyze numerical columns.
- Explore categorical value frequencies.
- Examine relationships between numerical variables.
- Generate charts and visual insights.

### 5. 🗄️ PostgreSQL Integration
- Store uploaded datasets in PostgreSQL.
- Automatically create dataset tables.
- Maintain a centralized dataset registry.
- Retrieve dataset information and metadata.
- Select stored datasets for further analysis.

### 6. 🤖 AI-Powered SQL Assistant
- Ask questions about uploaded datasets using natural language.
- Generate SQL queries using Google Gemini.
- Integrate Gemini through LangChain.
- Validate generated SQL before execution.
- Restrict queries to the selected registered dataset.
- Display structured query results.
- Generate visual insights from query results.

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python 3.12 |
| Backend | FastAPI, Uvicorn |
| Frontend | HTML, CSS, JavaScript |
| Data Processing | Pandas, NumPy |
| Database | PostgreSQL |
| AI Integration | Google Gemini, LangChain |
| SQL Validation | SQLGlot |
| Configuration | Pydantic Settings, python-dotenv |
| Testing | Pytest |
| Deployment | Render |

---

## 🏗️ System Architecture

```text
                USER
                  |
                  v
       Browser-Based Frontend
           HTML / CSS / JS
                  |
                  v
            FastAPI Backend
                  |
       +----------+-----------+
       |          |           |
       v          v           v
   Pandas     PostgreSQL    Gemini AI
  Processing   Database    SQL Assistant
       |          |           |
       v          v           v
  Profiling   Dataset      SQL Generation
  Cleaning    Registry     & Validation
  Validation  & Storage         |
  EDA             |             |
       +----------+-------------+
                  |
                  v
          Results & Insights
                  |
                  v
               USER
```

---

## 📁 Project Structure

```text
DataPilot-AI/
│
├── app/
│   ├── core/
│   ├── database/
│   ├── schemas/
│   ├── services/
│   └── main.py
│
├── data/
│   └── sample/
│
├── docs/
├── frontend/
│   └── index.html
│
├── scripts/
├── tests/
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.12
- PostgreSQL
- Git
- Google Gemini API key

### 1. Clone the Repository

```bash
git clone https://github.com/atulsahu003/DataPilot-AI.git
cd DataPilot-AI
```

### 2. Create a Virtual Environment

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a PostgreSQL database:

```sql
CREATE DATABASE datapilot_db;
```

### 5. Configure Environment Variables

Create your `.env` file:

```powershell
Copy-Item .env.example .env
```

Configure the following variables:

```dotenv
GOOGLE_API_KEY=your_google_gemini_api_key
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/datapilot_db
APP_NAME=DataPilot-AI
APP_ENV=development
DEBUG=true
```

Replace example credentials with your own configuration.

**Important:** Never commit your `.env` file or expose API keys and database credentials.

### 6. Start the Backend

```powershell
python -m uvicorn app.main:app --reload
```

Backend URL:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

### 7. Start the Frontend

Open another PowerShell terminal and execute:

```powershell
python -m http.server 5500 --directory frontend
```

Open:

http://127.0.0.1:5500

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Application status |
| GET | `/health` | Application health check |
| GET | `/db-health` | Database connectivity check |
| GET | `/profile-sample` | Profile sample dataset |
| POST | `/upload-csv` | Upload and profile CSV |
| POST | `/clean-csv` | Clean CSV dataset |
| POST | `/cleaning-summary` | Generate cleaning summary |
| POST | `/validate-csv` | Validate dataset |
| POST | `/eda` | Perform exploratory data analysis |
| POST | `/store-csv` | Store CSV in PostgreSQL |
| GET | `/datasets` | List registered datasets |
| POST | `/query-data` | Execute AI-powered data queries |

For detailed request and response schemas, visit the interactive API documentation.

---

## 🧪 Testing

Run the test suite:

```powershell
python -m pytest -v
```

**Latest recorded development test result:** 59 tests passed.

---

## 🔐 Security & Configuration

- Store sensitive configuration in environment variables.
- Keep `.env` and virtual environment files out of Git.
- Validate generated SQL before execution.
- Restrict SQL queries to the selected registered dataset.
- Use appropriate database permissions.
- Review security and error handling before production use.

---

## ☁️ Deployment

DataPilot-AI is deployed using Render.

| Component | Deployment |
|---|---|
| Frontend | Render Static Site |
| Backend | Render Web Service |
| Database | Render PostgreSQL |

**Live Links**

- Frontend: https://datapilot-ai-frontend-a123.onrender.com
- Backend: https://datapilot-ai-anaw.onrender.com
- API Docs: https://datapilot-ai-anaw.onrender.com/docs

Note: The application uses Render's free services, which may experience cold-start delays. Free database availability and retention are subject to Render's current limits.

---

## 🚧 Future Enhancements

- Improve natural-language SQL capabilities.
- Expand automated data quality checks.
- Add more advanced visualizations.
- Improve application monitoring and error handling.
- Strengthen SQL security and integration testing.
- Explore multi-agent orchestration.

---

## 👨‍💻 Author

**Atul Sahu**

GitHub: https://github.com/atulsahu003

Project Repository: https://github.com/atulsahu003/DataPilot-AI

---

⭐ If you find this project interesting, consider giving it a star on GitHub.

**DataPilot-AI — Your Data, Understood.**