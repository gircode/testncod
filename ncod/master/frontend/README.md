# Master Server Frontend

A clean and modern web interface for the Master Server using PyWebIO.

## Features

- Clean and minimalist login page
- Light blue background for better user experience
- Math captcha verification (random addition/subtraction within 20)
- Responsive design
- Secure password input

## Setup

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**2. Install dependencies:**

```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the server:

```bash
python main.py
```

**2. Access the application:**

- Open your web browser
- Navigate to `http://localhost:8080`

## Development

The frontend is built using:

- PyWebIO for the web interface
- FastAPI as the web framework
- Pillow for captcha image generation

### Project Structure

frontend/
├── main.py         # Main application entry point
├── login.py        # Login page implementation
├── requirements.txt # Project dependencies
└── README.md       # This file

## Security Notes

- The login page uses a math captcha to prevent automated attacks
- Passwords are handled securely and never displayed
- All input is validated before processing
