# Purchase Management System

A Django-based procurement management system for handling purchase requests, supplier records, RFQs, quotations, approvals, supplier awarding, and PDF/email workflows. The project is structured as a practical business application suitable for portfolio review, demonstrating role-based procurement operations, clean data modeling, and end-to-end purchasing workflows.

## Key Features

- Role-based access for requesters, approvers, purchasing officers, and administrators
- Custom email-based user model with profile and activity tracking
- Purchase request creation with material line items, priorities, departments, and approval states
- Approval and rejection workflow with approval history
- Supplier and raw material management
- Supplier-material availability and lead-time mapping
- RFQ tracking and supplier email workflow
- Quotation creation, quotation comparison, and supplier recommendation scoring
- Supplier awarding workflow
- Dashboard statistics and monthly request metrics
- Professional PDF export for purchase requests
- Responsive Bootstrap-based templates with shared static assets

## Tech Stack

- Python
- Django 4.2
- SQLite for local development
- Django templates
- Bootstrap 5 via crispy-bootstrap5
- Chart.js
- ReportLab for PDF generation
- python-dotenv for environment configuration

## Project Structure

```text
purchase_system/
├── accounts/              # Custom user model, roles, dashboard, activity logs
├── purchasing/            # Purchase requests, items, approvals, RFQs, PDFs
├── suppliers/             # Suppliers, materials, prices, quotations
├── purchase_system/       # Project settings, URLs, WSGI, context processors
├── templates/             # Shared and app-specific Django templates
├── static/                # CSS and JavaScript assets
├── manage.py
├── requirements.txt
├── .env.example
├── PROJECT_SUMMARY.md
└── README.md
```

## Main Modules

### Accounts

Handles authentication and user management using a custom `User` model with email login. Roles include requester, approver, purchasing officer, and admin. The module also stores user profiles and activity logs.

### Purchasing

Manages purchase requests from draft through approval, RFQ, quotation comparison, and award. It includes request items, RFQ logs, approval history, supplier recommendation scoring, and PDF generation.

### Suppliers

Maintains suppliers, raw materials, supplier-material availability, reference prices, lead times, quotations, and quotation line items.

## Important Workflows

1. A requester creates a purchase request and adds requested materials.
2. The request is submitted for approval.
3. An approver or authorized purchasing role approves or rejects the request.
4. A purchasing officer sends RFQs to matching suppliers.
5. Supplier quotations are entered and compared.
6. The system recommends a supplier using price, delivery time, and rating.
7. An authorized user awards the request to the selected supplier.
8. Purchase request PDFs can be exported or emailed.

## Installation

Clone the repository and enter the project directory:

```bash
git clone <your-repository-url>
cd purchase_system
```

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local environment file:

```bash
copy .env.example .env
```

Update `.env` with your local values. For development, the default console email backend is enough and does not send real email.

Run migrations:

```bash
python manage.py migrate
```

Create an admin user:

```bash
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

Open the app at:

```text
http://127.0.0.1:8000/
```

## Environment Variables

The project reads configuration from `.env`.

```env
DJANGO_SECRET_KEY=replace-with-a-secure-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@example.com
```

Never commit `.env`, database files, email passwords, API keys, or private credentials.

## Demo Users

No demo users are committed with this repository. Create users through the Django admin or the in-app user management screen after creating a superuser.

Suggested roles for testing:

- `requester`: creates and tracks purchase requests
- `approver`: approves or rejects pending requests
- `purchasing_officer`: manages RFQs, quotations, and supplier awarding
- `admin`: manages users and all system data

## Screenshots / Demo

Add screenshots here after running the project locally:

- Login screen
- Dashboard
- Purchase request detail
- Supplier list
- Quotation comparison
- PDF export example

## Business Value

This system models a real procurement workflow for organizations that need better control over purchase requests, supplier communication, and approval visibility. It reduces manual tracking, centralizes supplier and quotation data, improves auditability through activity and approval logs, and supports more objective supplier selection using measurable criteria.

## Future Improvements

- Add automated tests for role permissions and procurement workflows
- Add REST API endpoints for integration with ERP or inventory systems
- Add file attachments for quotations and purchase requests
- Add notification queues and asynchronous email delivery
- Add PostgreSQL production settings
- Add Docker and deployment configuration
- Add richer reporting for spend analysis and supplier performance
- Add seed data or fixtures for a public demo environment

## Repository Notes

- Local SQLite databases are ignored and should not be committed.
- `.env` is ignored; use `.env.example` as the template.
- The default email backend prints messages to the console for safe local testing.
- Run `python manage.py check` before publishing or deploying.
