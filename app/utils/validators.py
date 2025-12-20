import re
from app.models.issue import IssueSeverity, IssuePriority

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_coordinates(lat, lng):
    """Validate latitude and longitude"""
    try:
        lat = float(lat)
        lng = float(lng)
        return -90 <= lat <= 90 and -180 <= lng <= 180
    except (ValueError, TypeError):
        return False

def validate_issue_data(data):
    """Validate issue creation data"""
    required_fields = ['category', 'latitude', 'longitude']
    
    # Check required fields
    for field in required_fields:
        if field not in data or data[field] is None:
            return f"Field '{field}' is required"
    
    # Validate coordinates
    if not validate_coordinates(data['latitude'], data['longitude']):
        return "Invalid latitude or longitude coordinates"
    
    # Validate category
    valid_categories = [
        'Pothole', 'Street Light', 'Garbage', 'Graffiti', 
        'Traffic Signal', 'Road Damage', 'Sidewalk Issue', 
        'Water Leak', 'Noise Complaint', 'Other'
    ]
    
    if data['category'] not in valid_categories:
        return f"Invalid category. Must be one of: {', '.join(valid_categories)}"
    
    # Validate severity if provided
    if 'severity' in data:
        try:
            IssueSeverity(data['severity'])
        except ValueError:
            return "Invalid severity. Must be one of: LOW, MEDIUM, HIGH, CRITICAL"
    
    # Validate priority if provided
    if 'priority' in data:
        try:
            IssuePriority(data['priority'])
        except ValueError:
            return "Invalid priority. Must be one of: LOW, MEDIUM, HIGH, URGENT"
    
    # Validate description length
    if 'description' in data and data['description']:
        if len(data['description']) > 1000:
            return "Description must be less than 1000 characters"
    
    # Validate address length
    if 'address' in data and data['address']:
        if len(data['address']) > 255:
            return "Address must be less than 255 characters"
    
    # Validate media URLs if provided
    if 'media_urls' in data:
        if not isinstance(data['media_urls'], list):
            return "media_urls must be a list"
        
        if len(data['media_urls']) > 5:
            return "Maximum 5 media files allowed per issue"
        
        for media in data['media_urls']:
            if not isinstance(media, dict):
                return "Each media item must be an object"
            
            if 'url' not in media or 'type' not in media:
                return "Each media item must have 'url' and 'type' fields"
            
            if media['type'] not in ['IMAGE', 'VIDEO']:
                return "Media type must be 'IMAGE' or 'VIDEO'"
    
    return None  # No validation errors

def validate_user_data(data):
    """Validate user data"""
    if 'email' in data and not validate_email(data['email']):
        return "Invalid email format"
    
    if 'name' in data:
        if not data['name'] or len(data['name'].strip()) < 1:
            return "Name is required"
        
        if len(data['name']) > 100:
            return "Name must be less than 100 characters"
    
    return None