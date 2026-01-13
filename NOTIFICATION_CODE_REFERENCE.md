# Notification System - Complete Code Reference

## Files Overview

### 1. Core Models (core/models.py)
**Location:** Line ~250-290

```python
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('APPROVAL', 'Approval'),
        ('REJECTION', 'Rejection'),
        ('SECURITY', 'Security'),
        ('INFO', 'Information'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='INFO'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
```

**Key Features:**
- UUID primary key (no enumerable IDs)
- `is_read` field controls visibility on dashboard
- `notification_type` for color-coding and filtering
- Auto timestamp creation
- Ordered by most recent first

---

### 2. Admin Interface (core/admin.py)
**Location:** Lines for NotificationAdmin

```python
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__email')
    readonly_fields = ('id', 'created_at')
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notification(s) marked as read.')
    mark_as_read.short_description = 'Mark selected as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    mark_as_unread.short_description = 'Mark selected as unread'

admin.site.register(Notification, NotificationAdmin)
```

**Admin Features:**
- View all notifications with filters
- Bulk mark as read/unread
- Search by content
- Filter by type, read status, date

---

### 3. Views (web/views.py)

#### Dashboard View
**Location:** Lines 89-101

```python
@login_required
def dashboard(request):
    account = get_or_create_account(request.user)
    recent_transactions = account.transactions.all().order_by('-timestamp')[:10]
    unread_notifications = Notification.objects.filter(
        user=request.user, 
        is_read=False  # KEY: Only unread notifications
    )
    debit_card = DebitCard.objects.filter(user=request.user).first()
    
    return render(request, "web/dashboard.html", {
        "account": account, 
        "recent_transactions": recent_transactions,
        "unread_notifications": unread_notifications,  # Filtered list
        "debit_card": debit_card,
    })
```

**Key Points:**
- Filters for `is_read=False` only
- Shows only new/unread notifications
- Updates context variable name for clarity

#### Notifications List View
**Location:** Lines 291-302

```python
@login_required
def notifications_list(request):
    """View all notifications history"""
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')  # Most recent first
    
    unread_count = notifications.filter(is_read=False).count()
    
    return render(request, "web/notifications.html", {
        "notifications": notifications,
        "unread_count": unread_count,
    })
```

**Key Points:**
- Gets ALL notifications (read and unread)
- Orders by most recent
- Calculates unread count for badge
- Protected with @login_required

#### Mark as Read API
**Location:** Lines 205-213

```python
@login_required
def mark_notification_as_read(request, notification_id):
    """API endpoint to mark a notification as read"""
    if request.method != 'POST':
        return JsonResponse({"status": "error"}, status=405)
    
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user  # Security: user can only mark own notifications
        )
        notification.is_read = True
        notification.save()
        return JsonResponse({"status": "success"})
    except Notification.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "Notification not found"
        }, status=404)
```

**Security Features:**
- Only marks own notifications
- UUID prevents ID enumeration
- CSRF protection required (frontend handles)

#### Creating Notifications (Examples)

**On User Approval:**
```python
def approve_user(request, user_id):
    user = User.objects.get(id=user_id)
    user.is_approved = True
    user.save()
    
    # Create notification
    Notification.objects.create(
        user=user,
        title="Account Approved",
        message="Your account has been approved by admin!",
        notification_type='APPROVAL'
    )
    # ...
```

**On Profile Update Approval:**
```python
def approve_profile_update(profile_update):
    profile_update.status = 'APPROVED'
    profile_update.save()
    
    Notification.objects.create(
        user=profile_update.user,
        title="Profile Updated",
        message="Your profile update has been approved.",
        notification_type='APPROVAL'
    )
    # ...
```

---

### 4. URLs (web/urls.py)

```python
urlpatterns = [
    # ... other urls ...
    
    # Notifications routes
    path('notifications/', views.notifications_list, name='notifications'),
    path('api/notification/<str:notification_id>/mark-read/', 
         views.mark_notification_as_read, 
         name='mark_notification_as_read'),
    
    # ... other urls ...
]
```

**Route Details:**
- `GET /notifications/` - View all notifications
- `POST /api/notification/{id}/mark-read/` - Mark single notification as read

---

### 5. Templates

#### Base Template (web/templates/web/base.html)
**Lines: Navbar section**

```html
<li class="nav-item">
    <a class="nav-link" href="{% url 'notifications' %}">
        <i class="bi bi-bell"></i> Notifications
    </a>
</li>
```

**Key Features:**
- Bell icon indicator
- Direct link to notifications center
- Works on mobile (Bootstrap collapse)

#### Dashboard Template (web/templates/web/dashboard.html)
**Lines: 8-40**

```html
<!-- Unread Notifications Banner -->
{% if unread_notifications %}
<div class="row mb-4">
    <div class="col-12">
        <!-- Summary Banner -->
        <div class="alert alert-info alert-custom d-flex align-items-center justify-content-between">
            <div class="d-flex align-items-center">
                <i class="bi bi-bell-fill me-2"></i>
                <div>
                    <strong>You have {{ unread_notifications.count }} new notification{{ unread_notifications.count|pluralize }}</strong><br>
                    <small>Check below or visit your <a href="{% url 'notifications' %}">Notifications Center</a></small>
                </div>
            </div>
            <a href="{% url 'notifications' %}" class="btn btn-sm btn-primary-custom">
                <i class="bi bi-bell"></i> View All
            </a>
        </div>

        <!-- Show first 3 unread -->
        {% for notification in unread_notifications|slice:":3" %}
        <div class="alert alert-custom d-flex align-items-center justify-content-between" 
             style="border-left: 4px solid {% if notification.notification_type == 'APPROVAL' %}#10b981{% elif notification.notification_type == 'REJECTION' %}#ef4444{% else %}#3b82f6{% endif %};">
            <div class="d-flex align-items-center">
                <!-- Icon based on type -->
                {% if notification.notification_type == 'APPROVAL' %}
                    <i class="bi bi-check-circle-fill me-2"></i>
                {% elif notification.notification_type == 'REJECTION' %}
                    <i class="bi bi-x-circle-fill me-2"></i>
                {% else %}
                    <i class="bi bi-info-circle-fill me-2"></i>
                {% endif %}
                <div>
                    <strong>{{ notification.title }}</strong><br>
                    <small>{{ notification.message }}</small>
                </div>
            </div>
            <!-- Close button triggers mark-as-read -->
            <button type="button" class="btn-close" 
                    data-bs-dismiss="alert" 
                    onclick="markNotificationAsRead('{{ notification.id }}')"></button>
        </div>
        {% endfor %}
    </div>
</div>
{% endif %}
```

**Features:**
- Shows count with pluralization
- First 3 notifications displayed
- Color-coded left border
- Matching icons
- Dismiss triggers mark-as-read
- Link to notifications center

**Dashboard JavaScript:**
```javascript
function markNotificationAsRead(notificationId) {
    fetch(`/api/notification/${notificationId}/mark-read/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
        }
    })
    .then(response => {
        if (response.ok) {
            console.log('Notification marked as read');
        }
    })
    .catch(error => console.error('Error:', error));
}
```

#### Notifications Center (web/templates/web/notifications.html)
**Complete template: ~120 lines**

```html
{% extends "web/base.html" %}

{% block title %}Notifications - BankApp{% endblock %}

{% block content %}
<div class="row">
    <div class="col-lg-8 mx-auto">
        <!-- Header with unread count -->
        <div class="card card-custom mb-4">
            <div class="card-header-custom">
                <div class="d-flex justify-content-between align-items-center">
                    <h2 class="mb-0 text-white"><i class="bi bi-bell"></i> Notifications Center</h2>
                    {% if unread_count > 0 %}
                    <span class="badge bg-danger">{{ unread_count }} unread</span>
                    {% endif %}
                </div>
            </div>
            <div class="card-body p-5">
                <!-- Empty state -->
                {% if not notifications %}
                <div class="text-center py-5">
                    <i class="bi bi-inbox" style="font-size: 3rem; color: #ccc;"></i>
                    <p class="text-muted mt-3">No notifications yet</p>
                </div>
                {% else %}
                <!-- Notification list -->
                <div class="list-group">
                    {% for notification in notifications %}
                    <div class="list-group-item list-group-item-action 
                                {% if not notification.is_read %}active-notification{% endif %}" 
                         style="border-left: 4px solid 
                            {% if notification.notification_type == 'APPROVAL' %}#10b981
                            {% elif notification.notification_type == 'REJECTION' %}#ef4444
                            {% else %}#3b82f6{% endif %};
                            background: {% if not notification.is_read %}rgba(102, 126, 234, 0.05){% endif %};">
                        
                        <!-- Header row -->
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div class="d-flex align-items-center gap-2">
                                <!-- Icon -->
                                {% if notification.notification_type == 'APPROVAL' %}
                                <i class="bi bi-check-circle-fill text-success"></i>
                                {% elif notification.notification_type == 'REJECTION' %}
                                <i class="bi bi-x-circle-fill text-danger"></i>
                                {% elif notification.notification_type == 'SECURITY' %}
                                <i class="bi bi-shield-exclamation text-warning"></i>
                                {% else %}
                                <i class="bi bi-info-circle-fill text-info"></i>
                                {% endif %}
                                <!-- Title and time -->
                                <div>
                                    <h6 class="mb-0 fw-bold">{{ notification.title }}</h6>
                                    <small class="text-muted">{{ notification.created_at|date:"M d, Y H:i" }}</small>
                                </div>
                            </div>
                            <!-- NEW badge -->
                            <div>
                                {% if not notification.is_read %}
                                <span class="badge bg-success">NEW</span>
                                {% endif %}
                            </div>
                        </div>
                        
                        <!-- Message -->
                        <p class="mb-0 text-muted">{{ notification.message }}</p>
                        
                        <!-- Mark as read button -->
                        {% if not notification.is_read %}
                        <button class="btn btn-sm btn-outline-primary mt-2" 
                                onclick="markNotificationAsRead('{{ notification.id }}')">
                            <i class="bi bi-check"></i> Mark as Read
                        </button>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>

                <!-- Back button -->
                <div class="d-grid gap-2 mt-4">
                    <a href="{% url 'dashboard' %}" class="btn btn-secondary">
                        <i class="bi bi-arrow-left"></i> Back to Dashboard
                    </a>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>

<!-- Styling -->
<style>
    .active-notification {
        font-weight: 500;
    }
    .list-group-item {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        margin-bottom: 12px;
        padding: 16px;
        transition: all 0.3s ease;
    }
    .list-group-item:hover {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
</style>

<!-- JavaScript for mark-as-read -->
<script>
    function markNotificationAsRead(notificationId) {
        fetch(`/api/notification/${notificationId}/mark-read/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
            }
        })
        .then(response => {
            if (response.ok) {
                location.reload();
            }
        })
        .catch(error => console.error('Error:', error));
    }
</script>
{% endblock %}
```

**Features:**
- Unread count badge in header
- All notifications in list
- Color-coded by type
- Icons matching notification type
- NEW badge on unread items
- Individual mark-as-read buttons
- Timestamps
- Empty state message
- Back to dashboard button
- Reload on mark-as-read

---

## Database Query Examples

### Get unread notifications for user
```python
unread = Notification.objects.filter(user=user, is_read=False)
```

### Get all notifications ordered by date
```python
all_notifs = Notification.objects.filter(user=user).order_by('-created_at')
```

### Get count of unread
```python
count = Notification.objects.filter(user=user, is_read=False).count()
```

### Get by type
```python
approvals = Notification.objects.filter(
    user=user,
    notification_type='APPROVAL'
)
```

### Create notification
```python
Notification.objects.create(
    user=user,
    title="Title Here",
    message="Message here",
    notification_type='APPROVAL'
)
```

### Mark as read
```python
notification.is_read = True
notification.save()

# Or bulk update
Notification.objects.filter(user=user).update(is_read=True)
```

---

## CSS Classes Used

```css
.alert-custom         /* Custom styled alerts */
.card-custom          /* Custom card styling */
.card-header-custom   /* Gradient header */
.btn-primary-custom   /* Custom button style */
.active-notification  /* Unread notification styling */
.list-group-item      /* Notification list item */
.badge                /* Count badges */
```

---

## Bootstrap Classes Used

- `d-flex` - Flexbox display
- `align-items-center` - Vertical alignment
- `justify-content-between` - Space between items
- `gap-2` - Gap between flex items
- `mb-4`, `mt-2`, etc. - Margins
- `p-5` - Padding
- `text-muted` - Muted text
- `badge` - Badge styling
- `btn-sm` - Small buttons
- `col-lg-8`, `mx-auto` - Grid layout
- `list-group` - List styling
- `d-grid` - Full-width grid

---

## Security Considerations

1. **User Isolation** - Queries always filter by `request.user`
2. **UUID IDs** - No enumerable notification IDs
3. **CSRF Protection** - API endpoints require CSRF token
4. **Login Required** - All views protected with @login_required
5. **No Direct SQL** - Uses Django ORM (prevents SQL injection)
6. **Validation** - Checks notification ownership before marking

---

## Performance Notes

- Notifications indexed on user_id and created_at
- Most queries filtered by user (efficient)
- Slice first 3 on dashboard (not fetching all)
- No N+1 queries
- Minimal database load

---

## Customization Points

### Change notification colors:
Edit HTML: `border-left: 4px solid #COLOR`

### Change notification types:
Edit models.py Notification.NOTIFICATION_TYPES

### Change icon mappings:
Edit templates: if/elif blocks for notification_type

### Change number of notifications shown:
Dashboard template: `slice:":3"` (change 3 to desired number)

### Change ordering:
Edit view: `.order_by('-created_at')` or other field

---

## Testing Checklist

- [ ] Create notification via admin
- [ ] Check appears on dashboard as alert (unread)
- [ ] Click mark as read
- [ ] Navigate away and back, notification shouldn't appear
- [ ] Check notifications center, still visible
- [ ] Click notifications in navbar
- [ ] See full history with timestamps
- [ ] Click individual mark as read
- [ ] Page reloads showing updated status
- [ ] Test on mobile (responsive)
- [ ] Test with multiple notifications
- [ ] Test with no notifications (empty state)
- [ ] Test CSRF token handling
- [ ] Verify login required enforcement
