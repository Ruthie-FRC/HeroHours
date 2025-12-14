# HeroHours

A Django-based time tracking system for managing member check-ins and check-outs, designed for team time management and activity logging.

## Features

- **Member Management**: Track team members with their ID, name, and total hours
- **Check-In/Check-Out System**: Simple interface for members to check in and out
- **Activity Logging**: Comprehensive logging of all check-in/check-out activities
- **Admin Interface**: Full Django admin interface for managing members and viewing logs
- **API Integration**: RESTful API endpoints for data access and Google Sheets integration
- **Real-time Dashboard**: Live view of checked-in members and recent activity

## Tech Stack

- **Backend**: Django 5.1.2
- **Database**: PostgreSQL (production) / SQLite (development)
- **API**: Django REST Framework
- **Deployment**: Heroku-ready with Gunicorn
- **Authentication**: Token-based API authentication

## Installation

### Prerequisites

- Python 3.8+
- pip
- PostgreSQL (for production)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Ruthie-FRC/HeroHours.git
   cd HeroHours
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Fill in the required values:
     ```
     SECRET_KEY=your-secret-key
     APP_SCRIPT_URL=your-google-apps-script-url
     DATABASE_URL=your-database-url
     DJANGO_DATABASE=default
     DEBUG=True  # Set to False in production
     ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Collect static files:
   ```bash
   python manage.py collectstatic
   ```

8. Run the development server:
   ```bash
   python manage.py runserver
   ```

Visit `http://localhost:8000/HeroHours/` to access the application.

## Usage

### For Members

1. Navigate to the main page
2. Enter your member ID to check in or check out
3. The system automatically tracks your time

### For Administrators

1. Access the admin panel at `/admin/`
2. Manage members, view activity logs, and export data
3. Use bulk actions for checking in/out multiple members

### API Endpoints

- `GET /api/sheet/users/` - Export all members data (CSV format)
- `GET /api/sheet/<year>/<month>/<day>/` - Get meeting attendance for a specific date

API endpoints require token authentication via the `key` query parameter.

## Configuration

### Database

The application supports both SQLite (development) and PostgreSQL (production). Configure via the `DATABASE_URL` and `DJANGO_DATABASE` environment variables.

### Google Sheets Integration

Set the `APP_SCRIPT_URL` environment variable to enable data syncing with Google Sheets.

## Deployment

The application is configured for Heroku deployment:

1. Ensure all environment variables are set in Heroku
2. The `Procfile` is already configured
3. Push to Heroku:
   ```bash
   git push heroku main
   ```

## Security

- Always use HTTPS in production (enforced via `SECURE_SSL_REDIRECT`)
- Keep `SECRET_KEY` and other sensitive data in environment variables
- Set `DEBUG=False` in production
- Use strong passwords for admin accounts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under standard licensing terms.

## Support

For issues and questions, please use the GitHub issue tracker.
