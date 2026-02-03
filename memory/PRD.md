# Download Portal - Product Requirements Document

## Original Problem Statement
Build a feature-rich download portal website with Python (FastAPI), React, and MongoDB. Core features include: main page with downloads list, submission form, admin panel, user authentication, sponsored links, analytics, and trending section.

**Technology Pivot (User Request):** Complete rewrite in PHP, HTML, JavaScript, CSS, and MySQL, replicating all features from the original Python/React version.

## Target Audience
- Public users browsing and downloading files (games, software, movies, TV shows)
- Registered users submitting new downloads
- Administrators managing content and site settings

## Core Requirements

### Frontend (Public)
- [x] Downloads displayed in table format with columns: Name, Date, Type, Size, Site, Downloads
- [x] Type filtering (All, Games, Software, Movies, TV Shows)
- [x] Sorting options (Date, Downloads, Name)
- [x] Search functionality
- [x] Pagination
- [x] Top Downloads section (card grid)
- [x] Trending Downloads section (card grid)
- [x] Sponsored links in Top Downloads
- [x] Dark/Light theme toggle
- [x] Color-coded type badges
- [x] User registration/login
- [x] Download submission form with captcha
- [x] Rate limiting for submissions

### Admin Panel
- [x] Admin authentication (password-based)
- [x] Site settings management
- [x] Theme settings (mode + accent color with presets)
- [x] Site name typography (font family, weight, color)
- [x] Body typography (font family, weight)
- [x] Footer settings (enable/disable + templates)
- [x] Top Downloads settings (enable, count)
- [x] Trending Downloads settings (enable, count)
- [x] Sponsored Downloads management (1-5 items)
- [x] Sponsored analytics (24h, 7d, total clicks)
- [x] Submissions management (approve/reject/delete)
- [x] Downloads management (search/delete)
- [x] Admin credentials (email, password change)
- [x] Resend email settings
- [x] reCAPTCHA settings
- [x] Database seeding (5000 items)

## Technology Stack

### Original (Deprecated)
- Backend: Python FastAPI
- Frontend: React
- Database: MongoDB

### Current (PHP Version)
- Backend: Plain PHP (procedural)
- Frontend: HTML5, CSS3, JavaScript (ES6)
- Database: MySQL/MariaDB
- Location: `/app/download-portal-php/`

## Implementation Status

### Completed (Dec 2025)
- [x] Complete PHP application structure
- [x] Database schema (MySQL)
- [x] All API endpoints
- [x] Homepage with downloads table
- [x] Admin dashboard with all settings
- [x] Theme customization (dark/light + colors)
- [x] Typography settings (header + body)
- [x] Footer customization
- [x] Sponsored downloads with analytics
- [x] Downloads management (search/delete)
- [x] Password change functionality
- [x] Updated README documentation
- [x] ZIP package created

### Known Limitations
- PHP/MySQL cannot be tested in current environment (no LAMP stack)
- Email functionality requires Resend API key configuration
- reCAPTCHA requires Google API keys

## File Structure
```
/app/download-portal-php/
├── admin/                 # Admin panel pages
├── api/                   # PHP API endpoints
├── assets/css/            # Stylesheets
├── assets/js/             # JavaScript
├── config/                # Database configuration
├── includes/              # PHP helper functions
├── sql/                   # Database schema
├── index.php              # Homepage
├── submit.php             # Submission form
├── login.php              # Auth pages
└── README.md              # Documentation
```

## Deployment
1. Upload to PHP/MySQL web server
2. Configure `config/database.php`
3. Run `install.php` or import `sql/schema.sql`
4. Delete `install.php` after setup
5. Access `/admin/` to initialize admin credentials

## Next Steps / Backlog
- [ ] User testing on live PHP environment
- [ ] Advanced filters (date range, file size)
- [ ] Categories/tags filter on homepage
- [ ] User profile page with submission history
- [ ] Email verification for user registration
- [ ] Admin dashboard statistics charts
- [ ] Bulk submission approval
- [ ] Export downloads list (CSV)
