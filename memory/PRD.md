# Download Zone Portal - PRD

## Original Problem Statement
Build a download website where you can download software, games, movies, tv shows, all listed line by line, 50 items per page, paginated. First column is the download name, second column submission date, third column type (game, software, movie, tv show). In the top menu, a link to submit. On the submission form, a place to submit game, software, movie, tv show. Up to 10 submissions per day. Allow an admin section where the admin can check and allow the submissions through which will appear on the first page pushing previous submissions down. Also create themes for the front page which can be edited.

### Additional Requirements (Phase 2)
- Download counters/statistics per item in final column
- Search functionality
- File size/description fields (optional)
- Pre-fill database with 5000 items (mix of realistic sample + public domain)

## User Personas
1. **Visitors** - Browse and download content, search for specific items
2. **Submitters** - Users who submit new download links for approval
3. **Admin** - Manages submissions, controls themes, monitors statistics

## Core Requirements
- [x] Downloads listing with 50 items per page
- [x] Pagination system
- [x] Type filtering (Game, Software, Movie, TV Show)
- [x] Submission form for new downloads
- [x] Admin approval system
- [x] Theme system (dark/light + accent colors)
- [x] Retro 2000s warez aesthetic

## Architecture

### Backend (FastAPI) - Refactored Feb 2026
- **Port**: 8001 (internal)
- **Database**: MongoDB
- **API Prefix**: /api

**Directory Structure:**
```
/app/backend/
├── server.py              # Main app entry (54 lines)
├── models/
│   └── schemas.py         # Pydantic models (312 lines)
├── services/
│   ├── database.py        # DB connection (25 lines)
│   ├── email.py           # Email functions (244 lines)
│   ├── captcha.py         # Captcha logic (84 lines)
│   └── utils.py           # Helpers (45 lines)
└── routers/
    ├── downloads.py       # Download endpoints (325 lines)
    ├── auth.py            # Auth endpoints (158 lines)
    ├── submissions.py     # Submission endpoints (225 lines)
    └── admin.py           # Admin endpoints (728 lines)
```

### Frontend (React)
- **Port**: 3000
- **Styling**: Tailwind CSS + Custom retro CSS
- **Components**: Shadcn/UI

### Key Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/downloads | GET | List downloads (paginated, filterable, searchable) |
| /api/downloads/{id}/increment | POST | Increment download counter |
| /api/downloads/{id}/track | POST | Track download activity for trending |
| /api/downloads/top | GET | Get top downloads with sponsored |
| /api/downloads/trending | GET | Get trending downloads |
| /api/sponsored/{id}/click | POST | Track sponsored link click |
| /api/admin/sponsored/analytics | GET | Get sponsored click analytics |
| /api/submissions | POST | Create new submission |
| /api/admin/login | POST | Admin authentication |
| /api/admin/submissions | GET | List submissions |
| /api/admin/submissions/{id}/approve | POST | Approve submission |
| /api/admin/submissions/{id}/reject | POST | Reject submission |
| /api/theme | GET/PUT | Get/Update theme settings |
| /api/stats | GET | Get database statistics |
| /api/admin/seed | POST | Seed database with 5000 items |

## What's Been Implemented

### Phase 1 (Initial MVP) - Jan 2026
- Home page with downloads table
- Type filtering (ALL, Game, Software, Movie, TV Show)
- Pagination (50 items per page)
- Submit page with terminal-style form
- Admin login (password: admin123)
- Admin dashboard with submission management
- Theme editor (dark/light mode + accent colors)
- Retro Matrix/Win95 aesthetic

### Phase 2 (Enhancements) - Jan 2026
- Search functionality (regex search on name)
- Download counters with K/M formatting
- File size column
- Description field (optional)
- Database statistics (total + by type)
- Seeded 5000 items

### Phase 3 (Advanced Features) - Jan 2026
- Top Downloads section
- Sponsored Downloads (1-5 admin-configured)
- Rate limiting (configurable)
- Advanced filters (date range, size)
- Categories/tags system
- User authentication with reCAPTCHA
- Multi-item submission mode
- Site branding customization
- Footer customization
- Admin password management via DB
- Email notifications (Resend integration)
- Submission approval workflow
- Auto-approve submissions toggle

### Phase 4 (Analytics & Trending) - Feb 2026
- **Sponsored Links Analytics**: Track clicks on sponsored downloads with 24h/7d/total metrics
- **Trending Downloads Section**: Display downloads with recent high activity on homepage
- **Admin Trending Toggle**: Enable/disable trending section via admin panel
- **Download Activity Tracking**: Record download activity for trending calculation
- **Dedicated Submissions Page**: New `/admin/submissions` page with:
  - Status filters (ALL, PENDING, APPROVED, REJECTED)
  - Bulk selection (Select All + individual checkboxes)
  - Bulk actions (Approve/Delete multiple submissions)
  - Red notification badge showing pending count
- **Email Notification on Approval**: Submitters receive an email when their submission is approved (requires Resend configuration)

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn/UI, React Router
- **Backend**: FastAPI, Motor (async MongoDB), Pydantic
- **Database**: MongoDB
- **Email**: Resend
- **Fonts**: Press Start 2P, VT323, JetBrains Mono

## Credentials
- **Admin Password**: admin123 (stored in DB, configurable via admin UI)
- **Admin Email**: admin@example.com

## Prioritized Backlog

### P0 (Critical)
- All features implemented ✅

### P1 (High) - COMPLETED
- [x] Download counters/statistics per item
- [x] Search functionality
- [x] Sorting options (date, downloads, name)
- [x] Rate limiting (configurable 5-100/day)
- [x] Advanced search filters (date range)
- [x] Top downloads section
- [x] Top downloads toggle (enable/disable)
- [x] Top downloads count (5-20)
- [x] Sponsored downloads (1-5 admin-configured)
- [x] Sponsored Links Analytics
- [x] Trending Downloads Section (with admin toggle)
- [x] Dedicated Submissions Management Page with bulk actions
- [x] Email Notification on Submission Approval

### P2 (Medium)
- [ ] Download history tracking
- [ ] Bulk download selection
- [x] Refactor server.py into proper project structure ✅

### P3 (Nice to have)
- [ ] User comments on downloads
- [ ] Rating system
- [ ] Report broken links
- [ ] Extended admin analytics dashboard

## Next Tasks
1. **(P2)** Add download history tracking per user
2. **(P2)** Implement bulk download selection

## Test Credentials
- **Admin Password**: admin123
- **Admin Email**: admin@example.com
