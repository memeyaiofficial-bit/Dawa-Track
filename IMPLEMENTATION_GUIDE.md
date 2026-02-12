# DawaTrack Hospital - Implementation Guide

## Quick Start Guide

### Prerequisites
- Python 3.9+
- MySQL 5.7+
- Redis
- pip and virtualenv

### 1. Initial Setup

```bash
# Clone/navigate to project directory
cd /path/to/Dawa\ Track

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env

# Minimum settings for development:
# - DEBUG=True
# - SECRET_KEY=your-dev-key
# - DB_NAME=dawatrack_dev
# - DB_USER=root
# - DB_PASSWORD=
# - AFRICA_TALKING_API_KEY=your-test-key
```

### 3. Database Setup

```bash
# Create MySQL database
mysql -u root -p
CREATE DATABASE dawatrack_dev;

# Run migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser
# Email: admin@dawatrack.local
# Password: (choose strong password)

# Load initial data (optional)
python manage.py loaddata initial_data.json
```

### 4. Redis Setup (Development)

```bash
# Windows: Download and run Redis from https://github.com/microsoftarchive/redis/releases
# Linux/Mac:
brew install redis  # Mac
sudo apt-get install redis-server  # Linux

# Start Redis
redis-server

# Test Redis connection
redis-cli ping  # Should return PONG
```

### 5. Celery Setup (Development)

```bash
# In a new terminal (with venv activated):

# Start Celery worker
celery -A dawatrack worker -l info

# In another terminal:
# Start Celery Beat scheduler
celery -A dawatrack beat -l info
```

### 6. Run Development Server

```bash
# Original terminal with venv activated
python manage.py runserver

# Access at http://localhost:8000
# Admin at http://localhost:8000/admin
# API docs at http://localhost:8000/api/docs/
```

---

## API Endpoints Summary

### Authentication
```
POST /api/token/                    # Get JWT token
POST /api/token/refresh/            # Refresh JWT token
POST /api/users/register/           # Register new user
POST /api/users/login/              # Login
GET  /api/users/me/                 # Get current user
```

### Patients
```
GET    /api/patients/               # List patients
POST   /api/patients/               # Create patient
GET    /api/patients/{id}/          # Get patient details
PATCH  /api/patients/{id}/          # Update patient
GET    /api/patients/{id}/prescriptions/    # Get patient prescriptions
GET    /api/patients/{id}/adherence-report/ # Get adherence data
GET    /api/patients/my-profile/    # Get current patient's profile
```

### Prescriptions
```
GET    /api/prescriptions/          # List prescriptions
POST   /api/prescriptions/          # Create prescription (doctor only)
GET    /api/prescriptions/{id}/     # Get prescription details
PATCH  /api/prescriptions/{id}/     # Update prescription
DELETE /api/prescriptions/{id}/     # Delete prescription
POST   /api/prescriptions/{id}/create-reminders/  # Auto-create reminders
GET    /api/prescriptions/{id}/dose-logs/         # Get dose logs
```

### Reminders
```
GET    /api/reminders/              # List reminders
GET    /api/reminders/pending/      # List pending reminders
GET    /api/reminders/my-pending/   # Get patient's pending reminders
POST   /api/reminders/bulk-create/  # Create multiple reminders
POST   /api/reminders/{id}/respond/ # Patient responds to reminder
```

### Alerts
```
GET    /api/alerts/                 # List alerts
GET    /api/alerts/unresolved/      # Get unresolved alerts
POST   /api/alerts/{id}/resolve/    # Mark alert as resolved
```

---

## Usage Examples

### 1. Register as Doctor

```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dr.smith@hospital.local",
    "username": "drsmith",
    "first_name": "John",
    "last_name": "Smith",
    "phone_number": "+254712345678",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "role": "doctor"
  }'
```

### 2. Login & Get Token

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dr.smith@hospital.local",
    "password": "SecurePass123!"
  }'

# Response includes:
# {
#   "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
# }
```

### 3. Create Patient

```bash
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

curl -X POST http://localhost:8000/api/patients/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user": {
      "email": "john.doe@example.com",
      "username": "johndoe",
      "first_name": "John",
      "last_name": "Doe",
      "phone_number": "+254798765432",
      "password": "PatientPass456!",
      "role": "patient"
    },
    "date_of_birth": "1990-01-15",
    "gender": "M",
    "blood_type": "O+",
    "care_category": "normal",
    "assigned_doctor": 1
  }'
```

### 4. Create Prescription

```bash
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

curl -X POST http://localhost:8000/api/prescriptions/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient": 1,
    "drug_name": "Amoxicillin",
    "dosage": "500mg",
    "frequency": "thrice_daily",
    "duration_days": 7,
    "start_date": "2024-02-09",
    "indication": "Bacterial infection",
    "schedule_times": [
      {
        "scheduled_time": "08:00:00",
        "description": "Morning with breakfast"
      },
      {
        "scheduled_time": "14:00:00",
        "description": "Afternoon after lunch"
      },
      {
        "scheduled_time": "20:00:00",
        "description": "Evening before bed"
      }
    ]
  }'
```

### 5. Auto-Create Reminders

```bash
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

# For prescription ID 1
curl -X POST http://localhost:8000/api/prescriptions/1/create-reminders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reminder_type": "whatsapp"
  }'
```

### 6. Get Patient's Pending Reminders

```bash
TOKEN="patient_token"

curl -X GET http://localhost:8000/api/reminders/my-pending/ \
  -H "Authorization: Bearer $TOKEN"
```

### 7. Patient Confirms Dose Taken

```bash
TOKEN="patient_token"

curl -X POST http://localhost:8000/api/reminders/1/respond/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "response_type": "acknowledged",
    "message": "Took the medication with breakfast"
  }'
```

### 8. Get Adherence Report

```bash
TOKEN="doctor_token"

curl -X GET http://localhost:8000/api/patients/1/adherence-report/ \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "patient_id": 1,
#   "adherence_30_days": 95.5,
#   "adherence_7_days": 100.0,
#   "missed_doses_30_days": 2,
#   "active_prescriptions": 1
# }
```

---

## Testing

### Run Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.patients

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

### Celery Tasks

Check task status:

```bash
# In Python shell
python manage.py shell

from apps.reminders.tasks import send_scheduled_reminders
result = send_scheduled_reminders.delay()
print(result.get())
```

---

## Project Structure Explanation

```
dawatrack_hospital/
├── dawatrack/              # Main Django project
│   ├── settings.py        # Global configuration
│   ├── urls.py            # URL routing
│   ├── wsgi.py            # Production server
│   └── celery_app.py      # Celery configuration
│
├── apps/                   # Django applications
│   ├── users/             # Authentication & user management
│   ├── patients/          # Patient profiles
│   ├── prescriptions/     # Medication prescriptions
│   ├── reminders/         # SMS/WhatsApp reminders
│   ├── palliative_care/   # Palliative care module
│   ├── dashboards/        # Web dashboards
│   └── analytics/         # Reporting & analytics
│
├── templates/              # HTML templates
├── static/                 # CSS, JavaScript, images
├── ARCHITECTURE.md        # System design
└── DEPLOYMENT_AND_SECURITY.md  # Production guide
```

---

## Key Features Implementation

### 1. Automatic Reminder Scheduling

The system automatically:
- Creates reminders at scheduled times
- Sends SMS/WhatsApp via Africa's Talking
- Tracks delivery status
- Retries failed deliveries
- Creates alerts if doses are missed

### 2. Adherence Tracking

Tracks for each patient:
- Percentage of doses taken on time
- Missed dose alerts
- Trend analysis (7-day, 30-day)
- Notifications to doctors/nurses

### 3. Palliative Care Support

Special features for end-of-life patients:
- Daily check-ins
- Comfort medication scheduling
- Family notifications
- Multi-dose alerts
- Care team coordination

### 4. Role-Based Access

- **Patients**: See own medications only
- **Doctors**: Manage patients and prescriptions
- **Nurses**: Support care, track adherence
- **Admins**: System configuration and monitoring

### 5. Data Security

- End-to-end encryption
- Database encryption
- Audit logging of all changes
- Session management
- HIPAA-compliant

---

## Troubleshooting

### Cannot Connect to Africa's Talking

```python
# Check credentials in .env
AFRICA_TALKING_API_KEY=your-key
AFRICA_TALKING_USERNAME=your-username

# Test in Python shell
from apps.reminders.integrations.africa_talking import gateway
print(gateway.is_configured())  # Should be True

# Check if gateway can reach API
result = gateway.send_sms('+254712345678', 'Test message')
print(result)
```

### Celery Tasks Not Running

```bash
# Check if Redis is running
redis-cli ping  # Should return PONG

# Check Celery worker logs for errors
# In celery worker terminal, look for error messages

# Verify task is registered
celery -A dawatrack inspect active

# Check task queue
celery -A dawatrack inspect reserved
```

### Database Migration Errors

```bash
# Check current migrations
python manage.py showmigrations

# Rollback if needed
python manage.py migrate apps.patients 0001

# Check for circular dependencies
python manage.py check --deploy
```

---

## Next Steps

1. **Customize Email Templates**: Add hospital branding
2. **Configure Africa's Talking**: Set up production credentials
3. **Create Doctor Accounts**: Register doctors in admin
4. **Design Dashboards**: Build custom reporting views
5. **Patient Education**: Create welcome messages
6. **Staff Training**: Train on system usage
7. **Go Live**: Deploy to production

---

## Support Resources

- Django Documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- Celery: https://docs.celeryproject.org/
- Africa's Talking API: https://africastalking.com/
- Hospital IT Best Practices: https://www.hipaajournal.com/

---

## Quick Commands Reference

```bash
# Development server
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Database shell
python manage.py dbshell

# Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test

# Create superuser
python manage.py createsuperuser

# Backup database
mysqldump -u root dawatrack_dev > backup.sql

# Restore database
mysql -u root dawatrack_dev < backup.sql
```

---

**Last Updated**: February 9, 2024
**Status**: Ready for Development & Testing
