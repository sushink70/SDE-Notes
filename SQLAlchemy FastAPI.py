# SQLAlchemy is a powerful Python SQL toolkit and Object-Relational Mapping (ORM) library that provides a high-level abstraction over database operations. Let me explain its core functionality and how it integrates with FastAPI.

## What is SQLAlchemy?

# SQLAlchemy operates on two main levels:

# **Core Layer**: Provides a SQL expression language and connection pooling
# **ORM Layer**: Maps Python classes to database tables, enabling object-oriented database interactions

## How SQLAlchemy Works Internally

# SQLAlchemy uses several key architectural patterns:

# 1. **Unit of Work Pattern**: Tracks changes to objects and commits them as a single transaction
# 2. **Data Mapper Pattern**: Separates business logic from database access code
# 3. **Connection Pooling**: Manages database connections efficiently to avoid connection overhead
# 4. **Lazy Loading**: Loads related data only when accessed, optimizing performance

## SQLAlchemy with FastAPI Integration

# Here's how they work together with practical examples:

### 1. Database Connection Setup


# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

# Database URL (PostgreSQL in your case)
DATABASE_URL = "postgresql://user:password@localhost/dbname"

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Connection pool size
    max_overflow=30,  # Additional connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for getting DB session
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


### 2. Model Definition with Security Best Practices


# models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from passlib.context import CryptContext
from database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)  # Never store plain passwords
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship with posts
    posts = relationship("Post", back_populates="author")
    
    def verify_password(self, plain_password: str) -> bool:
        """Verify password using bcrypt - security best practice"""
        return pwd_context.verify(plain_password, self.hashed_password)
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash password before storing"""
        return pwd_context.hash(password)

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship back to user
    author = relationship("User", back_populates="posts")


### 3. Pydantic Schemas for Type Safety


# schemas.py
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import List, Optional

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        """Security: Enforce strong password requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True  # SQLAlchemy 2.0 style

class PostCreate(BaseModel):
    title: str
    content: str

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    created_at: datetime
    author: UserResponse
    
    class Config:
        from_attributes = True


### 4. FastAPI Endpoints with SQLAlchemy


# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import engine, get_db

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Blog API", version="1.0.0")
security = HTTPBearer()

@app.post("/users/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create new user with hashed password
    SQLAlchemy handles the database transaction internally
    """
    # Check if user already exists (security best practice)
    db_user = db.query(models.User).filter(
        (models.User.email == user.email) | 
        (models.User.username == user.username)
    ).first()
    
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email or username already registered"
        )
    
    # Hash password before storing
    hashed_password = models.User.hash_password(user.password)
    
    # Create user instance
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    
    # SQLAlchemy's Unit of Work pattern in action
    db.add(db_user)  # Add to session
    db.commit()      # Commit transaction
    db.refresh(db_user)  # Refresh instance with DB data
    
    return db_user

@app.get("/users/", response_model=List[schemas.UserResponse])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get users with pagination
    SQLAlchemy automatically handles SQL generation
    """
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@app.get("/users/{user_id}/posts", response_model=List[schemas.PostResponse])
def get_user_posts(user_id: int, db: Session = Depends(get_db)):
    """
    Demonstrates SQLAlchemy's relationship loading
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # SQLAlchemy's lazy loading - posts are loaded when accessed
    return user.posts

@app.post("/posts/", response_model=schemas.PostResponse)
def create_post(
    post: schemas.PostCreate, 
    current_user_id: int,  # In real app, get from JWT token
    db: Session = Depends(get_db)
):
    """
    Create post with relationship to user
    """
    db_post = models.Post(
        title=post.title,
        content=post.content,
        author_id=current_user_id
    )
    
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return db_post


## Key Benefits of SQLAlchemy with FastAPI

### 1. **Type Safety & IDE Support**

# With SQLAlchemy + Pydantic, you get full type checking
def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()
    # IDE knows return type is User or None


### 2. **Automatic SQL Generation**

# This Python code:
db.query(models.User).join(models.Post).filter(models.Post.title.like("%python%")).all()

# Generates optimized SQL:
# SELECT users.* FROM users JOIN posts ON users.id = posts.author_id 
# WHERE posts.title LIKE '%python%'


### 3. **Connection Pool Management**
# SQLAlchemy automatically manages database connections, preventing connection leaks and optimizing performance.

### 4. **Security Features**
# - **SQL Injection Prevention**: Parameterized queries by default
# - **Password Hashing**: Easy integration with security libraries
# - **Input Validation**: Combined with Pydantic for robust validation

## Real-World Usage Example: E-commerce API


# Advanced example showing complex relationships
class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Integer)  # Store in cents for precision
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

# Complex query with aggregation
@app.get("/analytics/top-customers")
def get_top_customers(db: Session = Depends(get_db)):
    result = db.query(
        models.User.username,
        func.sum(models.Order.total_amount).label("total_spent"),
        func.count(models.Order.id).label("order_count")
    ).join(models.Order).group_by(models.User.id).order_by(
        func.sum(models.Order.total_amount).desc()
    ).limit(10).all()
    
    return [
        {
            "username": username,
            "total_spent": total_spent / 100,  # Convert cents to dollars
            "order_count": order_count
        }
        for username, total_spent, order_count in result
    ]


## Performance Optimizations

### 1. **Eager Loading**

# Avoid N+1 queries by eager loading relationships
users_with_posts = db.query(models.User).options(
    joinedload(models.User.posts)
).all()


### 2. **Query Optimization**

# Use select_related equivalent for better performance
from sqlalchemy.orm import selectinload

users = db.query(models.User).options(
    selectinload(models.User.posts)
).all()


# SQLAlchemy with FastAPI provides a robust, type-safe, and secure foundation for building APIs. It handles the complex database operations while you focus on business logic, making it an excellent choice for your Python backend development alongside your Django expertise.