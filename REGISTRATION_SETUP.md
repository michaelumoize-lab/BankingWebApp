# BankApp - Registration & Admin Approval System

## Overview
Customers can now self-register for accounts, which require your (admin) approval before they can log in.

## New Features

### 1. **Customer Registration**
- Customers can create accounts at `/signup/`
- Required information:
  - First Name
  - Last Name
  - Email Address
  - Phone Number
  - Password (minimum 6 characters)

### 2. **Admin Approval Workflow**
- New accounts are created with `is_approved=False`
- Customers cannot log in until approved
- You can approve/disapprove users in the admin panel

### 3. **Updated Admin Interface**
- Go to `http://127.0.0.1:8000/admin/Users`
- View all users with their approval status
- Filter by approval status
- Use bulk actions to approve/disapprove multiple users at once

## How to Use

### For Customers:
1. Click "Sign up here" on the login page
2. Fill in registration form with required information
3. Submit and wait for admin approval
4. Once approved, they can log in

### For You (Admin):
1. Access admin panel: `http://127.0.0.1:8000/admin/`
2. Navigate to Users section
3. View pending approvals (is_approved = False)
4. Select users and use "Approve selected users" action
5. Or click individual user to approve

## Login Restrictions
- Unapproved users see: "Your account is pending admin approval. Please check back soon."
- Only approved users can access the banking features

## Database Changes
New User model fields:
- `first_name` - Customer's first name
- `last_name` - Customer's last name
- `phone` - Customer's phone number
- `is_approved` - Admin approval status (True/False)

## Files Modified/Created
- ✅ `core/models.py` - Updated User model
- ✅ `core/admin.py` - Enhanced admin interface
- ✅ `web/views.py` - Added signup view
- ✅ `web/urls.py` - Added signup URL
- ✅ `web/templates/web/login.html` - Added signup link
- ✅ `web/templates/web/signup.html` - Registration form
- ✅ `web/templates/web/signup_success.html` - Success message
- ✅ Migrations created and applied

## Testing
1. Start your server: `python manage.py runserver`
2. Go to `http://127.0.0.1:8000/login/`
3. Click "Sign up here"
4. Fill out and submit registration
5. Try to log in - you should see the pending approval message
6. Go to admin panel and approve the user
7. Now they can log in successfully
