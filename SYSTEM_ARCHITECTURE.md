# SYSTEM ARCHITECTURE

## Detailed Architecture Documentation for Purchase Management System

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Layers](#2-architecture-layers)
3. [Component Diagram](#3-component-diagram)
4. [Data Flow](#4-data-flow)
5. [Database Schema](#5-database-schema)
6. [Model Relationships](#6-model-relationships)
7. [Request Lifecycle](#7-request-lifecycle)
8. [Service Layer Architecture](#8-service-layer-architecture)
9. [Security Architecture](#9-security-architecture)
10. [Deployment Architecture](#10-deployment-architecture)
11. [Performance Considerations](#11-performance-considerations)
12. [Scalability](#12-scalability)

---

## 1. System Overview

The Purchase Management System follows a **Monolithic Django Architecture** with clear separation of concerns through Django's app structure. The system is divided into three main Django apps, each responsible for a distinct domain.

### Technology Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, Tailwind CSS, JavaScript, Chart.js |
| Backend | Django 4.2 (Python 3.8+) |
| Database | SQLite (Development) / PostgreSQL (Production) |
| PDF Generation | ReportLab |
| Email | Django SMTP (Gmail) |
| Authentication | Django Authentication System |
| Session | Django Session Framework |

---

## 2. Architecture Layers

```
+-----------------------------------------------------------------+
|                    PRESENTATION LAYER                           |
|  +--------------+  +--------------+  +------------------------+ |
|  |  HTML Views  |  |   Tailwind   |  | JavaScript/Chart.js   | |
|  | (Templates)  |  |  CSS Theme   |  | (Interactive UI)     | |
|  +------+-------+  +------+-------+  +----------+-----------+ |
|         |                 |                      |             |
+---------+-----------------+----------------------+-------------+
|         |                 |                      |             |
|         v                 v                      v             |
|  +-----------------------------------------------------------+ |
|  |                  APPLICATION LAYER                        | |
|  |  +------------+  +------------+  +------------+          | |
|  |  |  accounts  |  | purchasing |  | suppliers  |          | |
|  |  |    App     |  |    App     |  |    App     |          | |
|  |  +-----+------+  +-----+------+  +-----+------+          | |
|  +-------+-------------+--------------+----------------------+ |
+---------+-------------+--------------+------------------------+
          |             |              |
          v             v              v
+-----------------------------------------------------------------+
|                     SERVICE LAYER                               |
|  +-----------------------------------------------------------+ |
|  |  purchasing/services.py                                    | |
|  |  - PDF Generation (generate_purchase_pdf)                 | |
|  |  - Email/RFQ (send_rfq)                                  | |
|  |  - Best Supplier Algorithm (suggest_best_supplier)       | |
|  +-----------------------------------------------------------+ |
+-----------------------------------------------------------------+
|                        DATA LAYER                               |
|  +-----------------------------------------------------------+ |
|  |         Database (SQLite / PostgreSQL)                    | |
|  +-----------------------------------------------------------+ |
+-----------------------------------------------------------------+
```

---

## 3. Component Diagram

```
+------------------------------------------------------------------+
|                       DJANGO PROJECT                             |
|                                                                  |
|  +----------------+      +-------------------+     +-----------+ |
|  |   accounts/    |<---->|   purchasing/     |<---->| suppliers/| |
|  +----------------+      +-------------------+     +-----------+ |
|        |                         |                       |       |
|        v                         v                       v       |
|  +----------------+      +-------------------+     +-----------+ |
|  | models.py:     |      | models.py:        |     | models.py:| |
|  | - User (custom)|      | - PurchaseRequest |     | - Supplier| |
|  | - UserProfile  |      | - PurchaseItem    |     | - Material| |
|  | - ActivityLog  |      | - RFQLog          |     | - Quotation| |
|  |                |      | - ApprovalHistory |     | - QuotationItem|
|  | views.py:      |      | views.py:         |     | views.py: | |
|  | - LoginView    |      | - RequestListView |     | - SupplierList|
|  | - DashboardView|      | - RequestCreate   |     | - MaterialList|
|  | - UserListView |      | - RequestDetail   |     | - QuotationList|
|  | - ProfileView  |      | - ...             |     | - ...      | |
|  +----------------+      +-------------------+     +-----------+ |
|                           |         |                             |
|                           v         v                             |
|                    +-----------+ +----------+                    |
|                    | services  | |  admin   |                    |
|                    |  .py      | |  .py     |                    |
|                    +-----------+ +----------+                    |
+------------------------------------------------------------------+
```

---

## 4. Data Flow

### 4.1 Request/Response Flow

```
User Request
     |
     v
URL Dispatcher (urls.py)
     |
     v
Middleware Pipeline
  - SecurityMiddleware
  - SessionMiddleware
  - AuthenticationMiddleware
  - MessageMiddleware
  - CsrfViewMiddleware
  - CommonMiddleware
     |
     v
View Function/Class (views.py)
  - Authentication Check
  - Permission Check
  - Business Logic
  - Service Layer calls (services.py)
  - Database Queries (ORM)
     |
     v
Template Rendering (templates/)
     |
     v
HTTP Response (HTML/JSON/PDF)
```

### 4.2 Authentication Flow

```
User visits /login/
  -> POST credentials (email + password)
  -> Django Authenticate: lookup by email, verify password hash
  -> If valid: create session, redirect to /dashboard/
  -> If invalid: return form errors, stay on login page
```

### 4.3 PDF Generation Flow

```
User clicks "Download PDF"
  -> RequestDetailView (GET /purchasing/<id>/pdf/)
  -> generate_purchase_pdf(request_id) in services.py
  -> Fetch PurchaseRequest with related items
  -> Create ReportLab Canvas:
     - Header (system name + logo placeholder)
     - Request info section
     - Materials table
     - Approval status section
     - Notes section
     - Signature section
  -> Build PDF in memory (BytesIO)
  -> Return HttpResponse (Content-Type: application/pdf)
```

### 4.4 RFQ Email Flow

```
User clicks "Send RFQ"
  -> send_rfq(request_id) in services.py
  -> Get PurchaseRequest with items and materials
  -> For each material: find linked suppliers
  -> Deduplicate suppliers
  -> For each supplier:
     - Build HTML email template
     - Send via Django EmailMultiAlternatives
     - Create RFQLog entry (success/fail)
  -> If at least one email sent: update PR status to 'rfq_sent'
  -> Return messages
```

---

## 5. Database Schema (ER Diagram)

```
+------------------+       +----------------------+       +------------------+
|      User        |       |   PurchaseRequest    |       |    Supplier      |
+------------------+       +----------------------+       +------------------+
| PK: id           |       | PK: id               |       | PK: id           |
| email (unique)   |<------| FK: created_by       |       | name             |
| password         |       | FK: approved_by      |       | email            |
| full_name        |       | FK: rejected_by      |       | phone            |
| role             |       | FK: awarded_supplier |<------| rating           |
| is_active        |       | request_number(uniq) |       | address          |
| date_joined      |       | title                |       | created_at       |
+--------+---------+       | description          |       +--------+---------+
         |                 | status               |                |
         v                 | notes                |                |
+------------------+       | created_at           |                |
|   UserProfile    |       | updated_at           |                |
+------------------+       +----------+-----------+                |
| PK: id           |                  |                            |
| FK: user (1:1)   |                  | 1                          |
| avatar           |                  |                            |
| phone            |                  v                            |
| department       |       +----------------------+                |
+------------------+       |    PurchaseItem      |                |
                           +----------------------+                |
+------------------+       | PK: id               |                |
|   ActivityLog    |       | FK: purchase_request |                |
+------------------+       | FK: material         |                |
| PK: id           |       | quantity             |                |
| FK: user         |       | unit_price           |                |
| action           |       | total_price          |                |
| entity_type      |       +----------------------+                |
| entity_id        |                                               |
| details (JSON)   |       +----------------------+                |
| timestamp        |       |       Material       |                |
+------------------+       +----------------------+                |
                           | PK: id               |                |
+------------------+       | name                 |                |
|  ApprovalHistory |       | category             |                |
+------------------+       | unit                 |                |
| PK: id           |       | description          |                |
| FK: request      |       +----------+-----------+                |
| FK: action_by    |                  |                            |
| action           |                  v                            |
| reason           |       +----------------------+                |
| timestamp        |       |SupplierMaterialPrice |                |
+------------------+       +----------------------+                |
                           | PK: id               |                |
+------------------+       | FK: supplier         |<---------------+
|     RFQLog       |       | FK: material         |<---------------+
+------------------+       | price                |
| PK: id           |       | lead_time_days       |
| FK: request      |       +----------------------+
| FK: supplier     |
| FK: sent_by      |       +----------------------+
| email_to         |       |     Quotation        |
| status           |       +----------------------+
| sent_at          |       | PK: id               |
+------------------+       | FK: supplier         |<---------------+
                           | FK: purchase_request |
                           | notes                |
                           | submitted_at         |
                           +----------+-----------+
                                      |
                                      v
                           +----------------------+
                           |   QuotationItem      |
                           +----------------------+
                           | PK: id               |
                           | FK: quotation        |
                           | FK: material         |
                           | quantity             |
                           | unit_price           |
                           | total_price          |
                           | delivery_days        |
                           +----------------------+
```

---

## 6. Model Relationships Summary

| Relationship | Type | Description |
|---|---|---|
| User -> PurchaseRequest (created_by) | 1:N | One user creates many requests |
| User -> PurchaseRequest (approved_by) | 1:N | One user approves many requests |
| User -> PurchaseRequest (rejected_by) | 1:N | One user rejects many requests |
| PurchaseRequest -> PurchaseItem | 1:N | One request has many items |
| PurchaseRequest -> ApprovalHistory | 1:N | One request has many approval actions |
| PurchaseRequest -> RFQLog | 1:N | One request has many RFQ logs |
| PurchaseRequest -> Quotation | 1:N | One request can receive many quotations |
| PurchaseRequest -> Supplier (awarded) | N:1 | Many requests awarded to same supplier |
| Material -> PurchaseItem | 1:N | One material appears in many request items |
| Material -> SupplierMaterialPrice | 1:N | One material has many supplier prices |
| Supplier -> SupplierMaterialPrice | 1:N | One supplier offers prices for many materials |
| Supplier -> Quotation | 1:N | One supplier submits many quotations |
| User -> ActivityLog | 1:N | One user generates many activity logs |
| User -> UserProfile | 1:1 | Each user has one profile |

---

## 7. Request Lifecycle

### 7.1 State Machine

```
                    +-------------+
                    |    Draft    |
                    +------+------+
                           | Submit
                           v
                 +-------------------+
            +----| Pending Approval  |<----+
            |    +--------+----------+     |
            |             |                |
            |      +------+------+         |
            |      |             |         |
            v      v             v         |
      +---------+           +--------------+--+
      | Approved |           |   Rejected     |
      +----+----+           +-----------------+
           | Send RFQ
           v
      +----------+
      | RFQ Sent |
      +----+-----+
           | Award
           v
      +----------+
      | Awarded  |
      +----------+
```

### 7.2 Permission Guards

| Transition | Allowed Roles | Method |
|---|---|---|
| Draft -> Pending Approval | Requester, Admin, PO | `submit_request()` |
| Pending Approval -> Approved | Approver, Admin | `approve_request()` |
| Pending Approval -> Rejected | Approver, Admin | `reject_request()` |
| Approved -> RFQ Sent | PO, Admin | `send_rfq()` |
| RFQ Sent -> Awarded | PO, Admin | `award_supplier()` |

---

## 8. Service Layer Architecture

### 8.1 services.py Module

```
purchasing/services.py
  - generate_purchase_pdf(request_id)
  - send_rfq(request_id, request)
  - suggest_best_supplier(request_id)
```

### 8.2 Best Supplier Algorithm

```
Weights:
  - Price:           50% (lower is better)
  - Delivery Days:   30% (fewer is better)
  - Supplier Rating: 20% (higher is better)

Normalization:
  value_norm = (value - min) / (max - min)

Score Formula:
  score = (price_norm x 0.5) + (delivery_norm x 0.3) - (rating_norm x 0.2)

Selection:
  Supplier with LOWEST score wins
```

---

## 9. Security Architecture

| Security Layer | Implementation |
|---|---|
| Authentication | Custom User model (email as username), session-based, PBKDF2 hashing |
| Authorization | Role-based (User.role), @user_passes_test decorators |
| CSRF | Token required on all POST forms, CSRF middleware |
| XSS | Django template auto-escaping |
| SQL Injection | Django ORM, no raw SQL |
| Clickjacking | XFrameOptionsMiddleware |

### Middleware Stack

```
SecurityMiddleware
SessionMiddleware
CommonMiddleware
CsrfViewMiddleware
AuthenticationMiddleware
MessageMiddleware
XFrameOptionsMiddleware
```

---

## 10. Deployment Architecture

### Development Environment

```
+----------------------------------------+
|         Local Machine                   |
|  +-----------------------------------+ |
|  | Django Development Server         | |
|  | (runserver, Port: 8000)          | |
|  +---------------+-------------------+ |
|                  |                     |
|  +---------------v-------------------+ |
|  | SQLite Database (db.sqlite3)     | |
|  +-----------------------------------+ |
+----------------------------------------+
```

### Production Environment

```
              +---------------------+
              | Nginx Web Server    |
              | - Static files      |
              | - Reverse proxy     |
              +---------+-----------+
                        |
              +---------v-----------+
              | Gunicorn WSGI       |
              | - Django (wsgi.py) |
              | - Workers: 4       |
              +---------+-----------+
                        |
              +---------v-----------+
              | PostgreSQL Database |
              | - Production data   |
              +---------------------+
```

### Environment Variables

```python
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')
DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.sqlite3')
DB_NAME = os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
```

---

## 11. Performance Considerations

### 11.1 Query Optimization

```python
# Use select_related for ForeignKey relationships
request = PurchaseRequest.objects.select_related(
    'created_by', 'approved_by', 'awarded_supplier'
).get(id=request_id)

# Use prefetch_related for reverse relationships
request = PurchaseRequest.objects.prefetch_related(
    'items__material', 'approval_history__action_by'
).get(id=request_id)
```

### 11.2 Indexed Fields

| Field | Index Type |
|---|---|
| request_number | Unique + Indexed |
| status | Indexed |
| created_by | Indexed |
| created_at | Indexed |

---

## 12. Scalability

### Vertical Scaling
- Upgrade server CPU/RAM
- Switch to SSD storage
- Database connection pooling (PgBouncer)

### Horizontal Scaling (Future)
- Multiple Gunicorn workers per server
- Load balancing across servers
- Database read replicas
- Static file CDN (CloudFront, CloudFlare)

### Database Migration Path
```
SQLite  ---->  PostgreSQL  ---->  PostgreSQL + Read Replicas
(Dev)           (Prod)               (Scale)
```

---

## Appendix A: URL Routing Map

```
Root: /
  /login/                       [accounts.views.CustomLoginView]
  /logout/                      [django.contrib.auth.views.LogoutView]
  /dashboard/                   [accounts.views.DashboardView]
  /profile/                     [accounts.views.ProfileView]
  /users/                       [accounts.views.UserListView]
    /users/create/              [accounts.views.UserCreateView]
    /users/<id>/update/         [accounts.views.UserUpdateView]
    /users/<id>/delete/         [accounts.views.UserDeleteView]
  /activity/                    [accounts.views.ActivityLogView]

  /purchasing/                  [purchasing.views.RequestListView]
    /purchasing/create/         [purchasing.views.RequestCreateView]
    /purchasing/<id>/           [purchasing.views.RequestDetailView]
    /purchasing/<id>/update/    [purchasing.views.RequestUpdateView]
    /purchasing/<id>/submit/    [purchasing.views.submit_request]
    /purchasing/<id>/approve/   [purchasing.views.approve_request]
    /purchasing/<id>/reject/    [purchasing.views.reject_request]
    /purchasing/<id>/send-rfq/  [purchasing.views.send_rfq_view]
    /purchasing/<id>/suggest-supplier/ [purchasing.views.suggest_supplier]
    /purchasing/<id>/award/     [purchasing.views.award_supplier]
    /purchasing/<id>/pdf/       [purchasing.views.download_pdf]
    /purchasing/<id>/send-email/ [purchasing.views.send_email_view]
    /purchasing/<id>/comparison/ [purchasing.views.quotation_comparison]
    /purchasing/<id>/quotation/ [purchasing.views.create_quotation]
    /purchasing/api/stats/      [purchasing.views.api_stats]

  /suppliers/                   [suppliers.views.SupplierListView]
    /suppliers/create/          [suppliers.views.SupplierCreateView]
    /suppliers/<id>/            [suppliers.views.SupplierDetailView]
    /suppliers/<id>/update/     [suppliers.views.SupplierUpdateView]
    /suppliers/<id>/delete/     [suppliers.views.SupplierDeleteView]
    /suppliers/<id>/add-price/  [suppliers.views.SupplierMaterialPriceCreateView]
    /suppliers/materials/       [suppliers.views.MaterialListView]
    /suppliers/materials/create/ [suppliers.views.MaterialCreateView]
    /suppliers/materials/<id>/  [suppliers.views.MaterialDetailView]
    /suppliers/materials/<id>/update/ [suppliers.views.MaterialUpdateView]
    /suppliers/materials/<id>/delete/ [suppliers.views.MaterialDeleteView]
    /suppliers/quotations/      [suppliers.views.QuotationListView]
    /suppliers/quotations/<id>/ [suppliers.views.QuotationDetailView]

  /admin/                       [django.contrib.admin.urls]
```

---

## Appendix B: Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Custom User Model | Email as username | Modern auth UX, no username field |
| Database | SQLite (dev) / PostgreSQL (prod) | Simplicity vs production readiness |
| PDF Library | ReportLab | Full control over PDF layout |
| CSS Framework | Tailwind CSS | Utility-first, fast prototyping |
| Email Backend | SMTP (Gmail) | Reliable, free, well-documented |
| Session Backend | Database sessions | Simple, no extra dependencies |
| File Storage | Local filesystem | Simple, can migrate to S3 later |
| Auth System | Django built-in | Battle-tested, secure by default |

---

## Appendix C: Dependencies

| Package | Version | Purpose |
|---|---|---|
| Django | 4.2.x | Web framework |
| django-crispy-forms | 2.x | Form rendering |
| crispy-bootstrap5 | 0.7.x | Bootstrap 5 template pack |
| Pillow | 10.x | Image processing |
| reportlab | 4.x | PDF generation |
| python-dotenv | 1.x | Environment variables |
| chart.js | 2.9.x | Chart rendering (JavaScript) |

---

*Document Version: 1.0.0*
