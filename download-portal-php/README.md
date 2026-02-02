# Download Portal - PHP Version

A feature-rich download portal website built with plain PHP, MySQL, HTML, CSS, and JavaScript. Includes user authentication, admin panel, submissions management, sponsored links, trending downloads, and more.

## Features

### Public Features
- **Downloads Listing** - Browse downloads with pagination, search, and filtering
- **Type Filtering** - Filter by Games, Software, Movies, TV Shows
- **Sorting Options** - Sort by date, downloads, name
- **Advanced Search** - Search by name, tags, category
- **Top Downloads** - Display most downloaded items
- **Trending Section** - Show currently trending downloads
- **Sponsored Links** - Highlighted sponsored downloads with click tracking
- **Dark/Light Theme** - Toggle between themes
- **User Registration** - Create account with captcha protection
- **Submit Downloads** - Users can submit new content for approval
- **Rate Limiting** - Configurable daily submission limits

### Admin Features
- **Dashboard** - Overview of site settings and statistics
- **Submissions Management** - Approve, reject, or delete submissions
- **Sponsored Downloads** - Add/remove sponsored items with analytics
- **Top Downloads Toggle** - Enable/disable and configure count
- **Trending Toggle** - Enable/disable trending section
- **Site Customization** - Change site name, footer text
- **Email Notifications** - Resend integration for emails
- **reCAPTCHA Support** - Optional Google reCAPTCHA v2
- **Database Seeding** - Populate with 5000 sample items

## Requirements

- PHP 7.4 or higher
- MySQL 5.7 or higher (or MariaDB 10.3+)
- Apache with mod_rewrite enabled (or Nginx)
- PDO MySQL extension
- JSON extension

## Installation

### Method 1: Web Installer (Recommended)

1. Upload all files to your web server
2. Create a MySQL database (or let the installer create it)
3. Navigate to `http://yourdomain.com/install.php`
4. Fill in your database credentials
5. Click "Install"
6. **Delete `install.php` after installation!**

### Method 2: Manual Installation

1. **Upload Files**
   ```bash
   # Upload all files to your web server
   # Example: /var/www/html/download-portal/
   ```

2. **Create Database**
   ```bash
   mysql -u root -p
   ```
   ```sql
   CREATE DATABASE download_portal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

3. **Import Schema**
   ```bash
   mysql -u root -p download_portal < sql/schema.sql
   ```

4. **Configure Database Connection**
   
   Edit `config/database.php`:
   ```php
   define('DB_HOST', 'localhost');
   define('DB_NAME', 'download_portal');
   define('DB_USER', 'your_username');
   define('DB_PASS', 'your_password');
   define('SITE_URL', 'https://yourdomain.com/download-portal');
   ```

5. **Set Permissions**
   ```bash
   chmod 755 -R /path/to/download-portal/
   chmod 644 config/database.php
   ```

6. **Delete install.php**
   ```bash
   rm install.php
   ```

## Directory Structure

```
download-portal-php/
├── admin/                 # Admin panel
│   ├── index.php         # Admin dashboard
│   └── submissions.php   # Submissions management
├── api/                   # API endpoints
│   ├── admin.php         # Admin API
│   ├── auth.php          # Authentication API
│   ├── downloads.php     # Downloads API
│   ├── settings.php      # Settings API
│   ├── submissions.php   # Submissions API
│   └── theme.php         # Theme API
├── assets/
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   └── js/
│       └── app.js        # Main JavaScript
├── config/
│   └── database.php      # Database configuration
├── includes/
│   ├── auth.php          # Authentication functions
│   ├── captcha.php       # Captcha functions
│   ├── email.php         # Email functions
│   └── functions.php     # Helper functions
├── sql/
│   └── schema.sql        # Database schema
├── .htaccess             # Apache configuration
├── index.php             # Homepage
├── install.php           # Web installer (DELETE AFTER USE)
├── login.php             # Login/Register page
├── submit.php            # Submit download page
└── README.md             # This file
```

## Configuration

### Email Notifications (Resend)

1. Sign up at [resend.com](https://resend.com)
2. Get your API key
3. Go to Admin Dashboard → configure Resend API key
4. Or edit `config/database.php`:
   ```php
   define('RESEND_API_KEY', 'your_api_key');
   define('SENDER_EMAIL', 'noreply@yourdomain.com');
   ```

### Google reCAPTCHA v2

1. Go to [Google reCAPTCHA](https://www.google.com/recaptcha/admin)
2. Register your site for reCAPTCHA v2 "I'm not a robot"
3. Go to Admin Dashboard → enter Site Key and Secret Key
4. Enable for submissions and/or authentication

### Nginx Configuration

If using Nginx instead of Apache:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /var/www/download-portal;
    index index.php;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }

    location ~ /\.(ht|git) {
        deny all;
    }

    location ~ ^/(config|includes)/ {
        deny all;
    }
}
```

## First Time Setup

1. Navigate to `/admin/`
2. You'll be prompted to create admin credentials (email + password)
3. Log in with your new password
4. Configure site settings as needed
5. Optionally seed the database with sample data

## API Endpoints

### Public Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/downloads.php?action=list` | GET | List downloads with pagination |
| `/api/downloads.php?action=top` | GET | Get top downloads |
| `/api/downloads.php?action=trending` | GET | Get trending downloads |
| `/api/downloads.php?action=track&id={id}` | POST | Track download click |
| `/api/submissions.php?action=create` | POST | Submit new download |
| `/api/submissions.php?action=captcha` | GET | Generate captcha |
| `/api/submissions.php?action=remaining` | GET | Check remaining submissions |
| `/api/settings.php?action=get` | GET | Get public settings |
| `/api/settings.php?action=stats` | GET | Get download statistics |
| `/api/theme.php` | GET/POST | Get/Update theme |
| `/api/auth.php?action=register` | POST | Register user |
| `/api/auth.php?action=login` | POST | Login user |

### Admin Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin.php?action=login` | POST | Admin login |
| `/api/admin.php?action=submissions` | GET | List submissions |
| `/api/admin.php?action=approve&id={id}` | POST | Approve submission |
| `/api/admin.php?action=reject&id={id}` | POST | Reject submission |
| `/api/admin.php?action=sponsored-analytics` | GET | Get sponsored click analytics |
| `/api/admin.php?action=seed` | POST | Seed database |
| `/api/settings.php?action=update` | POST | Update settings |

## Security Notes

1. **Delete `install.php`** after installation
2. Keep `config/` and `includes/` directories protected (done via `.htaccess`)
3. Use HTTPS in production
4. Change default admin password immediately
5. Keep PHP and MySQL updated
6. Set proper file permissions (644 for files, 755 for directories)
7. Consider adding additional rate limiting at server level

## Upgrading

1. Backup your database
2. Backup `config/database.php`
3. Upload new files (except `config/database.php`)
4. Run any new SQL migrations if needed
5. Clear browser cache

## Troubleshooting

### "Database connection failed"
- Check database credentials in `config/database.php`
- Ensure MySQL is running
- Verify database exists

### Styles not loading
- Check file permissions on `assets/` directory
- Verify `.htaccess` is not blocking static files

### Admin login not working
- Clear browser cookies
- Check `session_start()` is working (sessions enabled in PHP)
- Try the fallback password from `config/database.php`

### Captcha always fails
- Check server time is correct
- Ensure sessions are working
- Try clearing expired captchas: `DELETE FROM captchas WHERE expires_at < NOW()`

## License

MIT License - Feel free to use and modify for your projects.

## Support

For issues and feature requests, please create an issue on the repository.
