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

### Backend (FastAPI)
- **Port**: 8001 (internal)
- **Database**: MongoDB
- **API Prefix**: /api

### Frontend (React)
- **Port**: 3000
- **Styling**: Tailwind CSS + Custom retro CSS
- **Components**: Shadcn/UI

### Key Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/downloads | GET | List downloads (paginated, filterable, searchable) |
| /api/downloads/{id}/increment | POST | Increment download counter |
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
- Seeded 5000 items:
  - ~1500 Games (fictional titles)
  - ~1200 Software (mix of open source + fictional)
  - ~1300 Movies (fictional)
  - ~1000 TV Shows (fictional series with episodes)

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn/UI, React Router
- **Backend**: FastAPI, Motor (async MongoDB), Pydantic
- **Database**: MongoDB
- **Fonts**: Press Start 2P, VT323, JetBrains Mono

## Credentials
- **Admin Password**: admin123 (configurable via ADMIN_PASSWORD env var)

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

### P2 (Medium)
- [ ] User authentication for submitters
- [ ] Download history tracking
- [ ] Categories/tags system
- [ ] File size range filter
- [ ] Bulk download selection

### P3 (Nice to have)
- [ ] User comments on downloads
- [ ] Rating system
- [ ] Report broken links
- [ ] Admin analytics dashboard

## Next Tasks
1. Add user authentication for submitters
2. Add file size range filter
3. Implement categories/tags system
