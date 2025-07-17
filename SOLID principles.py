SOLID is an acronym for five fundamental principles of object-oriented programming and design that help create more maintainable, flexible, and scalable software. Let me explain each principle with Python examples:The SOLID principles are fundamental design guidelines that help create better object-oriented code. Here's a quick summary:

## **The Five SOLID Principles:**

**🔸 S - Single Responsibility Principle**
- Each class should have only one reason to change
- Separate concerns into different classes
- Example: Don't mix user data, database operations, and email sending in one class

**🔸 O - Open/Closed Principle**
- Open for extension, closed for modification
- Add new functionality without changing existing code
- Use inheritance and polymorphism instead of modifying existing classes

**🔸 L - Liskov Substitution Principle**
- Subclasses should be substitutable for their parent classes
- Don't break the contract/behavior expected from the parent class
- Example: If a Bird class has a fly() method, all subclasses should be able to fly

**🔸 I - Interface Segregation Principle**
- Don't force classes to implement interfaces they don't use
- Create specific, focused interfaces instead of large, general ones
- Example: Separate Workable, Eatable, and Sleepable interfaces instead of one Worker interface

**🔸 D - Dependency Inversion Principle**
- High-level modules shouldn't depend on low-level modules
- Both should depend on abstractions (interfaces/abstract classes)
- Use dependency injection to provide concrete implementations

## **Benefits of Following SOLID:**

- **Maintainability**: Changes are localized and predictable
- **Testability**: Classes can be tested in isolation
- **Flexibility**: Easy to add new features without breaking existing code
- **Reusability**: Components can be reused in different contexts
- **Reduced Coupling**: Classes depend on abstractions, not concrete implementations

## **Real-World Impact:**

Following SOLID principles helps avoid common problems like:
- **Spaghetti code** (everything is interconnected)
- **Fragile code** (small changes break multiple things)
- **Rigid code** (hard to extend or modify)
- **Untestable code** (too many dependencies)

The principles work together to create a robust, flexible architecture that can evolve with changing requirements while maintaining code quality.

# SOLID Principles in Python - Complete Guide with Examples

"""
SOLID is an acronym for five design principles:
S - Single Responsibility Principle
O - Open/Closed Principle  
L - Liskov Substitution Principle
I - Interface Segregation Principle
D - Dependency Inversion Principle

These principles help create more maintainable, flexible, and scalable code.
"""

# ============================================================================
# 1. SINGLE RESPONSIBILITY PRINCIPLE (SRP)
# ============================================================================

print("="*60)
print("1. SINGLE RESPONSIBILITY PRINCIPLE (SRP)")
print("="*60)
print("A class should have only one reason to change (one responsibility)")
print()

# ❌ BAD: Class with multiple responsibilities
class BadUser:
    def __init__(self, name, email):
        self.name = name
        self.email = email
    
    def save_to_database(self):
        # Database logic
        print(f"Saving {self.name} to database")
    
    def send_email(self):
        # Email logic
        print(f"Sending email to {self.email}")
    
    def validate_email(self):
        # Validation logic
        return "@" in self.email

# Problems: This class handles user data, database operations, email sending, and validation
# Changes to any of these would require modifying this class

# ✅ GOOD: Separate responsibilities into different classes
class User:
    """Only responsible for user data"""
    def __init__(self, name, email):
        self.name = name
        self.email = email

class UserRepository:
    """Only responsible for database operations"""
    def save(self, user):
        print(f"Saving {user.name} to database")
    
    def find_by_email(self, email):
        print(f"Finding user by email: {email}")

class EmailService:
    """Only responsible for sending emails"""
    def send_email(self, user, message):
        print(f"Sending email to {user.email}: {message}")

class EmailValidator:
    """Only responsible for email validation"""
    def validate(self, email):
        return "@" in email and "." in email

# Usage
user = User("Alice", "alice@example.com")
repository = UserRepository()
email_service = EmailService()
validator = EmailValidator()

if validator.validate(user.email):
    repository.save(user)
    email_service.send_email(user, "Welcome!")

print("SRP: Each class now has a single, well-defined responsibility\n")

# ============================================================================
# 2. OPEN/CLOSED PRINCIPLE (OCP)
# ============================================================================

print("="*60)
print("2. OPEN/CLOSED PRINCIPLE (OCP)")
print("="*60)
print("Classes should be open for extension but closed for modification")
print()

# ❌ BAD: Need to modify existing code to add new functionality
class BadShapeCalculator:
    def calculate_area(self, shape):
        if shape.type == "rectangle":
            return shape.width * shape.height
        elif shape.type == "circle":
            return 3.14159 * shape.radius ** 2
        # Adding triangle would require modifying this method
        # elif shape.type == "triangle":
        #     return 0.5 * shape.base * shape.height

# ✅ GOOD: Using inheritance and polymorphism for extension
from abc import ABC, abstractmethod

class Shape(ABC):
    """Abstract base class for all shapes"""
    @abstractmethod
    def calculate_area(self):
        pass

class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height
    
    def calculate_area(self):
        return self.width * self.height

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius
    
    def calculate_area(self):
        return 3.14159 * self.radius ** 2

# NEW: Adding triangle doesn't require modifying existing code
class Triangle(Shape):
    def __init__(self, base, height):
        self.base = base
        self.height = height
    
    def calculate_area(self):
        return 0.5 * self.base * self.height

class AreaCalculator:
    def calculate_total_area(self, shapes):
        return sum(shape.calculate_area() for shape in shapes)

# Usage
shapes = [
    Rectangle(5, 4),
    Circle(3),
    Triangle(6, 8)
]

calculator = AreaCalculator()
total_area = calculator.calculate_total_area(shapes)
print(f"Total area: {total_area}")
print("OCP: New shapes can be added without modifying existing code\n")

# ============================================================================
# 3. LISKOV SUBSTITUTION PRINCIPLE (LSP)
# ============================================================================

print("="*60)
print("3. LISKOV SUBSTITUTION PRINCIPLE (LSP)")
print("="*60)
print("Objects of a superclass should be replaceable with objects of subclasses")
print()

# ❌ BAD: Subclass violates the contract of the parent class
class BadBird:
    def fly(self):
        print("Flying high!")

class BadPenguin(BadBird):
    def fly(self):
        raise Exception("Penguins can't fly!")  # Violates LSP

# This would break: all birds should be able to fly if Bird has a fly method
# def make_bird_fly(bird: BadBird):
#     bird.fly()  # This would fail for penguin

# ✅ GOOD: Proper inheritance hierarchy
class Bird(ABC):
    @abstractmethod
    def move(self):
        pass

class FlyingBird(Bird):
    def move(self):
        return self.fly()
    
    def fly(self):
        return "Flying high!"

class SwimmingBird(Bird):
    def move(self):
        return self.swim()
    
    def swim(self):
        return "Swimming gracefully!"

class Eagle(FlyingBird):
    def fly(self):
        return "Eagle soaring!"

class Penguin(SwimmingBird):
    def swim(self):
        return "Penguin swimming!"

# Now all birds can be substituted safely
def make_bird_move(bird: Bird):
    return bird.move()

# Usage
eagle = Eagle()
penguin = Penguin()

print(f"Eagle: {make_bird_move(eagle)}")
print(f"Penguin: {make_bird_move(penguin)}")
print("LSP: All subclasses can be used interchangeably with their parent\n")

# ============================================================================
# 4. INTERFACE SEGREGATION PRINCIPLE (ISP)
# ============================================================================

print("="*60)
print("4. INTERFACE SEGREGATION PRINCIPLE (ISP)")
print("="*60)
print("Clients should not be forced to depend on interfaces they don't use")
print()

# ❌ BAD: Fat interface forces classes to implement methods they don't need
class BadWorker(ABC):
    @abstractmethod
    def work(self):
        pass
    
    @abstractmethod
    def eat(self):
        pass
    
    @abstractmethod
    def sleep(self):
        pass

class BadHuman(BadWorker):
    def work(self):
        print("Human working")
    
    def eat(self):
        print("Human eating")
    
    def sleep(self):
        print("Human sleeping")

class BadRobot(BadWorker):
    def work(self):
        print("Robot working")
    
    def eat(self):
        # Robots don't eat! But forced to implement
        raise NotImplementedError("Robots don't eat")
    
    def sleep(self):
        # Robots don't sleep! But forced to implement
        raise NotImplementedError("Robots don't sleep")

# ✅ GOOD: Segregated interfaces
class Workable(ABC):
    @abstractmethod
    def work(self):
        pass

class Eatable(ABC):
    @abstractmethod
    def eat(self):
        pass

class Sleepable(ABC):
    @abstractmethod
    def sleep(self):
        pass

class Human(Workable, Eatable, Sleepable):
    def work(self):
        print("Human working")
    
    def eat(self):
        print("Human eating")
    
    def sleep(self):
        print("Human sleeping")

class Robot(Workable):  # Only implements what it needs
    def work(self):
        print("Robot working")

# Usage
human = Human()
robot = Robot()

human.work()
human.eat()
human.sleep()

robot.work()
# robot.eat()  # This method doesn't exist - good!

print("ISP: Classes only implement interfaces they actually need\n")

# ============================================================================
# 5. DEPENDENCY INVERSION PRINCIPLE (DIP)
# ============================================================================

print("="*60)
print("5. DEPENDENCY INVERSION PRINCIPLE (DIP)")
print("="*60)
print("High-level modules should not depend on low-level modules")
print("Both should depend on abstractions")
print()

# ❌ BAD: High-level class depends on concrete low-level class
class BadEmailService:
    def send_email(self, message):
        print(f"Sending email: {message}")

class BadSMSService:
    def send_sms(self, message):
        print(f"Sending SMS: {message}")

class BadNotificationService:
    def __init__(self):
        self.email_service = BadEmailService()  # Tight coupling
        self.sms_service = BadSMSService()      # Tight coupling
    
    def send_notification(self, message, type):
        if type == "email":
            self.email_service.send_email(message)
        elif type == "sms":
            self.sms_service.send_sms(message)

# ✅ GOOD: Both depend on abstraction
class NotificationSender(ABC):
    @abstractmethod
    def send(self, message):
        pass

class EmailService(NotificationSender):
    def send(self, message):
        print(f"Sending email: {message}")

class SMSService(NotificationSender):
    def send(self, message):
        print(f"Sending SMS: {message}")

class PushNotificationService(NotificationSender):
    def send(self, message):
        print(f"Sending push notification: {message}")

class NotificationService:
    def __init__(self, sender: NotificationSender):
        self.sender = sender  # Depends on abstraction
    
    def send_notification(self, message):
        self.sender.send(message)

# Usage - dependency injection
email_service = EmailService()
sms_service = SMSService()
push_service = PushNotificationService()

# Can easily switch between different notification methods
email_notifier = NotificationService(email_service)
sms_notifier = NotificationService(sms_service)
push_notifier = NotificationService(push_service)

email_notifier.send_notification("Hello via email!")
sms_notifier.send_notification("Hello via SMS!")
push_notifier.send_notification("Hello via push!")

print("DIP: High-level code doesn't depend on concrete implementations\n")

# ============================================================================
# PRACTICAL EXAMPLE: COMBINING ALL PRINCIPLES
# ============================================================================

print("="*60)
print("PRACTICAL EXAMPLE: E-COMMERCE ORDER SYSTEM")
print("="*60)

# Abstract interfaces (DIP)
class PaymentProcessor(ABC):
    @abstractmethod
    def process_payment(self, amount):
        pass

class InventoryManager(ABC):
    @abstractmethod
    def reserve_items(self, items):
        pass
    
    @abstractmethod
    def release_items(self, items):
        pass

class NotificationSender(ABC):
    @abstractmethod
    def send(self, message, recipient):
        pass

# Concrete implementations (OCP - can add new ones without modifying existing code)
class CreditCardProcessor(PaymentProcessor):
    def process_payment(self, amount):
        return f"Processed ${amount} via credit card"

class PayPalProcessor(PaymentProcessor):
    def process_payment(self, amount):
        return f"Processed ${amount} via PayPal"

class DatabaseInventoryManager(InventoryManager):
    def reserve_items(self, items):
        return f"Reserved {len(items)} items in database"
    
    def release_items(self, items):
        return f"Released {len(items)} items in database"

class EmailNotificationSender(NotificationSender):
    def send(self, message, recipient):
        return f"Email sent to {recipient}: {message}"

# Business logic classes (SRP - each has single responsibility)
class Order:
    def __init__(self, order_id, items, customer_email):
        self.order_id = order_id
        self.items = items
        self.customer_email = customer_email
        self.total = sum(item['price'] for item in items)

class OrderProcessor:
    def __init__(self, 
                 payment_processor: PaymentProcessor,
                 inventory_manager: InventoryManager,
                 notification_sender: NotificationSender):
        self.payment_processor = payment_processor
        self.inventory_manager = inventory_manager
        self.notification_sender = notification_sender
    
    def process_order(self, order: Order):
        # Reserve inventory
        inventory_result = self.inventory_manager.reserve_items(order.items)
        print(inventory_result)
        
        try:
            # Process payment
            payment_result = self.payment_processor.process_payment(order.total)
            print(payment_result)
            
            # Send confirmation
            notification_result = self.notification_sender.send(
                f"Order {order.order_id} confirmed!", 
                order.customer_email
            )
            print(notification_result)
            
            return "Order processed successfully"
            
        except Exception as e:
            # Release inventory if payment fails
            self.inventory_manager.release_items(order.items)
            raise e

# Usage demonstrating all principles
items = [
    {'name': 'Laptop', 'price': 999.99},
    {'name': 'Mouse', 'price': 29.99}
]

order = Order("ORD-001", items, "customer@example.com")

# Different configurations can be injected (DIP)
processor = OrderProcessor(
    CreditCardProcessor(),
    DatabaseInventoryManager(),
    EmailNotificationSender()
)

result = processor.process_order(order)
print(f"\nResult: {result}")

print("\n" + "="*60)
print("SUMMARY OF SOLID PRINCIPLES")
print("="*60)
print("S - Single Responsibility: Each class has one reason to change")
print("O - Open/Closed: Open for extension, closed for modification")
print("L - Liskov Substitution: Subclasses can replace parent classes")
print("I - Interface Segregation: Don't force unused interface methods")
print("D - Dependency Inversion: Depend on abstractions, not concretions")
print("\nThese principles lead to:")
print("✅ More maintainable code")
print("✅ Better testability")
print("✅ Increased flexibility")
print("✅ Reduced coupling")
print("✅ Higher cohesion")