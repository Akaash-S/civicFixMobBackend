"""
AI Service Client for CivicFix Backend
Handles communication with the AI Verification Service
"""

import os
import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# AI Service Configuration
AI_SERVICE_URL = os.environ.get('AI_SERVICE_URL', 'http://localhost:8001')
AI_SERVICE_API_KEY = os.environ.get('AI_SERVICE_API_KEY', '')
AI_SERVICE_ENABLED = os.environ.get('AI_SERVICE_ENABLED', 'true').lower() == 'true'
AI_SERVICE_TIMEOUT = int(os.environ.get('AI_SERVICE_TIMEOUT', '30'))


class AIServiceClient:
    """Client for communicating with AI Verification Service"""
    
    def __init__(self):
        self.base_url = AI_SERVICE_URL.rstrip('/')
        self.api_key = AI_SERVICE_API_KEY
        self.enabled = AI_SERVICE_ENABLED
        self.timeout = AI_SERVICE_TIMEOUT
        
        if self.enabled and not self.api_key:
            logger.warning("AI Service enabled but no API key configured")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        return headers
    
    async def verify_issue_initial(
        self,
        issue_id: int,
        image_urls: List[str],
        category: str,
        location: Dict[str, float],
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Verify a newly submitted issue
        
        Args:
            issue_id: Issue ID
            image_urls: List of image URLs
            category: Issue category
            location: Dict with latitude and longitude
            description: Issue description
            metadata: Optional additional metadata
        
        Returns:
            Verification result or None if service disabled/failed
        """
        if not self.enabled:
            logger.info("AI service disabled, skipping initial verification")
            return None
        
        try:
            payload = {
                "issue_id": issue_id,
                "image_urls": image_urls,
                "category": category,
                "location": {
                    "latitude": location.get('latitude'),
                    "longitude": location.get('longitude')
                },
                "description": description
            }
            
            if metadata:
                payload["metadata"] = metadata
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/verify/initial",
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"AI verification completed for issue #{issue_id}: {result.get('status')}")
                return result
                
        except httpx.TimeoutException:
            logger.error(f"AI verification timeout for issue #{issue_id}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"AI verification HTTP error for issue #{issue_id}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"AI verification failed for issue #{issue_id}: {str(e)}")
            return None
    
    async def verify_cross_check(
        self,
        issue_id: int,
        citizen_images: List[str],
        government_images: List[str],
        location: Dict[str, float],
        issue_category: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Perform cross-verification between citizen and government images
        
        Args:
            issue_id: Issue ID
            citizen_images: List of original citizen image URLs
            government_images: List of government resolution image URLs
            location: Dict with latitude and longitude
            issue_category: Issue category
            metadata: Optional additional metadata
        
        Returns:
            Cross-verification result or None if service disabled/failed
        """
        if not self.enabled:
            logger.info("AI service disabled, skipping cross-verification")
            return None
        
        try:
            payload = {
                "issue_id": issue_id,
                "citizen_images": citizen_images,
                "government_images": government_images,
                "location": {
                    "latitude": location.get('latitude'),
                    "longitude": location.get('longitude')
                },
                "issue_category": issue_category
            }
            
            if metadata:
                payload["metadata"] = metadata
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/verify/cross-check",
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Cross-verification completed for issue #{issue_id}: {result.get('status')}")
                return result
                
        except httpx.TimeoutException:
            logger.error(f"Cross-verification timeout for issue #{issue_id}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Cross-verification HTTP error for issue #{issue_id}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Cross-verification failed for issue #{issue_id}: {str(e)}")
            return None
    
    async def get_verification_status(self, issue_id: int) -> Optional[Dict[str, Any]]:
        """
        Get AI verification status for an issue
        
        Args:
            issue_id: Issue ID
        
        Returns:
            Verification status or None if not found/failed
        """
        if not self.enabled:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/verify/status/{issue_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"No verification found for issue #{issue_id}")
            else:
                logger.error(f"Failed to get verification status for issue #{issue_id}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to get verification status for issue #{issue_id}: {str(e)}")
            return None
    
    async def health_check(self) -> bool:
        """
        Check if AI service is healthy
        
        Returns:
            True if service is healthy, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()
                return data.get('status') == 'healthy'
                
        except Exception as e:
            logger.error(f"AI service health check failed: {str(e)}")
            return False


# Global AI service client instance
ai_client = AIServiceClient()
