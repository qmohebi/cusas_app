# Software Development Requirements Document (SDRD)

**Project Title:** Equipment Library loan request  
**Prepared by:** [Qurban Mohebi/Connectivity team]  
**Date:** 2024-08-29

---

## 1. Introduction

The current workflow of clinical users requesting equipment by bleeping the eqiupment library team is inefficient. An application is needed to address this issue.

### 1.1 Purpose

The purpose of this document is to define the requirements for a web-based application that allows clinical users to request equipment while ensuring operational control, user accessibility, and automated notification to the technical team.

### 1.2 Scope

The system will provide clinical staff with an intuitive user interface to request equipment. The system will enforce availability rules (no requests during weekends, outside 09:00–17:00, or on bank holidays). Once a valid request is submitted, the technical team will be notified immediately.

The system will be accessible from web browsers and secured via institutional authentication mechanisms (e.g., LDAP/Active Directory).

---

## 2. Functional Requirements

### 2.1 User Roles

- **Clinical User (Requester):** Submits equipment requests.
- **Technical Team Member (Responder):** Receives notifications, reviews, and processes requests.
- **Administrator:** Manages system settings (bank holiday dates, working hours, adding new category that can be loaned).

### 2.2 Core Features

1. **Web-Based Access**

   - The application must be browser-based and responsive (accessible on desktop and mobile).

2. **Equipment Request Form**

   - Clinical users must be able to submit requests through a structured form.
   - Mandatory fields: equipment type, location, person requesting, extension
   - Optional field - email address and additional notes.

3. **Operational Time Restrictions**

   - Requests can only be submitted between **09:00 and 17:00, Monday–Friday**.
   - Requests outside these times must be blocked with an informative message.
   - Requests must also be blocked on pre-configured **bank holidays**.

4. **Notifications**

   - When a valid request is submitted, the system must notify the technical team:
     - Via bleep to equipment library bleep.
     - Via equipment library desktop app

5. **User Interface (UI)**

   - The UI must be **intuitive and simple**, requiring minimal training.
   - Features:
     - Equipment as a card with image of equipment and name of equipment.
     - Clear feedback messages (e.g., “Request submitted successfully”).
     - Error handling (e.g., “Requests cannot be made outside working hours”).

6. **Administration Functions**
   - Admins can add new model, upload images and give title
   - Admins can configure the opening and closing hours.

---

## 3. Non-Functional Requirements

### 3.1 Usability

- The system must be easy to use with a clean, minimal design.
- The interface must comply with accessibility standards (WCAG 2.1 AA).

### 3.2 Performance

- The application should respond within 2 seconds for typical requests.

### 3.3 Security

- Authentication via institutional login (LDAP/AD) for the admin.
- Data transmission must use HTTPS.
- Role-based access control.

### 3.4 Availability

- 99.9% uptime (excluding planned maintenance).

### 3.5 Scalability

- The application must support at least 500 concurrent users.

---

## 4. Technical Requirements

- **Platform:** Web-based (Django).
- **Database:** MSSQL server (existing department database). PostgreSQL for user management.
- **Frontend:** HTML5, CSS3 (Bootstrap/Tailwind), JavaScript (React optional).
- **Notifications:** SMTP server integration for email to bleep.
- **Deployment:** Dockerized for portability or IIS
- **Hosting:** Internal servers.

---

## 5. Constraints & Assumptions

- Clinical staff will access the system via secure institutional network.
- The institution will provide an SMTP service for notifications.

---

## 6. Success Criteria

- Clinical users can submit equipment requests during valid hours only.
- Technical team is notified within 1 minute of submission.
- UI is adopted with minimal training (validated by user testing).
- Admin can configure out of hours, add new model.
