# Product Marketing AI - Architecture

## Overview
Product Marketing AI is a SaaS platform that automatically turns any SaaS product into a complete LinkedIn marketing kit by crawling websites, discovering features, capturing screenshots, and generating marketing content using AI.

## Technology Stack
- **Frontend**: Next.js, React, TypeScript
- **Backend**: Python, FastAPI
- **Database**: PostgreSQL
- **Browser Automation**: Playwright (for crawling, page discovery, and screenshot capture)
- **Video Generation**: Playwright recording + FFmpeg
- **AI/LLM**: LLM-based product analysis and content generation

## System Components
1. **Next.js UI**: Frontend dashboard for entering URLs, reviewing generated content, and exporting assets.
2. **FastAPI Backend**: Orchestrates the crawling, analysis, and generation workflows.
3. **Playwright Service**: Headless browser automation for discovering user flows and capturing raw screenshots.
4. **AI Engine (LLM)**: Analyzes page content to extract features, identify modules, determine personas, and write LinkedIn posts.
5. **Content Engine**: Composes marketing screenshots (HTML/CSS to screenshot) and generates video scripts/demos.
6. **PostgreSQL Database**: Stores product intelligence (features, personas, URLs, generated content).

## Architecture Flow
```text
                     ┌───────────────┐
                     │   Next.js UI  │
                     └───────┬───────┘
                             │
                             ▼
                     ┌───────────────┐
                     │   FastAPI     │
                     │   Backend     │
                     └───────┬───────┘
                             │
             ┌───────────────┼────────────────┐
             ▼               ▼                ▼
       ┌──────────┐    ┌───────────┐    ┌───────────┐
       │ Playwright│    │ AI Engine │    │ PostgreSQL│
       └─────┬────┘    └─────┬─────┘    └───────────┘
             │               │
             ▼               ▼
       Screenshots      Product Intelligence
       Page discovery   Features
       User flows       Personas
       Video recording  Benefits
             │               │
             └───────┬───────┘
                     ▼
             ┌──────────────────┐
             │ Content Engine   │
             └────────┬─────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   LinkedIn       Images         Video
   Posts          Carousel       Demo
```
