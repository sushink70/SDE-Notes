# Python Typing Module Complete Guide
# Comprehensive examples for Django/DRF backend development

from typing import (
    Dict, List, Optional, Union, Any, Callable, TypeVar, Generic,
    Protocol, Literal, TypedDict, Final, ClassVar, Annotated,
    overload, get_type_hints, TYPE_CHECKING
)
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import json

# =============================================================================
# 1. BASIC TYPES - Foundation for type safety
# =============================================================================

# Basic type annotations
user_id: int = 123
username: str = "john_doe"
is_active: bool = True
balance: float = 99.99

# Function with type hints - Essential for API endpoints
def authenticate_user(username: str, password: str) -> bool:
    """
    Real-world usage: DRF authentication endpoint
    Type safety prevents passing wrong data types
    """
    # Security: Type checking prevents injection attacks through wrong types
    if not isinstance(username, str) or not isinstance(password, str):
        raise TypeError("Username and password must be strings")
    return username == "admin" and password == "secret"

# =============================================================================
# 2. OPTIONAL AND UNION TYPES - Handle nullable database fields
# =============================================================================

# Optional for nullable fields (common in Django models)
def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Real-world: Django model with nullable foreign key
    class UserProfile(models.Model):
        bio = models.TextField(null=True, blank=True)
        avatar = models.ImageField(null=True, blank=True)
    """
    if user_id == 1:
        return {
            "bio": "Software Developer",
            "avatar": "/media/avatars/user1.jpg"
        }
    return None  # Type checker knows this is valid

# Union types for multiple possible return types
def process_api_response(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> int:
    """
    Real-world: DRF serializer handling both single objects and lists
    POST /api/users/ (single) vs GET /api/users/ (list)
    """
    if isinstance(data, dict):
        return 1  # Single object
    return len(data)  # List of objects

# Modern Union syntax (Python 3.10+)
def handle_payment_amount(amount: int | float | Decimal) -> Decimal:
    """
    Real-world: Stripe payment processing with multiple numeric types
    Security: Type checking prevents string injection in financial calculations
    """
    return Decimal(str(amount))

# =============================================================================
# 3. GENERIC TYPES - Reusable components for DRF serializers
# =============================================================================

# Generic API response wrapper
from typing import TypeVar, Generic

T = TypeVar('T')  # Type variable for generic programming

@dataclass
class APIResponse(Generic[T]):
    """
    Real-world: Standardized API response format for DRF
    Usage in views.py:
    - APIResponse[User] for user endpoints
    - APIResponse[List[Product]] for product lists
    """
    data: T
    status: str
    message: str
    timestamp: datetime

# Generic repository pattern for database operations
class Repository(Generic[T]):
    """
    Real-world: Generic Django model repository
    Architectural knowledge: Repository pattern separates business logic
    """
    def __init__(self, model_class: type[T]):
        self.model_class = model_class
    
    def get_by_id(self, id: int) -> Optional[T]:
        # In real Django: return self.model_class.objects.get(id=id)
        return None
    
    def create(self, **kwargs) -> T:
        # In real Django: return self.model_class.objects.create(**kwargs)
        pass

# Usage with Django models
# user_repo = Repository[User](User)
# product_repo = Repository[Product](Product)

# =============================================================================
# 4. TYPEDDICT - Structured data for API requests/responses
# =============================================================================

class UserRegistrationData(TypedDict):
    """
    Real-world: DRF serializer validation schema
    Security: Ensures all required fields are present
    """
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    age: Optional[int]  # Optional field

class PaymentData(TypedDict, total=False):  # All fields optional
    """
    Real-world: Stripe payment webhook data
    total=False means all fields are optional
    """
    amount: int
    currency: str
    customer_id: str
    description: str

def process_user_registration(data: UserRegistrationData) -> Dict[str, Any]:
    """
    Real-world: DRF CreateAPIView with validated data
    Type safety prevents missing required fields
    """
    # Type checker ensures all required fields exist
    username = data['username']  # Safe access
    email = data['email']        # Safe access
    age = data.get('age')        # Optional field
    
    return {"user_id": 123, "status": "created"}

# =============================================================================
# 5. PROTOCOLS - Duck typing for dependency injection
# =============================================================================

class EmailSender(Protocol):
    """
    Real-world: Email service abstraction for Django
    Architectural knowledge: Protocol enables dependency injection
    """
    def send_email(self, to: str, subject: str, body: str) -> bool:
        ...

class SMTPEmailSender:
    """Real implementation using Django's email backend"""
    def send_email(self, to: str, subject: str, body: str) -> bool:
        # Django: send_mail(subject, body, 'from@example.com', [to])
        return True

class MockEmailSender:
    """Test implementation for unit testing"""
    def send_email(self, to: str, subject: str, body: str) -> bool:
        print(f"Mock email sent to {to}")
        return True

def notify_user(email_sender: EmailSender, user_email: str) -> None:
    """
    Real-world: Service layer in Django
    Both SMTPEmailSender and MockEmailSender work here
    """
    email_sender.send_email(user_email, "Welcome!", "Thanks for joining!")

# =============================================================================
# 6. LITERAL TYPES - Restrict values for security
# =============================================================================

UserRole = Literal["admin", "user", "moderator"]
HTTPMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]

def check_permission(user_role: UserRole, method: HTTPMethod) -> bool:
    """
    Real-world: DRF permission system
    Security: Prevents typos in role/method names
    """
    admin_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
    user_methods = {"GET", "POST"}
    
    if user_role == "admin":
        return method in admin_methods
    return method in user_methods

# =============================================================================
# 7. ANNOTATED TYPES - Add metadata for validation
# =============================================================================

from typing import Annotated

# Custom type aliases with validation metadata
EmailAddress = Annotated[str, "Must be valid email format"]
PositiveInt = Annotated[int, "Must be positive integer"]
JSONString = Annotated[str, "Must be valid JSON string"]

def create_user_account(
    email: EmailAddress,
    age: PositiveInt,
    preferences: JSONString
) -> Dict[str, Any]:
    """
    Real-world: DRF serializer with custom validation
    Metadata helps with documentation and validation
    """
    # Validation logic would go here
    prefs = json.loads(preferences)  # Type hints help IDE
    return {"email": email, "age": age, "preferences": prefs}

# =============================================================================
# 8. FUNCTION OVERLOADING - Multiple signatures for flexibility
# =============================================================================

@overload
def get_user_data(user_id: int) -> Dict[str, Any]:
    ...

@overload
def get_user_data(username: str) -> Dict[str, Any]:
    ...

def get_user_data(identifier: Union[int, str]) -> Dict[str, Any]:
    """
    Real-world: DRF viewset with multiple lookup methods
    /api/users/123/ or /api/users/john_doe/
    """
    if isinstance(identifier, int):
        # Query by ID
        return {"id": identifier, "username": "user123"}
    else:
        # Query by username
        return {"id": 456, "username": identifier}

# =============================================================================
# 9. ADVANCED PATTERNS - Real-world Django/DRF scenarios
# =============================================================================

class DatabaseConnection(Protocol):
    """Protocol for database abstraction"""
    def execute_query(self, query: str, params: List[Any]) -> List[Dict[str, Any]]:
        ...

class UserService:
    """
    Real-world: Service layer with dependency injection
    Architectural knowledge: Separates business logic from views
    """
    def __init__(self, db: DatabaseConnection, email_sender: EmailSender):
        self.db = db
        self.email_sender = email_sender
    
    def create_user_with_notification(
        self, 
        user_data: UserRegistrationData
    ) -> APIResponse[Dict[str, Any]]:
        """
        Real-world: Complex business operation with multiple dependencies
        """
        # Database operation
        query = "INSERT INTO users (username, email) VALUES (%s, %s)"
        params = [user_data['username'], user_data['email']]
        self.db.execute_query(query, params)
        
        # Email notification
        self.email_sender.send_email(
            user_data['email'],
            "Welcome!",
            f"Hello {user_data['first_name']}!"
        )
        
        return APIResponse(
            data={"user_id": 123, "username": user_data['username']},
            status="success",
            message="User created successfully",
            timestamp=datetime.now()
        )

# =============================================================================
# 10. TYPE CHECKING AT RUNTIME - Security and validation
# =============================================================================

def validate_api_input(data: Dict[str, Any]) -> UserRegistrationData:
    """
    Real-world: DRF serializer validation
    Security: Runtime type checking prevents malicious input
    """
    required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
        if not isinstance(data[field], str):
            raise TypeError(f"{field} must be a string")
    
    # Type checker knows this is safe after validation
    return data  # type: ignore

# =============================================================================
# 11. BEST PRACTICES FOR DJANGO/DRF DEVELOPMENT
# =============================================================================

# Final - prevents inheritance/reassignment
API_VERSION: Final[str] = "v1"
MAX_PAGE_SIZE: Final[int] = 100

# ClassVar - class-level variables
class UserModel:
    """
    Real-world: Django model with proper type hints
    """
    table_name: ClassVar[str] = "users"
    
    def __init__(self, id: int, username: str, email: str):
        self.id = id
        self.username = username
        self.email = email

# Type checking imports (won't be imported at runtime)
if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from rest_framework.request import Request

def get_authenticated_user(request: 'Request') -> Optional['User']:
    """
    Real-world: DRF authentication check
    TYPE_CHECKING prevents circular imports
    """
    if hasattr(request, 'user') and request.user.is_authenticated:
        return request.user
    return None

# =============================================================================
# 12. MYPY CONFIGURATION EXAMPLES
# =============================================================================

# Example mypy.ini configuration for Django projects:
"""
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[mypy-django.*]
ignore_missing_imports = True

[mypy-rest_framework.*]
ignore_missing_imports = True
"""

# =============================================================================
# USAGE EXAMPLES AND TESTING
# =============================================================================

def main():
    """
    Real-world usage examples for testing
    """
    # Test basic functionality
    print("Testing authentication:", authenticate_user("admin", "secret"))
    
    # Test API response
    user_data = {"id": 1, "username": "john"}
    response = APIResponse(
        data=user_data,
        status="success",
        message="User retrieved",
        timestamp=datetime.now()
    )
    print("API Response:", response)
    
    # Test registration
    registration_data: UserRegistrationData = {
        "username": "newuser",
        "email": "user@example.com",
        "password": "secure123",
        "first_name": "John",
        "last_name": "Doe",
        "age": 25
    }
    
    result = process_user_registration(registration_data)
    print("Registration result:", result)
    
    # Test permission system
    print("Admin POST permission:", check_permission("admin", "POST"))
    print("User DELETE permission:", check_permission("user", "DELETE"))

if __name__ == "__main__":
    main()

# I'll teach you how to use Python's `typing` module properly with a focus on type safety and real-world examples that align with your Django/DRF backend development.This comprehensive guide covers the `typing` module with real-world examples tailored to your Django/DRF backend development. Here's how the concepts work internally and their architectural significance:

# ## Key Internal Concepts:

# **1. Type Erasure**: Python's type hints are erased at runtime - they're primarily for static analysis tools like mypy. This is why you can still run code with wrong types, but tools catch errors before deployment.

# **2. Protocol vs ABC**: Protocols use structural typing (duck typing) while Abstract Base Classes use nominal typing. Protocols are better for dependency injection in Django services.

# **3. Generic Type Variables**: `TypeVar` creates placeholder types that maintain relationships between input and output types, crucial for reusable repository patterns.

# ## Security Benefits:

# - **Input Validation**: TypedDict ensures API request data has required fields
# - **SQL Injection Prevention**: Type checking prevents passing wrong types to database queries
# - **Configuration Safety**: Literal types prevent typos in critical settings like user roles

# ## Creative Implementation Ideas:

# 1. **Custom Type Guards** for Django model validation
# 2. **Protocol-based Service Layer** for clean architecture
# 3. **Generic Repository Pattern** for database operations
# 4. **Type-safe Configuration** using Literal types
# 5. **Webhook Type Safety** with TypedDict for external APIs

# ## System Design Connection:

# The typing system supports several architectural patterns:
# - **Dependency Injection**: Using Protocols for service abstraction
# - **Repository Pattern**: Generic types for database operations
# - **API Gateway Pattern**: Standardized response types
# - **Service Layer Pattern**: Type-safe business logic separation

# For your Django/DRF stack, I recommend:
# 1. Use mypy in your CI/CD pipeline
# 2. Create TypedDict schemas for all API endpoints
# 3. Use Protocols for service layer abstraction
# 4. Apply Generic types for reusable components
# 5. Leverage Literal types for configuration safety

# The type system becomes especially powerful when combined with tools like `pydantic` for runtime validation and `mypy` for static analysis, creating a robust foundation for scalable backend systems.