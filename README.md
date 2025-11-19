# 🎯 TalentRadar v2 - AI-Powered Applicant Tracking System

## 📋 Overview

TalentRadar v2 is a professional, enterprise-grade ATS (Applicant Tracking System) built with modern technologies and AI-powered resume analysis. It features an advanced graduated scoring system, candidate profile management, duplicate detection, and intelligent interview question generation.

### 🌟 Key Features

- ✅ **Advanced Scoring System**: Graduated scoring with multiple strategies (ranged, categorical, boolean, text matching)
- ✅ **AI-Powered Analysis**: Intelligent resume parsing using Claude Sonnet 4.5
- ✅ **SQLite Database**: Professional data storage with full relational integrity
- ✅ **Candidate Profiles**: Automatic de-duplication by phone number
- ✅ **Interview Questions**: AI-generated customized questions for each candidate
- ✅ **Multi-Resume Processing**: Batch upload and processing capabilities
- ✅ **Criteria Management**: Flexible, customizable evaluation criteria per position
- ✅ **User Authentication**: Secure JWT-based authentication with role-based access
- ✅ **Manager Notes**: Collaborative notes on candidate profiles
- ✅ **English Interface**: Modern, responsive UI in English
- ✅ **Audit Trail**: Complete logging of all system actions

---

## 🏗️ Architecture

```
TalentRadar v2
│
├── Backend (Flask + SQLAlchemy)
│   ├── RESTful API
│   ├── JWT Authentication
│   ├── AI Service Integration
│   ├── Advanced Scoring Engine
│   └── Database Management
│
├── Frontend (Vanilla JS + Modern CSS)
│   ├── Component-Based Architecture
│   ├── Responsive Design
│   ├── Dark Theme
│   └── Real-Time Updates
│
└── Database (SQLite)
    ├── Users & Auth
    ├── Positions & Criteria
    ├── Candidates & Resumes
    ├── Scores & Analytics
    └── Audit Logs
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- pip
- Virtual environment (recommended)

### Installation

1. **Clone/Extract the project**
```bash
cd TalentRadar-v2
```

2. **Create virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
cd backend
pip install -r requirements.txt
```

4. **Configure environment**
```bash
# Copy template and edit
cp ../.env.template ../.env

# Edit .env file with your settings
nano ../.env  # or use any text editor
```

**Important**: Add your AI API key:
```env
LIARA_API_KEY=your-actual-api-key-here
```

5. **Initialize database**
```bash
cd backend
python init_db.py
```

This will:
- Create SQLite database
- Initialize all tables
- Create default admin user (username: `admin`, password: `admin123`)
- Seed initial position and criteria

6. **Start the server**
```bash
python app.py
```

Server will run on `http://localhost:5000`

7. **Open frontend**

Open `frontend/index.html` in your browser or serve with a simple HTTP server:

```bash
cd ../frontend
python -m http.server 8000
```

Then visit `http://localhost:8000`

---

## 📚 Core Concepts

### 1. Graduated Scoring System

Unlike binary scoring (0 or full points), TalentRadar v2 uses **graduated scoring** to provide nuanced evaluation:

#### Example: Years of Experience

**Old System (Binary)**:
```
1 year 11 months → 0 points (below 2 year minimum)
2 years → 20 points
10 years → 20 points (same as 2 years!)
```

**New System (Graduated)**:
```
1 year → 3 points (15% - Junior)
3 years → 12 points (60% - Qualified)
7 years → 17 points (85% - Senior)
12 years → 20 points (100% - Expert)
```

This provides fair recognition of experience levels.

### 2. Criterion Types

#### A. Ranged Number
For numeric values (age, years of experience, language percentage):

```json
{
  "data_type": "ranged_number",
  "weight": 20,
  "config_json": {
    "scoring_type": "ranged",
    "ranges": [
      {"min": 10, "max": 999, "score_multiplier": 1.0, "label": "Expert"},
      {"min": 5, "max": 9, "score_multiplier": 0.85, "label": "Senior"},
      {"min": 2, "max": 4, "score_multiplier": 0.6, "label": "Qualified"}
    ]
  }
}
```

#### B. Graded Category
For skill levels (Basic, Intermediate, Advanced):

```json
{
  "data_type": "graded_category",
  "weight": 8,
  "config_json": {
    "scoring_type": "categorical",
    "levels": {
      "Advanced": 1.0,
      "Intermediate": 0.65,
      "Basic": 0.2
    }
  }
}
```

#### C. Boolean
For yes/no criteria (has experience or not):

```json
{
  "data_type": "boolean",
  "weight": 2,
  "config_json": {
    "scoring_type": "binary",
    "true_value": 1.0,
    "false_value": 0.0
  }
}
```

#### D. Text Match
For keyword matching (education field, industry):

```json
{
  "data_type": "text_match",
  "weight": 10,
  "config_json": {
    "scoring_type": "keyword_match",
    "required_keywords": ["Accounting", "Finance"],
    "match_type": "any"
  }
}
```

### 3. Candidate De-duplication

TalentRadar automatically detects duplicate candidates by **phone number**:

```
Upload Resume 1 (Phone: +98 912 345 6789)
  → Creates new candidate profile

Upload Resume 2 (Phone: +98 912 345 6789)
  → Links to existing candidate profile
  → Both resumes visible in candidate history
```

### 4. AI-Generated Interview Questions

For each resume, the system generates **3 customized interview questions**:

- **Technical**: Based on required skills
- **Behavioral**: Based on experience level
- **Situational**: Based on job requirements

Questions are stored in the database and visible in the candidate profile.

---

## 🎨 User Interface

### Dashboard
- Overview statistics (total, qualified, rejected, average score)
- Quick actions (upload, bulk upload, export)
- Recent applications table

### Positions Management
- Create/edit job positions
- Set qualification threshold
- Manage evaluation criteria

### Criteria Management
- Add/remove criteria per position
- Configure scoring ranges
- Set weights and requirements
- Drag-and-drop ordering

### Candidates
- View all candidate profiles
- See submission history per candidate
- Add manager notes
- View interview questions

### Resume Analysis
- Upload single or multiple resumes
- Real-time processing status
- Detailed score breakdown
- Overall assessment

---

## 🔐 Security Features

### API Key Management
- API keys encrypted in database
- Stored separately from code
- Never exposed to frontend

### Authentication
- JWT-based authentication
- Role-based access control (Admin, Recruiter, Viewer)
- Secure password hashing (bcrypt)

### Audit Trail
- All actions logged
- User tracking
- Change history
- IP address recording

---

## 📊 Scoring Examples

### Example 1: Strong Candidate

```
Position: Senior Accountant (Threshold: 75%)

Criteria Scores:
✓ Work Experience: 8 years → 17/20 points (85%)
✓ Education Level: Masters → 13.5/15 points (90%)
✓ Education Field: Accounting → 10/10 points (100%)
✓ Responsibility Level: Supervisor → 12/15 points (80%)
✓ Last Job Title: "Senior Accountant" → 15/15 points (100%)
✓ Sepidar Software: Advanced → 10/10 points (100%)
✓ Excel Skills: Advanced → 8/8 points (100%)
✓ English Level: 65% → 4/5 points (80%)

Total: 89.5/98 points = 91.3% ✅ QUALIFIED

Assessment: "Excellent candidate - Exceeds requirements significantly. 
Strong performance across all core criteria."
```

### Example 2: Marginal Candidate

```
Position: Senior Accountant (Threshold: 75%)

Criteria Scores:
⚠ Work Experience: 2.5 years → 12/20 points (60%)
✓ Education Level: Bachelors → 10.5/15 points (70%)
✓ Education Field: Finance → 10/10 points (100%)
⚠ Responsibility Level: Specialist → 4.5/15 points (30%)
⚠ Last Job Title: "Accountant" → 0/15 points (0%)
⚠ Sepidar Software: Basic → 2/10 points (20%)
✓ Excel Skills: Intermediate → 5.2/8 points (65%)
✓ English Level: 45% → 2.5/5 points (50%)

Total: 46.7/98 points = 47.7% ❌ REJECTED

Assessment: "Below threshold by 27.3 percentage points. 
Areas for improvement: 4 criteria below expectations."
```

---

## 🛠️ API Endpoints

### Authentication
```
POST /api/auth/login
POST /api/auth/register
POST /api/auth/logout
GET  /api/auth/me
```

### Positions
```
GET    /api/positions
POST   /api/positions
GET    /api/positions/<id>
PUT    /api/positions/<id>
DELETE /api/positions/<id>
```

### Criteria
```
GET    /api/positions/<id>/criteria
POST   /api/positions/<id>/criteria
PUT    /api/criteria/<id>
DELETE /api/criteria/<id>
```

### Resumes
```
POST   /api/resumes/upload
POST   /api/resumes/bulk-upload
GET    /api/resumes
GET    /api/resumes/<id>
DELETE /api/resumes/<id>
```

### Candidates
```
GET    /api/candidates
GET    /api/candidates/<id>
POST   /api/candidates/<id>/notes
GET    /api/candidates/<id>/notes
```

### Scoring
```
GET    /api/resumes/<id>/scores
GET    /api/resumes/<id>/assessment
```

---

## 🧪 Testing

Run tests:
```bash
cd backend
pytest tests/ -v
```

Test coverage:
```bash
pytest tests/ --cov=backend --cov-report=html
```

---

## 📈 Performance

### Database Optimization
- Proper indexing on frequently queried columns
- Connection pooling
- Query optimization
- Batch operations support

### Expected Performance
- Resume processing: < 10 seconds per resume
- Database queries: < 100ms response time
- Concurrent users: 50+ supported
- Bulk upload: 50 resumes in parallel

---

## 🔧 Configuration

### Key Configuration Options

**.env file**:
```env
# Database
DATABASE_URL=sqlite:///data/talentdatar.db

# AI Configuration
AI_MODEL=claude-sonnet-4-20250514
AI_TEMPERATURE=0.1
LIARA_BASE_URL=https://ai.liara.ir/api/...

# Security
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-key

# Server
PORT=5000
DEBUG=True

# File Upload
MAX_CONTENT_LENGTH=16777216  # 16MB
ALLOWED_EXTENSIONS=pdf,docx,doc,jpg,jpeg,png
```

---

## 📝 Prompts

Prompts are stored separately in `backend/prompts/`:

- `extraction_prompt.txt`: Resume data extraction
- `scoring_prompt.txt`: Scoring logic explanation
- `questions_prompt.txt`: Interview question generation

This separation allows easy updates without code changes.

---

## 🤝 Contributing

### Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write docstrings for all functions
- Add unit tests for new features

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/your-feature
```

---

## 🐛 Troubleshooting

### Database Issues

**Error: "database is locked"**
```bash
# Check for open connections
lsof data/talentdatar.db

# Restart server
```

**Reset database** (development only):
```python
from backend.database.db import reset_database
reset_database()
```

### API Key Issues

**Error: "API key not configured"**
1. Check `.env` file has `LIARA_API_KEY`
2. Restart Flask server
3. Verify API key in database:
```sql
SELECT * FROM api_keys WHERE service_name='liara';
```

### Frontend Connection Issues

**Update API URL** in `frontend/assets/js/api.js`:
```javascript
const API_URL = 'http://localhost:5000/api';
```

---

## 📚 Additional Resources

### Documentation
- [API Documentation](docs/API.md)
- [Database Schema](docs/DATABASE.md)
- [Scoring System Guide](docs/SCORING.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

### External Links
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Anthropic API](https://docs.anthropic.com/)

---

## 📄 License

This project is proprietary software developed for internal use.

---

## 👥 Team

- **Project Lead**: Your Name
- **Backend Development**: Development Team
- **Frontend Development**: Development Team
- **AI Integration**: AI Team

---

## 📞 Support

For issues or questions:
- Email: support@talentdatar.com
- Slack: #talentdatar-support
- Documentation: [Wiki](https://wiki.company.com/talentdatar)

---

## 🎯 Roadmap

### v2.1 (Q1 2025)
- [ ] Email integration
- [ ] Calendar sync
- [ ] Advanced analytics dashboard
- [ ] Bulk actions

### v2.2 (Q2 2025)
- [ ] Mobile app
- [ ] API webhooks
- [ ] Custom report builder
- [ ] Interview scheduling

### v3.0 (Q3 2025)
- [ ] Multi-language support
- [ ] Video interview integration
- [ ] AI bias detection
- [ ] Skills gap analysis

---

## ⭐ Acknowledgments

Special thanks to:
- Anthropic for Claude AI
- Liara for infrastructure
- Open source community

---

**Made with ❤️ by the TalentRadar Team**