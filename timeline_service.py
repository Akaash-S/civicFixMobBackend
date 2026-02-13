"""
Timeline Service for CivicFix Backend
Manages immutable timeline events for issues
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)


class TimelineService:
    """Service for managing timeline events"""
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
    
    def create_event(
        self,
        issue_id: int,
        event_type: str,
        actor_type: str,
        actor_id: Optional[int],
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        image_urls: Optional[List[str]] = None
    ) -> Optional[int]:
        """
        Create a new timeline event
        
        Args:
            issue_id: Issue ID
            event_type: Type of event (ISSUE_CREATED, AI_VERIFIED, etc.)
            actor_type: Type of actor (CITIZEN, AI, GOVERNMENT, SYSTEM)
            actor_id: ID of the actor (user_id, null for AI/SYSTEM)
            description: Human-readable description
            metadata: Optional JSON metadata
            image_urls: Optional list of image URLs
        
        Returns:
            Event ID or None if failed
        """
        try:
            import json
            
            # Prepare metadata and image_urls as JSON strings
            metadata_json = json.dumps(metadata) if metadata else None
            image_urls_json = json.dumps(image_urls) if image_urls else None
            
            # Insert event
            result = self.db.session.execute(
                self.db.text("""
                    INSERT INTO timeline_events 
                    (issue_id, event_type, actor_type, actor_id, description, metadata, image_urls, created_at)
                    VALUES 
                    (:issue_id, :event_type, :actor_type, :actor_id, :description, :metadata, :image_urls, :created_at)
                    RETURNING id
                """),
                {
                    'issue_id': issue_id,
                    'event_type': event_type,
                    'actor_type': actor_type,
                    'actor_id': actor_id,
                    'description': description,
                    'metadata': metadata_json,
                    'image_urls': image_urls_json,
                    'created_at': datetime.utcnow()
                }
            )
            self.db.session.commit()
            
            event_id = result.fetchone()[0]
            logger.info(f"Timeline event created: #{event_id} for issue #{issue_id} - {event_type}")
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to create timeline event: {str(e)}")
            self.db.session.rollback()
            return None
    
    def get_events(self, issue_id: int) -> List[Dict[str, Any]]:
        """
        Get all timeline events for an issue
        
        Args:
            issue_id: Issue ID
        
        Returns:
            List of timeline events
        """
        try:
            import json
            
            result = self.db.session.execute(
                self.db.text("""
                    SELECT id, issue_id, event_type, actor_type, actor_id, 
                           description, metadata, image_urls, created_at
                    FROM timeline_events
                    WHERE issue_id = :issue_id
                    ORDER BY created_at ASC
                """),
                {'issue_id': issue_id}
            )
            
            events = []
            for row in result:
                event = {
                    'id': row[0],
                    'issue_id': row[1],
                    'event_type': row[2],
                    'actor_type': row[3],
                    'actor_id': row[4],
                    'description': row[5],
                    'metadata': json.loads(row[6]) if row[6] else None,
                    'image_urls': json.loads(row[7]) if row[7] else None,
                    'created_at': row[8].isoformat() if row[8] else None
                }
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get timeline events for issue #{issue_id}: {str(e)}")
            return []
    
    def get_event_count(self, issue_id: int) -> int:
        """
        Get count of timeline events for an issue
        
        Args:
            issue_id: Issue ID
        
        Returns:
            Number of events
        """
        try:
            result = self.db.session.execute(
                self.db.text("""
                    SELECT COUNT(*) FROM timeline_events WHERE issue_id = :issue_id
                """),
                {'issue_id': issue_id}
            )
            return result.fetchone()[0]
            
        except Exception as e:
            logger.error(f"Failed to get event count for issue #{issue_id}: {str(e)}")
            return 0


# Event type constants
class EventType:
    ISSUE_CREATED = 'ISSUE_CREATED'
    AI_VERIFICATION_STARTED = 'AI_VERIFICATION_STARTED'
    AI_VERIFICATION_COMPLETED = 'AI_VERIFICATION_COMPLETED'
    ISSUE_PUBLISHED = 'ISSUE_PUBLISHED'
    ISSUE_REJECTED = 'ISSUE_REJECTED'
    GOVERNMENT_ASSIGNED = 'GOVERNMENT_ASSIGNED'
    WORK_STARTED = 'WORK_STARTED'
    WORK_COMPLETED = 'WORK_COMPLETED'
    CROSS_VERIFICATION_STARTED = 'CROSS_VERIFICATION_STARTED'
    CROSS_VERIFICATION_COMPLETED = 'CROSS_VERIFICATION_COMPLETED'
    CITIZEN_VERIFICATION_REQUESTED = 'CITIZEN_VERIFICATION_REQUESTED'
    CITIZEN_VERIFICATION_COMPLETED = 'CITIZEN_VERIFICATION_COMPLETED'
    ISSUE_CLOSED = 'ISSUE_CLOSED'
    ISSUE_DISPUTED = 'ISSUE_DISPUTED'
    ESCALATION_TRIGGERED = 'ESCALATION_TRIGGERED'
    COMMENT_ADDED = 'COMMENT_ADDED'
    STATUS_CHANGED = 'STATUS_CHANGED'


# Actor type constants
class ActorType:
    CITIZEN = 'CITIZEN'
    AI = 'AI'
    GOVERNMENT = 'GOVERNMENT'
    SYSTEM = 'SYSTEM'
