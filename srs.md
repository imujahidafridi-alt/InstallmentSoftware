# Software Requirements Specification (SRS)

# Device/Mobile Installment Management System

## Version

1.0

## Technology Stack

### Frontend

* Python PyQt6 (Desktop Application)
* Modern Responsive UI
* Dark/Light Theme Support

### Backend

* Supabase

  * PostgreSQL Database
  * Authentication
  * Realtime Updates
  * Row Level Security (RLS)

### Reporting

* PDF Generation
* Excel Export
* CSV Export

### Architecture

* Layered Architecture
* MVVM (Model View ViewModel) Pattern
* Repository Pattern
* Service Layer Architecture

---

# 1. Project Overview

The Device/Mobile Installment Management System is a desktop-based application designed for mobile shops, electronics stores, and installment businesses.

The system allows administrators to:

* Register customers
* Record device sales
* Create installment plans
* Track payments
* Monitor due installments
* Generate customer ledgers
* Generate financial reports
* Calculate profits and margins
* Manage complete installment lifecycle

---

# 2. Business Objectives

### Primary Goals

* Digitize installment management
* Reduce manual bookkeeping
* Improve installment recovery tracking
* Generate accurate financial reports
* Maintain customer payment history
* Monitor profit margins

---

# 3. User Roles

## Administrator

Permissions:

* Create customer records
* Sell devices
* Create installment plans
* Record installment payments
* Generate reports
* Edit customer information
* Manage ledgers
* View dashboards

---

# 4. Functional Requirements

# Module 1: Customer Management

## Customer Registration Form

Fields:

| Field         | Type           | Required |
| ------------- | -------------- | -------- |
| Customer ID   | Auto Generated | Yes      |
| Name          | Text           | Yes      |
| Father Name   | Text           | Yes      |
| CNIC          | Text           | Yes      |
| Mobile Number | Text           | Yes      |
| Address       | Text Area      | Optional |
| Remarks       | Text Area      | Optional |

### Validation Rules

#### CNIC

Format:

XXXXX-XXXXXXX-X

Example:

12345-1234567-1

#### Mobile Number

Format:

03XXXXXXXXX

Example:

03001234567

---

# Module 2: Device Management

## Device Information Form

### Device Details

| Field       | Type     |
| ----------- | -------- |
| Device Name | Text     |
| Brand       | Text     |
| Model       | Text     |
| RAM         | Dropdown |
| ROM         | Dropdown |

### SIM Configuration

Radio Buttons:

* Single SIM
* Dual SIM
* Triple SIM
* Four SIM

### Dynamic IMEI Fields

#### Single SIM

IMEI 1

#### Dual SIM

IMEI 1
IMEI 2

#### Triple SIM

IMEI 1
IMEI 2
IMEI 3

#### Four SIM

IMEI 1
IMEI 2
IMEI 3
IMEI 4

### IMEI Validation

* Numeric Only
* 15 Digits
* No Duplicate IMEIs

---

# Module 3: Device Sale Management

## Sale Creation

Fields:

| Field                  | Type                |
| ---------------------- | ------------------- |
| Sale ID                | Auto Generated      |
| Customer               | Searchable Dropdown |
| Device                 | Device Record       |
| Cost Price             | Currency            |
| Selling Price          | Currency            |
| Down Payment           | Currency            |
| Installment Duration   | Months              |
| Installment Start Date | Date                |

---

## Real-Time Margin Calculator

### Formula

Margin = Selling Price - Cost Price

### Display

* Amount
* Percentage

Example:

Cost Price = 40,000

Selling Price = 50,000

Margin = 10,000

Margin % = 25%

---

## Real-Time Installment Calculator

### Formula

Remaining Amount = Selling Price - Down Payment

Monthly Installment = Remaining Amount / Duration

Example:

Selling Price = 60,000

Down Payment = 10,000

Duration = 10 Months

Monthly Installment = 5,000

### Live Update

Whenever:

* Selling price changes
* Down payment changes
* Duration changes

Calculator updates instantly.

---

# Module 4: Installment Ledger

Each customer shall have a dedicated ledger.

## Ledger Information

### Sale Summary

* Sale ID
* Device Name
* Total Amount
* Down Payment
* Remaining Balance

### Installment Entries

| Date         | Amount      | Status  |
| ------------ | ----------- | ------- |
| Due Date     | Installment | Pending |
| Payment Date | Amount Paid | Paid    |

### Running Balance

System shall automatically calculate:

Outstanding Balance

Remaining Installments

Next Due Date

### Ledger Repayment & Rescheduling Features
* **Automatic Balance Calculation**: The system dynamically updates the customer ledger and overall outstanding balance after every payment or rescheduling action.
* **Partial Payments**: Payments that are less than the due amount are recorded, and the installment status is set to "Partial".
* **Advance Payments**: Overpayments are automatically allocated to the next unpaid installment(s) in chronological order.
* **Extra Payments**: Excess payments beyond the total outstanding schedule are allocated as a credit on the final installment.
* **Installment Rescheduling**: Administrators can reschedule remaining unpaid/partially paid installments. This converts any partially paid installments into fully "Paid" installments with the paid amount as the new installment value, deletes future pending installments, and splits the remaining balance into N new monthly installments starting on a user-specified date.

---

# Module 5: Installment Collection

## Payment Entry Screen

Fields:

* Customer
* Ledger
* Due Installment
* Amount Received
* Payment Date
* Notes

### Features

* Partial Payment Support
* Full Payment Support
* Advance Payment Support
* Auto Balance Update

---

# Module 6: Due Tracking System

## Upcoming Installments

Dashboard Widget and Due Tracking View:

### Due Today
* Customer Name, Device Name, Mobile, Due Amount, Outstanding Amount

### Due Tomorrow
* Customer Name, Device Name, Mobile, Due Amount, Outstanding Amount

### Due This Week
* Customer Name, Device Name, Mobile, Due Date, Due Amount, Outstanding Amount

### Due This Month
* Customer Name, Device Name, Mobile, Due Date, Due Amount, Outstanding Amount

### Overdue Tracking
Segmented into aging buckets:
* **1–30 Days Overdue**
* **31–60 Days Overdue**
* **61–90 Days Overdue**
* **90+ Days Overdue**

Each bucket displays: Customer Name, Device Name, Mobile, Due Date, Days Overdue, Due Amount, Outstanding Amount.

---

# Module 7: Customer Ledger Reports

## Individual Customer Ledger Report

Generate PDF

Contains:

### Customer Information

* Name
* Father Name
* CNIC
* Mobile Number

### Device Information

* Device Name
* RAM
* ROM
* IMEIs

### Financial Information

* Cost Price
* Selling Price
* Margin

### Installment History

Complete Payment Record

### Current Outstanding Balance

### Report Generation Date

---

# Module 8: Financial Reports

## Monthly Collection Report

Filters:

* Month
* Year

Display:

| Customer | Amount Received |
| -------- | --------------- |

### Totals

* Total Collection
* Total Outstanding
* Total Profit

### Export Options

* PDF
* Excel
* CSV

---

# Module 9: Dashboard & Executive KPIs

## KPIs

* **Total Customers**: Count of registered customers
* **Total Devices Sold**: Count of registered sales records
* **Active Installments**: Count of active (unpaid or partially paid) installments
* **Completed Installments**: Count of sales with zero outstanding balance
* **Overdue Installments**: Count of unpaid/partially paid installments whose due date has passed
* **Total Outstanding Balance**: Total remaining unpaid balance across all sales
* **Monthly Collection**: Payments collected in the current calendar month
* **Monthly Profit**: Net margin calculated on sales made in the current calendar month
* **Net Revenue**: Total accumulated collections across the entire system minus cost price of fully completed sales (or defined as total collections of all time).

---

## Analytics Charts

* **Monthly Collections Trend**: Line chart of collections over the last 6 months
* **Monthly Profit Trend**: Line chart of margins over the last 6 months
* **Outstanding Balance Analysis**: Bar chart of cumulative outstanding balance over the last 6 months
* **Recovery Performance Chart**: Line or bar chart showing the percentage of due payments that were successfully recovered each month (Collections received / total amount due in that month)
* **Installment Completion Rate**: Gauge or pie chart showing the ratio of completed (fully paid) installments/sales to active ones.

---

# Module 10: Audit & Activity Logs

## System Audit Trail

The system logs administrative actions to a central database table to ensure compliance, security, and record recovery.

### Tracked Actions
* **Customer Creation**: Logged when a customer is registered
* **Customer Updates**: Logged when customer information is edited
* **Sales Creation**: Logged when a new device sale/installment plan is created
* **Payment Entries**: Logged when an installment payment is collected
* **Deleted Records**: Logged when database reset/wipe operations are executed
* **User Login Activity**: Logged when an administrator signs in

### Logged Fields
* **User**: The email address of the active user session
* **Action**: Descriptive summary of the action (e.g., "Updated Customer: Jane Doe (CNIC: ...)")
* **Date**: Date of the action (YYYY-MM-DD)
* **Time**: Time of the action (HH:MM:SS)
* **IP Address**: Public IP address of the client machine (fetched from api.ipify.org with a fallback to local IP)

---

# 5. Database Design

## customers

| Column      | Type      |
| ----------- | --------- |
| id          | UUID      |
| name        | VARCHAR   |
| father_name | VARCHAR   |
| cnic        | VARCHAR   |
| mobile      | VARCHAR   |
| address     | TEXT      |
| created_at  | TIMESTAMP |

---

## devices

| Column   | Type    |
| -------- | ------- |
| id       | UUID    |
| name     | VARCHAR |
| brand    | VARCHAR |
| model    | VARCHAR |
| ram      | VARCHAR |
| rom      | VARCHAR |
| sim_type | INTEGER |
| imei_1   | VARCHAR |
| imei_2   | VARCHAR |
| imei_3   | VARCHAR |
| imei_4   | VARCHAR |

---

## sales

| Column             | Type    |
| ------------------ | ------- |
| id                 | UUID    |
| customer_id        | UUID    |
| device_id          | UUID    |
| cost_price         | NUMERIC |
| selling_price      | NUMERIC |
| down_payment       | NUMERIC |
| installment_months | INTEGER |
| start_date         | DATE    |
| margin             | NUMERIC |

---

## installments

| Column    | Type    |
| --------- | ------- |
| id        | UUID    |
| sale_id   | UUID    |
| due_date  | DATE    |
| amount    | NUMERIC |
| status    | VARCHAR |
| paid_date | DATE    |

---

## payments

| Column          | Type    |
| --------------- | ------- |
| id              | UUID    |
| installment_id  | UUID    |
| amount_received | NUMERIC |
| payment_date    | DATE    |
| notes           | TEXT    |

---

## audit_logs

| Column      | Type      |
| ----------- | --------- |
| id          | UUID      |
| user_email  | VARCHAR   |
| action      | VARCHAR   |
| log_date    | DATE      |
| log_time    | VARCHAR   |
| ip_address  | VARCHAR   |
| created_at  | TIMESTAMP |

---

# 6. Non-Functional Requirements

## Performance

* Dashboard load under 2 seconds
* Search results under 500ms
* Report generation under 5 seconds

## Scalability

Support:

* 50,000+ customers
* 100,000+ installment records

## Reliability

* 99.9% uptime
* Automatic data synchronization

## Security

* Supabase Authentication
* Encrypted API communication
* Role Based Access Control
* Row Level Security Policies

## Backup

* Daily Database Backup
* Recovery Point Objective (RPO): 24 Hours

---

# 7. User Experience Requirements

## UI Design

Modern POS-style interface

### Sidebar Navigation

* Dashboard
* Customers
* Devices
* Sales
* Installments
* Reports
* Settings

### Global Search

Search by:

* Customer Name
* CNIC
* Mobile Number
* IMEI
* Sale ID

### Quick Actions

* New Sale
* Receive Payment
* Generate Report

---

# 8. Future Enhancements

## Mobile App

Android companion application.

---

# 9. Acceptance Criteria

The project shall be considered complete when:

* Customer management is functional.
* Device registration is functional.
* Installment calculations work correctly.
* Ledger system works correctly.
* PDF reports generate successfully.
* Monthly collection reports generate successfully.
* Due tracking works accurately.
* Dashboard metrics update in real time.
* Supabase synchronization works correctly.
* System passes UAT testing.
