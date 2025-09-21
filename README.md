# Civic Issue Reporting and Resolution System

A comprehensive backend system for crowdsourced civic issue reporting and resolution, built with FastAPI and SQLAlchemy.

## Features

### Core Functionality
- **User Management**: Citizen registration, authentication, and role-based access control
- **Issue Reporting**: Submit issues with photos, location data, and detailed descriptions
- **Issue Tracking**: Real-time status updates and progress tracking
- **Automated Routing**: Intelligent department assignment based on issue category
- **Notification System**: Real-time notifications for status changes and updates
- **Analytics Dashboard**: Comprehensive reporting and analytics for administrators

### Key Components

#### 1. User Roles
- **Citizens**: Can report issues and track their submissions
- **Department Staff**: Can manage assigned issues and update status
- **Administrators**: Full system access with analytics and management capabilities

#### 2. Issue Categories
- Road Maintenance
- Streetlight Issues
- Sanitation Problems
- Water Supply Issues
- Electricity Problems
- Traffic Issues
- Parks and Recreation
- Other

#### 3. Issue Status Flow
- **Submitted** → **Acknowledged** → **In Progress** → **Resolved** → **Closed**
- **Rejected** (if issue is invalid)

#### 4. Priority Levels
- **Urgent**: Critical issues requiring immediate attention
- **High**: Important issues requiring prompt attention
- **Medium**: Standard issues (default)
- **Low**: Minor issues

## API Endpoints

### Authentication
- `POST /signup` - Register a new user
- `POST /login` - Login and get access token
- `GET /me` - Get current user information

### Issues Management
- `POST /issues/` - Create a new issue report
- `GET /issues/` - Get issues with filtering options
- `GET /issues/{issue_id}` - Get specific issue details
- `PUT /issues/{issue_id}` - Update issue (admin/staff only)
- `POST /issues/{issue_id}/upload-photo` - Upload photo for issue
- `GET /issues/{issue_id}/updates` - Get issue update history
- `GET /issues/nearby/{latitude}/{longitude}` - Find nearby issues

### User Management
- `GET /users/` - Get all users (admin only)
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update current user profile
- `PUT /users/{user_id}` - Update user (admin only)
- `DELETE /users/{user_id}` - Deactivate user (admin only)
- `GET /users/staff` - Get staff users

### Notifications
- `GET /notifications/` - Get user notifications
- `GET /notifications/unread-count` - Get unread notification count
- `PUT /notifications/{notification_id}/read` - Mark notification as read
- `PUT /notifications/mark-all-read` - Mark all notifications as read
- `DELETE /notifications/{notification_id}` - Delete notification

### Admin Dashboard
- `GET /admin/dashboard` - Get comprehensive dashboard statistics
- `GET /admin/issues/analytics` - Get detailed issue analytics
- `GET /admin/comprehensive-report` - Generate comprehensive analytics report
- `GET /admin/system-health` - Get system health metrics
- `GET /admin/issues/priority-queue` - Get priority queue for staff
- `POST /admin/issues/{issue_id}/auto-route` - Auto-route issue to department
- `POST /admin/departments` - Create new department
- `GET /admin/departments` - Get all departments
- `POST /admin/issues/{issue_id}/assign` - Assign issue to staff member

## Installation and Setup

### Prerequisites
- Python 3.8+
- SQLite (or PostgreSQL for production)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd civic-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the API**
   - API Base URL: `http://localhost:8000`
   - Interactive API Documentation: `http://localhost:8000/docs`
   - Alternative Documentation: `http://localhost:8000/redoc`

## Database Schema

### Core Tables
- **users**: User accounts with role-based access
- **issues**: Civic issue reports with location and media data
- **departments**: Government departments for issue routing
- **issue_updates**: Status change history and comments
- **notifications**: User notifications for system events

### Key Relationships
- Users can report multiple issues
- Issues belong to departments and can be assigned to staff
- Issue updates track the complete lifecycle
- Notifications keep users informed of changes

## Configuration

### Environment Variables
Create a `.env` file with the following variables:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./civic.db
GEOCODING_API_KEY=your-geocoding-api-key
```

### Database Configuration
The system uses SQLite by default for development. For production, configure PostgreSQL:

```python
DATABASE_URL = "postgresql://user:password@localhost/civic_db"
```

## Features in Detail

### 1. Automated Issue Routing
The system automatically routes issues to appropriate departments based on:
- Issue category (road maintenance → Public Works)
- Location data (if available)
- Historical routing patterns

### 2. Priority Management
Issues are automatically prioritized based on:
- User-selected priority level
- Issue category criticality
- Location importance
- Historical resolution times

### 3. Real-time Notifications
Users receive notifications for:
- Issue status changes
- Assignment updates
- New comments
- Resolution confirmations

### 4. Analytics and Reporting
Comprehensive analytics include:
- Issue volume trends
- Resolution time metrics
- Department performance
- Geographic hotspots
- User engagement metrics

### 5. Location Services
- GPS coordinate capture
- Address geocoding
- Nearby issue detection
- Geographic clustering
- Hotspot identification

## Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control
- Input validation and sanitization
- CORS configuration for web clients

## API Usage Examples

### Register a New User
```bash
curl -X POST "http://localhost:8000/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepassword",
    "phone": "+1234567890"
  }'
```

### Login
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john@example.com&password=securepassword"
```

### Create an Issue
```bash
curl -X POST "http://localhost:8000/issues/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Pothole on Main Street",
    "description": "Large pothole causing traffic issues",
    "category": "road_maintenance",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "address": "123 Main Street, City, State"
  }'
```

## Development

### Project Structure
```
civic-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models.py            # SQLAlchemy models
│   ├── database.py          # Database configuration
│   ├── auth.py              # Authentication utilities
│   ├── routers/             # API route modules
│   │   ├── issues.py
│   │   ├── users.py
│   │   ├── admin.py
│   │   └── notifications.py
│   └── services/            # Business logic services
│       ├── analytics.py
│       ├── routing.py
│       ├── notifications.py
│       └── location.py
├── requirements.txt
└── README.md
```

### Adding New Features
1. Create new models in `models.py`
2. Add API endpoints in appropriate router files
3. Implement business logic in service classes
4. Update database schema as needed
5. Add comprehensive tests

## Production Deployment

### Recommended Setup
- Use PostgreSQL for production database
- Configure proper CORS settings
- Set up SSL/TLS certificates
- Use environment variables for secrets
- Implement proper logging
- Set up monitoring and alerting

### Scaling Considerations
- Database connection pooling
- Redis for caching
- CDN for static file serving
- Load balancing for multiple instances
- Background task processing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact the development team or create an issue in the repository.
