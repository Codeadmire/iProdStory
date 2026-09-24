# Product Requirements Document - Product Marketing AI

## Objective
Build a production-ready SaaS application that automates the creation of marketing materials (LinkedIn posts, product pages, images, videos) from a given SaaS product URL.

## Core Principles
- **Evidence-Based**: Every discovered feature must have evidence (URL, page title, visible text, screenshot).
- **No Hallucinations**: Do not invent product features. Distinguish implemented features from proposed features.
- **Human-in-the-Loop**: All AI-generated content must be reviewable and editable before export.
- **Security**: Do not permanently store user passwords for authenticated applications.

## Phase 1: Core Analysis & Public Websites
1. Product URL input interface
2. Product analysis dashboard
3. Website crawler and page discovery
4. Feature extraction (evidence-based)
5. Product/module classification
6. User persona detection
7. Raw application screenshot capture
8. LinkedIn Product Page content generation
9. LinkedIn post generation

## Phase 2: Authenticated Applications & Marketing Assets
1. Authenticated application analysis
2. Browser session support for apps behind login
3. Application navigation and user flow detection
4. Marketing screenshot generator (HTML/CSS composition)
5. Screenshot annotations (callouts, arrows)

## Phase 3: Video & Advanced Content
1. Product Demo Video generation (Playwright recording + FFmpeg)
2. LinkedIn carousel generation
3. Multiple social media format exports (16:9, 1:1, 4:5, 9:16)
4. Brand kit integration
5. Content calendar scheduling
