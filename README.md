# RegShift — Insurance Regulatory Intelligence

## Overview
RegShift is an AI-powered regulatory intelligence prototype designed to help insurance teams translate regulatory updates into structured compliance requirements, identify potentially affected insurance products and prepare proposed implementation changes for human review.

## Problem
Insurance organizations must interpret regulatory documents and determine how new requirements affect policy forms, disclosures, rating rules and reporting processes. Manual analysis can be time-consuming and make it difficult to trace proposed changes back to their source.

## Solution
RegShift uses Gemini-powered requirement extraction to identify requirements from uploaded documents, preserve supporting source passages, flag ambiguities and generate structured outputs for downstream impact analysis.

## Key Features
- Regulatory document upload and analysis
- AI-powered requirement extraction using Gemini
- Source-passage traceability and ambiguity flags
- Potential insurance product impact analysis
- Change ticket creation and human review workflow
- Application audit trail

## Technology Stack
- **Frontend:** React, TypeScript, Vite
- **Backend:** Python, FastAPI
- **AI:** Gemini API through an OpenAI-compatible client
- **Database:** SQLite

## Run Locally

### Backend
1. Open a terminal in the `backend` directory.
2. Install dependencies:

   `pip install -r requirements.txt`

3. Create a `.env` file using `.env.example` as a template.
4. Add your Gemini API key and provider configuration to `.env`.
5. Start the API:

   `python -m uvicorn app.main:app --reload --port 8000`

### Frontend
1. Open another terminal in the `frontend` directory.
2. Install dependencies:

   `npm install`

3. Start the development server:

   `npm run dev`

4. Open `http://localhost:5173`.
