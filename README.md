# GuitarTab Pro

A comprehensive web-based guitar TAB and lyrics/chord organizer application designed for musicians, worship leaders, music therapists, and entertainers.

## Overview

GuitarTab Pro solves the problem of managing and organizing guitar tabs, chord charts, and lyrics in a digital format, replacing physical binders and scattered digital files. It provides intelligent song search capabilities, customizable display formatting, and performance-ready features for live gigs and practice sessions.

## Project Structure

```
guitartab-pro/
├── frontend/          # React/Vue.js frontend application
│   ├── src/           # Source code
│   ├── public/        # Static assets
│   ├── components/    # React/Vue components
│   └── styles/        # CSS/SCSS files
├── backend/           # Python Flask API server
│   ├── src/           # Source code
│   │   ├── app/       # Flask application
│   │   ├── models/    # Database models
│   │   ├── routes/    # API routes
│   │   └── utils/     # Utility functions
│   ├── tests/         # Test files
│   └── requirements/  # Python dependencies
├── docs/              # Project documentation
│   ├── api/           # API documentation
│   ├── user-guides/   # User documentation
│   └── dev-guides/    # Development guides
├── scripts/           # Build and utility scripts
│   └── PRD.txt        # Product Requirements Document
├── .github/           # GitHub workflows and templates
│   └── workflows/     # CI/CD workflows
└── .taskmaster/       # Task Master project management
    ├── tasks/         # Task definitions
    ├── reports/       # Analysis reports
    └── templates/     # PRD templates
```

## Getting Started

This project is currently in development. See the Task Master task list for current progress and next steps.

### Prerequisites

- Node.js (LTS version)
- Python 3.11+
- PostgreSQL 12+
- Git

### Development Setup

1. Clone the repository: `git clone https://github.com/johnnyhayden/guitartab-pro.git`
2. Navigate to the project directory: `cd guitartab-pro`
3. Follow the Task Master workflow for development tasks

## Features

- **Intelligent Song Search**: Find popular tab versions with artist disambiguation
- **API Integration**: Connect to Ultimate Guitar, Songsterr, and other tab sources
- **User Management**: Secure authentication with private song libraries
- **Songlist Organization**: Create and manage custom songlists for gigs
- **Professional Display**: Customizable formatting with color schemes
- **Performance Tools**: Full-screen mode, auto-scroll, metronome, key transposition
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Getting Started

This project is currently in development. See the Task Master task list for current progress and next steps.

## Technology Stack

- **Frontend**: React/Vue.js, HTML5, CSS3, JavaScript
- **Backend**: Python Flask, PostgreSQL
- **Authentication**: JWT-based user authentication
- **Search**: Full-text search capabilities
- **Deployment**: Local development with future cloud deployment

## Contributing

This project uses Task Master for development workflow management. See `.taskmaster/` directory for task details and progress tracking.
