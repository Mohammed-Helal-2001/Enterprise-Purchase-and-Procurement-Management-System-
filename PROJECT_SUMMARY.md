# Project Summary

## Business Problem

Procurement teams often manage purchase requests, supplier communication, approvals, and quotation comparisons across spreadsheets, email threads, and manual follow-ups. This creates delays, weak auditability, inconsistent supplier evaluation, and limited visibility into request status.

## Solution

The Purchase Management System centralizes the procurement workflow in a Django web application. Users can create purchase requests, submit them for approval, manage suppliers and materials, send RFQs, record supplier quotations, compare offers, recommend a supplier, award the request, and export professional PDF documents.

## Modules

- `accounts`: Custom email-based users, role management, profile details, dashboard views, and activity logs.
- `purchasing`: Purchase requests, request items, approval history, RFQ logs, supplier recommendation logic, award workflow, dashboard statistics, and PDF generation.
- `suppliers`: Supplier records, raw materials, supplier-material mapping, reference pricing, lead times, quotations, and quotation items.

## Technical Decisions

- Django was selected to provide a mature MVC-style framework, built-in authentication foundations, ORM, admin tooling, template rendering, and migration support.
- A custom user model was implemented to support email-based authentication and procurement-specific roles.
- SQLite is used for local development because it is simple to run and easy for reviewers to test.
- Environment variables are used for secrets and deployment-specific settings.
- The default development email backend writes emails to the console to avoid accidental external email delivery.
- ReportLab is used to generate formal purchase request PDFs directly from server-side data.
- The supplier recommendation logic uses weighted criteria: price, delivery time, and supplier rating.

## Portfolio Relevance

This project demonstrates practical Django application design, relational data modeling, role-based workflows, business process automation, document generation, and professional repository preparation for GitHub review.
