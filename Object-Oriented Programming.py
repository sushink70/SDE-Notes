# Complete Object-Oriented Programming Guide in Python
# Real-world examples with Django, API development, and modern patterns

from typing import Optional, List, Dict, Any, Protocol, TypeVar, Generic
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import wraps
import json
import hashlib
from datetime import datetime
import asyncio

# =============================================================================
# 1. CLASSES AND OBJECTS - Foundation
# =============================================================================

class User:
    """Basic User class - similar to Django User model structure"""
    
    # Class variables (shared across all instances)
    total_users: int = 0
    
    def __init__(self, username: str, email: str, password: str):
        # Instance variables (unique to each instance)
        self.username = username
        self.email = email
        self._password_hash = self._hash_password(password)  # Private attribute
        self.created_at = datetime.now()
        self.is_active = True
        
        # Increment class variable
        User.total_users += 1
    
    def _hash_password(self, password: str) -> str:
        """Private method for password hashing - security practice"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password: str) -> bool:
        """Public method to verify password"""
        return self._hash_password(password) == self._password_hash
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses (like DRF serializer)"""
        return {
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }
    
    def __str__(self) -> str:
        return f"User(username='{self.username}', email='{self.email}')"
    
    def __repr__(self) -> str:
        return f"User(username='{self.username}', email='{self.email}', created_at='{self.created_at}')"

# Usage example
user1 = User("john_doe", "john@example.com", "secure_password")
user2 = User("jane_smith", "jane@example.com", "another_password")

print(f"Total users: {User.total_users}")  # 2
print(user1)  # User(username='john_doe', email='john@example.com')
print(user1.check_password("secure_password"))  # True

# =============================================================================
# 2. INHERITANCE - Code Reusability
# =============================================================================

class BaseModel:
    """Base model similar to Django's Model class"""
    
    def __init__(self):
        self.id: Optional[int] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def save(self) -> None:
        """Simulate saving to database"""
        self.updated_at = datetime.now()
        print(f"Saved {self.__class__.__name__} with ID: {self.id}")
    
    def delete(self) -> None:
        """Simulate deletion from database"""
        print(f"Deleted {self.__class__.__name__} with ID: {self.id}")

class AdminUser(User, BaseModel):
    """Admin user inheriting from both User and BaseModel (Multiple Inheritance)"""
    
    def __init__(self, username: str, email: str, password: str, permissions: List[str]):
        # Call parent constructors
        User.__init__(self, username, email, password)
        BaseModel.__init__(self)
        
        self.permissions = permissions
        self.is_admin = True
    
    def grant_permission(self, permission: str) -> None:
        """Add permission to admin user"""
        if permission not in self.permissions:
            self.permissions.append(permission)
            print(f"Granted '{permission}' permission to {self.username}")
    
    def revoke_permission(self, permission: str) -> None:
        """Remove permission from admin user"""
        if permission in self.permissions:
            self.permissions.remove(permission)
            print(f"Revoked '{permission}' permission from {self.username}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Override parent method to include admin-specific fields"""
        user_dict = super().to_dict()  # Call parent method
        user_dict.update({
            'is_admin': self.is_admin,
            'permissions': self.permissions
        })
        return user_dict

# Usage example
admin = AdminUser("admin_user", "admin@example.com", "admin_pass", ["read", "write"])
admin.grant_permission("delete")
print(admin.to_dict())

# =============================================================================
# 3. ENCAPSULATION - Data Security
# =============================================================================

class BankAccount:
    """Demonstrates encapsulation for secure financial operations"""
    
    def __init__(self, account_number: str, initial_balance: float = 0.0):
        self.account_number = account_number
        self.__balance = initial_balance  # Private attribute
        self.__transaction_history: List[Dict[str, Any]] = []
    
    @property
    def balance(self) -> float:
        """Getter for balance - read-only access"""
        return self.__balance
    
    @property
    def transaction_history(self) -> List[Dict[str, Any]]:
        """Getter for transaction history - read-only access"""
        return self.__transaction_history.copy()  # Return copy to prevent modification
    
    def deposit(self, amount: float) -> bool:
        """Deposit money with validation"""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        self.__balance += amount
        self.__add_transaction("deposit", amount)
        return True
    
    def withdraw(self, amount: float) -> bool:
        """Withdraw money with validation"""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        
        if amount > self.__balance:
            raise ValueError("Insufficient funds")
        
        self.__balance -= amount
        self.__add_transaction("withdrawal", amount)
        return True
    
    def __add_transaction(self, transaction_type: str, amount: float) -> None:
        """Private method to record transactions"""
        transaction = {
            'type': transaction_type,
            'amount': amount,
            'timestamp': datetime.now().isoformat(),
            'balance_after': self.__balance
        }
        self.__transaction_history.append(transaction)

# Usage example
account = BankAccount("ACC001", 1000.0)
account.deposit(500.0)
account.withdraw(200.0)
print(f"Balance: ${account.balance}")
print(f"Transactions: {len(account.transaction_history)}")

# =============================================================================
# 4. POLYMORPHISM - Flexible Interface
# =============================================================================

class PaymentProcessor(ABC):
    """Abstract base class for payment processing (like Stripe integration)"""
    
    @abstractmethod
    def process_payment(self, amount: float, currency: str = "USD") -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def refund_payment(self, transaction_id: str) -> Dict[str, Any]:
        pass

class StripePaymentProcessor(PaymentProcessor):
    """Stripe payment processor implementation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def process_payment(self, amount: float, currency: str = "USD") -> Dict[str, Any]:
        # Simulate Stripe API call
        transaction_id = f"stripe_{hashlib.md5(str(amount).encode()).hexdigest()[:8]}"
        
        return {
            'status': 'success',
            'transaction_id': transaction_id,
            'amount': amount,
            'currency': currency,
            'processor': 'stripe',
            'timestamp': datetime.now().isoformat()
        }
    
    def refund_payment(self, transaction_id: str) -> Dict[str, Any]:
        return {
            'status': 'refunded',
            'transaction_id': transaction_id,
            'processor': 'stripe',
            'timestamp': datetime.now().isoformat()
        }

class PayPalPaymentProcessor(PaymentProcessor):
    """PayPal payment processor implementation"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
    
    def process_payment(self, amount: float, currency: str = "USD") -> Dict[str, Any]:
        # Simulate PayPal API call
        transaction_id = f"paypal_{hashlib.md5(str(amount).encode()).hexdigest()[:8]}"
        
        return {
            'status': 'completed',
            'transaction_id': transaction_id,
            'amount': amount,
            'currency': currency,
            'processor': 'paypal',
            'timestamp': datetime.now().isoformat()
        }
    
    def refund_payment(self, transaction_id: str) -> Dict[str, Any]:
        return {
            'status': 'refunded',
            'transaction_id': transaction_id,
            'processor': 'paypal',
            'timestamp': datetime.now().isoformat()
        }

def process_multiple_payments(processors: List[PaymentProcessor], amount: float) -> List[Dict[str, Any]]:
    """Polymorphism in action - same interface, different implementations"""
    results = []
    
    for processor in processors:
        try:
            result = processor.process_payment(amount)
            results.append(result)
        except Exception as e:
            results.append({'status': 'error', 'message': str(e)})
    
    return results

# Usage example
stripe_processor = StripePaymentProcessor("sk_test_...")
paypal_processor = PayPalPaymentProcessor("client_id", "client_secret")

results = process_multiple_payments([stripe_processor, paypal_processor], 100.0)
for result in results:
    print(f"Payment via {result.get('processor', 'unknown')}: {result['status']}")

# =============================================================================
# 5. MODERN PYTHON PATTERNS - Dataclasses, Type Hints, Protocols
# =============================================================================

@dataclass
class Product:
    """Modern Python dataclass for product management"""
    name: str
    price: float
    category: str
    in_stock: bool = True
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validation after initialization"""
        if self.price < 0:
            raise ValueError("Price cannot be negative")
        
        # Auto-generate SKU
        self.sku = f"{self.category.upper()[:3]}-{hash(self.name) % 10000:04d}"
    
    def to_api_response(self) -> Dict[str, Any]:
        """Convert to API response format (like DRF serializer)"""
        return {
            'name': self.name,
            'price': self.price,
            'category': self.category,
            'in_stock': self.in_stock,
            'sku': self.sku,
            'tags': self.tags
        }

class OrderStatus(Enum):
    """Enum for order status - type-safe constants"""
    PENDING = auto()
    PROCESSING = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()

@dataclass
class Order:
    """Order management with modern Python features"""
    order_id: str
    customer_email: str
    products: List[Product]
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def total_amount(self) -> float:
        """Calculate total order amount"""
        return sum(product.price for product in self.products)
    
    def update_status(self, new_status: OrderStatus) -> None:
        """Update order status with validation"""
        if self.status == OrderStatus.CANCELLED:
            raise ValueError("Cannot update cancelled order")
        
        self.status = new_status
        print(f"Order {self.order_id} status updated to {new_status.name}")

# Usage example
product1 = Product("Laptop", 999.99, "electronics", tags=["computer", "portable"])
product2 = Product("Mouse", 29.99, "electronics", tags=["computer", "accessory"])

order = Order("ORD-001", "customer@example.com", [product1, product2])
print(f"Order total: ${order.total_amount}")
order.update_status(OrderStatus.PROCESSING)

# =============================================================================
# 6. PROTOCOLS AND DUCK TYPING - Modern Type System
# =============================================================================

class Serializable(Protocol):
    """Protocol for serializable objects (like Django serializers)"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary"""
        ...
    
    def to_json(self) -> str:
        """Convert object to JSON string"""
        ...

class APIResponse:
    """Generic API response handler"""
    
    def __init__(self, data: Any, status_code: int = 200):
        self.data = data
        self.status_code = status_code
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'data': self.data,
            'status_code': self.status_code,
            'timestamp': self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

def serialize_object(obj: Serializable) -> str:
    """Function that works with any serializable object"""
    return obj.to_json()

# Usage example
api_response = APIResponse({"message": "Success", "user_id": 123})
print(serialize_object(api_response))

# =============================================================================
# 7. GENERICS AND TYPE VARIABLES - Advanced Typing
# =============================================================================

T = TypeVar('T')

class Repository(Generic[T]):
    """Generic repository pattern for database operations"""
    
    def __init__(self, model_class: type[T]):
        self.model_class = model_class
        self._items: List[T] = []
    
    def add(self, item: T) -> T:
        """Add item to repository"""
        self._items.append(item)
        return item
    
    def get_by_id(self, item_id: int) -> Optional[T]:
        """Get item by ID (simplified)"""
        if 0 <= item_id < len(self._items):
            return self._items[item_id]
        return None
    
    def get_all(self) -> List[T]:
        """Get all items"""
        return self._items.copy()
    
    def filter_by(self, predicate) -> List[T]:
        """Filter items by predicate"""
        return [item for item in self._items if predicate(item)]

# Usage example
user_repo = Repository[User](User)
product_repo = Repository[Product](Product)

user_repo.add(User("test_user", "test@example.com", "password"))
product_repo.add(Product("Test Product", 19.99, "test"))

# =============================================================================
# 8. DECORATORS AND METACLASSES - Advanced OOP
# =============================================================================

def api_endpoint(method: str = "GET", auth_required: bool = True):
    """Decorator for API endpoints (like Django REST framework)"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if auth_required and not hasattr(self, 'authenticated_user'):
                raise PermissionError("Authentication required")
            
            print(f"API {method} request to {func.__name__}")
            result = func(self, *args, **kwargs)
            print(f"API response: {result}")
            return result
        
        wrapper.method = method
        wrapper.auth_required = auth_required
        return wrapper
    return decorator

class APIController:
    """API controller with decorated methods"""
    
    def __init__(self, authenticated_user: Optional[User] = None):
        self.authenticated_user = authenticated_user
    
    @api_endpoint(method="GET", auth_required=False)
    def get_public_data(self) -> Dict[str, Any]:
        return {"message": "Public data", "timestamp": datetime.now().isoformat()}
    
    @api_endpoint(method="POST", auth_required=True)
    def create_resource(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"message": "Resource created", "data": data}

# Usage example
controller = APIController(authenticated_user=user1)
controller.get_public_data()
controller.create_resource({"name": "New Resource"})

# =============================================================================
# 9. ASYNC OOP - Modern Python Async/Await
# =============================================================================

class AsyncDatabaseManager:
    """Async database manager for modern web applications"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connected = False
    
    async def connect(self) -> None:
        """Async connection to database"""
        print("Connecting to database...")
        await asyncio.sleep(0.1)  # Simulate connection delay
        self.connected = True
        print("Database connected!")
    
    async def disconnect(self) -> None:
        """Async disconnection from database"""
        print("Disconnecting from database...")
        await asyncio.sleep(0.1)  # Simulate disconnection delay
        self.connected = False
        print("Database disconnected!")
    
    async def fetch_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Async fetch user data"""
        if not self.connected:
            raise ConnectionError("Database not connected")
        
        print(f"Fetching user {user_id}...")
        await asyncio.sleep(0.1)  # Simulate database query
        
        return {
            "id": user_id,
            "username": f"user_{user_id}",
            "email": f"user_{user_id}@example.com"
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

# Usage example (would need to be run in async context)
async def example_async_usage():
    async with AsyncDatabaseManager("postgresql://localhost/mydb") as db:
        user_data = await db.fetch_user(1)
        print(f"Retrieved user: {user_data}")

# =============================================================================
# 10. COMPOSITION OVER INHERITANCE - Modern Design Pattern
# =============================================================================

class Logger:
    """Logging component for composition"""
    
    def log(self, message: str, level: str = "INFO") -> None:
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] {level}: {message}")

class Cache:
    """Caching component for composition"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
    
    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value
    
    def clear(self) -> None:
        self._cache.clear()

class UserService:
    """User service using composition instead of inheritance"""
    
    def __init__(self, logger: Logger, cache: Cache):
        self.logger = logger
        self.cache = cache
        self.users: List[User] = []
    
    def create_user(self, username: str, email: str, password: str) -> User:
        """Create user with logging and caching"""
        self.logger.log(f"Creating user: {username}")
        
        user = User(username, email, password)
        self.users.append(user)
        
        # Cache the user
        self.cache.set(f"user_{username}", user)
        
        self.logger.log(f"User created successfully: {username}")
        return user
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user with caching"""
        # Try cache first
        cached_user = self.cache.get(f"user_{username}")
        if cached_user:
            self.logger.log(f"User retrieved from cache: {username}")
            return cached_user
        
        # Search in users list
        for user in self.users:
            if user.username == username:
                self.cache.set(f"user_{username}", user)
                self.logger.log(f"User retrieved from database: {username}")
                return user
        
        self.logger.log(f"User not found: {username}", "WARNING")
        return None

# Usage example
logger = Logger()
cache = Cache()
user_service = UserService(logger, cache)

user = user_service.create_user("compose_user", "compose@example.com", "password")
retrieved_user = user_service.get_user("compose_user")  # From cache

# =============================================================================
# 11. DESIGN PATTERNS IN PYTHON OOP
# =============================================================================

# Singleton Pattern
class DatabaseConnection:
    """Singleton pattern for database connection"""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.connection_string = "postgresql://localhost/app_db"
            self.connected = False
            self._initialized = True
    
    def connect(self):
        if not self.connected:
            print(f"Connecting to {self.connection_string}")
            self.connected = True

# Factory Pattern
class NotificationFactory:
    """Factory pattern for creating notifications"""
    
    @staticmethod
    def create_notification(notification_type: str, recipient: str, message: str):
        if notification_type == "email":
            return EmailNotification(recipient, message)
        elif notification_type == "sms":
            return SMSNotification(recipient, message)
        elif notification_type == "push":
            return PushNotification(recipient, message)
        else:
            raise ValueError(f"Unknown notification type: {notification_type}")

class EmailNotification:
    def __init__(self, recipient: str, message: str):
        self.recipient = recipient
        self.message = message
    
    def send(self):
        print(f"Sending email to {self.recipient}: {self.message}")

class SMSNotification:
    def __init__(self, recipient: str, message: str):
        self.recipient = recipient
        self.message = message
    
    def send(self):
        print(f"Sending SMS to {self.recipient}: {self.message}")

class PushNotification:
    def __init__(self, recipient: str, message: str):
        self.recipient = recipient
        self.message = message
    
    def send(self):
        print(f"Sending push notification to {self.recipient}: {self.message}")

# Usage examples
db1 = DatabaseConnection()
db2 = DatabaseConnection()
print(f"Same instance: {db1 is db2}")  # True

email_notification = NotificationFactory.create_notification("email", "user@example.com", "Welcome!")
email_notification.send()

# =============================================================================
# 12. CONTEXT MANAGERS AND RESOURCE MANAGEMENT
# =============================================================================

class FileManager:
    """Custom context manager for file operations"""
    
    def __init__(self, filename: str, mode: str = 'r'):
        self.filename = filename
        self.mode = mode
        self.file = None
    
    def __enter__(self):
        print(f"Opening file: {self.filename}")
        self.file = open(self.filename, self.mode)
        return self.file
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            print(f"Closing file: {self.filename}")
            self.file.close()
        
        if exc_type:
            print(f"Exception occurred: {exc_type.__name__}: {exc_val}")
        
        return False  # Don't suppress exceptions

# Usage example (would create/read actual file)
# with FileManager("example.txt", "w") as f:
#     f.write("Hello, World!")

print("=== OOP Examples Complete ===")
print(f"Total users created: {User.total_users}")
print("All examples demonstrate modern Python OOP patterns for web development!")

#I'll explain Object-Oriented Programming (OOP) concepts in Python with detailed examples, real-world use cases, and modern trends that align with your tech stack.This comprehensive guide covers all major OOP concepts in Python with practical examples that align with your tech stack. Here's a breakdown of what we covered:

## Core OOP Concepts Explained:

### 1. **Classes and Objects**
#- **Real-world use**: Django User model structure
#- **Security focus**: Password hashing, private attributes
#- **API integration**: `to_dict()` method for DRF serializers

### 2. **Inheritance**
#- **Multiple inheritance**: `AdminUser` inherits from both `User` and `BaseModel`
#- **Method overriding**: Enhanced `to_dict()` for admin users
#- **Real-world use**: Django's Model inheritance pattern

### 3. **Encapsulation**
#- **Security critical**: `BankAccount` with private balance
#- **Property decorators**: Read-only access to sensitive data
#- **Validation**: Input validation for financial operations

### 4. **Polymorphism**
#- **Payment processing**: Stripe and PayPal implementations
#- **Abstract base classes**: Enforced interface consistency
#- **Real-world use**: Multiple payment gateways in e-commerce

### 5. **Modern Python Features**
#- **Dataclasses**: Clean, readable code with automatic methods
#- **Type hints**: Better IDE support and code documentation
#- **Enums**: Type-safe constants for order status
#- **Protocols**: Duck typing with type checking

### 6. **Advanced Patterns**
#- **Generics**: Type-safe repository pattern
#- **Decorators**: API endpoint decoration (like DRF)
#- **Async/await**: Modern async database operations
#- **Composition**: Service-oriented architecture

## How These Apply to Your Stack:

### **Django Backend**
#- `BaseModel` mirrors Django's Model class
#- `AdminUser` shows Django's user permission system
#- Repository pattern for database operations
#- API response formatting for DRF

### **Security Best Practices**
#- Password hashing in User class
#- Private attributes with proper encapsulation
#- Input validation in all methods
#- Authentication decorators for API endpoints

### **NextJS Frontend Integration**
#- `to_dict()` and `to_json()` methods for API responses
#- Type-safe data structures for TypeScript compatibility
#- Async patterns for API calls

### **Modern Development Trends**
#- **Dataclasses** for clean, readable code
#- **Type hints** for better IDE support
#- **Protocols** for duck typing with type safety
#- **Composition over inheritance** for maintainable code
#- **Async/await** for modern web applications

## Key Architectural Insights:

#1. **Separation of Concerns**: Each class has a single responsibility
#2. **Dependency Injection**: Services composed of smaller components
#3. **Interface Segregation**: Abstract base classes define contracts
#4. **Type Safety**: Extensive use of type hints and protocols
#5. **Resource Management**: Context managers for proper cleanup

## System Design Connections:

#- **Repository Pattern**: Database abstraction layer
#- **Factory Pattern**: Object creation abstraction
#- **Singleton Pattern**: Shared resource management
#- **Observer Pattern**: Event-driven architecture possibilities

#These patterns are essential for building scalable web applications with Django and NextJS. They provide the foundation for clean, maintainable, and secure code that follows modern Python best practices.

#Would you like me to dive deeper into any specific pattern or show how to implement these concepts in your Django models or NextJS API integration?