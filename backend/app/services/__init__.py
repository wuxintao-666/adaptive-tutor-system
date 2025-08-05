# backend/app/services/__init__.py
from .user_state_service import UserStateService
from .behavior_interpreter_service import BehaviorInterpreterService

# Create a global instance
user_state_service = UserStateService()