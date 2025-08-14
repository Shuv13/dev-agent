"""Comprehensive error handling utilities"""

import logging
import traceback
from typing import Any, Dict, Optional, Type, Union
from enum import Enum
import time


class ErrorCategory(Enum):
    """Categories of errors"""
    USER_INPUT = "user_input"
    FILE_SYSTEM = "file_system"
    LLM_PROVIDER = "llm_provider"
    NETWORK = "network"
    VALIDATION = "validation"
    INTERNAL = "internal"


class DevAgentError(Exception):
    """Base exception for DevAgent"""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.INTERNAL, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.details = details or {}
        self.timestamp = time.time()


class UserInputError(DevAgentError):
    """Error in user input"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.USER_INPUT, details)


class FileSystemError(DevAgentError):
    """File system related error"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.FILE_SYSTEM, details)


class LLMProviderError(DevAgentError):
    """LLM provider related error"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.LLM_PROVIDER, details)


class ValidationError(DevAgentError):
    """Validation error"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.VALIDATION, details)


class ErrorHandler:
    """Central error handling system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_counts = {}
        self.recovery_strategies = {
            ErrorCategory.LLM_PROVIDER: self._handle_llm_error,
            ErrorCategory.FILE_SYSTEM: self._handle_file_error,
            ErrorCategory.NETWORK: self._handle_network_error,
            ErrorCategory.USER_INPUT: self._handle_user_error,
            ErrorCategory.VALIDATION: self._handle_validation_error,
        }
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle an error and return recovery information"""
        context = context or {}
        
        # Convert to DevAgentError if needed
        if not isinstance(error, DevAgentError):
            error = DevAgentError(str(error), ErrorCategory.INTERNAL, {"original_error": str(error)})
        
        # Log error
        self._log_error(error, context)
        
        # Track error count
        self._track_error(error)
        
        # Attempt recovery
        recovery_info = self._attempt_recovery(error, context)
        
        return {
            "error": error,
            "category": error.category.value,
            "message": error.message,
            "details": error.details,
            "recovery": recovery_info,
            "context": context
        }
    
    def _log_error(self, error: DevAgentError, context: Dict[str, Any]) -> None:
        """Log error with appropriate level"""
        log_message = f"[{error.category.value}] {error.message}"
        
        if error.category in [ErrorCategory.USER_INPUT, ErrorCategory.VALIDATION]:
            self.logger.warning(log_message)
        elif error.category == ErrorCategory.INTERNAL:
            self.logger.error(log_message, exc_info=True)
        else:
            self.logger.error(log_message)
        
        if error.details:
            self.logger.debug(f"Error details: {error.details}")
        
        if context:
            self.logger.debug(f"Error context: {context}")
    
    def _track_error(self, error: DevAgentError) -> None:
        """Track error statistics"""
        category = error.category.value
        if category not in self.error_counts:
            self.error_counts[category] = 0
        self.error_counts[category] += 1
    
    def _attempt_recovery(self, error: DevAgentError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to recover from error"""
        recovery_strategy = self.recovery_strategies.get(error.category)
        
        if recovery_strategy:
            try:
                return recovery_strategy(error, context)
            except Exception as recovery_error:
                self.logger.error(f"Recovery failed: {recovery_error}")
                return {"success": False, "message": "Recovery failed"}
        
        return {"success": False, "message": "No recovery strategy available"}
    
    def _handle_llm_error(self, error: DevAgentError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle LLM provider errors"""
        if "rate_limit" in error.message.lower():
            return {
                "success": True,
                "strategy": "retry_with_backoff",
                "message": "Rate limit hit, will retry with exponential backoff",
                "retry_after": 60
            }
        elif "api_key" in error.message.lower():
            return {
                "success": True,
                "strategy": "fallback_to_mock",
                "message": "API key issue, falling back to mock provider",
                "fallback_provider": "mock"
            }
        else:
            return {
                "success": True,
                "strategy": "retry",
                "message": "Temporary LLM error, will retry",
                "max_retries": 3
            }
    
    def _handle_file_error(self, error: DevAgentError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file system errors"""
        if "permission" in error.message.lower():
            return {
                "success": True,
                "strategy": "request_permission",
                "message": "Permission denied, please check file permissions"
            }
        elif "not found" in error.message.lower():
            return {
                "success": True,
                "strategy": "create_file",
                "message": "File not found, will attempt to create"
            }
        else:
            return {
                "success": False,
                "message": "Unrecoverable file system error"
            }
    
    def _handle_network_error(self, error: DevAgentError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle network errors"""
        return {
            "success": True,
            "strategy": "retry_with_backoff",
            "message": "Network error, will retry with backoff",
            "max_retries": 3,
            "backoff_factor": 2
        }
    
    def _handle_user_error(self, error: DevAgentError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user input errors"""
        return {
            "success": True,
            "strategy": "user_correction",
            "message": "Please correct the input and try again",
            "suggestions": self._get_input_suggestions(error)
        }
    
    def _handle_validation_error(self, error: DevAgentError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle validation errors"""
        return {
            "success": True,
            "strategy": "validation_correction",
            "message": "Validation failed, please check input",
            "validation_details": error.details
        }
    
    def _get_input_suggestions(self, error: DevAgentError) -> list:
        """Get suggestions for fixing user input"""
        suggestions = []
        
        if "file" in error.message.lower():
            suggestions.extend([
                "Check that the file path is correct",
                "Ensure the file exists and is readable",
                "Use absolute path if relative path fails"
            ])
        
        if "function" in error.message.lower():
            suggestions.extend([
                "Check that the function name is spelled correctly",
                "Ensure the function exists in the specified file",
                "Use exact function name (case-sensitive)"
            ])
        
        return suggestions
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        return self.error_counts.copy()


# Global error handler instance
_error_handler = ErrorHandler()


def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Global error handling function"""
    return _error_handler.handle_error(error, context)


def get_error_stats() -> Dict[str, int]:
    """Get global error statistics"""
    return _error_handler.get_error_stats()