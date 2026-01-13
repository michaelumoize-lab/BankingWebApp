# Notification System - Visual Workflow

## User Journey with Notifications

```
┌─────────────────────────────────────────────────────────────────┐
│                    NOTIFICATION LIFECYCLE                       │
└─────────────────────────────────────────────────────────────────┘

1. NOTIFICATION CREATED (by system)
   ├─ Admin approves user account
   ├─ Admin approves profile update
   ├─ Admin approves card application
   ├─ Card fee paid
   └─ Transfer completed
   
   → Notification created with is_read=False

2. FIRST LOGIN (Dashboard)
   ├─ User logs in
   ├─ Dashboard renders
   └─ System fetches unread notifications
   
   → Shows alert banner:
      "You have X new notification(s)"
      [View All] button

3. USER INTERACTION OPTIONS
   
   Option A: Dismiss from Dashboard
   ├─ Click X button on notification
   ├─ JavaScript calls: /api/notification/{id}/mark-read/
   ├─ Notification is_read set to True
   └─ Alert removed from view
   
   Option B: View Notifications Center
   ├─ Click "View All" or navbar "Notifications"
   ├─ Navigate to /notifications/
   ├─ See all notifications (read and unread)
   ├─ Click "Mark as Read" on individual items
   └─ Page reloads showing updated status

4. SUBSEQUENT LOGINS (Dashboard)
   ├─ Only NEW unread notifications appear
   ├─ Previously read notifications hidden
   └─ User still has access to full history
   
   → Click Notifications Center anytime
      to see all previous messages

┌─────────────────────────────────────────────────────────────────┐
│                      DASHBOARD VIEW                             │
└─────────────────────────────────────────────────────────────────┘

ONLY IF UNREAD NOTIFICATIONS EXIST:

┌─────────────────────────────────────────────────────┐
│ 🔔 You have 2 new notification(s)                   │
│    Check below or visit Notifications Center...     │ [View All]
│                                                     │
├─────────────────────────────────────────────────────┤
│ ✅ Profile Approved                              [X]│
│    Your profile update has been approved.           │
│                                                     │
├─────────────────────────────────────────────────────┤
│ 💳 Debit Card Activated                         [X]│
│    Your card has been activated successfully.       │
│                                                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  NOTIFICATIONS CENTER                │
│                   /notifications/                    │
└─────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│ 🔔 Notifications Center         [3 unread] ┌─────┐ │
├────────────────────────────────────────────────────┤
│                                                    │
│ [NEW] ✅ Profile Approved                         │
│       Your profile update has been approved.      │
│       Jan 13, 2026 8:30 AM                        │
│       [Mark as Read] button                       │
│                                                    │
├────────────────────────────────────────────────────┤
│ [NEW] 💳 Debit Card Activated                     │
│       Your card has been activated successfully.  │
│       Jan 13, 2026 8:25 AM                        │
│       [Mark as Read] button                       │
│                                                    │
├────────────────────────────────────────────────────┤
│ ❌ Card Application Rejected                       │
│    Your card application was rejected.             │
│    Jan 12, 2026 4:15 PM                           │
│    (no button - already read)                      │
│                                                    │
├────────────────────────────────────────────────────┤
│ ℹ️  Account Created Successfully                   │
│    Your account has been created and is pending   │
│    Jan 10, 2026 2:00 PM                           │
│                                                    │
│         [← Back to Dashboard]                      │
└────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│              COLOR CODE REFERENCE                   │
└─────────────────────────────────────────────────────┘

Type          | Color  | Icon              | Examples
──────────────┼────────┼───────────────────┼──────────────────────
APPROVAL      | 🟢 GRN | ✅ check-circle   | Profile approved
              |        |                   | Card activated
REJECTION     | 🔴 RED | ❌ x-circle       | Card rejected
              |        |                   | Profile denied
SECURITY      | 🟡 YEL | ⚠️  shield        | Login attempt
              |        |                   | Account warning
INFO          | 🔵 BLU | ℹ️  info-circle   | Account created
              |        |                   | Transfer sent

┌─────────────────────────────────────────────────────┐
│           NOTIFICATION TRIGGERS                     │
└─────────────────────────────────────────────────────┘

EVENT                          | TYPE      | When Created
───────────────────────────────┼───────────┼─────────────────────
User signs up                  | INFO      | Immediately
Admin approves user            | APPROVAL  | On approval action
Admin rejects user             | REJECTION | On rejection action
User updates profile           | INFO      | On submission
Admin approves profile update  | APPROVAL  | On approval action
Admin rejects profile update   | REJECTION | On rejection action
User applies for card          | INFO      | On application
Admin approves card app        | APPROVAL  | On approval (card created)
Admin rejects card app         | REJECTION | On rejection action
User pays card fee             | INFO      | On payment
Transfer completed             | INFO      | On successful transfer

┌─────────────────────────────────────────────────────┐
│              API ENDPOINTS                          │
└─────────────────────────────────────────────────────┘

GET /notifications/
├─ Returns: notifications.html page
├─ Requires: Login
├─ Parameters: None
└─ Context: All notifications, unread count

POST /api/notification/{notification_id}/mark-read/
├─ Returns: {"status": "success"} or error
├─ Requires: Login, CSRF token
├─ Body: JSON (empty)
└─ Side Effect: Sets is_read=True for notification

GET /dashboard/
├─ Returns: dashboard.html page
├─ Requires: Login
├─ Context: Account info, unread_notifications (filtered)
└─ Note: Only shows is_read=False notifications

┌─────────────────────────────────────────────────────┐
│              DATA MODEL                             │
└─────────────────────────────────────────────────────┘

Notification:
  id (UUID)
  user_id (FK → User)
  title (str)
  message (str)
  notification_type (enum)
    - APPROVAL
    - REJECTION
    - SECURITY
    - INFO
  is_read (bool, default=False)
  created_at (datetime, auto_now_add=True)

KEY FEATURE: is_read field determines visibility
  - is_read=False → Appears in Dashboard alerts
  - is_read=True  → Only visible in Notifications Center

┌─────────────────────────────────────────────────────┐
│           NAVIGATION PATHS                          │
└─────────────────────────────────────────────────────┘

From Dashboard:
  ├─ Click "View All" button → /notifications/
  ├─ Click "Notifications" in navbar → /notifications/
  └─ Close X on alert → Marks as read (stays on page)

From Notifications Center:
  ├─ Click "Back to Dashboard" → /dashboard/
  ├─ Click navbar brand → /home/
  └─ Click individual "Mark as Read" → Reloads page

Mobile (Responsive):
  ├─ All features work on mobile
  ├─ Hamburger menu for navbar
  └─ Touch-friendly buttons and dismiss

┌─────────────────────────────────────────────────────┐
│              IMPLEMENTATION STATUS                  │
└─────────────────────────────────────────────────────┘

✅ Notification model with is_read field
✅ Dashboard showing only unread notifications
✅ Notifications center page with full history
✅ Mark-as-read API endpoint
✅ Navbar integration
✅ Color-coded display
✅ NEW badges for unread items
✅ Timestamps
✅ Responsive design
✅ CSRF protection
✅ Login required enforcement
✅ Admin actions for managing notifications

┌─────────────────────────────────────────────────────┐
│                  QUICK TEST                         │
└─────────────────────────────────────────────────────┘

1. Sign up as new user
   ✓ See welcome INFO notification
   
2. Wait for admin approval
   ✓ Log in and see APPROVAL notification as alert
   
3. Close notification
   ✓ Notification disappears from dashboard
   
4. Click "Notifications" link
   ✓ See full notification history
   ✓ Can still mark items as read
   
5. Log out and log back in
   ✓ Previously read notifications NOT shown as alerts
   ✓ Only new/unread notifications appear as alerts
   ✓ Full history still visible in Notifications Center
