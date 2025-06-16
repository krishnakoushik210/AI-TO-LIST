# AI-Powered Smart To-Do List

An intelligent to-do list application that leverages OpenAI's GPT-3.5 Turbo to automatically categorize tasks, suggest deadlines, and provide smart recommendations.

## Features

- ✨ Add and delete tasks
- 🤖 AI-powered task analysis
- 📱 Responsive design for all devices
- ⏰ Smart deadline suggestions
- 📋 Task categorization
- 💡 Smart task recommendations

## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python (Flask)
- AI: OpenAI API (GPT-3.5 Turbo)

## Setup Instructions

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your OpenAI API key in `.env` file
4. Run the Flask application:
   ```bash
   python app.py
   ```
5. Open `index.html` in your browser

## Project Structure

```
ai-todo-list/
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   └── index.html
├── app.py
├── requirements.txt
└── .env
```

## Environment Variables

Create a `.env` file with the following:
```
OPENAI_API_KEY=your_api_key_here
``` 