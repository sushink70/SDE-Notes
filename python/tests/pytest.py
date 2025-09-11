## Key Pytest Concepts and Best Practices

### **Running Tests**

```bash
# Run all tests
pytest

# Run specific test file
pytest test_calculator.py

# Run specific test class or function
pytest test_calculator.py::TestCalculator::test_add
pytest test_calculator.py::TestCalculator

# Run tests with verbose output
pytest -v

# Run tests with coverage report
pytest --cov=calculator --cov-report=html

# Run tests in parallel
pytest -n 4  # requires pytest-xdist plugin

# Run only failed tests from last run
pytest --lf

# Stop on first failure
pytest -x
```

### **Advanced Pytest Features**

**Marks and Markers:**
- `@pytest.mark.slow` - Mark slow tests
- `@pytest.mark.integration` - Mark integration tests
- `@pytest.mark.skip` - Skip tests
- `@pytest.mark.skipif(condition)` - Conditional skip
- `@pytest.mark.xfail` - Expected to fail

**Pytest Configuration (pytest.ini):**
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### **Real-World Use Cases Summary**

**1. Web Application Testing:**
- Test API endpoints and responses
- Test authentication and authorization
- Test form validation and data processing
- Integration testing of complete user workflows

**2. Data Processing and ETL Testing:**
- Test data cleaning and transformation logic
- Test data validation rules
- Test performance with different dataset sizes
- Test error handling for malformed data

**3. API and External Service Testing:**
- Mock external API calls to avoid dependencies
- Test different response scenarios (success, error, timeout)
- Test rate limiting and authentication
- Integration testing with multiple services

**4. Database Testing:**
- Test database operations (CRUD)
- Test data migrations
- Test database transactions and rollbacks
- Test connection pooling and performance

**5. Machine Learning Testing:**
- Test data preprocessing pipelines
- Test model training and prediction accuracy
- Test feature engineering functions
- Test model serialization/deserialization

### **Benefits of Using Pytest**

1. **Simplicity**: Write tests using plain assert statements
2. **Powerful Fixtures**: Reusable setup/teardown with dependency injection
3. **Parametrization**: Run same test with different inputs
4. **Rich Plugin Ecosystem**: Coverage, parallel execution, HTML reports, etc.
5. **Detailed Failure Reports**: Clear information about what went wrong
6. **Flexible Test Discovery**: Automatic detection of test files and functions
7. **Mocking Support**: Easy integration with unittest.mock
8. **CI/CD Integration**: Works seamlessly with continuous integration pipelines

Pytest is essential for maintaining code quality, catching regressions early, and enabling confident refactoring. It scales from simple unit tests to complex integration test suites, making it the go-to testing framework for Python projects of all sizes.

# calculator.py - Simple calculator module to test
class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    def power(self, base, exponent):
        return base ** exponent

# test_calculator.py - Basic tests
import pytest
from calculator import Calculator

class TestCalculator:
    def setup_method(self):
        """Setup method called before each test method"""
        self.calc = Calculator()

    def test_add(self):
        assert self.calc.add(2, 3) == 5
        assert self.calc.add(-1, 1) == 0
        assert self.calc.add(0, 0) == 0

    def test_subtract(self):
        assert self.calc.subtract(5, 3) == 2
        assert self.calc.subtract(0, 5) == -5

    def test_multiply(self):
        assert self.calc.multiply(3, 4) == 12
        assert self.calc.multiply(-2, 3) == -6
        assert self.calc.multiply(0, 100) == 0

    def test_divide(self):
        assert self.calc.divide(10, 2) == 5
        assert self.calc.divide(7, 2) == 3.5

    def test_divide_by_zero(self):
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            self.calc.divide(10, 0)

    @pytest.mark.parametrize("base,exponent,expected", [
        (2, 3, 8),
        (5, 2, 25),
        (3, 0, 1),
        (10, 1, 10),
        (-2, 2, 4),
        (-2, 3, -8)
    ])
    def test_power(self, base, exponent, expected):
        assert self.calc.power(base, exponent) == expected


# models.py - Sample models for testing
import requests
from datetime import datetime
from typing import List, Dict, Optional

class User:
    def __init__(self, user_id: int, username: str, email: str):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.created_at = datetime.now()
        self.posts = []

    def add_post(self, title: str, content: str) -> dict:
        post = {
            'id': len(self.posts) + 1,
            'title': title,
            'content': content,
            'author': self.username,
            'created_at': datetime.now()
        }
        self.posts.append(post)
        return post

    def get_posts(self) -> List[dict]:
        return self.posts.copy()

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_user_data(self, user_id: int) -> dict:
        response = requests.get(f"{self.base_url}/users/{user_id}")
        response.raise_for_status()
        return response.json()

    def create_user(self, user_data: dict) -> dict:
        response = requests.post(f"{self.base_url}/users", json=user_data)
        response.raise_for_status()
        return response.json()

# conftest.py - Shared fixtures
import pytest
from unittest.mock import Mock, patch
from models import User, APIClient

@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    return User(user_id=1, username="testuser", email="test@example.com")

@pytest.fixture
def users_list():
    """Create a list of users for bulk testing"""
    users = []
    for i in range(1, 4):
        user = User(
            user_id=i,
            username=f"user{i}",
            email=f"user{i}@example.com"
        )
        users.append(user)
    return users

@pytest.fixture
def api_client():
    """Create an API client for testing"""
    return APIClient("https://api.example.com")

@pytest.fixture
def mock_requests():
    """Mock requests module"""
    with patch('models.requests') as mock:
        yield mock

# test_models_advanced.py - Advanced testing examples
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import requests
from models import User, APIClient

class TestUser:
    def test_user_creation(self, sample_user):
        assert sample_user.user_id == 1
        assert sample_user.username == "testuser"
        assert sample_user.email == "test@example.com"
        assert isinstance(sample_user.created_at, datetime)
        assert sample_user.posts == []

    def test_add_post(self, sample_user):
        post = sample_user.add_post("Test Title", "Test Content")

        assert post['id'] == 1
        assert post['title'] == "Test Title"
        assert post['content'] == "Test Content"
        assert post['author'] == "testuser"
        assert isinstance(post['created_at'], datetime)

        # Verify post is added to user's posts
        assert len(sample_user.posts) == 1
        assert sample_user.posts[0] == post

    def test_multiple_posts(self, sample_user):
        post1 = sample_user.add_post("First Post", "First Content")
        post2 = sample_user.add_post("Second Post", "Second Content")

        assert len(sample_user.posts) == 2
        assert post1['id'] == 1
        assert post2['id'] == 2

    def test_get_posts_returns_copy(self, sample_user):
        sample_user.add_post("Test", "Content")
        posts = sample_user.get_posts()

        # Modify the returned list
        posts.append({'id': 999, 'title': 'Fake'})

        # Original posts should be unchanged
        assert len(sample_user.posts) == 1
        assert len(sample_user.get_posts()) == 1

    @pytest.mark.parametrize("username,email", [
        ("alice", "alice@test.com"),
        ("bob123", "bob@company.org"),
        ("user_with_underscore", "user@domain.co.uk")
    ])
    def test_user_creation_parametrized(self, username, email):
        user = User(1, username, email)
        assert user.username == username
        assert user.email == email

class TestAPIClient:
    def test_get_user_data_success(self, api_client, mock_requests):
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com'
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.get.return_value = mock_response

        # Test the method
        result = api_client.get_user_data(1)

        # Verify the call
        mock_requests.get.assert_called_once_with("https://api.example.com/users/1")
        assert result['username'] == 'testuser'

    def test_get_user_data_http_error(self, api_client, mock_requests):
        # Setup mock to raise an exception
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_requests.get.return_value = mock_response

        # Test that exception is raised
        with pytest.raises(requests.HTTPError):
            api_client.get_user_data(999)

    def test_create_user_success(self, api_client, mock_requests):
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 2,
            'username': 'newuser',
            'email': 'new@example.com',
            'created': True
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response

        user_data = {'username': 'newuser', 'email': 'new@example.com'}
        result = api_client.create_user(user_data)

        # Verify the call
        mock_requests.post.assert_called_once_with(
            "https://api.example.com/users",
            json=user_data
        )
        assert result['created'] is True
        assert result['id'] == 2

# test_integration.py - Integration testing example
import pytest
from unittest.mock import patch
import time

class TestIntegration:
    """Integration tests that test multiple components together"""

    def test_user_workflow(self):
        # Create user
        user = User(1, "integrationuser", "integration@test.com")

        # Add multiple posts
        post1 = user.add_post("First Post", "This is my first post")
        post2 = user.add_post("Second Post", "This is my second post")

        # Verify workflow
        posts = user.get_posts()
        assert len(posts) == 2
        assert posts[0]['title'] == "First Post"
        assert posts[1]['title'] == "Second Post"

        # Verify all posts have the same author
        for post in posts:
            assert post['author'] == user.username

    @patch('time.sleep')  # Mock time.sleep to speed up test
    def test_user_post_timing(self, mock_sleep):
        user = User(1, "timeuser", "time@test.com")

        start_time = datetime.now()
        post1 = user.add_post("Post 1", "Content 1")

        mock_sleep(1)  # Simulate 1 second delay
        post2 = user.add_post("Post 2", "Content 2")

        # Both posts should have recent timestamps
        assert (post1['created_at'] - start_time).total_seconds() < 1
        assert (post2['created_at'] - start_time).total_seconds() < 2

# Fixtures with different scopes
@pytest.fixture(scope="session")
def database_connection():
    """Session-scoped fixture - created once per test session"""
    print("\nSetting up database connection")
    connection = {"host": "localhost", "port": 5432, "connected": True}
    yield connection
    print("\nTearing down database connection")

@pytest.fixture(scope="module")
def test_data():
    """Module-scoped fixture - created once per test module"""
    return {"test_users": 100, "test_posts": 500}

@pytest.fixture(scope="class")
def class_setup():
    """Class-scoped fixture - created once per test class"""
    return {"class_initialized": True}

@pytest.fixture(scope="function")
def function_setup():
    """Function-scoped fixture - created for each test function (default)"""
    return {"function_initialized": True}

# app.py - Flask web application
from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'test_secret_key'

class UserService:
    def __init__(self, db_path=':memory:'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def create_user(self, username, email, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        password_hash = generate_password_hash(password)

        try:
            cursor.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            conn.commit()
            user_id = cursor.lastrowid
            return {'id': user_id, 'username': username, 'email': email}
        except sqlite3.IntegrityError as e:
            return None
        finally:
            conn.close()

    def authenticate_user(self, username, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT id, username, email, password_hash FROM users WHERE username = ?',
            (username,)
        )
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            return {'id': user[0], 'username': user[1], 'email': user[2]}
        return None

user_service = UserService()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'error': 'Missing required fields'}), 400

    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    user = user_service.create_user(
        data['username'],
        data['email'],
        data['password']
    )

    if user:
        return jsonify(user), 201
    else:
        return jsonify({'error': 'Username or email already exists'}), 409

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not all(k in data for k in ('username', 'password')):
        return jsonify({'error': 'Missing username or password'}), 400

    user = user_service.authenticate_user(data['username'], data['password'])

    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'message': 'Login successful', 'user': user}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    return jsonify({
        'user_id': session['user_id'],
        'username': session['username']
    }), 200

# test_webapp.py - Web application tests
import pytest
import json
from app import app, UserService

@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def user_service():
    """Create a fresh UserService instance for each test"""
    return UserService()

class TestUserService:
    def test_create_user_success(self, user_service):
        user = user_service.create_user("testuser", "test@example.com", "password123")

        assert user is not None
        assert user['username'] == "testuser"
        assert user['email'] == "test@example.com"
        assert 'id' in user

    def test_create_user_duplicate_username(self, user_service):
        # Create first user
        user1 = user_service.create_user("testuser", "test1@example.com", "password123")
        assert user1 is not None

        # Try to create user with same username
        user2 = user_service.create_user("testuser", "test2@example.com", "password456")
        assert user2 is None

    def test_authenticate_user_success(self, user_service):
        # Create user first
        user_service.create_user("testuser", "test@example.com", "password123")

        # Authenticate
        user = user_service.authenticate_user("testuser", "password123")
        assert user is not None
        assert user['username'] == "testuser"

    def test_authenticate_user_wrong_password(self, user_service):
        user_service.create_user("testuser", "test@example.com", "password123")

        user = user_service.authenticate_user("testuser", "wrongpassword")
        assert user is None

    def test_authenticate_nonexistent_user(self, user_service):
        user = user_service.authenticate_user("nonexistent", "password")
        assert user is None

class TestWebApp:
    def test_register_success(self, client):
        response = client.post('/register',
            data=json.dumps({
                'username': 'newuser',
                'email': 'new@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['username'] == 'newuser'
        assert data['email'] == 'new@example.com'
        assert 'id' in data

    def test_register_missing_fields(self, client):
        response = client.post('/register',
            data=json.dumps({
                'username': 'newuser'
                # Missing email and password
            }),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_register_password_too_short(self, client):
        response = client.post('/register',
            data=json.dumps({
                'username': 'newuser',
                'email': 'new@example.com',
                'password': '123'  # Too short
            }),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'Password must be at least 6 characters' in data['error']

    def test_login_success(self, client):
        # Register user first
        client.post('/register',
            data=json.dumps({
                'username': 'loginuser',
                'email': 'login@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )

        # Now login
        response = client.post('/login',
            data=json.dumps({
                'username': 'loginuser',
                'password': 'password123'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Login successful'
        assert 'user' in data

    def test_login_invalid_credentials(self, client):
        response = client.post('/login',
            data=json.dumps({
                'username': 'nonexistent',
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )

        assert response.status_code == 401
        data = response.get_json()
        assert 'Invalid credentials' in data['error']

    def test_profile_authenticated(self, client):
        # Register and login first
        client.post('/register',
            data=json.dumps({
                'username': 'profileuser',
                'email': 'profile@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )

        client.post('/login',
            data=json.dumps({
                'username': 'profileuser',
                'password': 'password123'
            }),
            content_type='application/json'
        )

        # Access profile
        response = client.get('/profile')
        assert response.status_code == 200
        data = response.get_json()
        assert data['username'] == 'profileuser'

    def test_profile_unauthenticated(self, client):
        response = client.get('/profile')
        assert response.status_code == 401
        data = response.get_json()
        assert 'Authentication required' in data['error']

    def test_logout(self, client):
        # Login first
        client.post('/register',
            data=json.dumps({
                'username': 'logoutuser',
                'email': 'logout@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )

        client.post('/login',
            data=json.dumps({
                'username': 'logoutuser',
                'password': 'password123'
            }),
            content_type='application/json'
        )

        # Logout
        response = client.post('/logout')
        assert response.status_code == 200

        # Verify session is cleared - profile should be inaccessible
        profile_response = client.get('/profile')
        assert profile_response.status_code == 401

# test_webapp_integration.py - End-to-end integration tests
class TestWebAppIntegration:
    def test_complete_user_workflow(self, client):
        """Test complete user registration, login, and profile access workflow"""

        # Step 1: Register a new user
        register_response = client.post('/register',
            data=json.dumps({
                'username': 'workflowuser',
                'email': 'workflow@example.com',
                'password': 'securepassword123'
            }),
            content_type='application/json'
        )
        assert register_response.status_code == 201

        # Step 2: Login with the registered user
        login_response = client.post('/login',
            data=json.dumps({
                'username': 'workflowuser',
                'password': 'securepassword123'
            }),
            content_type='application/json'
        )
        assert login_response.status_code == 200

        # Step 3: Access profile (should work)
        profile_response = client.get('/profile')
        assert profile_response.status_code == 200
        profile_data = profile_response.get_json()
        assert profile_data['username'] == 'workflowuser'

        # Step 4: Logout
        logout_response = client.post('/logout')
        assert logout_response.status_code == 200

        # Step 5: Try to access profile after logout (should fail)
        profile_after_logout = client.get('/profile')
        assert profile_after_logout.status_code == 401

    @pytest.mark.parametrize("username,email,password,expected_status", [
        ("user1", "user1@test.com", "password123", 201),
        ("user2", "user2@test.com", "pass", 400),  # Password too short
        ("", "user3@test.com", "password123", 400),  # Empty username
        ("user4", "", "password123", 400),  # Empty email
    ])
    def test_registration_validation(self, client, username, email, password, expected_status):
        response = client.post('/register',
            data=json.dumps({
                'username': username,
                'email': email,
                'password': password
            }),
            content_type='application/json'
        )
        assert response.status_code == expected_status


# data_processor.py - Data processing module
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import json
from datetime import datetime, timedelta

class SalesDataProcessor:
    def __init__(self):
        self.data = None
        self.processed_data = None

    def load_data(self, data_source):
        """Load data from various sources"""
        if isinstance(data_source, str):
            # Assume it's a file path
            if data_source.endswith('.csv'):
                self.data = pd.read_csv(data_source)
            elif data_source.endswith('.json'):
                self.data = pd.read_json(data_source)
        elif isinstance(data_source, pd.DataFrame):
            self.data = data_source.copy()
        elif isinstance(data_source, list):
            self.data = pd.DataFrame(data_source)
        else:
            raise ValueError("Unsupported data source type")

        return self.data

    def clean_data(self):
        """Clean and preprocess the data"""
        if self.data is None:
            raise ValueError("No data loaded")

        cleaned_data = self.data.copy()

        # Remove duplicates
        cleaned_data = cleaned_data.drop_duplicates()

        # Handle missing values
        if 'amount' in cleaned_data.columns:
            cleaned_data['amount'].fillna(0, inplace=True)

        if 'date' in cleaned_data.columns:
            cleaned_data['date'] = pd.to_datetime(cleaned_data['date'])

        # Remove negative amounts (assuming they're errors)
        if 'amount' in cleaned_data.columns:
            cleaned_data = cleaned_data[cleaned_data['amount'] >= 0]

        self.processed_data = cleaned_data
        return self.processed_data

    def calculate_metrics(self):
        """Calculate various sales metrics"""
        if self.processed_data is None:
            raise ValueError("Data not processed yet")

        data = self.processed_data
        metrics = {}

        if 'amount' in data.columns:
            metrics['total_sales'] = data['amount'].sum()
            metrics['average_sale'] = data['amount'].mean()
            metrics['median_sale'] = data['amount'].median()
            metrics['min_sale'] = data['amount'].min()
            metrics['max_sale'] = data['amount'].max()
            metrics['std_sale'] = data['amount'].std()

        if 'date' in data.columns:
            date_range = data['date'].max() - data['date'].min()
            metrics['date_range_days'] = date_range.days
            metrics['sales_per_day'] = len(data) / max(date_range.days, 1)

        if 'product' in data.columns:
            metrics['unique_products'] = data['product'].nunique()
            metrics['product_distribution'] = data['product'].value_counts().to_dict()

        if 'customer_id' in data.columns:
            metrics['unique_customers'] = data['customer_id'].nunique()
            metrics['repeat_customers'] = len(data[data.duplicated(subset=['customer_id'], keep=False)])

        return metrics

    def filter_by_date_range(self, start_date: str, end_date: str):
        """Filter data by date range"""
        if self.processed_data is None:
            raise ValueError("Data not processed yet")

        if 'date' not in self.processed_data.columns:
            raise ValueError("No date column in data")

        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        filtered_data = self.processed_data[
            (self.processed_data['date'] >= start_date) &
            (self.processed_data['date'] <= end_date)
        ]

        return filtered_data

    def get_top_products(self, n: int = 5):
        """Get top N products by sales amount"""
        if self.processed_data is None:
            raise ValueError("Data not processed yet")

        if not all(col in self.processed_data.columns


# data_processor.py - Data processing module
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import json
from datetime import datetime, timedelta

class SalesDataProcessor:
    def __init__(self):
        self.data = None
        self.processed_data = None
    
    def load_data(self, data_source):
        """Load data from various sources"""
        if isinstance(data_source, str):
            # Assume it's a file path
            if data_source.endswith('.csv'):
                self.data = pd.read_csv(data_source)
            elif data_source.endswith('.json'):
                self.data = pd.read_json(data_source)
        elif isinstance(data_source, pd.DataFrame):
            self.data = data_source.copy()
        elif isinstance(data_source, list):
            self.data = pd.DataFrame(data_source)
        else:
            raise ValueError("Unsupported data source type")
        
        return self.data
    
    def clean_data(self):
        """Clean and preprocess the data"""
        if self.data is None:
            raise ValueError("No data loaded")
        
        cleaned_data = self.data.copy()
        
        # Remove duplicates
        cleaned_data = cleaned_data.drop_duplicates()
        
        # Handle missing values
        if 'amount' in cleaned_data.columns:
            cleaned_data['amount'].fillna(0, inplace=True)
        
        if 'date' in cleaned_data.columns:
            cleaned_data['date'] = pd.to_datetime(cleaned_data['date'])
        
        # Remove negative amounts (assuming they're errors)
        if 'amount' in cleaned_data.columns:
            cleaned_data = cleaned_data[cleaned_data['amount'] >= 0]
        
        self.processed_data = cleaned_data
        return self.processed_data
    
    def calculate_metrics(self):
        """Calculate various sales metrics"""
        if self.processed_data is None:
            raise ValueError("Data not processed yet")
        
        data = self.processed_data
        metrics = {}
        
        if 'amount' in data.columns:
            metrics['total_sales'] = data['amount'].sum()
            metrics['average_sale'] = data['amount'].mean()
            metrics['median_sale'] = data['amount'].median()
            metrics['min_sale'] = data['amount'].min()
            metrics['max_sale'] = data['amount'].max()
            metrics['std_sale'] = data['amount'].std()
        
        if 'date' in data.columns:
            date_range = data['date'].max() - data['date'].min()
            metrics['date_range_days'] = date_range.days
            metrics['sales_per_day'] = len(data) / max(date_range.days, 1)
        
        if 'product' in data.columns:
            metrics['unique_products'] = data['product'].nunique()
            metrics['product_distribution'] = data['product'].value_counts().to_dict()
        
        if 'customer_id' in data.columns:
            metrics['unique_customers'] = data['customer_id'].nunique()
            metrics['repeat_customers'] = len(data[data.duplicated(subset=['customer_id'], keep=False)])
        
        return metrics
    
    def filter_by_date_range(self, start_date: str, end_date: str):
        """Filter data by date range"""
        if self.processed_data is None:
            raise ValueError("Data not processed yet")
        
        if 'date' not in self.processed_data.columns:
            raise ValueError("No date column in data")
        
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        
        filtered_data = self.processed_data[
            (self.processed_data['date'] >= start_date) &
            (self.processed_data['date'] <= end_date)
        ]
        
        return filtered_data
    
    def get_top_products(self, n: int = 5):
        """Get top N products by sales amount"""
        if self.processed_data is None:
            raise ValueError("Data not processed yet")
        
        if not all(col in self.processed_data.columns for col in ['product', 'amount']):
            raise ValueError("Missing required columns: product and amount")
        
        top_products = (self.processed_data
                       .groupby('product')['amount']
                       .sum()
                       .sort_values(ascending=False)
                       .head(n)
                       .to_dict())
        
        return top_products
    
    def get_monthly_trends(self):
        """Calculate monthly sales trends"""
        if self.processed_data is None:
            raise ValueError("Data not processed yet")
        
        if not all(col in self.processed_data.columns for col in ['date', 'amount']):
            raise ValueError("Missing required columns: date and amount")
        
        monthly_data = (self.processed_data
                       .set_index('date')
                       .resample('M')['amount']
                       .agg(['sum', 'count', 'mean'])
                       .round(2))
        
        return monthly_data.to_dict('index')

class DataValidator:
    @staticmethod
    def validate_sales_data(data: pd.DataFrame) -> List[str]:
        """Validate sales data and return list of validation errors"""
        errors = []
        
        required_columns = ['date', 'amount', 'product']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
        
        if 'amount' in data.columns:
            if data['amount'].isnull().sum() > len(data) * 0.1:  # More than 10% missing
                errors.append("Too many missing values in amount column")
            
            if (data['amount'] < 0).sum() > 0:
                errors.append("Negative amounts found in data")
        
        if 'date' in data.columns:
            try:
                pd.to_datetime(data['date'])
            except:
                errors.append("Invalid date format in date column")
        
        if len(data) == 0:
            errors.append("Dataset is empty")
        
        duplicate_count = data.duplicated().sum()
        if duplicate_count > len(data) * 0.05:  # More than 5% duplicates
            errors.append(f"High number of duplicates: {duplicate_count}")
        
        return errors

# test_data_processor.py - Comprehensive data processing tests
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_processor import SalesDataProcessor, DataValidator

@pytest.fixture
def sample_sales_data():
    """Create sample sales data for testing"""
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    np.random.seed(42)  # For reproducible tests
    
    data = []
    products = ['Widget A', 'Widget B', 'Gadget X', 'Gadget Y', 'Tool Z']
    
    for i in range(1000):
        date = np.random.choice(dates)
        product = np.random.choice(products)
        amount = np.random.uniform(10, 1000)
        customer_id = np.random.randint(1, 200)
        
        data.append({
            'date': date,
            'product': product,
            'amount': round(amount, 2),
            'customer_id': customer_id
        })
    
    return pd.DataFrame(data)

@pytest.fixture
def dirty_sales_data():
    """Create dirty sales data with various issues for testing"""
    data = [
        {'date': '2023-01-01', 'product': 'Widget A', 'amount': 100.0, 'customer_id': 1},
        {'date': '2023-01-01', 'product': 'Widget A', 'amount': 100.0, 'customer_id': 1},  # Duplicate
        {'date': '2023-01-02', 'product': 'Widget B', 'amount': -50.0, 'customer_id': 2},  # Negative
        {'date': '2023-01-03', 'product': 'Gadget X', 'amount': None, 'customer_id': 3},  # Missing amount
        {'date': 'invalid-date', 'product': 'Gadget Y', 'amount': 200.0, 'customer_id': 4},  # Invalid date
        {'date': '2023-01-05', 'product': 'Tool Z', 'amount': 150.0, 'customer_id': 5},
    ]
    return pd.DataFrame(data)

@pytest.fixture
def processor():
    """Create a SalesDataProcessor instance"""
    return SalesDataProcessor()

class TestSalesDataProcessor:
    def test_load_data_dataframe(self, processor, sample_sales_data):
        result = processor.load_data(sample_sales_data)
        
        assert processor.data is not None
        assert len(processor.data) == 1000
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ['date', 'product', 'amount', 'customer_id']
    
    def test_load_data_list(self, processor):
        data_list = [
            {'date': '2023-01-01', 'product': 'Widget A', 'amount': 100},
            {'date': '2023-01-02', 'product': 'Widget B', 'amount': 200}
        ]
        
        result = processor.load_data(data_list)
        
        assert len(result) == 2
        assert 'date' in result.columns
        assert 'product' in result.columns
        assert 'amount' in result.columns
    
    def test_load_data_invalid_type(self, processor):
        with pytest.raises(ValueError, match="Unsupported data source type"):
            processor.load_data(123)  # Invalid type
    
    def test_clean_data_no_data_loaded(self, processor):
        with pytest.raises(ValueError, match="No data loaded"):
            processor.clean_data()
    
    def test_clean_data_removes_duplicates(self, processor, dirty_sales_data):
        processor.load_data(dirty_sales_data)
        cleaned = processor.clean_data()
        
        # Should have removed the duplicate row
        assert len(cleaned) < len(dirty_sales_data)
        assert not cleaned.duplicated().any()
    
    def test_clean_data_handles_missing_amounts(self, processor, dirty_sales_data):
        processor.load_data(dirty_sales_data)
        cleaned = processor.clean_data()
        
        # Missing amounts should be filled with 0
        assert not cleaned['amount'].isnull().any()
        assert 0 in cleaned['amount'].values
    
    def test_clean_data_removes_negative_amounts(self, processor, dirty_sales_data):
        processor.load_data(dirty_sales_data)
        cleaned = processor.clean_data()
        
        # Negative amounts should be removed
        assert (cleaned['amount'] >= 0).all()
    
    def test_calculate_metrics_basic(self, processor, sample_sales_data):
        processor.load_data(sample_sales_data)
        processor.clean_data()
        metrics = processor.calculate_metrics()
        
        assert 'total_sales' in metrics
        assert 'average_sale' in metrics
        assert 'median_sale' in metrics
        assert 'unique_products' in metrics
        assert 'unique_customers' in metrics
        
        assert metrics['total_sales'] > 0
        assert metrics['unique_products'] == 5  # We have 5 products
        assert metrics['unique_customers'] > 0
    
    def test_calculate_metrics_no_processed_data(self, processor):
        with pytest.raises(ValueError, match="Data not processed yet"):
            processor.calculate_metrics()
    
    @pytest.mark.parametrize("start_date,end_date,expected_min_count", [
        ('2023-01-01', '2023-01-31', 1),
        ('2023-06-01', '2023-06-30', 1),
        ('2023-12-01', '2023-12-31', 1),
    ])
    def test_filter_by_date_range(self, processor, sample_sales_data, start_date, end_date, expected_min_count):
        processor.load_data(sample_sales_data)
        processor.clean_data()
        
        filtered = processor.filter_by_date_range(start_date, end_date)
        
        assert len(filtered) >= expected_min_count
        assert (filtered['date'] >= pd.to_datetime(start_date)).all()
        assert (filtered['date'] <= pd.to_datetime(end_date)).all()
    
    def test_get_top_products(self, processor, sample_sales_data):
        processor.load_data(sample_sales_data)
        processor.clean_data()
        
        top_products = processor.get_top_products(3)
        
        assert isinstance(top_products, dict)
        assert len(top_products) <= 3
        
        # Results should be sorted by amount (highest first)
        amounts = list(top_products.values())
        assert amounts == sorted(amounts, reverse=True)
    
    def test_get_monthly_trends(self, processor, sample_sales_data):
        processor.load_data(sample_sales_data)
        processor.clean_data()
        
        trends = processor.get_monthly_trends()
        
        assert isinstance(trends, dict)
        assert len(trends) > 0  # Should have at least some months
        
        # Each month should have sum, count, and mean
        for month_data in trends.values():
            assert 'sum' in month_data
            assert 'count' in month_data
            assert 'mean' in month_data

class TestDataValidator:
    def test_validate_clean_data(self):
        clean_data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=10),
            'amount': np.random.uniform(10, 100, 10),
            'product': ['Product A'] * 10
        })
        
        errors = DataValidator.validate_sales_data(clean_data)
        assert len(errors) == 0
    
    def test_validate_missing_columns(self):
        incomplete_data = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-02'],
            'amount': [100, 200]
            # Missing 'product' column
        })
        
        errors = DataValidator.validate_sales_data(incomplete_data)
        assert any("Missing required columns" in error for error in errors)
    
    def test_validate_negative_amounts(self):
        data_with_negatives = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-02'],
            'amount': [100, -50],  # Negative amount
            'product': ['A', 'B']
        })
        
        errors = DataValidator.validate_sales_data(data_with_negatives)
        assert any("Negative amounts" in error for error in errors)
    
    def test_validate_empty_dataset(self):
        empty_data = pd.DataFrame()
        
        errors = DataValidator.validate_sales_data(empty_data)
        assert any("Dataset is empty" in error for error in errors)
    
    def test_validate_too_many_missing_values(self):
        data_with_missing = pd.DataFrame({
            'date': ['2023-01-01'] * 10,
            'amount': [100] + [None] * 9,  # 90% missing values
            'product': ['A'] * 10
        })
        
        errors = DataValidator.validate_sales_data(data_with_missing)
        assert any("Too many missing values" in error for error in errors)

# test_data_integration.py - Integration tests for data processing
class TestDataProcessingIntegration:
    def test_complete_data_processing_workflow(self, processor):
        # Create realistic sales data
        data = []
        products = ['Laptop', 'Mouse', 'Keyboard', 'Monitor']
        
        for i in range(100):
            data.append({
                'date': datetime(2023, 1, 1) + timedelta(days=i % 365),
                'product': products[i % len(products)],
                'amount': round(np.random.uniform(50, 500), 2),
                'customer_id': i % 50  # 50 unique customers
            })
        
        # Add some problematic data
        data.append({'date': '2023-01-01', 'product': 'Laptop', 'amount': -100, 'customer_id': 1})  # Negative
        data.append({'date': '2023-01-01', 'product': 'Laptop', 'amount': 200, 'customer_id': 1})    # Duplicate
        data.append({'date': '2023-01-01', 'product': 'Laptop', 'amount': 200, 'customer_id': 1})    # Duplicate
        
        df = pd.DataFrame(data)
        
        # Step 1: Load data
        processor.load_data(df)
        assert processor.data is not None
        original_length = len(processor.data)
        
        # Step 2: Validate data
        errors = DataValidator.validate_sales_data(processor.data)
        assert len(errors) > 0  # Should detect negative amounts
        
        # Step 3: Clean data
        cleaned = processor.clean_data()
        assert len(cleaned) < original_length  # Should be smaller after cleaning
        assert (cleaned['amount'] >= 0).all()  # No negative amounts
        
        # Step 4: Calculate metrics
        metrics = processor.calculate_metrics()
        assert metrics['total_sales'] > 0
        assert metrics['unique_products'] == 4
        
        # Step 5: Get top products
        top_products = processor.get_top_products(2)
        assert len(top_products) <= 2
        
        # Step 6: Filter by date
        jan_data = processor.filter_by_date_range('2023-01-01', '2023-01-31')
        assert len(jan_data) >= 0
    
    @pytest.mark.parametrize("data_size", [10, 100, 1000])
    def test_performance_with_different_sizes(self, processor, data_size):
        """Test performance with different dataset sizes"""
        import time
        
        # Generate data of specified size
        data = []
        for i in range(data_size):
            data.append({
                'date': datetime(2023, 1, 1) + timedelta(days=i % 365),
                'product': f'Product_{i % 10}',
                'amount': round(np.random.uniform(10, 1000), 2),
                'customer_id': i % 100
            })
        
        df = pd.DataFrame(data)
        
        # Time the complete workflow
        start_time = time.time()
        
        processor.load_data(df)
        processor.clean_data()
        metrics = processor.calculate_metrics()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Basic assertions
        assert metrics['total_sales'] > 0
        assert len(processor.processed_data) <= data_size  # May be less due to cleaning
        
        # Performance should be reasonable (adjust thresholds as needed)
        if data_size <= 100:
            assert processing_time < 1.0  # Should process small datasets quickly
        elif data_size <= 1000:
            assert processing_time < 5.0  # Larger datasets should still be reasonable

# api_client.py - API client for external services
import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import time

@dataclass
class WeatherData:
    temperature: float
    humidity: int
    description: str
    city: str
    timestamp: datetime

class WeatherAPIClient:
    def __init__(self, api_key: str, base_url: str = "https://api.weather.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def get_current_weather(self, city: str) -> WeatherData:
        """Get current weather for a city"""
        url = f"{self.base_url}/current"
        params = {
            'q': city,
            'units': 'metric'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return WeatherData(
                temperature=data['main']['temp'],
                humidity=data['main']['humidity'],
                description=data['weather'][0]['description'],
                city=city,
                timestamp=datetime.now()
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timed out for city: {city}")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                raise ValueError(f"City not found: {city}")
            elif response.status_code == 401:
                raise ValueError("Invalid API key")
            elif response.status_code == 429:
                raise ValueError("Rate limit exceeded")
            else:
                raise ValueError(f"HTTP error: {e}")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Unable to connect to weather service")
    
    def get_forecast(self, city: str, days: int = 5) -> List[WeatherData]:
        """Get weather forecast for multiple days"""
        if days < 1 or days > 7:
            raise ValueError("Days must be between 1 and 7")
        
        url = f"{self.base_url}/forecast"
        params = {
            'q': city,
            'cnt': days,
            'units': 'metric'
        }
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        forecasts = []
        
        for item in data['list']:
            forecast = WeatherData(
                temperature=item['main']['temp'],
                humidity=item['main']['humidity'],
                description=item['weather'][0]['description'],
                city=city,
                timestamp=datetime.fromtimestamp(item['dt'])
            )
            forecasts.append(forecast)
        
        return forecasts
    
    def search_cities(self, query: str) -> List[Dict[str, str]]:
        """Search for cities matching the query"""
        url = f"{self.base_url}/search"
        params = {'q': query}
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        return response.json()['cities']

class PaymentProcessor:
    def __init__(self, api_key: str, environment: str = "sandbox"):
        self.api_key = api_key
        self.environment = environment
        self.base_url = f"https://api.{environment}.payment.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def create_payment_intent(self, amount: int, currency: str = "USD") -> Dict:
        """Create a payment intent"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if currency not in ["USD", "EUR", "GBP"]:
            raise ValueError(f"Unsupported currency: {currency}")
        
        url = f"{self.base_url}/payment_intents"
        data = {
            'amount': amount,
            'currency': currency.lower(),
            'confirm': True
        }
        
        response = self.session.post(url, json=data, timeout=15)
        response.raise_for_status()
        
        return response.json()
    
    def capture_payment(self, payment_intent_id: str) -> Dict:
        """Capture a payment"""
        url = f"{self.base_url}/payment_intents/{payment_intent_id}/capture"
        
        response = self.session.post(url, timeout=15)
        response.raise_for_status()
        
        return response.json()
    
    def refund_payment(self, payment_intent_id: str, amount: Optional[int] = None) -> Dict:
        """Refund a payment"""
        url = f"{self.base_url}/refunds"
        data = {'payment_intent': payment_intent_id}
        
        if amount:
            data['amount'] = amount
        
        response = self.session.post(url, json=data, timeout=15)
        response.raise_for_status()
        
        return response.json()

class RateLimiter:
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def acquire(self):
        now = time.time()
        # Remove calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
                return self.acquire()
        
        self.calls.append(now)

# test_api_client.py - Comprehensive API testing
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from datetime import datetime
from api_client import WeatherAPIClient, PaymentProcessor, WeatherData, RateLimiter

class TestWeatherAPIClient:
    @pytest.fixture
    def weather_client(self):
        return WeatherAPIClient("test_api_key")
    
    @pytest.fixture
    def mock_weather_response(self):
        return {
            'main': {
                'temp': 25.5,
                'humidity': 60
            },
            'weather': [
                {
                    'description': 'clear sky'
                }
            ]
        }
    
    @pytest.fixture
    def mock_forecast_response(self):
        return {
            'list': [
                {
                    'dt': 1609459200,  # timestamp
                    'main': {'temp': 20.0, 'humidity': 50},
                    'weather': [{'description': 'cloudy'}]
                },
                {
                    'dt': 1609545600,  # timestamp
                    'main': {'temp': 22.5, 'humidity': 55},
                    'weather': [{'description': 'sunny'}]
                }
            ]
        }
    
    @patch('api_client.requests.Session.get')
    def test_get_current_weather_success(self, mock_get, weather_client, mock_weather_response):
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test
        weather = weather_client.get_current_weather("London")
        
        # Assertions
        assert isinstance(weather, WeatherData)
        assert weather.temperature == 25.5
        assert weather.humidity == 60
        assert weather.description == "clear sky"
        assert weather.city == "London"
        assert isinstance(weather.timestamp, datetime)
        
        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "current" in call_args[0][0]  # URL contains 'current'
        assert call_args[1]['params']['q'] == "London"
    
    @patch('api_client.requests.Session.get')
    def test_get_current_weather_city_not_found(self, mock_get, weather_client):
        # Setup mock for 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_response
        
        # Test and assert
        with pytest.raises(ValueError, match="City not found"):
            weather_client.get_current_weather("NonexistentCity")
    
    @patch('api_client.requests.Session.get')
    def test_get_current_weather_invalid_api_key(self, mock_get, weather_client):
        # Setup mock for 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_response
        
        with pytest.raises(ValueError, match="Invalid API key"):
            weather_client.get_current_weather("London")
    
    @patch('api_client.requests.Session.get')
    def test_get_current_weather_rate_limit(self, mock_get, weather_client):
        # Setup mock for 429 response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_response
        
        with pytest.raises(ValueError, match="Rate limit exceeded"):
            weather_client.get_current_weather("London")
    
    @patch('api_client.requests.Session.get')
    def test_get_current_weather_timeout(self, mock_get, weather_client):
        # Setup mock for timeout
        mock_get.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(TimeoutError, match="Request timed out"):
            weather_client.get_current_weather("London")
    
    @patch('api_client.requests.Session.get')
    def test_get_current_weather_connection_error(self, mock_get, weather_client):
        # Setup mock for connection error
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(ConnectionError, match="Unable to connect"):
            weather_client.get_current_weather("London")
    
    @patch('api_client.requests.Session.get')
    def test_get_forecast_success(self, mock_get, weather_client, mock_forecast_response):
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = mock_forecast_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test
        forecasts = weather_client.get_forecast("London", days=2)
        
        # Assertions
        assert len(forecasts) == 2
        assert all(isinstance(f, WeatherData) for f in forecasts)
        assert forecasts[0].temperature == 20.0
        assert forecasts[1].temperature == 22.5
        assert forecasts[0].description == "cloudy"
        assert forecasts[1].description == "sunny"
    
    def test_get_forecast_invalid_days(self, weather_client):
        with pytest.raises(ValueError, match="Days must be between 1 and 7"):
            weather_client.get_forecast("London", days=0)
        
        with pytest.raises(ValueError, match="Days must be between 1 and 7"):
            weather_client.get_forecast("London", days=10)
    
    @pytest.mark.parametrize("city,expected_calls", [
        ("London", 1),
        ("Paris", 1),
        ("New York", 1),
    ])
    @patch('api_client.requests.Session.get')
    def test_multiple_cities(self, mock_get, weather_client, mock_weather_response, city, expected_calls):
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test
        weather = weather_client.get_current_weather(city)
        
        # Assertions
        assert weather.city == city
        assert mock_get.call_count == expected_calls

class TestPaymentProcessor:
    @pytest.fixture
    def payment_processor(self):
        return PaymentProcessor("test_secret_key", "sandbox")
    
    @pytest.fixture
    def mock_payment_intent_response(self):
        return {
            'id': 'pi_test123',
            'amount': 1000,
            'currency': 'usd',
            'status': 'succeeded',
            'client_secret': 'pi_test123_secret'
        }
    
    @patch('api_client.requests.Session.post')
    def test_create_payment_intent_success(self, mock_post, payment_processor, mock_payment_intent_response):
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = mock_payment_intent_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test
        result = payment_processor.create_payment_intent(1000, "USD")
        
        # Assertions
        assert result['id'] == 'pi_test123'
        assert result['amount'] == 1000
        assert result['status'] == 'succeeded'
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "payment_intents" in call_args[0][0]
        assert call_args[1]['json']['amount'] == 1000
        assert call_args[1]['json']['currency'] == 'usd'
    
    def test_create_payment_intent_negative_amount(self, payment_processor):
        with pytest.raises(ValueError, match="Amount must be positive"):
            payment_processor.create_payment_intent(-100)
        
        with pytest.raises(ValueError, match="Amount must be


# api_client.py - API client for external services
import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import time

@dataclass
class WeatherData:
    temperature: float
    humidity: int
    description: str
    city: str
    timestamp: datetime

class WeatherAPIClient:
    def __init__(self, api_key: str, base_url: str = "https://api.weather.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def get_current_weather(self, city: str) -> WeatherData:
        """Get current weather for a city"""
        url = f"{self.base_url}/current"
        params = {
            'q': city,
            'units': 'metric'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return WeatherData(
                temperature=data['main']['temp'],
                humidity=data['main']['humidity'],
                description=data['weather'][0]['description'],
                city=city,
                timestamp=datetime.now()
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timed out for city: {city}")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                raise ValueError(f"City not found: {city}")
            elif response.status_code == 401:
                raise ValueError("Invalid API key")
            elif response.status_code == 429:
                raise ValueError("Rate limit exceeded")
            else:
                raise ValueError(f"HTTP error: {e}")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Unable to connect to weather service")
    
    def get_forecast(self, city: str, days: int = 5) -> List[WeatherData]:
        """Get weather forecast for multiple days"""
        if days < 1 or days > 7:
            raise ValueError("Days must be between 1 and 7")
        
        url = f"{self.base_url}/forecast"
        params = {
            'q': city,
            'cnt': days,
            'units': 'metric'
        }
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        forecasts = []
        
        for item in data['list']:
            forecast = WeatherData(
                temperature=item['main']['temp'],
                humidity=item['main']['humidity'],
                description=item['weather'][0]['description'],
                city=city,
                timestamp=datetime.fromtimestamp(item['dt'])
            )
            forecasts.append(forecast)
        
        return forecasts
    
    def search_cities(self, query: str) -> List[Dict[str, str]]:
        """Search for cities matching the query"""
        url = f"{self.base_url}/search"
        params = {'q': query}
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        return response.json()['cities']

class PaymentProcessor:
    def __init__(self, api_key: str, environment: str = "sandbox"):
        self.api_key = api_key
        self.environment = environment
        self.base_url = f"https://api.{environment}.payment.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def create_payment_intent(self, amount: int, currency: str = "USD") -> Dict:
        """Create a payment intent"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if currency not in ["USD", "EUR", "GBP"]:
            raise ValueError(f"Unsupported currency: {currency}")
        
        url = f"{self.base_url}/payment_intents"
        data = {
            'amount': amount,
            'currency': currency.lower(),
            'confirm': True
        }
        
        response = self.session.post(url, json=data, timeout=15)
        response.raise_for_status()
        
        return response.json()
    
    def capture_payment(self, payment_intent_id: str) -> Dict:
        """Capture a payment"""
        url = f"{self.base_url}/payment_intents/{payment_intent_id}/capture"
        
        response = self.session.post(url, timeout=15)
        response.raise_for_status()
        
        return response.json()
    
    def refund_payment(self, payment_intent_id: str, amount: Optional[int] = None) -> Dict:
        """Refund a payment"""
        url = f"{self.base_url}/refunds"
        data = {'payment_intent': payment_intent_id}
        
        if amount:
            data['amount'] = amount
        
        response = self.session.post(url, json=data, timeout=15)
        response.raise_for_status()
        
        return response.json()

class RateLimiter:
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def acquire(self):
        now = time.time()
        # Remove calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
                return self.acquire()
        
        self.calls.append(now)

# test_api_client.py - Comprehensive API testing
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from datetime import datetime
from api_client import WeatherAPIClient, PaymentProcessor, WeatherData, RateLimiter

class TestWeatherAPIClient:
    @pytest.fixture
    def weather_client(self):
        return WeatherAPIClient("test_api_key")
    
    @pytest.fixture
    def mock_weather_response(self):
        return {
            'main': {
                'temp': 25.5,
                'humidity': 60
            },
            'weather': [
                {
                    'description': 'clear sky'
                }
            ]
        }
    
    @pytest.fixture
    def mock_forecast_response(self):
        return {
            'list': [
                {
                    'dt': 1609459200,  # timestamp
                    'main': {'temp': 20.0, 'humidity': 50},
                    'weather': [{'description': 'cloudy'}]
                },
                {
                    'dt': 1609545600,  # timestamp
                    'main': {'temp': 22.5, 'humidity': 55},
                    'weather': [{'description': 'sunny'}]
                }
            ]
        }
    
    @patch('api_client.requests.Session.get')
    def test_get_current_weather_success(self, mock_get, weather_client, mock_weather_response):
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test
        weather = weather_client.get_current_weather("London")
        
        # Assertions
        assert isinstance(weather, WeatherData)
        assert weather.temperature == 25.5
        assert weather.humidity == 60
        assert weather.description == "clear sky"
        assert weather.city == "London"
        assert isinstance(weather.timestamp, datetime)
        
        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "current" in call_args[0][0]  # URL contains 'current'
        assert call_args[1]['params']['q'] == "London"
    
    @patch('api_client.requests.Session.get')
    def test_get_current_weather_city_not_found(self, mock_get, weather_client):
        # Setup mock for 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_response
        
        # Test and assert
        with pytest.raises(ValueError, match="City not found"):
            weather_client.get_current_weather("NonexistentCity")
    
    @patch('api_client.requests.Session.get')
    def test_get_current_weather_invalid_api_key(self, mock_get, weather_client):
        # Setup mock for 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_response
        
        with pytest.raises(ValueError, match="Invalid API key"):
            weather_client.get_current_weather("London")
    
    @patch('api_client.requests.Session.get')
    def test_get_current_weather_rate_limit(self, mock_get, weather_client):
        # Setup mock for 429 response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_response
        
        with pytest.raises(ValueError, match="Rate limit exceeded"):
            weather_client.get_current_weather("London")
    
    @patch('api_client.requests.Session.get')
    def test_get_current_weather_timeout(self, mock_get, weather_client):
        # Setup mock for timeout
        mock_get.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(TimeoutError, match="Request timed out"):
            weather_client.get_current_weather("London")
    
    @patch('api_client.requests.Session.get')
    def test_get_current_weather_connection_error(self, mock_get, weather_client):
        # Setup mock for connection error
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(ConnectionError, match="Unable to connect"):
            weather_client.get_current_weather("London")
    
    @patch('api_client.requests.Session.get')
    def test_get_forecast_success(self, mock_get, weather_client, mock_forecast_response):
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = mock_forecast_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test
        forecasts = weather_client.get_forecast("London", days=2)
        
        # Assertions
        assert len(forecasts) == 2
        assert all(isinstance(f, WeatherData) for f in forecasts)
        assert forecasts[0].temperature == 20.0
        assert forecasts[1].temperature == 22.5
        assert forecasts[0].description == "cloudy"
        assert forecasts[1].description == "sunny"
    
    def test_get_forecast_invalid_days(self, weather_client):
        with pytest.raises(ValueError, match="Days must be between 1 and 7"):
            weather_client.get_forecast("London", days=0)
        
        with pytest.raises(ValueError, match="Days must be between 1 and 7"):
            weather_client.get_forecast("London", days=10)
    
    @pytest.mark.parametrize("city,expected_calls", [
        ("London", 1),
        ("Paris", 1),
        ("New York", 1),
    ])
    @patch('api_client.requests.Session.get')
    def test_multiple_cities(self, mock_get, weather_client, mock_weather_response, city, expected_calls):
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test
        weather = weather_client.get_current_weather(city)
        
        # Assertions
        assert weather.city == city
        assert mock_get.call_count == expected_calls

class TestPaymentProcessor:
    @pytest.fixture
    def payment_processor(self):
        return PaymentProcessor("test_secret_key", "sandbox")
    
    @pytest.fixture
    def mock_payment_intent_response(self):
        return {
            'id': 'pi_test123',
            'amount': 1000,
            'currency': 'usd',
            'status': 'succeeded',
            'client_secret': 'pi_test123_secret'
        }
    
    @patch('api_client.requests.Session.post')
    def test_create_payment_intent_success(self, mock_post, payment_processor, mock_payment_intent_response):
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = mock_payment_intent_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test
        result = payment_processor.create_payment_intent(1000, "USD")
        
        # Assertions
        assert result['id'] == 'pi_test123'
        assert result['amount'] == 1000
        assert result['status'] == 'succeeded'
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "payment_intents" in call_args[0][0]
        assert call_args[1]['json']['amount'] == 1000
        assert call_args[1]['json']['currency'] == 'usd'
    
    def test_create_payment_intent_negative_amount(self, payment_processor):
        with pytest.raises(ValueError, match="Amount must be positive"):
            payment_processor.create_payment_intent(-100)
        
        with pytest.raises(ValueError, match="Amount must be positive"):
            payment_processor.create_payment_intent(0)
    
    def test_create_payment_intent_invalid_currency(self, payment_processor):
        with pytest.raises(ValueError, match="Unsupported currency"):
            payment_processor.create_payment_intent(1000, "JPY")
    
    @pytest.mark.parametrize("amount,currency,expected_currency", [
        (1000, "USD", "usd"),
        (2000, "EUR", "eur"),
        (1500, "GBP", "gbp"),
    ])
    @patch('api_client.requests.Session.post')
    def test_create_payment_intent_currencies(self, mock_post, payment_processor, amount, currency, expected_currency):
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {'id': 'pi_test', 'amount': amount, 'currency': expected_currency}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test
        result = payment_processor.create_payment_intent(amount, currency)
        
        # Verify currency is converted to lowercase
        call_args = mock_post.call_args
        assert call_args[1]['json']['currency'] == expected_currency
    
    @patch('api_client.requests.Session.post')
    def test_capture_payment_success(self, mock_post, payment_processor):
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {'id': 'pi_test123', 'status': 'succeeded'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test
        result = payment_processor.capture_payment('pi_test123')
        
        # Assertions
        assert result['status'] == 'succeeded'
        mock_post.assert_called_once()
        assert "capture" in mock_post.call_args[0][0]
    
    @patch('api_client.requests.Session.post')
    def test_refund_payment_full(self, mock_post, payment_processor):
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {'id': 're_test123', 'status': 'succeeded', 'amount': 1000}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test full refund
        result = payment_processor.refund_payment('pi_test123')
        
        # Assertions
        assert result['status'] == 'succeeded'
        call_args = mock_post.call_args
        assert call_args[1]['json']['payment_intent'] == 'pi_test123'
        assert 'amount' not in call_args[1]['json']  # Full refund, no amount specified
    
    @patch('api_client.requests.Session.post')
    def test_refund_payment_partial(self, mock_post, payment_processor):
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {'id': 're_test123', 'status': 'succeeded', 'amount': 500}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test partial refund
        result = payment_processor.refund_payment('pi_test123', amount=500)
        
        # Assertions
        assert result['amount'] == 500
        call_args = mock_post.call_args
        assert call_args[1]['json']['amount'] == 500

class TestRateLimiter:
    def test_rate_limiter_allows_within_limit(self):
        limiter = RateLimiter(max_calls=3, time_window=1)
        
        # Should allow 3 calls without blocking
        start_time = time.time()
        limiter.acquire()
        limiter.acquire()
        limiter.acquire()
        end_time = time.time()
        
        # Should complete quickly (no rate limiting)
        assert end_time - start_time < 0.1
    
    @patch('time.sleep')
    def test_rate_limiter_blocks_when_exceeded(self, mock_sleep):
        limiter = RateLimiter(max_calls=2, time_window=1)
        
        # Use up the limit
        limiter.acquire()
        limiter.acquire()
        
        # Mock time to simulate rate limit window
        with patch('time.time', side_effect=[0, 0, 0, 0.5, 1.1]):
            limiter.acquire()  # This should trigger sleep
        
        mock_sleep.assert_called_once()
        assert mock_sleep.call_args[0][0] > 0  # Should sleep for some positive duration

# Integration tests
class TestAPIIntegration:
    """Integration tests that test multiple components working together"""
    
    @patch('api_client.requests.Session.get')
    def test_weather_client_with_rate_limiting(self, mock_get):
        """Test weather client with rate limiting"""
        # Setup
        weather_client = WeatherAPIClient("test_key")
        rate_limiter = RateLimiter(max_calls=2, time_window=1)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'main': {'temp': 20, 'humidity': 50},
            'weather': [{'description': 'clear'}]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test multiple API calls with rate limiting
        cities = ["London", "Paris", "Berlin"]
        results = []
        
        for city in cities:
            rate_limiter.acquire()
            weather = weather_client.get_current_weather(city)
            results.append(weather)
        
        assert len(results) == 3
        assert all(isinstance(w, WeatherData) for w in results)
        assert mock_get.call_count == 3
    
    @patch('api_client.requests.Session.post')
    def test_payment_workflow_integration(self, mock_post):
        """Test complete payment workflow"""
        processor = PaymentProcessor("test_key")
        
        # Mock responses for different endpoints
        def mock_post_side_effect(url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            
            if "payment_intents" in url and "capture" not in url:
                # Create payment intent
                mock_response.json.return_value = {
                    'id': 'pi_test123',
                    'status': 'requires_capture',
                    'amount': 1000
                }
            elif "capture" in url:
                # Capture payment
                mock_response.json.return_value = {
                    'id': 'pi_test123',
                    'status': 'succeeded',
                    'amount': 1000
                }
            elif "refunds" in url:
                # Refund payment
                mock_response.json.return_value = {
                    'id': 're_test123',
                    'status': 'succeeded',
                    'amount': 500
                }
            
            return mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        # Step 1: Create payment intent
        payment_intent = processor.create_payment_intent(1000, "USD")
        assert payment_intent['status'] == 'requires_capture'
        
        # Step 2: Capture payment
        captured = processor.capture_payment(payment_intent['id'])
        assert captured['status'] == 'succeeded'
        
        # Step 3: Partial refund
        refund = processor.refund_payment(payment_intent['id'], amount=500)
        assert refund['amount'] == 500
        
        # Verify all API calls were made
        assert mock_post.call_count == 3
    
    @patch('api_client.requests.Session.get')
    @patch('api_client.requests.Session.post')
    def test_error_handling_across_services(self, mock_post, mock_get):
        """Test error handling across different services"""
        weather_client = WeatherAPIClient("invalid_key")
        payment_processor = PaymentProcessor("invalid_key")
        
        # Setup weather API to return 401
        weather_mock = Mock()
        weather_mock.status_code = 401
        weather_mock.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = weather_mock
        
        # Setup payment API to return 401
        payment_mock = Mock()
        payment_mock.status_code = 401
        payment_mock.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_post.return_value = payment_mock
        
        # Both should raise authentication errors
        with pytest.raises(ValueError, match="Invalid API key"):
            weather_client.get_current_weather("London")
        
        with pytest.raises(requests.exceptions.HTTPError):
            payment_processor.create_payment_intent(1000)

# Performance and load testing
class TestAPIPerformance:
    @patch('api_client.requests.Session.get')
    def test_weather_api_performance(self, mock_get):
        """Test API performance with multiple concurrent-like requests"""
        weather_client = WeatherAPIClient("test_key")
        
        # Setup fast mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'main': {'temp': 20, 'humidity': 50},
            'weather': [{'description': 'clear'}]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Time multiple API calls
        cities = ["London", "Paris", "Berlin", "Madrid", "Rome"] * 10  # 50 cities
        
        start_time = time.time()
        results = []
        for city in cities:
            weather = weather_client.get_current_weather(city)
            results.append(weather)
        end_time = time.time()
        
        # Performance assertions
        total_time = end_time - start_time
        assert len(results) == 50
        assert total_time < 1.0  # Should complete quickly with mocked responses
        assert mock_get.call_count == 50
    
    def test_rate_limiter_performance(self):
        """Test rate limiter doesn't add significant overhead"""
        limiter = RateLimiter(max_calls=100, time_window=1)
        
        # Time many acquisitions within limit
        start_time = time.time()
        for _ in range(50):  # Well within limit
            limiter.acquire()
        end_time = time.time()
        
        # Should complete very quickly
        assert end_time - start_time < 0.1

# Fixtures for complex test scenarios
@pytest.fixture
def api_responses():
    """Fixture providing various API response scenarios"""
    return {
        'weather_success': {
            'main': {'temp': 25.0, 'humidity': 60},
            'weather': [{'description': 'sunny'}]
        },
        'weather_error_404': {
            'error': {'code': 404, 'message': 'City not found'}
        },
        'payment_success': {
            'id': 'pi_test123',
            'amount': 1000,
            'currency': 'usd',
            'status': 'succeeded'
        },
        'payment_error_insufficient_funds': {
            'error': {'code': 'insufficient_funds', 'message': 'Your card has insufficient funds'}
        }
    }

@pytest.fixture
def mock_external_services(api_responses):
    """Fixture that mocks all external services"""
    with patch('api_client.requests.Session') as mock_session_class:
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        def get_side_effect(url, **kwargs):
            mock_response = Mock()
            if 'current' in url:
                mock_response.json.return_value = api_responses['weather_success']
                mock_response.raise_for_status.return_value = None
            return mock_response
        
        def post_side_effect(url, **kwargs):
            mock_response = Mock()
            if 'payment_intents' in url:
                mock_response.json.return_value = api_responses['payment_success']
                mock_response.raise_for_status.return_value = None
            return mock_response
        
        mock_session.get.side_effect = get_side_effect
        mock_session.post.side_effect = post_side_effect
        
        yield mock_session

# ecommerce.py - E-commerce platform models
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum
import uuid
from dataclasses import dataclass, field

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

@dataclass
class Product:
    id: str
    name: str
    price: Decimal
    stock_quantity: int
    category: str
    weight: float = 0.0  # in kg
    dimensions: Dict[str, float] = field(default_factory=dict)  # L x W x H
    active: bool = True

@dataclass
class CartItem:
    product: Product
    quantity: int
    
    @property
    def total_price(self) -> Decimal:
        return self.product.price * self.quantity
    
    @property
    def total_weight(self) -> float:
        return self.product.weight * self.quantity

class ShoppingCart:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.items: List[CartItem] = []
        self.discount_code: Optional[str] = None
        self.discount_percentage: Decimal = Decimal('0')
    
    def add_item(self, product: Product, quantity: int = 1) -> bool:
        if not product.active:
            raise ValueError("Product is not available")
        
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if product.stock_quantity < quantity:
            raise ValueError("Insufficient stock")
        
        # Check if item already exists
        for item in self.items:
            if item.product.id == product.id:
                if product.stock_quantity < item.quantity + quantity:
                    raise ValueError("Insufficient stock")
                item.quantity += quantity
                return True
        
        # Add new item
        self.items.append(CartItem(product, quantity))
        return True
    
    def remove_item(self, product_id: str) -> bool:
        for i, item in enumerate(self.items):
            if item.product.id == product_id:
                del self.items[i]
                return True
        return False
    
    def update_quantity(self, product_id: str, quantity: int) -> bool:
        if quantity <= 0:
            return self.remove_item(product_id)
        
        for item in self.items:
            if item.product.id == product_id:
                if item.product.stock_quantity < quantity:
                    raise ValueError("Insufficient stock")
                item.quantity = quantity
                return True
        return False
    
    def apply_discount(self, code: str, percentage: Decimal) -> bool:
        if percentage < 0 or percentage > 100:
            raise ValueError("Invalid discount percentage")
        
        self.discount_code = code
        self.discount_percentage = percentage
        return True
    
    def get_subtotal(self) -> Decimal:
        return sum(item.total_price for item in self.items)
    
    def get_discount_amount(self) -> Decimal:
        subtotal = self.get_subtotal()
        return subtotal * (self.discount_percentage / 100)
    
    def get_total(self) -> Decimal:
        subtotal = self.get_subtotal()
        discount = self.get_discount_amount()
        return subtotal - discount
    
    def get_total_weight(self) -> float:
        return sum(item.total_weight for item in self.items)
    
    def clear(self):
        self.items = []
        self.discount_code = None
        self.discount_percentage = Decimal('0')

class ShippingCalculator:
    def __init__(self):
        self.base_rate = Decimal('5.99')
        self.weight_rate = Decimal('0.50')  # per kg
        self.free_shipping_threshold = Decimal('50.00')
    
    def calculate_shipping(self, total_amount: Decimal, total_weight: float, shipping_zone: str = "domestic") -> Decimal:
        if total_amount >= self.free_shipping_threshold:
            return Decimal('0')
        
        base_cost = self.base_rate
        weight_cost = Decimal(str(total_weight)) * self.weight_rate
        
        zone_multipliers = {
            "domestic": Decimal('1.0'),
            "international": Decimal('2.5'),
            "express": Decimal('3.0')
        }
        
        multiplier = zone_multipliers.get(shipping_zone, Decimal('1.0'))
        return (base_cost + weight_cost) * multiplier

class Order:
    def __init__(self, user_id: str, cart: ShoppingCart):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.items = cart.items.copy()
        self.subtotal = cart.get_subtotal()
        self.discount_amount = cart.get_discount_amount()
        self.discount_code = cart.discount_code
        self.total_weight = cart.get_total_weight()
        self.shipping_cost = Decimal('0')
        self.total = cart.get_total()
        self.status = OrderStatus.PENDING
        self.payment_status = PaymentStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.shipping_address = None
        self.tracking_number = None
    
    def set_shipping(self, shipping_cost: Decimal, address: Dict[str, str]):
        self.shipping_cost = shipping_cost
        self.shipping_address = address
        self.total = self.subtotal - self.discount_amount + self.shipping_cost
        self.updated_at = datetime.now()
    
    def confirm_payment(self) -> bool:
        if self.payment_status == PaymentStatus.COMPLETED:
            return True
        
        # Simulate payment processing
        self.payment_status = PaymentStatus.COMPLETED
        self.status = OrderStatus.CONFIRMED
        self.updated_at = datetime.now()
        
        # Reduce stock quantities
        for item in self.items:
            item.product.stock_quantity -= item.quantity
        
        return True
    
    def ship(self, tracking_number: str) -> bool:
        if self.status != OrderStatus.CONFIRMED:
            raise ValueError("Order must be confirmed before shipping")
        
        self.status = OrderStatus.SHIPPED
        self.tracking_number = tracking_number
        self.updated_at = datetime.now()
        return True
    
    def cancel(self) -> bool:
        if self.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise ValueError("Cannot cancel shipped or delivered orders")
        
        # Restore stock if payment was completed
        if self.payment_status == PaymentStatus.COMPLETED:
            for item in self.items:
                item.product.stock_quantity += item.quantity
        
        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.now()
        return True

class InventoryManager:
    def __init__(self):
        self.products: Dict[str, Product] = {}
        self.low_stock_threshold = 10
    
    def add_product(self, product: Product) -> bool:
        if product.id in self.products:
            raise ValueError("Product already exists")
        
        self.products[product.id] = product
        return True
    
    def update_stock(self, product_id: str, quantity: int) -> bool:
        if product_id not in self.products:
            raise ValueError("Product not found")
        
        product = self.products[product_id]
        if product.stock_quantity + quantity < 0:
            raise ValueError("Cannot reduce stock below zero")
        
        product.stock_quantity += quantity
        return True
    
    def get_low_stock_products(self) -> List[Product]:
        return [product for product in self.products.values() 
                if product.stock_quantity <= self.low_stock_threshold]
    
    def check_availability(self, product_id: str, quantity: int) -> bool:
        if product_id not in self.products:
            return False
        
        product = self.products[product_id]
        return product.active and product.stock_quantity >= quantity

# test_ecommerce.py - Comprehensive e-commerce testing
import pytest
from decimal import Decimal
from datetime import datetime
from ecommerce import (
    Product, CartItem, ShoppingCart, ShippingCalculator, 
    Order, InventoryManager, OrderStatus, PaymentStatus
)

@pytest.fixture
def sample_products():
    """Create sample products for testing"""
    return [
        Product("1", "Laptop", Decimal('999.99'), 5, "Electronics", 2.5),
        Product("2", "Mouse", Decimal('29.99'), 50, "Electronics", 0.2),
        Product("3", "Keyboard", Decimal('79.99'), 20, "Electronics", 0.8),
        Product("4", "Monitor", Decimal('299.99'), 10, "Electronics", 5.0),
        Product("5", "Book", Decimal('19.99'), 100, "Books", 0.3, active=False),
    ]

@pytest.fixture
def shopping_cart(sample_products):
    """Create a shopping cart with some items"""
    cart = ShoppingCart("user123")
    cart.add_item(sample_products[0], 1)  # Laptop
    cart.add_item(sample_products[1], 2)  # 2 Mice
    return cart

@pytest.fixture
def inventory_manager(sample_products):
    """Create inventory manager with sample products"""
    manager = InventoryManager()
    for product in sample_products:
        manager.add_product(product)
    return manager

class TestProduct:
    def test_product_creation(self, sample_products):
        laptop = sample_products[0]
        assert laptop.id == "1"
        assert laptop.name == "Laptop"
        assert laptop.price == Decimal('999.99')
        assert laptop.stock_quantity == 5
        assert laptop.active is True

class TestCartItem:
    def test_cart_item_total_price(self, sample_products):
        item = CartItem(sample_products[1], 3)  # 3 mice at $29.99 each
        expected = Decimal('29.99') * 3
        assert item.total_price == expected
    
    def test_cart_item_total_weight(self, sample_products):
        item = CartItem(sample_products[0], 2)  # 2 laptops at 2.5kg each
        assert item.total_weight == 5.0

class TestShoppingCart:
    def test_add_item_new_product(self, sample_products):
        cart = ShoppingCart("user123")
        result = cart.add_item(sample_products[0], 2)
        
        assert result is True
        assert len(cart.items) == 1
        assert cart.items[0].product.id == "1"
        assert cart.items[0].quantity == 2
    
    def test_add_item_existing_product(self, sample_products):
        cart = ShoppingCart("user123")
        cart.add_item(sample_products[0], 1)
        cart.add_item(sample_products[0], 2)  # Add more of the same product
        
        assert len(cart.items) == 1
        assert cart.items[0].quantity == 3
    
    def test_add_inactive_product(self, sample_products):
        cart = ShoppingCart("user123")
        
        with pytest.raises(ValueError, match="Product is not available"):
            cart.add_item(sample_products[4], 1)  # Inactive book
    
    def test_add_item_insufficient_stock(self, sample_products):
        cart = ShoppingCart("user123")
        
        with pytest.raises(ValueError, match="Insufficient stock"):
            cart.add_item(sample_products[0], 10)  # Only 5 laptops in stock
    
    def test_add_item_negative_quantity(self, sample_products):
        cart = ShoppingCart("user123")
        
        with pytest.raises(ValueError, match="Quantity must be positive"):
            cart.add_item(sample_products[0], -1)
    
    def test_remove_item_success(self, shopping_cart):
        result = shopping_cart.remove_item("1")  # Remove laptop
        
        assert result is True
        assert len(shopping_cart.items) == 1
        assert shopping_cart.items[0].product.id == "2"  # Only mouse remains
    
    def test_remove_item_not_found(self, shopping_cart):
        result = shopping_cart.remove_item("999")
        assert result is False
        assert len(shopping_cart.items) == 2  # Nothing removed
    
    def test_update_quantity(self, shopping_cart):
        result = shopping_cart.update_quantity("2", 5)  # Update mouse quantity
        
        assert result is True
        mouse_item = next(item for item in shopping_cart.items if item.product.id == "2")
        assert mouse_item.quantity == 5
    
    def test_update_quantity_to_zero_removes_item(self, shopping_cart):
        result = shopping_cart.update_quantity("1", 0)
        
        assert result is True
        assert len(shopping_cart.items) == 1
        assert shopping_cart.items[0].product.id == "2"
    
    def test_apply_discount_valid(self, shopping_cart):
        result = shopping_cart.apply_discount("SAVE20", Decimal('20'))
        
        assert result is True
        assert shopping_cart.discount_code == "SAVE20"
        assert shopping_cart.discount_percentage == Decimal('20')
    
    def test_apply_discount_invalid_percentage(self, shopping_cart):
        with pytest.raises(ValueError, match="Invalid discount percentage"):
            shopping_cart.apply_discount("INVALID", Decimal('150'))
        
        with pytest.raises(ValueError, match="Invalid discount percentage"):
            shopping_cart.apply_discount("INVALID", Decimal('-10'))
    
    def test_get_subtotal(self, shopping_cart):
        # Laptop ($999.99) + 2 Mice ($29.99 * 2)
        expected = Decimal('999.99') + (Decimal('29.99') * 2)
        assert shopping_cart.get_subtotal() == expected
    
    def test_get_total_with_discount(self, shopping_cart):
        shopping_cart.apply_discount("SAVE10", Decimal('10'))
        
        subtotal = shopping_cart.get_subtotal()
        discount = subtotal * Decimal('0.1')  # 10%
        expected_total = subtotal - discount
        
        assert shopping_cart.get_total() == expected_total
    
    def test_get_total_weight(self, shopping_cart):
        # Laptop (2.5kg) + 2 Mice (0.2kg * 2)
        expected = 2.5 + (0.2 * 2)
        assert shopping_cart.get_total_weight() == expected
    
    @pytest.mark.parametrize("product_index,quantity,expected_items", [
        (0, 1, 2),  # Add laptop
        (1, 3, 2),  # Add more mice (existing product)
        (2, 2, 3),  # Add keyboard (new product)
    ])
    def test_add_various_products(self, sample_products, product_index, quantity, expected_items):
        cart = ShoppingCart("user123")
        cart.add_item(sample_products[0], 1)  # Start with laptop
        cart.add_item(sample_products[1], 1)  # Add mouse
        
        cart.add_item(sample_products[product_index], quantity)
        assert len(cart.items) == expected_items

class TestShippingCalculator:
    def test_free_shipping_threshold(self):
        calc = ShippingCalculator()
        
        # Order above threshold
        shipping = calc.calculate_shipping(Decimal('60.00'), 2.0)
        assert shipping == Decimal('0')
        
        # Order at threshold
        shipping = calc.calculate_shipping(Decimal('50.00'), 2.0)
        assert shipping == Decimal('0')
    
    def test_domestic_shipping(self):
        calc = ShippingCalculator()
        
        # $5.99 base + (2.0kg * $0.50)
        expected = Decimal('5.99') + (Decimal('2.0') * Decimal('0.50'))
        shipping = calc.calculate_shipping(Decimal('30.00'), 2.0, "domestic")
        assert shipping == expected
    
    def test_international_shipping(self):
        calc = ShippingCalculator()
        
        base_shipping = Decimal('5.99') + (Decimal('1.0') * Decimal('0.50'))
        expected = base_shipping * Decimal('2.5')  # International multiplier
        
        shipping = calc.calculate_shipping(Decimal('30.00'), 1.0, "international")
        assert shipping == expected
    
    def test_express_shipping(self):
        calc = ShippingCalculator()
        
        base_shipping = Decimal('5.99') + (Decimal('1.0') * Decimal('0.50'))
        expected = base_shipping * Decimal('3.0')  # Express multiplier
        
        shipping = calc.calculate_shipping(Decimal('30.00'), 1.0, "express")
        assert shipping == expected
    
    @pytest.mark.parametrize("amount,weight,zone,expected_free", [
        (Decimal('60.00'), 1.0, "domestic", True),
        (Decimal('100.00'), 10.0, "international", True),
        (Decimal('40.00'), 1.0, "domestic", False),
    ])
    def test_various_shipping_scenarios(self, amount, weight, zone, expected_free):
        calc = ShippingCalculator()
        shipping = calc.calculate_shipping(amount, weight, zone)
        
        if expected_free:
            assert shipping == Decimal('0')
        else:
            assert shipping > Decimal('0')

class TestOrder:
    def test_order_creation(self, shopping_cart):
        order = Order("user123", shopping_cart)
        
        assert order.user_id == "user123"
        assert len(order.items) == 2
        assert order.status == OrderStatus.PENDING
        assert order.payment_status == PaymentStatus.PENDING
        assert order.subtotal == shopping_cart.get_subtotal()
        assert order.total == shopping_cart.get_total()
    
    def test_set_shipping(self, shopping_cart):
        order = Order("user123", shopping_cart)
        original_total = order.total
        
        shipping_cost = Decimal('10.00')
        address = {"street": "123 Main St", "city": "Anytown", "zip": "12345"}
        
        order.set_shipping(shipping_cost, address)
        
        assert order.shipping_cost == shipping_cost
        assert order.shipping_address == address
        assert order.total == original_total + shipping_cost
    
    def test_confirm_payment_success(self, shopping_cart):
        order = Order("user123", shopping_cart)
        original_laptop_stock = shopping_cart.items[0].product.stock_quantity
        original_mouse_stock = shopping_cart.items[1].product.stock_quantity
        
        result = order.confirm_payment()
        
        assert result is True
        assert order.payment_status == PaymentStatus.COMPLETED
        assert order.status == OrderStatus.CONFIRMED
        
        # Check stock was reduced
        assert shopping_cart.items[0].product.stock_quantity == original_laptop_stock - 1
        assert shopping_cart.items[1].product.stock_quantity == original_mouse_stock - 2
    
    def test_ship_order_success(self, shopping_cart):
        order = Order("user123", shopping_cart)
        order.confirm_payment()
        
        result = order.ship("TRACK123456")
        
        assert result is True
        assert order.status == OrderStatus.SHIPPED
        assert order.tracking_number == "TRACK123456"
    
    def test_ship_order_not_confirmed(self, shopping_cart):
        order = Order("user123", shopping_cart)
        
        with pytest.raises(ValueError, match="Order must be confirmed before shipping"):
            order.ship("TRACK123456")
    
    def test_cancel_order_pending(self, shopping_cart):
        order = Order("user123", shopping_cart)
        
        result = order.cancel()
        
        assert result is True
        assert order.status == OrderStatus.CANCELLED
    
    def test_cancel_order_confirmed_restores_stock(self, shopping_cart):
        order = Order("user123", shopping_cart)
        order.confirm_payment()
        
        # Stock should be reduced after payment
        laptop_stock_after_payment = shopping_cart.items[0].product.stock_quantity
        mouse_stock_after_payment = shopping_cart.items[1].product.stock_quantity
        
        order.cancel()
        
        # Stock should be restored after cancellation
        assert shopping_cart.items[0].product.stock_quantity == laptop_stock_after_payment + 1
        assert shopping_cart.items[1].product.stock_quantity == mouse_stock_after_payment + 2
        assert order.status == OrderStatus.CANCELLED
    
    def test_cancel_shipped_order_fails(self, shopping_cart):
        order = Order("user123", shopping_cart)
        order.confirm_payment()
        order.ship("TRACK123456")
        
        with pytest.raises(ValueError, match="Cannot cancel shipped or delivered orders"):
            order.cancel()

class TestInventoryManager:
    def test_add_product_success(self):
        manager = InventoryManager()
        product = Product("1", "Test Product", Decimal('10.00'), 5, "Test")
        
        result = manager.add_product(product)
        
        assert result is True
        assert "1" in manager.products
        assert manager.products["1"] == product
    
    def test_add_duplicate_product_fails(self, inventory_manager, sample_products):
        with pytest.raises(ValueError, match="Product already exists"):
            inventory_manager.add_product(sample_products[0])  # Laptop already exists
    
    def test_update_stock_increase(self, inventory_manager):
        original_stock = inventory_manager.products["1"].stock_quantity
        
        result = inventory_manager.update_stock("1", 10)
        
        assert result is True
        assert inventory_manager.products["1"].stock_quantity == original_stock + 10
    
    def test_update_stock_decrease(self, inventory_manager):
        original_stock = inventory_manager.products["1"].stock_quantity
        
        result = inventory_manager.update_stock("1", -2)
        
        assert result is True
        assert inventory_manager.products["1"].stock_quantity == original_stock - 2
    
    def test_update_stock_below_zero_fails(self, inventory_manager):
        with pytest.raises(ValueError, match="Cannot reduce stock below zero"):
            inventory_manager.update_stock("1", -100)  # Reduce by more than available
    
    def test_update_stock_nonexistent_product(self, inventory_manager):
        with pytest.raises(ValueError, match="Product not found"):
            inventory_manager.update_stock("999", 10)
    
    def test_get_low_stock_products(self, inventory_manager):
        # Reduce stock to trigger low stock alert
        inventory_manager.update_stock("1", -1)  # Laptop: 5 -> 4 (below threshold of 10)
        
        low_stock = inventory_manager.get_low_stock_products()
        
        assert len(low_stock) > 0
        laptop = next(p for p in low_stock if p.id == "1")
        assert laptop.stock_quantity <= inventory_manager.low_stock_threshold
    
    def test_check_availability_sufficient_stock(self, inventory_manager):
        result = inventory_manager.check_availability("1", 3)  # 3 out of 5 laptops
        assert result is True
    
    def test_check_availability_insufficient_stock(self, inventory_manager):
        result = inventory_manager.check_availability("1", 10)  # 10 out of 5 laptops
        assert result is False
    
    def test_check_availability_inactive_product(self, inventory_manager):
        result = inventory_manager.check_availability("5", 1)  # Inactive book
        assert result is False
    
    def test_check_availability_nonexistent_product(self, inventory_manager):
        result = inventory_manager.check_availability("999", 1)
        assert result is False

# Integration tests for complete e-commerce workflows
class TestEcommerceIntegration:
    def test_complete_purchase_workflow(self, sample_products, inventory_manager):
        """Test complete purchase workflow from cart to order"""
        # Step 1: Create cart and add items
        cart = ShoppingCart("user123")
        cart.add_item(sample_products[0], 1)  # Laptop
        cart.add_item(sample_products[1], 2)  # 2 Mice
        cart.apply_discount("SAVE10", Decimal('10'))
        
        # Step 2: Calculate shipping
        calc = ShippingCalculator()
        shipping_cost = calc.calculate_shipping(
            cart.get_total(), 
            cart.get_total_weight(), 
            "domestic"
        )
        
        # Step 3: Create order
        order = Order("user123", cart)
        order.set_shipping(shipping_cost, {
            "street": "123 Main St",
            "city": "Anytown", 
            "zip": "12345"
        })
        
        # Step 4: Process payment and ship
        original_laptop_stock = sample_products[0].stock_quantity
        original_mouse_stock = sample_products[1].stock_quantity
        
        order.confirm_payment()
        order.ship("TRACK123456789")
        
        # Verify final state
        assert order.status == OrderStatus.SHIPPED
        assert order.payment_status == PaymentStatus.COMPLETED
        assert order.tracking_number == "TRACK123456789"
        
        # Verify stock reduction
        assert sample_products[0].stock_quantity == original_laptop_stock - 1
        assert sample_products[1].stock_quantity == original_mouse_stock - 2
        
        # Verify totals
        expected_subtotal = Decimal('999.99') + (Decimal('29.99') * 2)
        expected_discount = expected_subtotal * Decimal('0.1')
        expected_total = expected_subtotal - expected_discount + shipping_cost
        
        assert order.subtotal == expected_subtotal
        assert order.discount_amount == expected_discount
        assert order.total == expected_total
    
    def test_out_of_stock_handling(self, sample_products):
        """Test handling when products go out of stock"""
        # Reduce laptop stock to 1
        sample_products[0].stock_quantity = 1
        
        cart1 = ShoppingCart("user1")
        cart2 = ShoppingCart("user2")
        
        # First user adds laptop successfully
        cart1.add_item(sample_products[0], 1)
        
        # First user creates and confirms order
        order1 = Order("user1", cart1)
        order1.confirm_payment()  # This should reduce stock to 0
        
        # Second user tries to add laptop (should fail)
        with pytest.raises(ValueError, match="Insufficient stock"):
            cart2.add_item(sample_products[0], 1)
        
        # Verify stock is actually 0
        assert sample_products[0].stock_quantity == 0
        
        # First user cancels order (stock should be restored)
        order1.cancel()
        assert sample_products[0].stock_quantity == 1
        
        # Now second user can add the laptop
        cart2.add_item(sample_products[0], 1)
        assert len(cart2.items) == 1
    
    @pytest.mark.parametrize("discount_code,discount_percent,shipping_zone,expected_free_shipping", [
        ("SAVE10", 10, "domestic", False),
        ("SAVE20", 20, "domestic", True),  # Should qualify for free shipping after discount
        ("SAVE50", 50, "international", True),
    ])
    def test_various_discount_shipping_combinations(
        self, sample_products, discount_code, discount_percent, shipping_zone, expected_free_shipping
    ):
        """Test various combinations of discounts and shipping"""
        cart = ShoppingCart("user123")
        
        # Add expensive item to test free shipping threshold
        cart.add_item(sample_products[0], 1)  # Laptop $999.99
        cart.apply_discount(discount_code, Decimal(str(discount_percent)))
        
        calc = ShippingCalculator()
        shipping_cost = calc.calculate_shipping(
            cart.get_total(),
            cart.get_total_weight(),
            shipping_zone
        )
        
        if expected_free_shipping:
            assert shipping_cost == Decimal('0')
        else:
            assert shipping_cost > Decimal('0')

# microservices.py - Microservices architecture components
import asyncio
import aiohttp
import json
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime, timedelta
import redis
from unittest.mock import Mock

# Message Queue and Event Bus
class EventType(Enum):
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    ORDER_PLACED = "order.placed"
    ORDER_CONFIRMED = "order.confirmed"
    PAYMENT_PROCESSED = "payment.processed"
    INVENTORY_UPDATED = "inventory.updated"

@dataclass
class Event:
    id: str
    type: EventType
    payload: Dict[str, Any]
    timestamp: datetime
    service_name: str
    correlation_id: Optional[str] = None

class MessageBus:
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or Mock()
        self.subscribers: Dict[EventType, List[callable]] = {}
        self.published_events: List[Event] = []  # For testing
    
    def subscribe(self, event_type: EventType, handler: callable):
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
    
    async def publish(self, event: Event):
        """Publish an event to all subscribers"""
        self.published_events.append(event)
        
        # Simulate Redis publish
        event_data = json.dumps({
            'id': event.id,
            'type': event.type.value,
            'payload': event.payload,
            'timestamp': event.timestamp.isoformat(),
            'service_name': event.service_name,
            'correlation_id': event.correlation_id
        })
        
        self.redis_client.publish(f"events:{event.type.value}", event_data)
        
        # Notify local subscribers
        if event.type in self.subscribers:
            for handler in self.subscribers[event.type]:
                try:
                    await handler(event)
                except Exception as e:
                    logging.error(f"Error handling event {event.id}: {e}")
    
    def get_published_events(self, event_type: EventType = None) -> List[Event]:
        """Get published events (for testing)"""
        if event_type:
            return [e for e in self.published_events if e.type == event_type]
        return self.published_events.copy()

# Circuit Breaker Pattern
class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        """Call function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and 
            time.time() - self.last_failure_time >= self.timeout
        )
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Service Discovery
class ServiceRegistry:
    def __init__(self):
        self.services: Dict[str, List[Dict[str, Any]]] = {}
    
    def register_service(self, name: str, host: str, port: int, health_check_url: str = None):
        """Register a service instance"""
        if name not in self.services:
            self.services[name] = []
        
        instance = {
            'id': str(uuid.uuid4()),
            'host': host,
            'port': port,
            'health_check_url': health_check_url,
            'last_seen': datetime.now(),
            'healthy': True
        }
        
        self.services[name].append(instance)
        return instance['id']
    
    def deregister_service(self, name: str, instance_id: str):
        """Deregister a service instance"""
        if name in self.services:
            self.services[name] = [
                instance for instance in self.services[name] 
                if instance['id'] != instance_id
            ]
    
    def get_service_instances(self, name: str) -> List[Dict[str, Any]]:
        """Get healthy instances of a service"""
        if name not in self.services:
            return []
        
        return [instance for instance in self.services[name] if instance['healthy']]
    
    def get_service_url(self, name: str) -> Optional[str]:
        """Get URL for a healthy service instance (load balancing)"""
        instances = self.get_service_instances(name)
        if not instances:
            return None
        
        # Simple round-robin (in real implementation, use more sophisticated methods)
        instance = instances[0]
        return f"http://{instance['host']}:{instance['port']}"

# API Gateway
class APIGateway:
    def __init__(self, service_registry: ServiceRegistry):
        self.service_registry = service_registry
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.rate_limiters: Dict[str, Dict] = {}
    
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]
    
    async def route_request(self, service_name: str, path: str, method: str = 'GET', **kwargs):
        """Route request to appropriate service with resilience patterns"""
        service_url = self.service_registry.get_service_url(service_name)
        if not service_url:
            raise Exception(f"No healthy instances of service {service_name}")
        
        full_url = f"{service_url}{path}"
        circuit_breaker = self.get_circuit_breaker(service_name)
        
        async def make_request():
            async with aiohttp.ClientSession() as session:
                async with session.request(method, full_url, **kwargs) as response:
                    if response.status >= 400:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status
                        )
                    return await response.json()
        
        return circuit_breaker.call(lambda: asyncio.run(make_request()))

# Microservices
class UserService:
    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus
        self.users: Dict[str, Dict] = {}
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        user = {
            'id': user_id,
            'email': user_data['email'],
            'name': user_data['name'],
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        self.users[user_id] = user
        
        # Publish event
        event = Event(
            id=str(uuid.uuid4()),
            type=EventType.USER_CREATED,
            payload={'user_id': user_id, 'email': user['email']},
            timestamp=datetime.now(),
            service_name='user-service'
        )
        
        await self.message_bus.publish(event)
        return user
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user"""
        if user_id not in self.users:
            raise ValueError("User not found")
        
        self.users[user_id].update(updates)
        self.users[user_id]['updated_at'] = datetime.now().isoformat()
        
        # Publish event
        event = Event(
            id=str(uuid.uuid4()),
            type=EventType.USER_UPDATED,
            payload={'user_id': user_id, 'updates': updates},
            timestamp=datetime.now(),
            service_name='user-service'
        )
        
        await self.message_bus.publish(event)
        return self.users[user_id]

class OrderService:
    def __init__(self, message_bus: MessageBus, user_service_url: str = None):
        self.message_bus = message_bus
        self.user_service_url = user_service_url
        self.orders: Dict[str, Dict] = {}
        
        # Subscribe to events
        self.message_bus.subscribe(EventType.PAYMENT_PROCESSED, self._handle_payment_processed)
    
    async def create_order(self, user_id: str, items: List[Dict]) -> Dict[str, Any]:
        """Create a new order"""
        # Verify user exists (simulate service call)
        if self.user_service_url:
            # In real implementation, make HTTP call to user service
            pass
        
        order_id = str(uuid.uuid4())
        order = {
            'id': order_id,
            'user_id': user_id,
            'items': items,
            'total': sum(item['price'] * item['quantity'] for item in items),
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        self.orders[order_id] = order
        
        # Publish event
        event = Event(
            id=str(uuid.uuid4()),
            type=EventType.ORDER_PLACED,
            payload={'order_id': order_id, 'user_id': user_id, 'total': order['total']},
            timestamp=datetime.now(),
            service_name='order-service'
        )
        
        await self.message_bus.publish(event)
        return order
    
    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        return self.orders.get(order_id)
    
    async def _handle_payment_processed(self, event: Event):
        """Handle payment processed event"""
        order_id = event.payload.get('order_id')
        if order_id and order_id in self.orders:
            self.orders[order_id]['status'] = 'confirmed'
            
            # Publish order confirmed event
            confirmed_event = Event(
                id=str(uuid.uuid4()),
                type=EventType.ORDER_CONFIRMED,
                payload={'order_id': order_id},
                timestamp=datetime.now(),
                service_name='order-service',
                correlation_id=event.correlation_id
            )
            
            await self.message_bus.publish(confirmed_event)

class PaymentService:
    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus
        self.payments: Dict[str, Dict] = {}
        
        # Subscribe to events
        self.message_bus.subscribe(EventType.ORDER_PLACED, self._handle_order_placed)
    
    async def process_payment(self, order_id: str, amount: float, payment_method: str) -> Dict[str, Any]:
        """Process payment"""
        payment_id = str(uuid.uuid4())
        
        # Simulate payment processing
        success = payment_method != 'invalid_card'  # Simple simulation
        
        payment = {
            'id': payment_id,
            'order_id': order_id,
            'amount': amount,
            'payment_method': payment_method,
            'status': 'completed' if success else 'failed',
            'processed_at': datetime.now().isoformat()
        }
        
        self.payments[payment_id] = payment
        
        if success:
            # Publish event
            event = Event(
                id=str(uuid.uuid4()),
                type=EventType.PAYMENT_PROCESSED,
                payload={'order_id': order_id, 'payment_id': payment_id, 'amount': amount},
                timestamp=datetime.now(),
                service_name='payment-service'
            )
            
            await self.message_bus.publish(event)
        
        return payment
    
    async def _handle_order_placed(self, event: Event):
        """Auto-process payment for orders (simplified)"""
        order_id = event.payload.get('order_id')
        amount = event.payload.get('total')
        
        if order_id and amount:
            # Simulate automatic payment processing
            await self.process_payment(order_id, amount, 'credit_card')

# test_microservices.py - Comprehensive microservices testing
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from microservices import (
    MessageBus, Event, EventType, CircuitBreaker, CircuitState,
    ServiceRegistry, APIGateway, UserService, OrderService, PaymentService
)

@pytest.fixture
def message_bus():
    """Create message bus for testing"""
    return MessageBus(redis_client=Mock())

@pytest.fixture
def service_registry():
    """Create service registry for testing"""
    return ServiceRegistry()

@pytest.fixture
def user_service(message_bus):
    """Create user service for testing"""
    return UserService(message_bus)

@pytest.fixture
def order_service(message_bus):
    """Create order service for testing"""
    return OrderService(message_bus)

@pytest.fixture
def payment_service(message_bus):
    """Create payment service for testing"""
    return PaymentService(message_bus)

class TestMessageBus:
    @pytest.mark.asyncio
    async def test_publish_event(self, message_bus):
        event = Event(
            id='test-1',
            type=EventType.USER_CREATED,
            payload={'user_id': '123'},
            timestamp=datetime.now(),
            service_name='test-service'
        )
        
        await message_bus.publish(event)
        
        published_events = message_bus.get_published_events()
        assert len(published_events) == 1
        assert published_events[0].id == 'test-1'
        assert published_events[0].type == EventType.USER_CREATED
    
    @pytest.mark.asyncio
    async def test_subscribe_and_handle_event(self, message_bus):
        handled_events = []
        
        async def handler(event: Event):
            handled_events.append(event)
        
        message_bus.subscribe(EventType.USER_CREATED, handler)
        
        event = Event(
            id='test-1',
            type=EventType.USER_CREATED,
            payload={'user_id': '123'},
            timestamp=datetime.now(),
            service_name='test-service'
        )
        
        await message_bus.publish(event)
        
        assert len(handled_events) == 1
        assert handled_events[0].id == 'test-1'
    
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, message_bus):
        handler1_events = []
        handler2_events = []
        
        async def handler1(event: Event):
            handler1_events.append(event)
        
        async def handler2(event: Event):
            handler2_events.append(event)
        
        message_bus.subscribe(EventType.USER_CREATED, handler1)
        message_bus.subscribe(EventType.USER_CREATED, handler2)
        
        event = Event(
            id='test-1',
            type=EventType.USER_CREATED,
            payload={'user_id': '123'},
            timestamp=datetime.now(),
            service_name='test-service'
        )
        
        await message_bus.publish(event)
        
        assert len(handler1_events) == 1
        assert len(handler2_events) == 1
    
    def test_get_published_events_by_type(self, message_bus):
        event1 = Event('1', EventType.USER_CREATED, {}, datetime.now(), 'service1')
        event2 = Event('2', EventType.ORDER_PLACED, {}, datetime.now(), 'service2')
        
        message_bus.published_events = [event1, event2]
        
        user_events = message_bus.get_published_events(EventType.USER_CREATED)
        order_events = message_bus.get_published_events(EventType.ORDER_PLACED)
        
        assert len(user_events) == 1
        assert len(order_events) == 1
        assert user_events[0].type == EventType.USER_CREATED
        assert order_events[0].type == EventType.ORDER_PLACED

class TestCircuitBreaker:
    def test_circuit_breaker_closed_state(self):
        cb = CircuitBreaker(failure_threshold=3)
        
        def successful_function():
            return "success"
        
        result = cb.call(successful_function)
        
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    def test_circuit_breaker_opens_after_failures(self):
        cb = CircuitBreaker(failure_threshold=3, expected_exception=ValueError)
        
        def failing_function():
            raise ValueError("Test failure")
        
        # Cause failures to open circuit
        for i in range(3):
            with pytest.raises(ValueError):
                cb.call(failing_function)
        
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3
        
        # Circuit should now prevent calls
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            cb.call(failing_function)
    
    def test_circuit_breaker_half_open_transition(self):
        cb = CircuitBreaker(failure_threshold=2, timeout=0.1, expected_exception=ValueError)
        
        def failing_function():
            raise ValueError("Test failure")
        
        # Open the circuit
        for i in range(2):
            with pytest.raises(ValueError):
                cb.call(failing_function)
        
        assert cb.state == CircuitState.OPEN
        
        # Wait for timeout
        time.sleep(0.2)
        
        # Next call should transition to HALF_OPEN
        with pytest.raises(ValueError):
            cb.call(failing_function)
        
        # State should have transitioned through HALF_OPEN back to OPEN
        assert cb.state == CircuitState.OPEN
    
    def test_circuit_breaker_recovery(self):
        cb = CircuitBreaker(failure_threshold=2, timeout=0.1, expected_exception=ValueError)
        
        def failing_function():
            raise ValueError("Test failure")
        
        def successful_function():
            return "success"
        
        # Open the circuit
        for i in range(2):
            with pytest.raises(ValueError):
                cb.call(failing_function)
        
        assert cb.state == CircuitState.OPEN
        
        # Wait for timeout
        time.sleep(0.2)
        
        # Successful call should close circuit
        result = cb.call(successful_function)
        
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

class TestServiceRegistry:
    def test_register_service(self, service_registry):
        instance_id = service_registry.register_service(
            "user-service", "localhost", 8001, "/health"
        )
        
        instances = service_registry.get_service_instances("user-service")
        
        assert len(instances) == 1
        assert instances[0]['id'] == instance_id
        assert instances[0]['host'] == "localhost"
        assert instances[0]['port'] == 8001
        assert instances[0]['healthy'] is True
    
    def test_register_multiple_instances(self, service_registry):
        id1 = service_registry.register_service("user-service", "host1", 8001)
        id2 = service_registry.register_service("user-service", "host2", 8002)
        
        instances = service_registry.get_service_instances("user-service")
        
        assert len(instances) == 2
        assert {inst['id'] for inst in instances} == {id1, id2}
    
    def test_deregister_service(self, service_registry):
        id1 = service_registry.register_service("user-service", "host1", 8001)
        id2 = service_registry.register_service("user-service", "host2", 8002)
        
        service_registry.deregister_service("user-service", id1)
        
        instances = service_registry.get_service_instances("user-service")
        
        assert len(instances) == 1
        assert instances[0]['id'] == id2
    
    def test_get_service_url(self, service_registry):
        service_registry.register_service("user-service", "localhost", 8001)
        
        url = service_registry.get_service_url("user-service")
        
        assert url == "http://localhost:8001"
    
    def test_get_service_url_no_instances(self, service_registry):
        url = service_registry.get_service_url("nonexistent-service")
        
        assert url is None

class TestAPIGateway:
    def test_get_circuit_breaker(self, service_registry):
        gateway = APIGateway(service_registry)
        
        cb1 = gateway.get_circuit_breaker("service1")
        cb2 = gateway.get_circuit_breaker("service1")  # Same service
        cb3 = gateway.get_circuit_breaker("service2")  # Different service
        
        assert cb1 is cb2  # Same instance
        assert cb1 is not cb3  # Different instance
        assert isinstance(cb1, CircuitBreaker)
    
    @pytest.mark.asyncio
    async def test_route_request_no_service(self, service_registry):
        gateway = APIGateway(service_registry)
        
        with pytest.raises(Exception, match="No healthy instances"):
            await gateway.route_request("nonexistent-service", "/users")

class TestUserService:
    @pytest.mark.asyncio
    async def test_create_user(self, user_service, message_bus):
        user_data = {
            'email': 'test@example.com',
            'name': 'Test User'
        }
        
        user = await user_service.create_user(user_data)
        
        assert user['email'] == 'test@example.com'
        assert user['name'] == 'Test User'
        assert user['status'] == 'active'
        assert 'id' in user
        assert 'created_at' in user
        
        # Check event was published
        events = message_bus.get_published_events(EventType.USER_CREATED)
        assert len(events) == 1
        assert events[0].payload['user_id'] == user['id']
        assert events[0].payload['email'] == user['email']
    
    def test_get_user(self, user_service):
        # Add user directly for testing
        user_id = 'test-123'
        user_service.users[user_id] = {
            'id': user_id,
            'email': 'test@example.com',
            'name': 'Test User'
        }
        
        user = user_service.get_user(user_id)
        
        assert user is not None
        assert user['id'] == user_id
        assert user['email'] == 'test@example.com'
    
    def test_get_user_not_found(self, user_service):
        user = user_service.get_user('nonexistent')
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_update_user(self, user_service, message_bus):
        # Create user first
        user = await user_service.create_user({
            'email': 'test@example.com',
            'name': 'Test User'
        })
        
        # Update user
        updates = {'name': 'Updated User', 'status': 'inactive'}
        updated_user = await user_service.update_user(user['id'], updates)
        
        assert updated_user['name'] == 'Updated User'
        assert updated_user['status'] == 'inactive'
        assert 'updated_at' in updated_user
        
        # Check event was published
        events = message_bus.get_published_events(EventType.USER_UPDATED)
        assert len(events) == 1
        assert events[0].payload['user_id'] == user['id']
        assert events[0].payload['updates'] == updates
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_user(self, user_service):
        with pytest.raises(ValueError, match="User not found"):
            await user_service.update_user('nonexistent', {'name': 'New Name'})

class TestOrderService:
    @pytest.mark.asyncio
    async def test_create_order(self, order_service, message_bus):
        items = [
            {'product_id': '1', 'price': 10.0, 'quantity': 2},
            {'product_id': '2', 'price': 5.0, 'quantity': 1}
        ]
        
        order = await order_service.create_order('user123', items)
        
        assert order['user_id'] == 'user123'
        assert order['items'] == items
        assert order['total'] == 25.0  # (10*2) + (5*1)
        assert order['status'] == 'pending'
        assert 'id' in order
        assert 'created_at' in order
        
        # Check event was published
        events = message_bus.get_published_events(EventType.ORDER_PLACED)
        assert len(events) == 1
        assert events[0].payload['order_id'] == order['id']
        assert events[0].payload['user_id'] == 'user123'
        assert events[0].payload['total'] == 25.0
    
    def test_get_order(self, order_service):
        # Add order directly for testing
        order_id = 'order-123'
        order_service.orders[order_id] = {
            'id': order_id,
            'user_id': 'user123',
            'total': 100.0
        }
        
        order = order_service.get_order(order_id)
        
        assert order is not None
        assert order['id'] == order_id
        assert order['total'] == 100.0
    
    @pytest.mark.asyncio
    async def test_handle_payment_processed(self, order_service, message_bus):
        # Create order
        order = await order_service.create_order('user123', [
            {'product_id': '1', 'price': 10.0, 'quantity': 1}
        ])
        
        # Simulate payment processed event
        payment_event = Event(
            id='payment-1',
            type=EventType.PAYMENT_PROCESSED,
            payload={'order_id': order['id'], 'payment_id': 'pay-123'},
            timestamp=datetime.now(),
            service_name='payment-service'
        )
        
        await order_service._handle_payment_processed(payment_event)
        
        # Order status should be updated
        updated_order = order_service.get_order(order['id'])
        assert updated_order['status'] == 'confirmed'
        
        # Order confirmed event should be published
        confirmed_events = message_bus.get_published_events(EventType.ORDER_CONFIRMED)
        assert len(confirmed_events) == 1
        assert confirmed_events[0].payload['order_id'] == order['id']

class TestPaymentService:
    @pytest.mark.asyncio
    async def test_process_payment_success(self, payment_service, message_bus):
        payment = await payment_service.process_payment(
            'order-123', 100.0, 'credit_card'
        )
        
        assert payment['order_id'] == 'order-123'
        assert payment['amount'] == 100.0
        assert payment['payment_method'] == 'credit_card'
        assert payment['status'] == 'completed'
        assert 'id' in payment
        assert 'processed_at' in payment
        
        # Check event was published
        events = message_bus.get_published_events(EventType.PAYMENT_PROCESSED)
        assert len(events) == 1
        assert events[0].payload['order_id'] == 'order-123'
        assert events[0].payload['payment_id'] == payment['id']
    
    @pytest.mark.asyncio
    async def test_process_payment_failure(self, payment_service, message_bus):
        payment = await payment_service.process_payment(
            'order-123', 100.0, 'invalid_card'
        )
        
        assert payment['status'] == 'failed'
        
        # No event should be published for failed payments
        events = message_bus.get_published_events(EventType.PAYMENT_PROCESSED)
        assert len(events) == 0
    
    @pytest.mark.asyncio
    async def test_handle_order_placed(self, payment_service, message_bus):
        # Simulate order placed event
        order_event = Event(
            id='order-1',
            type=EventType.ORDER_PLACED,
            payload={'order_id': 'order-123', 'total': 50.0},
            timestamp=datetime.now(),
            service_name='order-service'
        )
        
        await payment_service._handle_order_placed(order_event)
        
        # Payment should be created automatically
        assert 'order-123' in [p['order_id'] for p in payment_service.payments.values()]
        
        # Payment processed event should be published
        events = message_bus.get_published_events(EventType.PAYMENT_PROCESSED)
        assert len(events) == 1
        assert events[0].payload['order_id'] == 'order-123'

# Integration tests for microservices
class TestMicroservicesIntegration:
    @pytest.mark.asyncio
    async def test_complete_order_workflow(self, message_bus):
        """Test complete order workflow across services"""
        # Initialize services
        user_service = UserService(message_bus)
        order_service = OrderService(message_bus)
        payment_service = PaymentService(message_bus)
        
        # Step 1: Create user
        user = await user_service.create_user({
            'email': 'customer@example.com',
            'name': 'Test Customer'
        })
        
        # Step 2: Create order
        items = [{'product_id': '1', 'price': 25.0, 'quantity': 2}]
        order = await order_service.create_order(user['id'], items)
        
        # Wait a bit for event processing (in real scenario, use better synchronization)
        await asyncio.sleep(0.1)