# comPASS - AI-Powered Exam Management System

A comprehensive Streamlit-based application for creating, managing, and analyzing exams with AI-powered insights and detailed analytics.

## Features

- **User Authentication**: Secure login system with Firebase integration
- **Exam Management**: Create, view, and manage exams
- **Test Interface**: Interactive exam-taking experience
- **AI Insights**: Intelligent analysis of test results using AI
- **Analytics Dashboard**: Comprehensive performance metrics and analytics
- **HTML Reports**: Generate detailed exam reports
- **Multi-page Interface**: Organized navigation across different modules

## Project Structure

```
comPASS/
├── app.py                          # Main Streamlit application entry point
├── pages/                          # Multi-page Streamlit app modules
│   ├── login.py                    # User authentication page
│   ├── dashboard.py                # Main dashboard view
│   ├── create_test.py              # Exam creation interface
│   ├── take_test.py                # Student exam-taking interface
│   ├── submit_test.py              # Test submission handler
│   ├── view_test.py                # View exam details
│   ├── exam_interface.py           # Exam interaction logic
│   └── test_results.py             # Results and performance view
├── utils/                          # Utility modules
│   ├── auth.py                     # Authentication utilities
│   ├── firebase.py                 # Firebase integration
│   ├── ai_insights.py              # AI-powered analysis
│   ├── analytics.py                # Analytics calculations
│   ├── report_generator.py         # Report generation
│   └── html_report_generator.py    # HTML report formatting
├── scripts/                        # Utility scripts
│   └── verify_firebase.py          # Firebase verification script
├── assets/                         # Static assets directory
├── .streamlit/                     # Streamlit configuration
│   └── config.toml                 # Streamlit settings
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker container configuration
├── .dockerignore                   # Docker build exclusions
└── README.md                       # This file
```

## Requirements

- Python 3.10+
- Streamlit
- Firebase Admin SDK
- pandas
- Additional dependencies in requirements.txt

## Installation

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd comPASS
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Firebase credentials and configuration
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

The application will be available at `http://localhost:8501`

### Docker Setup

1. **Build the Docker image**
   ```bash
   docker build -t compass-app .
   ```

2. **Run the Docker container**
   ```bash
   docker run -p 7860:7860 -e STREAMLIT_SERVER_PORT=7860 compass-app
   ```

The application will be available at `http://localhost:7860`

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY=your_private_key
FIREBASE_CLIENT_EMAIL=your_client_email
STREAMLIT_SERVER_PORT=8501
```

### Streamlit Configuration

Modify `.streamlit/config.toml` for Streamlit-specific settings.

## Usage

### For Students

1. Log in with your credentials
2. Navigate to "Take Test" to view available exams
3. Complete the exam and submit
4. View results and AI-powered insights on the results page

### For Instructors

1. Log in with instructor credentials
2. Create new exams via "Create Test"
3. View submissions and analytics on the Dashboard
4. Generate detailed reports for analysis

## Firebase Setup

1. Create a Firebase project at https://console.firebase.google.com
2. Generate a service account key
3. Store credentials securely in `.env` or Streamlit secrets
4. Run verification script:
   ```bash
   python scripts/verify_firebase.py
   ```

## Key Modules

- **utils/auth.py**: Handles user authentication logic
- **utils/firebase.py**: Firebase database and authentication integration
- **utils/ai_insights.py**: AI-powered analysis of exam results
- **utils/analytics.py**: Performance metrics and analytics calculations
- **utils/report_generator.py**: PDF/document report generation

## Development

### Running Tests

```bash
pytest
```

### Code Style

Follow PEP 8 guidelines. Format code with:

```bash
black .
```

## Deployment

### HuggingFace Spaces

This application is configured for deployment on HuggingFace Spaces:

- Container port: 7860
- Exposed port: 7860
- Health check enabled

## Troubleshooting

- **Firebase connection issues**: Verify credentials in `.env` and run `verify_firebase.py`
- **Port already in use**: Change `STREAMLIT_SERVER_PORT` in configuration
- **Missing dependencies**: Run `pip install -r requirements.txt` again

## Security

- Never commit `.env` or Firebase credentials
- All sensitive files are listed in `.gitignore`
- Use Streamlit secrets management in production
- Keep dependencies updated: `pip install --upgrade -r requirements.txt`

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please open an issue in the repository.