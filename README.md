# WearWise

## Project Overview
This project implements an AI agent that helps users find fashion rental items across multiple platforms.
The agent takes a brief from the user (desired article of clothing, colour, vibe etc.) and then:
- Determines which rental platforms are suitable
- Formulates a search query based on the user brief
- Finds items and item details from these rental platforms
- Ranks items based on how well-suited they are for the user

## Setup Instructions

1. Clone the repository
```bash
git clone agent-marcy
cd agent-marcy
```
2. Create and activate a virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate # Windows
source .venv/bin/activate # Mac/Linux
```
3. Install dependencies
```bash
pip install -r requirements.txt
```
4. Set environment variables (see .env.example)

## How to run

1. Run the main pipeline
```bash
python app.py
```
2. Fill out your requirements on the questionnaire

3. Enjoy your fashion rental recommendations