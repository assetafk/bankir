# Banking Service Frontend

Modern React frontend for the Banking Service application.

## Tech Stack

- **React 18**: UI library
- **Webpack**: Module bundler
- **Babel**: JavaScript compiler
- **Tailwind CSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **Axios**: HTTP client

## Development

### Prerequisites

- Node.js 18+ and npm

### Setup

1. Install dependencies:
```bash
npm install
```

2. Create `.env` file (optional):
```bash
cp .env.example .env
```

3. Start development server:
```bash
npm start
```

The app will be available at http://localhost:3000

### Build for Production

```bash
npm run build
```

The built files will be in the `build/` directory.

## Features

- **Authentication**: Login and registration pages
- **Dashboard**: Overview with account summaries
- **Accounts**: Create and manage multi-currency accounts
- **Transfers**: Transfer money between accounts
- **Transactions**: View transaction history with filters

## Project Structure

```
frontend/
├── public/              # Static assets
│   └── index.html
├── src/
│   ├── components/      # Reusable components
│   ├── pages/          # Page components
│   ├── services/       # API service layer
│   ├── utils/          # Utility functions
│   ├── App.js          # Main app component
│   ├── index.js        # Entry point
│   └── index.css       # Global styles
├── package.json
└── webpack.config.js
```
