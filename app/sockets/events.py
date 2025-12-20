from flask_socketio import emit, join_room, leave_room, disconnect, request
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def register_socket_events(socketio):
    """Register Socket.IO event handlers"""
    
    @socketio.on('connect')
    def handle_connect(auth):
        """Handle client connection"""
        logger.info(f"Client connected: {request.sid}")
        emit('connected', {'message': 'Connected to CivicFix real-time service'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('join_location')
    def handle_join_location(data):
        """Join location-based room for real-time updates"""
        try:
            lat = data.get('latitude')
            lng = data.get('longitude')
            radius = data.get('radius', 10)  # km
            
            if lat is None or lng is None:
                emit('error', {'message': 'Latitude and longitude are required'})
                return
            
            # Create room name based on location grid
            # This is a simple implementation - in production, you might use geohashing
            lat_grid = int(lat * 100) // 10  # ~1km grid
            lng_grid = int(lng * 100) // 10
            room_name = f"location_{lat_grid}_{lng_grid}"
            
            join_room(room_name)
            emit('joined_location', {
                'room': room_name,
                'message': f'Joined location updates for area around {lat}, {lng}'
            })
            
            logger.info(f"Client joined location room: {room_name}")
            
        except Exception as e:
            logger.error(f"Error joining location room: {str(e)}")
            emit('error', {'message': 'Failed to join location updates'})
    
    @socketio.on('leave_location')
    def handle_leave_location(data):
        """Leave location-based room"""
        try:
            lat = data.get('latitude')
            lng = data.get('longitude')
            
            if lat is None or lng is None:
                emit('error', {'message': 'Latitude and longitude are required'})
                return
            
            lat_grid = int(lat * 100) // 10
            lng_grid = int(lng * 100) // 10
            room_name = f"location_{lat_grid}_{lng_grid}"
            
            leave_room(room_name)
            emit('left_location', {
                'room': room_name,
                'message': 'Left location updates'
            })
            
            logger.info(f"Client left location room: {room_name}")
            
        except Exception as e:
            logger.error(f"Error leaving location room: {str(e)}")
            emit('error', {'message': 'Failed to leave location updates'})
    
    @socketio.on('join_issue')
    def handle_join_issue(data):
        """Join issue-specific room for updates"""
        try:
            issue_id = data.get('issue_id')
            
            if not issue_id:
                emit('error', {'message': 'Issue ID is required'})
                return
            
            room_name = f"issue_{issue_id}"
            join_room(room_name)
            
            emit('joined_issue', {
                'issue_id': issue_id,
                'message': f'Joined updates for issue {issue_id}'
            })
            
            logger.info(f"Client joined issue room: {room_name}")
            
        except Exception as e:
            logger.error(f"Error joining issue room: {str(e)}")
            emit('error', {'message': 'Failed to join issue updates'})
    
    @socketio.on('leave_issue')
    def handle_leave_issue(data):
        """Leave issue-specific room"""
        try:
            issue_id = data.get('issue_id')
            
            if not issue_id:
                emit('error', {'message': 'Issue ID is required'})
                return
            
            room_name = f"issue_{issue_id}"
            leave_room(room_name)
            
            emit('left_issue', {
                'issue_id': issue_id,
                'message': 'Left issue updates'
            })
            
            logger.info(f"Client left issue room: {room_name}")
            
        except Exception as e:
            logger.error(f"Error leaving issue room: {str(e)}")
            emit('error', {'message': 'Failed to leave issue updates'})
    
    # Utility functions for emitting events from other parts of the app
    def emit_issue_created(issue_data):
        """Emit issue created event to location-based rooms"""
        try:
            lat = issue_data.get('latitude')
            lng = issue_data.get('longitude')
            
            if lat and lng:
                lat_grid = int(lat * 100) // 10
                lng_grid = int(lng * 100) // 10
                room_name = f"location_{lat_grid}_{lng_grid}"
                
                socketio.emit('issue_created', issue_data, room=room_name)
                logger.info(f"Emitted issue_created to room {room_name}")
        
        except Exception as e:
            logger.error(f"Error emitting issue_created: {str(e)}")
    
    def emit_issue_status_updated(issue_id, status_data):
        """Emit issue status update to issue room"""
        try:
            room_name = f"issue_{issue_id}"
            socketio.emit('issue_status_updated', status_data, room=room_name)
            logger.info(f"Emitted issue_status_updated to room {room_name}")
        
        except Exception as e:
            logger.error(f"Error emitting issue_status_updated: {str(e)}")
    
    def emit_issue_upvoted(issue_id, upvote_data):
        """Emit issue upvote to issue room"""
        try:
            room_name = f"issue_{issue_id}"
            socketio.emit('issue_upvoted', upvote_data, room=room_name)
            logger.info(f"Emitted issue_upvoted to room {room_name}")
        
        except Exception as e:
            logger.error(f"Error emitting issue_upvoted: {str(e)}")
    
    def emit_comment_added(issue_id, comment_data):
        """Emit new comment to issue room"""
        try:
            room_name = f"issue_{issue_id}"
            socketio.emit('comment_added', comment_data, room=room_name)
            logger.info(f"Emitted comment_added to room {room_name}")
        
        except Exception as e:
            logger.error(f"Error emitting comment_added: {str(e)}")
    
    def emit_notification(user_id, notification_data):
        """Emit notification to specific user"""
        try:
            room_name = f"user_{user_id}"
            socketio.emit('notification_new', notification_data, room=room_name)
            logger.info(f"Emitted notification to user {user_id}")
        
        except Exception as e:
            logger.error(f"Error emitting notification: {str(e)}")
    
    # Store utility functions in socketio for access from other modules
    socketio.emit_issue_created = emit_issue_created
    socketio.emit_issue_status_updated = emit_issue_status_updated
    socketio.emit_issue_upvoted = emit_issue_upvoted
    socketio.emit_comment_added = emit_comment_added
    socketio.emit_notification = emit_notification