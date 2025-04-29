# M31-Mini Frontend

## Overview
This is the frontend application for the M31-Mini Autonomous Agent Framework. It is built with Next.js, React, and Tailwind CSS.

## Setup

### Prerequisites
- Node.js 18+
- npm

### Local Development
1. Install dependencies:
```bash
npm install
```
2. Run the development server:
```bash
npm run dev
```
3. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build and Production
Build the application:
```bash
npm run build
```
Start the production server:
```bash
npm start
```

## Project Structure
- `src/`: Source code including components, pages, hooks, and utilities
- `public/`: Static assets
- `styles/`: Global and Tailwind CSS styles
- `package.json`: Project metadata and scripts
- `next.config.js`: Next.js configuration
- `tailwind.config.js`: Tailwind CSS configuration

## Linting and Type Checking
Run linting:
```bash
npm run lint
```
Run type checking:
```bash
npm run type-check
```

## Notes
- Telemetry is disabled in Docker builds.
- Environment variables can be set in the `.env` file.
