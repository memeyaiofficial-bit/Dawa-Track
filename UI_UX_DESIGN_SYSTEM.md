# DawaTrack Hospital - UI/UX Design System

## Design Philosophy

**Hospital-Grade, User-Centered Design**
- Calm, professional aesthetic
- Large, accessible fonts for elderly patients
- Clear information hierarchy
- Minimal cognitive load
- Trust-building visual language

---

## 1. COLOR PALETTE

### Primary Colors
```
✓ Hospital Blue:     #0066CC (Trust, professionalism)
✓ Healthcare Green:  #00AB44 (Health, vitality, confidence)
✓ Warning Red:       #DC3545 (Alerts, critical issues)
✓ Alert Orange:      #FF9800 (Caution, missed doses)
```

### Neutral Colors
```
✓ Dark Text:         #1A1A1A (Readability)
✓ Light Text:        #FFFFFF (Contrast)
✓ Light Gray:        #F5F5F5 (Backgrounds)
✓ Medium Gray:       #E0E0E0 (Borders, dividers)
✓ Dark Gray:         #7A7A7A (Secondary text)
```

### Status Colors
```
✓ Success (Green):   #28a745 (Dose taken, no alerts)
✓ Pending (Blue):    #0066CC (Pending doses)
✓ Missed (Red):      #dc3545 (Missed doses)
✓ Warning (Orange):  #ff9800 (Low adherence, alerts)
✓ Info (Light Blue): #17a2b8 (Information, notifications)
```

---

## 2. TYPOGRAPHY

### Font Stack
```
Primary Font:   'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
Monospace:      'Courier New', monospace
Fallback:       system-ui, -apple-system, sans-serif
```

### Font Sizes (For Accessibility)
```
H1 (Page Title):     32px (bold)
H2 (Section Title):  24px (bold)
H3 (Subsection):     20px (bold)
Body Text:           16px (regular) ← Large for elderly
Labels:              14px (regular)
Small Text:          12px (regular)
Caption:             12px (lighter)
```

### Line Heights
```
Headings:            1.2
Body Text:           1.6 (Spaces content, improves readability)
Form Labels:         1.4
```

---

## 3. SPACING SYSTEM

```
Minimal Unit:     8px
Standard Unit:    16px
Large Unit:       24px
Extra Large:      32px

Margins:    8, 16, 24, 32px
Padding:    8, 16, 24, 32px
```

### Button Sizing
```
Small Button:      32px height (minimal use)
Standard Button:   44px height (large touch target)
Large Button:      56px height (primary CTAs)
Min Button Width:  120px
```

---

## 4. COMPONENT DESIGN

### Cards
- Border Radius: 8px
- Box Shadow: 0 2px 8px rgba(0,0,0,0.1)
- Padding: 24px
- Background: #FFFFFF
- Border: 1px solid #E0E0E0

### Buttons
- Border Radius: 6px
- Padding: 12px 24px
- Font Weight: 600
- Cursor: pointer
- Transition: all 0.3s ease
- Min Height: 44px (accessibility)

### Input Fields
- Border Radius: 6px
- Padding: 12px 16px
- Border: 2px solid #E0E0E0
- Font Size: 16px
- Focus: Border color #0066CC, outline none
- Placeholder: #999999 (visible)

### Tables
- Row Height: 48px (large)
- Cell Padding: 12px 16px
- Alternating Row Colors: #F5F5F5 / #FFFFFF
- Border Collapse: Separate
- Bottom Border on Cells: 1px solid #E0E0E0

---

## 5. DASHBOARD LAYOUT

### Common Structure
```
┌─────────────────────────────────────────────────┐
│  Header (Nav, User Menu)                        │
├──────────┬──────────────────────────────────────┤
│          │                                      │
│ Sidebar  │   Main Content Area                 │
│          │                                      │
│          │                                      │
│          │                                      │
└──────────┴──────────────────────────────────────┘
```

### Sidebar Navigation
```
- Width on Desktop: 280px
- Width on Mobile: Full overlay
- Background: #FFFFFF with subtle border
- Icons: 24px, left-aligned
- Text: 16px
- Hover: Background #F5F5F5
- Active: Border-left 4px #0066CC, background #E3F2FD

Menu Items (High visibility, large touch targets):
- 48px height per item
- Padding: 12px 16px
- Icon + Text combined
```

### Header
```
- Height: 64px (desktop), 56px (mobile)
- Background: #FFFFFF
- Border-bottom: 1px solid #E0E0E0
- Left: Logo/Branding
- Center: Page title
- Right: User menu, notifications, logout
- Sticky positioning
```

---

## 6. DASHBOARD SECTIONS

### Doctor Dashboard
1. **Top Stats Bar** - 4 cards with KPIs
   - Patients Assigned
   - Average Adherence
   - Alerts (Missed Doses)
   - Prescriptions (Active)

2. **Quick Actions** - 3 primary buttons
   - Add New Prescription
   - View All Patients
   - Search Patient

3. **Patient List** - Sortable table
   - Patient Name | Adherence Rate | Last Check-in | Status | Actions

4. **Alerts Section** - Timeline view
   - Missed Dose Alert
   - Low Adherence Alert
   - Prescription Expiring
   - With timestamps & action buttons

5. **Adherence Trends** - Chart
   - Line chart: 7-day, 30-day averages by patient

### Nurse Dashboard
1. **Today's Check-ins** - List
   - Patient name, check-in time, status (pending/complete)

2. **Medication Schedule** - Today's timeline
   - Time-based medication for assigned patients
   - Mark as taken / Not taken

3. **Alerts & Tasks** - Priority list
   - Overdue check-ins
   - Missed doses to verify
   - New patients assigned

4. **Palliative Care Patients** - Focused list
   - Special care patients with daily goals

### Admin Dashboard
1. **System Health** - Stats cards
   - Total Users | Total Patients | Alert Queue | API Health

2. **User Management** - List with filters
   - Username | Role | Status | Last Login | Actions (Edit/Suspend)

3. **Recent Activity** - Audit log
   - User | Action | Timestamp | Details

4. **System Status** - Health checks
   - Database: ✓ Connected
   - Redis: ✓ Connected
   - Celery: ✓ Running (tasks/queue)
   - Email: Status & test

---

## 7. RESPONSIVE DESIGN

### Breakpoints
```
Mobile:     < 768px   (Single column, full-width)
Tablet:     768-1024px (2 columns, adjustable)
Desktop:    > 1024px  (Full layout)
```

### Mobile Optimizations
- Stack all sections vertically
- Single-column layouts
- Full-width buttons
- Hamburger menu (sidebar becomes overlay)
- Larger touch targets (48px minimum)
- Remove unnecessary columns from tables

### Tablet Optimizations
- 2-column layouts where appropriate
- Sidebar visible but narrower
- Larger cards for readability

---

## 8. ACCESSIBILITY FEATURES

### Color Contrast
- Text on Background: Minimum 4.5:1 ratio (WCAG AA)
- Large Text (18px+): Minimum 3:1 ratio

### Font Features
```
Font Weight: 400-600 (avoid ultra-light)
Line Spacing: 1.5-1.6 for body text
Text Alignment: Left-aligned (easier to read)
Letter Spacing: Normal (no tightening)
```

### Interactive Elements
```
Minimum Size: 44px x 44px (touch targets)
Focus States: Visible (outline, color change)
Hover States: Visible feedback
Active States: Clear indication
Disabled States: Greyed out, cursor: not-allowed
```

### Form Accessibility
- Labels always visible (not placeholders only)
- Required fields marked with * and aria-required
- Error messages in red + icon
- Input validation on blur (not just submit)
- Success messages with checkmark

### Content Hierarchy
- Clear H1, H2, H3 structure
- Meaningful link text (avoid "click here")
- Lists for grouped information
- Proper semantic HTML

---

## 9. HEALTHCARE-SPECIFIC DESIGN

### For Elderly/Palliative Care Patients
```
Font Size: Minimum 18px for patient-facing content
High Contrast: Dark text on light background
Large Buttons: 56px+ height
Simple Language: Avoid jargon
Clear Status Indicators: Icons + text
Limited Options: No overwhelming choices
```

### For Medical Accuracy
```
Time Display: 24-hour format (medical standard)
Dates: DD/MM/YYYY or YYYY-MM-DD (ISO standard)
Dosage: Clear units (mg, ml, tablets)
Status: Medical terminology (taken, missed, pending)
```

### Trust-Building Elements
```
Hospital Logo: Visible on every page
Medical Terminology: Appropriate but understandable
Secure Icons: Padlock for security-related items
Confirmation Dialogs: For critical actions
Undo Options: Where possible
```

---

## 10. INTERACTION PATTERNS

### Buttons
```
Primary CTA:    Blue (#0066CC), white text
Secondary:      White background, blue border, blue text
Danger:         Red background, white text
Success:        Green background, white text
Disabled:       Gray background, gray text, no cursor
Loading:        Spinner, text changes to "Loading..."
```

### Forms
```
Validation:     Real-time on blur
Error Display:  Red border + error message below field
Success State:  Green checkmark (if needed)
Focus State:    Blue border, shadow
Placeholder:    Gray, visible
Label Position: Above input (mobile-friendly)
```

### Data Tables
```
Sorting:        Click column header
Filtering:      Dropdown or search above table
Pagination:     "Previous | 1 2 3 | Next" (large touch targets)
Row Selection:  Checkboxes (easy for batch actions)
Actions:        Right side (Edit, Delete, View)
Row Hover:      Subtle background change
```

### Notifications
```
Success Alert:  Green background, checkmark icon, dismissible
Error Alert:    Red background, X icon, persistent until fixed
Warning Alert:  Orange background, warning icon, dismissible
Info Alert:     Blue background, info icon, dismissible
Position:       Top-right (doesn't block content)
Auto-dismiss:   After 5 seconds (except errors)
```

---

## 11. PROFESSIONAL HOSPITAL AESTHETIC

### Design Principles
```
✓ Minimalism: Remove visual clutter
✓ Clarity: Every element has a purpose
✓ Consistency: Uniform styling across pages
✓ Safety: Error prevention, confirmation dialogs
✓ Efficiency: Reduce clicks to important information
✓ Trust: Professional, medical branding
✓ Accessibility: Inclusive design for all users
✓ Responsiveness: Works on all devices
```

### Visual Elements to Include
```
✓ Medical Icons: Pill bottle, stethoscope, heart, calendar
✓ Status Indicators: Dots, badges (green/red/yellow)
✓ Progress Bars: Medication adherence visualization
✓ Timeline: Dose history, check-in history
✓ Charts: Adherence trends (line, bar)
✓ Cards: Content containers with shadow
✓ Badges: Status labels (Active, Pending, Overdue)
```

### Elements to Avoid
```
✗ Bright, neon colors (unprofessional)
✗ Comic Sans or playful fonts
✗ Heavy drop shadows
✗ Cluttered layouts
✗ Small text (hard to read)
✗ Tiny buttons (hard to click)
✗ No clear information hierarchy
✗ Animations that distract
```

---

## 12. EXAMPLE LAYOUTS

### Doctor's Patient Card
```
┌─────────────────────────────────────┐
│ John Doe, 45y, Male          #ID123 │
├─────────────────────────────────────┤
│ Adherence: 92% (30-day)             │ ← Green status
│ Last Check-in: 2 hours ago          │
│ Active Prescriptions: 3             │
│ Status: ⚠️ 1 Missed Dose            │
├─────────────────────────────────────┤
│ [View] [Edit] [Prescriptions]       │
└─────────────────────────────────────┘
```

### Medication Timeline
```
Timeline for Today (Feb 9, 2024)

08:00 ✓ Amoxicillin 500mg          Confirmed
      With breakfast

14:00 ⏱️ Paracetamol 250mg          Pending
      Afternoon dose

20:00 ○ Metformin 850mg            Not yet due
      Before bed

[Show Full History]
```

### Adherence Chart
```
Medication Adherence - Last 30 Days

100% ││                    ╱╲
      ││                  ╱  ╲
80%  ││  ╱╲              ╱    ╲
      ││ ╱  ╲________╱ ╲      ╲
60%  ││╱                  ╲
      │└─────────────────────────
      1  5  10  15  20  25  30

Current: 92% ✓ Good
Target: 95%
```

---

## 13. STYLE GUIDE CHECKLIST

- [ ] Primary button (44px height, blue)
- [ ] Secondary button (44px height, outline)
- [ ] Form inputs (16px font, clear focus state)
- [ ] Data table (48px rows, clear headers)
- [ ] Alert cards (with icons, dismissible)
- [ ] Status badges (green/yellow/red)
- [ ] Navigation sidebar (280px, clear items)
- [ ] Header (64px, sticky)
- [ ] Patient cards (shadow, organized layout)
- [ ] Modal dialogs (centered, overlay)
- [ ] Error messages (red, actionable)
- [ ] Success messages (green, confirmatory)
- [ ] Loading state (spinner, text)
- [ ] Empty state (icon, text, CTA)

---

## 14. IMPLEMENTATION NOTES

### HTML Structure
```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DawaTrack Hospital</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header class="navbar">...</header>
    <div class="container">
        <aside class="sidebar">...</aside>
        <main class="main-content">...</main>
    </div>
    <script src="script.js"></script>
</body>
</html>
```

### CSS Classes Naming
```
.btn-primary      Primary button
.btn-secondary    Secondary button
.card             Card container
.alert-success    Success alert
.alert-error      Error alert
.table            Data table
.sidebar          Sidebar navigation
.navbar           Top navigation
.badge-success    Green badge
.badge-warning    Orange badge
```

### Responsive Classes
```
.container        Max width container
.row              Flex row
.col-md-6         Medium column (half width)
.col-lg-4         Large column (third width)
.d-none           Display none
.d-md-block       Show on medium+
@media (max-width: 768px)  Mobile styles
```

---

## 15. MEDICAL COMPLIANCE

### Privacy & Security
- Minimize personal data visible in lists
- Secure login page with clear messaging
- Session timeout warning
- No PHI (Protected Health Information) in URLs
- Encrypted communication indicators

### Medical Accuracy
- Time: 24-hour format (02:00 PM = 14:00)
- Dates: ISO format YYYY-MM-DD
- Dosage: Clear units (500mg, 2 tablets, 5ml)
- Status: Medical terminology (taken, missed, pending)

### Compliance Indicators
- HTTPS lock icon visible
- Terms & Privacy links in footer
- audit trail link for admin
- Logout status confirmation

---

## DESIGN TAKEAWAYS

✅ **Professional**: Looks like a real hospital system, not a side project  
✅ **Accessible**: Large fonts (16px+), high contrast, large buttons  
✅ **Efficient**: Minimal clicks to important information  
✅ **Safe**: Confirmation dialogs, clear error messages  
✅ **Mobile-Friendly**: Works on phones, tablets, desktops  
✅ **Hospital-Grade**: Trust-building design, medical terminology  
✅ **Low-Tech Friendly**: Simple interactions, large targets  
✅ **Elderly-Friendly**: Large text, clear navigation, simple language  

This design system ensures DawaTrack looks and feels like a professional hospital management system that elderly patients and low-tech users can confidently use.
