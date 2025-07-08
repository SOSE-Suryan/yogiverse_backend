# Follower App - Search and Remove Follower Features

## Overview
This document describes the new search functionality and remove follower API that have been added to the follower app.

## Search Functionality

### Available Search Endpoints
All list endpoints now support search functionality through the `search` query parameter:

1. **Followers List**: `/followers/?search=<query>`
2. **Following List**: `/following/?search=<query>`
3. **Pending Requests**: `/pending-requests/?search=<query>`
4. **Notifications**: `/notifications/?search=<query>`

### Search Parameters
- **search**: String to search for in usernames, first names, and last names
- **user_id**: (Optional) To view another user's followers/following list

### Search Behavior
- Case-insensitive search
- Searches across username, first_name, and last_name fields
- For notifications, also searches title, body, and sender information
- Returns paginated results

### Example Usage

```bash
# Search followers by username
GET /followers/?search=john

# Search following by first name
GET /following/?search=Alice

# Search pending requests
GET /pending-requests/?search=pending_user

# Search notifications
GET /notifications/?search=follow request
```

## Remove Follower API

### Endpoint
`POST /remove-follower/`

### Purpose
Allows users to remove followers from their followers list. This gives users control over who can follow them.

### Request Body
```json
{
    "follower_id": 123
}
```

### Response
```json
{
    "success": true,
    "message": "Follower removed successfully",
    "data": {
        "removed_follower_id": 123,
        "removed_follower_username": "username"
    }
}
```

### Error Responses

#### Missing follower_id
```json
{
    "success": false,
    "message": "follower_id is required",
    "data": null
}
```

#### User not following
```json
{
    "success": false,
    "message": "This user is not following you",
    "data": null
}
```

#### Invalid ID format
```json
{
    "success": false,
    "message": "Invalid follower_id format",
    "data": null
}
```

### Example Usage

```bash
# Remove a follower
POST /remove-follower/
Content-Type: application/json

{
    "follower_id": 123
}
```

## WebSocket Updates
Both search and remove follower operations trigger WebSocket updates to keep follower counts synchronized across all connected clients.

## Logging
All operations are logged for debugging and monitoring purposes:
- Search queries are logged with user ID and search term
- Remove follower operations are logged with user IDs involved

## Testing
Comprehensive test cases have been added to verify:
- Search functionality across all endpoints
- Remove follower API with various scenarios
- Error handling and edge cases
- Authentication requirements

Run tests with:
```bash
python manage.py test follower_app
```

## Security Considerations
- All endpoints require authentication
- Users can only remove followers from their own followers list
- Search results respect user privacy and only show approved relationships
- Input validation prevents SQL injection and other attacks 