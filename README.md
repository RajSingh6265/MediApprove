# 🏥 MediApprove

#AI-Powered Insurance Approval Decision Engine for Medical Imaging Procedures

## 📋 Overview

**MediApprove is a complete solution for automating insurance approval decisions for medical imaging procedures. It combines clinical document processing, AI-powered policy analysis, and real-time policy verification to provide instant insurance approval decisions with full transparency.**

## ✨ Features

- 📄 **Document Processing** - Converts PDFs and images to structured clinical data
- 🤖 **AI Extraction** - Uses Google Gemini API for intelligent document understanding
- 🏥 **FHIR Compliance** - Generates HL7 FHIR-compliant healthcare data
- 💰 **Insurance Analysis** - 6 intelligent policy categories with automatic matching
- 🌐 **Real-Time Policies** - Live search from CMS, Medicare, and NIH databases
- 📋 **Local Database** - Vector-based policy search with FAISS
- ✅ **Smart Decisions** - APPROVED/CONDITIONAL/DENIED with confidence scores
- 📊 **Professional Reports** - Clean formatted output with policy references and links
- 🚀 **REST API** - FastAPI backend for integration
- 💻 **Web Dashboard** - Streamlit-based user interface
- ⚡ **Fast Processing** - Process documents in < 5 seconds

## 🛠️ Technology Stack

Frontend: Streamlit 1.28+ for web interface

Backend: Python 3.9+ with FastAPI

AI/ML: Google Gemini API for document extraction

Vector Database: FAISS for semantic policy search

Real-Time Search: DuckDuckGo API (no API key required)

Healthcare Standard: HL7 FHIR v4.0 compliance

Hosting: Streamlit Cloud (24/7 deployment)

Version Control: Git/GitHub

## 📦 Installation
Prerequisites
Python 3.9+
Git
Google Gemini API key (free tier available)

**Setup**
**1. Clone the repository**
git clone https://github.com/RajSingh6265/mediapprove.git
cd mediapprove

**2. Create virtual environment**
**# Windows**
python -m venv venv
venv\Scripts\activate

**#** **macOS/Linux**
python3 -m venv venv
source venv/bin/activate

3. **Install dependencies**
pip install -r requirements.txt

4.** Configure API key**
Create .streamlit/secrets.toml:
GEMINI_API_KEY = "your-api-key-here"
Get free API key: https://ai.google.dev

5. **Run the application**
streamlit run swarms_dashboard.py


## 🚀 Quick Start
1. **Process Documents**

 Open dashboard and go to "🚀 Process" tab
Upload PDF or image
 Click "START SWARMS PROCESSING"
View extracted FHIR resources

2. **Check Insurance Approval**

 Go to "💰 Insurance Approval" tab
 Upload clinical document
 Click "CHECK INSURANCE APPROVAL"
 See decision with policy references

3. **Download Results**

Download FHIR JSON
Download Text Report
View policy sources with links


## 📊 Supported Features
**Document Types**

-- Clinical Notes
-- Prescriptions
-- Discharge Summaries
-- Lab Reports
-- Imaging Reports
-- Medical Images

**Policy Categories**

1a: Chronic Pain - Conservative Therapy
1b: Chronic Pain - Worsening
2: Abnormal Neurologic Findings
3: Tumor/Malignancy
4: Acute Trauma - Spinal Injury
5: Neurologic Emergency

**Decisions**
✅ APPROVED (80-100%)
⚠️ CONDITIONAL (70-89%)

## 📁 Project Structure

mediapprove/
├── swarms_dashboard.py              # Main Streamlit app
├── insurance_approval_agent.py      # Approval engine
├── internet_search_agent.py         # DuckDuckGo search
├── policy_vectordb.py               # FAISS database
├── swarms_orchestrator.py           # Document processing
├── document_classifier.py           # Document type detection
├── requirements.txt                 # Dependencies
├── README.md                        # This file
├── .gitignore                       # Git ignore rules
│
├── data/
│   └── Lumbar-Spine-MRI.pdf        # Sample policy
│
├── policy_db/                       # Vector database (auto-created)
│   └── faiss_index.bin
│
└── .streamlit/
    └── secrets.toml                # API keys (PRIVATE)



## 🔄 How It Works
Step 1: Upload clinical document (PDF/image)
Step 2: AI extracts medical information
Step 3: Convert to FHIR-compliant format
Step 4: Detect policy category
Step 5: Search policies (real-time + local)
Step 6: Match approval criteria
Step 7: Generate professional report
Step 8: Display decision with policy links


## 🙏 Acknowledgments

Google Gemini for AI extraction
Streamlit for web framework
FAISS for vector search
DuckDuckGo for policy search
HL7 for FHIR standard
Python community

# Built with ❤️ for healthcare automation
    










