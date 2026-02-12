# DawaTrack Hospital - System Architecture & Design

## 1. SYSTEM ARCHITECTURE OVERVIEW

### High-Level Architecture Diagram (Text Representation)

```
┌─────────────────────────────────────────────────────────────────┐
│                        DAWATRACK HOSPITAL                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Patients   │  │   Doctors    │  │   Admins     │          │
│  │   (Web UI)   │  │   (Web UI)   │  │   (Web UI)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                  │
│                            │                                     │
│                    ┌───────▼────────┐                            │
│                    │  Django REST   │                            │
│                    │   API Server   │                            │
│                    │  (Port 8000)   │                            │
│                    └───────┬────────┘                            │
│                            │                                     │
│         ┌──────────────────┼──────────────────┐                 │
│         │                  │                  │                 │
│    ┌────▼─────┐      ┌─────▼──────┐    ┌─────▼──────┐         │
│    │  MySQL   │      │   Redis    │    │   Celery   │         │
│    │ Database │      │   Cache    │    │   Tasks    │         │
│    └──────────┘      └────────────┘    └─────┬──────┘         │
│                                               │                 │
│                                ┌──────────────┴─────────────┐  │
│                                │                            │  │
│                         ┌──────▼──────┐        ┌───────────▼──┐│
│                         │  Scheduler  │        │ Message      ││
│                         │  (Background)│       │ Queue        ││
│                         └──────┬───────┘       └──────────────┘│
│                                │                                │
│         ┌──────────────────────┼──────────────────────┐        │
│         │                      │                      │        │
│    ┌────▼──────┐         ┌─────▼──────┐         ┌────▼─────┐  │
│    │ WhatsApp  │         │    SMS     │         │   Email  │  │
│    │ (Africa's │         │ (Africa's  │         │ (SMTP)   │  │
│    │ Talking)  │         │  Talking)  │         │          │  │
│    └───────────┘         └────────────┘         └──────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Web Server**: Django application handling web requests
2. **API Layer**: RESTful APIs for mobile/external integrations
3. **Database**: MySQL for persistent data storage
4. **Cache**: Redis for session management & rate limiting
5. **Task Queue**: Celery for asynchronous reminder jobs
6. **Message Gateway**: Africa's Talking for SMS/WhatsApp delivery
7. **Scheduler**: Background process for periodic checks

---

## 2. DATABASE SCHEMA

### Core Tables & Relationships

```
USERS (User Roles)
├── id (PK)
├── username (UNIQUE)
├── email (UNIQUE)
├── password_hash
├── role (ENUM: admin, doctor, nurse, patient)
├── phone_number (for SMS/WhatsApp)
├── is_active
├── created_at
└── updated_at

PATIENTS
├── id (PK)
├── user_id (FK → USERS)
├── date_of_birth
├── gender
├── blood_type
├── care_category (ENUM: normal, palliative)
├── emergency_contact
├── emergency_phone
├── medical_history (TEXT)
├── allergies (TEXT)
├── assigned_doctor_id (FK → USERS)
├── assigned_nurse_id (FK → USERS, nullable)
├── created_at
└── updated_at

DOCTORS
├── id (PK)
├── user_id (FK → USERS)
├── specialty
├── license_number (UNIQUE)
├── department
├── phone_number
├── available_hours (JSON)
├── created_at
└── updated_at

PRESCRIPTIONS
├── id (PK)
├── patient_id (FK → PATIENTS)
├── doctor_id (FK → USERS)
├── drug_name
├── dosage (e.g., "500mg")
├── frequency (ENUM: once_daily, twice_daily, thrice_daily, four_times_daily, custom)
├── custom_frequency_description (nullable, for complex schedules)
├── duration_days
├── start_date (DATE)
├── end_date (DATE)
├── notes
├── is_active
├── created_at
├── updated_at

PRESCRIPTION_SCHEDULES (For complex dosing patterns)
├── id (PK)
├── prescription_id (FK → PRESCRIPTIONS)
├── scheduled_time (TIME, e.g., "09:00:00")
├── day_index (0-6 for recurring schedules, nullable)
├── description (e.g., "Morning with breakfast")

REMINDERS
├── id (PK)
├── prescription_id (FK → PRESCRIPTIONS)
├── patient_id (FK → PATIENTS)
├── scheduled_time (DATETIME)
├── reminder_type (ENUM: whatsapp, sms, email)
├── status (ENUM: pending, sent, failed, acknowledged)
├── message_content
├── sent_at (nullable)
├── delivery_status (for tracking)
├── external_message_id (from Africa's Talking)
├── retry_count
├── created_at
└── updated_at

DOSE_LOGS (Adherence Tracking)
├── id (PK)
├── prescription_id (FK → PRESCRIPTIONS)
├── patient_id (FK → PATIENTS)
├── scheduled_time (DATETIME)
├── actual_intake_time (DATETIME, nullable)
├── status (ENUM: pending, taken, missed, skipped)
├── notes (why missed if applicable)
├── confirmed_by (FK → USERS, nullable, for nurse verification)
├── created_at
└── updated_at

PALLIATIVE_CARE_PLANS
├── id (PK)
├── patient_id (FK → PATIENTS)
├── doctor_id (FK → USERS)
├── diagnosis
├── goals_of_care (TEXT)
├── comfort_measures (JSON)
├── check_in_frequency (ENUM: daily, twice_daily, every_other_day)
├── alert_threshold (e.g., 2 missed doses = alert)
├── start_date
├── notes
├── is_active
├── created_at
└── updated_at

AUDIT_LOGS
├── id (PK)
├── user_id (FK → USERS, who performed action)
├── action_type (ENUM: created, updated, deleted, viewed)
├── model_name (ENUM: prescription, patient, reminder)
├── record_id
├── old_values (JSON, for changes)
├── new_values (JSON, for changes)
├── ip_address
├── created_at

NOTIFICATIONS
├── id (PK)
├── user_id (FK → USERS)
├── notification_type (ENUM: missed_dose_alert, low_adherence, system_alert)
├── title
├── message
├── is_read
├── related_patient_id (FK → PATIENTS, nullable)
├── related_prescription_id (FK → PRESCRIPTIONS, nullable)
├── created_at
└── read_at (nullable)
```

### Key Relationships

- **Users** → **Patients** (One-to-One): User account linked to patient profile
- **Users** → **Doctors** (One-to-One): User account linked to doctor profile
- **Patients** → **Prescriptions** (One-to-Many): One patient, multiple prescriptions
- **Prescriptions** → **Reminders** (One-to-Many): One prescription generates multiple reminders
- **Prescriptions** → **Dose_Logs** (One-to-Many): Track each dose instance
- **Patients** → **Palliative_Care_Plans** (One-to-One): Special care plan for palliative patients

---

## 3. DJANGO PROJECT STRUCTURE

```
dawatrack_hospital/
├── manage.py
├── requirements.txt
├── .env (environment variables)
├── .gitignore
├── README.md
│
├── dawatrack/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py (common settings)
│       ├── development.py
│       ├── production.py
│       └── testing.py
│
├── apps/
│   ├── users/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── forms.py
│   │   ├── permissions.py
│   │   └── templates/
│   │
│   ├── patients/
│   │   ├── models.py
│   │   ├── views.py (DRF + Django views)
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── forms.py
│   │   └── templates/
│   │       ├── patient_dashboard.html
│   │       ├── patient_profile.html
│   │       └── medication_schedule.html
│   │
│   ├── prescriptions/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── forms.py
│   │   └── templates/
│   │       ├── prescription_list.html
│   │       ├── add_prescription.html
│   │       └── prescription_detail.html
│   │
│   ├── reminders/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── tasks.py (Celery tasks)
│   │   ├── scheduler.py
│   │   └── integrations/
│   │       ├── africa_talking.py
│   │       └── email_service.py
│   │
│   ├── palliative_care/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── templates/
│   │
│   ├── dashboards/
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── templates/
│   │       ├── doctor_dashboard.html
│   │       ├── admin_dashboard.html
│   │       └── nurse_dashboard.html
│   │
│   ├── analytics/
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── utils.py (adherence calculations)
│   │   └── templates/
│   │       ├── adherence_report.html
│   │       └── missed_dose_report.html
│   │
│   ├── audit/
│   │   ├── models.py
│   │   ├── middleware.py
│   │   ├── signals.py
│   │   └── utils.py
│   │
│   └── api/
│       ├── views.py
│       ├── serializers.py
│       └── urls.py
│
├── static/
│   ├── css/
│   │   ├── bootstrap.css
│   │   ├── style.css
│   │   └── dashboard.css
│   ├── js/
│   │   ├── chart.min.js
│   │   ├── main.js
│   │   └── notifications.js
│   └── images/
│
├── templates/
│   ├── base.html
│   ├── navbar.html
│   ├── sidebar.html
│   ├── login.html
│   ├── registration.html
│   └── 404.html
│
├── media/ (User uploads)
│
├── logs/
│
├── utils/
│   ├── decorators.py
│   ├── helpers.py
│   └── validators.py
│
├── celery_config.py
├── docker-compose.yml
├── Dockerfile
└── deployment/
    ├── nginx.conf
    ├── gunicorn.conf.py
    ├── .env.example
    └── README.md
```

---

## 4. SECURITY & COMPLIANCE CONSIDERATIONS

### Healthcare Data Protection
- **Encryption**: All patient data encrypted at rest and in transit (HTTPS/TLS)
- **Authentication**: Multi-factor authentication (MFA) for doctors/admins
- **Role-Based Access Control (RBAC)**: Patients see only their data
- **Audit Logging**: All modifications logged with timestamps and user IDs
- **Data Retention**: Compliance with local healthcare regulations (HIPAA-equivalent)
- **Password Policy**: Strong requirements, expiration policies

### Privacy Best Practices
- Minimal data collection (only what's needed)
- Consent management for reminders
- Right to be forgotten (patient data deletion)
- Secure communication channels
- No unsecured messaging in logs

---

## 5. KEY DESIGN DECISIONS

### Why Celery + Redis for Reminders?
- **Scale**: Handle thousands of patients with reliable scheduling
- **Resilience**: Failed reminders are retried automatically
- **Flexibility**: Easy to add new reminder channels (voice calls, push notifications)
- **Separation of Concerns**: API server stays responsive

### Why MySQL?
- ACID compliance ensures prescription data integrity
- Strong relational structure fits healthcare data model
- Robust backup/recovery tools
- Wide support in hospitals

### Frontend Architecture
- **Template-First UI**: For quick deployment (server-rendered)
- **Charts**: Chart.js for adherence dashboards
- **AJAX**: Minimal client-size interactive updates
- **Mobile Responsive**: Works on phones (patients' primary device)

---

## 6. INTEGRATION POINTS

### Africa's Talking Integration
- **SMS**: Reminder notifications
- **WhatsApp**: Interactive reminders (with button responses)
- **Credentials**: Stored securely in environment variables
- **Webhook**: Handle delivery confirmations and responses

### External Systems
- **Patient Registration**: Import from hospital's existing system (API)
- **Doctor Database**: Sync specialties and schedules
- **Lab Results**: Integration point for clinical data

---

## Next Steps

1. Set up Django project with proper structure
2. Create models with migrations
3. Implement authentication & permissions
4. Build API endpoints
5. Integrate Celery for reminders
6. Connect Africa's Talking
7. Create dashboards
8. Implement analytics
9. Set up deployment infrastructure

