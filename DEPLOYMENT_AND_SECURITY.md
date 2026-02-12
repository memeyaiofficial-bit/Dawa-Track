# DawaTrack Hospital - Deployment & Security Guide

## 1. PRE-DEPLOYMENT CHECKLIST

### Security Hardening
- [ ] Change all default passwords and secret keys
- [ ] Set `DEBUG = False` in production settings
- [ ] Configure HTTPS/TLS for all traffic
- [ ] Set up firewall rules
- [ ] Enable CSRF protection
- [ ] Configure CORS properly
- [ ] Set secure cookie flags
- [ ] Enable HSTS headers
- [ ] Implement rate limiting
- [ ] Set up WAF (Web Application Firewall)

### Database Security
- [ ] Use strong MySQL password
- [ ] Enable MySQL encryption at rest
- [ ] Enable MySQL binary logging for audit trail
- [ ] Create database backups (daily)
- [ ] Test backup restoration procedure
- [ ] Set up automated backup to external storage (S3)
- [ ] Enable database connection encryption
- [ ] Restrict database access to app server only
- [ ] Create read-only replicas for reports

### Infrastructure
- [ ] Set up on dedicated server/VPS in healthcare-compliant cloud
- [ ] Enable server firewall
- [ ] Configure VPN for admin access
- [ ] Set up monitoring and alerting
- [ ] Enable server access logs
- [ ] Configure DDoS protection
- [ ] Set up load balancer with SSL termination
- [ ] Configure auto-scaling

### Application Level
- [ ] All dependencies updated to latest secure versions
- [ ] Code reviewed for vulnerabilities
- [ ] Dependency scanning (e.g., safety, PyUp)
- [ ] SAST scan (Static Application Security Testing)
- [ ] Hidden files and secrets removed
- [ ] Proper error handling (no stack traces in production)
- [ ] Logging configured without sensitive data

---

## 2. ENVIRONMENT SETUP

### Create Production Settings

```bash
# Copy example env to production env
cp .env.example .env

# Edit .env with production values
nano .env
```

### Critical Environment Variables

```bash
# Security
SECRET_KEY=generate-32-char-random-string-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (use managed database service)
DB_ENGINE=django.db.backends.mysql
DB_NAME=dawatrack_production
DB_USER=dawatrack_user
DB_PASSWORD=generate-strong-password
DB_HOST=mysql.yourdomain.com
DB_PORT=3306
ATOMIC_REQUESTS=True

# Redis (for Celery and caching)
REDIS_URL=redis://redis.yourdomain.com:6379/0
CELERY_BROKER_URL=redis://redis.yourdomain.com:6379/0
CELERY_RESULT_BACKEND=redis://redis.yourdomain.com:6379/0

# Email (for notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password

# Africa's Talking (SMS/WhatsApp)
AFRICA_TALKING_API_KEY=your-production-api-key
AFRICA_TALKING_USERNAME=DawaTrack

# Security Headers
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Monitoring
SENTRY_DSN=your-sentry-dsn-url
```

---

## 3. DATABASE SETUP & MIGRATION

### Create Database

```bash
# Connect to MySQL server as admin
mysql -u admin -p

# Create database and user
CREATE DATABASE dawatrack_production;
CREATE USER 'dawatrack_user'@'%' IDENTIFIED BY 'strong-password';
GRANT ALL PRIVILEGES ON dawatrack_production.* TO 'dawatrack_user'@'%';
FLUSH PRIVILEGES;
EXIT;
```

### Run Migrations

```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations
python manage.py migrate --database production

# Create superuser (admin account)
python manage.py createsuperuser

# Load initial data (templates, etc.)
python manage.py loaddata initial_data.json
```

### Database Indexes

```sql
-- Create performance indexes
CREATE INDEX idx_patient_doctor ON patients(assigned_doctor_id);
CREATE INDEX idx_prescription_patient ON prescriptions(patient_id);
CREATE INDEX idx_reminder_status ON reminders(status, scheduled_time);
CREATE INDEX idx_dose_log_status ON dose_logs(patient_id, status);
CREATE INDEX idx_user_email ON users(email);

-- Enable query logging for audit
SET GLOBAL general_log = 'ON';
```

---

## 4. CELERY & REDIS SETUP

### Redis Installation (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf

# Important settings:
# requirepass your-strong-password
# maxmemory 2gb
# maxmemory-policy allkeys-lru
# appendonly yes (for persistence)

# Restart Redis
sudo systemctl restart redis-server
```

### Celery Configuration

```bash
# Install Celery worker dependencies
pip install celery redis django-celery-beat django-celery-results

# Create Celery startup script
sudo nano /etc/systemd/system/celery.service
```

Content for celery.service:

```ini
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/dawatrack
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A dawatrack worker -l info --concurrency=4

[Install]
WantedBy=multi-user.target
```

```bash
# Create Celery Beat (scheduler) startup script
sudo nano /etc/systemd/system/celery-beat.service
```

Content for celery-beat.service:

```ini
[Unit]
Description=Celery Beat Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/dawatrack
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A dawatrack beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start services
sudo systemctl enable celery.service
sudo systemctl enable celery-beat.service
sudo systemctl start celery.service
sudo systemctl start celery-beat.service

# Check status
sudo systemctl status celery.service
sudo systemctl status celery-beat.service
```

---

## 5. WEB SERVER SETUP (Gunicorn + Nginx)

### Gunicorn Configuration

```bash
# Install Gunicorn
pip install gunicorn

# Create gunicorn config file
nano /path/to/dawatrack/gunicorn.conf.py
```

Content:

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
max_requests = 1000
max_requests_jitter = 100
timeout = 60
graceful_timeout = 30
keepalive = 5
worker_tmp_dir = "/dev/shm"
accesslog = "/var/log/dawatrack/gunicorn_access.log"
errorlog = "/var/log/dawatrack/gunicorn_error.log"
loglevel = "info"
```

### Nginx Configuration

```bash
# Install Nginx
sudo apt-get install nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/dawatrack
```

Content:

```nginx
upstream dawatrack_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'" always;

    # Logging
    access_log /var/log/nginx/dawatrack_access.log;
    error_log /var/log/nginx/dawatrack_error.log;

    # Client upload limit
    client_max_body_size 10M;

    location / {
        proxy_pass http://dawatrack_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static/ {
        alias /path/to/dawatrack/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /path/to/dawatrack/media/;
        expires 7d;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/dawatrack /etc/nginx/sites-enabled/

# Test Nginx config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

---

## 6. MONITORING & LOGGING

### Application Monitoring

```bash
# Install monitoring tools
pip install sentry-sdk prometheus-client

# Configure Sentry in settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False,
)
```

### Centralized Logging

```bash
# Install ELK stack or use managed service
pip install python-json-logger

# Logs to /var/log/dawatrack/dawatrack.log
```

### Health Checks

```python
# Add health check endpoint
# urls.py
path('health/', views.health_check, name='health_check'),

# views.py
def health_check(request):
    return JsonResponse({'status': 'healthy'})
```

---

## 7. BACKUP STRATEGY

### Database Backups

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups/mysql"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/dawatrack_$TIMESTAMP.sql.gz"

mysqldump -u dawatrack_user -p$DB_PASSWORD dawatrack_production | gzip > $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE s3://your-backup-bucket/

# Keep only 30 days of backups
find $BACKUP_DIR -mtime +30 -delete
```

### Application Code Backups

```bash
# GitHub backup
git push origin main

# Plus automated snapshots of server disks
```

### Disaster Recovery Plan

- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 1 hour
- Test restore procedure quarterly

---

## 8. HEALTHCARE COMPLIANCE

### HIPAA/GDPR Compliance

#### Data Privacy
- [ ] Patient consent management
- [ ] Data encryption (AES-256)
- [ ] Access controls by role
- [ ] Audit logging of all data access
- [ ] Data anonymization for analytics

#### Required Audit Information
- Who accessed what data
- When they accessed it
- What changes they made
- From what IP address

#### Retention Policies
```python
# Delete old reminders after 90 days
# Keep audit logs for 7 years
# Allow patient data export on request
```

### Data Protection Best Practices

```python
# In models:
- Encrypt sensitive fields (phone numbers, IDs)
- Use Django-encrypted-model-fields
- Hash passwords (Django handles this)
- Avoid storing credit card info

# In views:
- Never log passwords or tokens
- Validate and sanitize all inputs
- Use parameterized queries (Django ORM does this)
- Implement rate limiting on login
```

---

## 9. PERFORMANCE OPTIMIZATION

### Caching Strategy

```python
# Cache patient adherence reports (5 minutes)
# Cache user permissions (1 hour)
# Cache prescription templates (1 day)
```

### Database Optimization

```sql
-- Analyze slow queries
EXPLAIN ANALYZE SELECT * FROM prescriptions WHERE patient_id = 1;

-- Create composite indexes for common filters
CREATE INDEX idx_prescription_status ON prescriptions(patient_id, is_active, end_date);
```

### API Optimization

```python
# Use select_related() for foreign keys
# Use prefetch_related() for reverse relations
# Implement pagination (20 items per page default)
# Use caching for expensive operations
```

---

## 10. INCIDENT RESPONSE

### Security Incident Response Plan

1. **Detect**: Automated alerts via Sentry, logs, monitoring
2. **Assess**: Determine scope and data affected
3. **Contain**: Disable compromised accounts, revoke sessions
4. **Eradicate**: Patch vulnerabilities, update passwords
5. **Recover**: Restore from clean backups
6. **Review**: Post-incident analysis, update procedures

### Contact Escalation Chain

1. On-call developer (alert via PagerDuty)
2. Security team lead
3. Hospital IT director
4. Hospital legal/compliance
5. Regulatory authorities (if required)

---

## 11. TESTING CHECKLIST

### Functional Testing
- [ ] User registration and authentication
- [ ] Prescription creation and editing
- [ ] Reminder scheduling and delivery
- [ ] Adherence tracking
- [ ] Doctor/patient dashboards
- [ ] Report generation

### Security Testing
- [ ] SQL injection tests
- [ ] XSS prevention tests
- [ ] CSRF token validation
- [ ] Authentication/authorization bypass attempts
- [ ] Rate limiting enforcement
- [ ] Sensitive data in logs

### Load Testing

```bash
# Load test with Locust
pip install locust

# Run: locust -f locustfile.py --host=https://yourdomain.com
```

### Penetration Testing
- Professional pen test quarterly
- Bug bounty program
- Security audit annually

---

## 12. ONGOING MAINTENANCE

### Weekly Tasks
- Check server disk space
- Review error logs
- Monitor Celery/Redis

### Monthly Tasks
- Update dependencies (security patches)
- Review access logs for anomalies
- Test backup restoration
- Generate compliance reports

### Quarterly Tasks
- Update SSL certificates
- Security audit
- Performance review
- Disaster recovery test

### Annually
- Full security audit
- Penetration testing
- Compliance audit
- Architecture review

---

## 13. DEPLOYMENT COMMANDS

### Full Deployment

```bash
#!/bin/bash
set -e

# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx
sudo systemctl restart celery
sudo systemctl restart celery-beat

# Run tests
python manage.py test

echo "Deployment successful!"
```

### Rollback Procedure

```bash
#!/bin/bash

# Revert to previous commit
git checkout previous-tag

# Re-run deployment
bash deploy.sh
```

---

## 14. TROUBLESHOOTING

### Common Issues

**High CPU from Celery**
- Reduce worker concurrency
- Check for task deadlocks
- Monitor task queue size

**Database Connection Errors**
- Check MySQL is running
- Verify credentials
- Check firewall rules

**Reminders Not Sending**
- Check Africa's Talking credentials
- Verify patient phone numbers
- Check patient consent settings
- Review Celery task logs

**High Memory Usage**
- Enable Redis memory limits
- Reduce cache TTL
- Check for memory leaks
- Use Django debug toolbar in dev

---

## 15. RESOURCES

- Django Security: https://docs.djangoproject.com/en/4.2/topics/security/
- HIPAA Compliance: https://www.healthitgov.org/
- GDPR Compliance: https://gdpr-info.eu/
- Africa's Talking API: https://africastalking.com/
- Django REST Framework: https://www.django-rest-framework.org/
