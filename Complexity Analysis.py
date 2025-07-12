# How Complexity Analysis Helps in System Design
# 
# Code complexity is **the foundation of system design** - it determines whether your system can handle 100 users or 100 million users!

## System Design Impact

### 1. **Scalability Decisions**
# 
# Complexity analysis helps you choose the right architecture:

# Bad: O(n²) approach - won't scale
class SimpleUserService:
    # This works for 1000 users, fails at 1 million
    def get_user_recommendations(self, user_id: str) -> list[dict]:
        """This works for 1000 users, fails at 1 million"""
        # O(n²) approach - won't scale
        all_users = self.get_all_users()  # 1M users
        user_interests = self.get_user_interests(user_id)
        
        recommendations = []
        for other_user in all_users:  # 1M iterations
            similarity = 0
            for interest in user_interests:  # 100 interests
                if interest in other_user['interests']:
                    similarity += 1
            
            if similarity > 50:
                recommendations.append(other_user)
        
        return recommendations
# Impact: 1M × 100 = 100M operations per request = system crash!

# Good: O(log n) approach - scales to billions
class ScalableUserService:
    # This scales to billions of users
    def get_user_recommendations(self, user_id: str) -> list[dict]:
        """This scales to billions of users"""
        # Use pre-computed similarity clusters
        user_cluster = self.redis_client.get(f"user_cluster:{user_id}")
        
        # Get recommendations from same cluster (indexed)
        recommendations = self.elasticsearch.search({
            "query": {
                "bool": {
                    "must": [
                        {"term": {"cluster": user_cluster}},
                        {"range": {"similarity_score": {"gte": 0.8}}}
                    ]
                }
            }
        })
        
        return recommendations['hits']['hits']
# Impact: ~10 operations per request = system handles billions!


### 2. **Infrastructure Capacity Planning**
# 
# Complexity determines your server needs:

# Example: E-commerce search system
class SearchAnalysis:
    # Scenario: 10M products, 100K concurrent users
    def calculate_infrastructure_needs(self):
        # Bad O(n) approach per search
        operations_per_search = 10_000_000  # Linear search
        searches_per_second = 100_000
        total_operations = operations_per_search * searches_per_second
        # = 1 trillion operations/second = Need 10,000 servers!
        
        # Good O(1) approach with indexing
        operations_per_search = 1  # Hash table lookup
        total_operations = operations_per_search * searches_per_second
        # = 100K operations/second = Need 1 server!
        
        return {
            'bad_approach_servers': 10000,
            'good_approach_servers': 1,
            'cost_difference': '$2M/month vs $200/month'
        }


### 3. **Database Design Choices**
# 
# Complexity guides database selection:

# Different complexity characteristics guide DB choice

# SQL (PostgreSQL) - Good for complex queries
class SQLUserService:
    # O(log n) with proper indexing
    def get_user_analytics(self, user_id: str) -> dict:
        """O(log n) with proper indexing"""
        query = """
        SELECT u.*, 
               COUNT(o.id) as order_count,
               AVG(o.amount) as avg_order_value
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.id = %s
        GROUP BY u.id
        """
        # With proper indexes: O(log n)
        return self.db.execute(query, [user_id])

# NoSQL (MongoDB) - Good for simple, fast lookups
class NoSQLUserService:
    # O(1) for document retrieval
    def get_user_profile(self, user_id: str) -> dict:
        """O(1) for document retrieval"""
        return self.mongodb.users.find_one({"_id": user_id})
        # Document stores: O(1) lookup

# Redis - Good for caching and real-time data
class CacheUserService:
    # O(1) for in-memory access
    def get_user_session(self, user_id: str) -> dict:
        """O(1) for in-memory access"""
        return self.redis.get(f"session:{user_id}")
        # In-memory: O(1) access


## System Design Patterns Based on Complexity

### 1. **Microservices Architecture**
# 
# Split services based on complexity requirements:

# User Service - Simple O(1) operations
class UserService:
    # O(1) - Single record lookup
    def get_user(self, user_id: str) -> dict:
        """O(1) - Single record lookup"""
        return self.cache.get(user_id) or self.db.get_user(user_id)

# Recommendation Service - Complex O(n log n) operations
class RecommendationService:
    # O(n log n) - Complex ML calculations
    def generate_recommendations(self, user_id: str) -> list[dict]:
        """O(n log n) - Complex ML calculations"""
        # This needs separate scaling strategy
        user_vector = self.get_user_embedding(user_id)
        similar_users = self.vector_db.similarity_search(user_vector)
        return self.rank_recommendations(similar_users)

# Search Service - O(log n) with specialized indexing
class SearchService:
    # O(log n) - Requires Elasticsearch cluster
    def search_products(self, query: str) -> list[dict]:
        """O(log n) - Requires Elasticsearch cluster"""
        return self.elasticsearch.search({
            "query": {"match": {"name": query}},
            "size": 20
        })


### 2. **Caching Strategy**
# 
# Cache based on complexity patterns:

# Multi-level caching based on complexity
class CachingStrategy:
    def __init__(self):
        # In-memory - O(1)
        self.l1_cache = {}  
        # Redis - O(1)
        self.l2_cache = redis.Redis()  
        # Memcached - O(1)
        self.l3_cache = memcached.Client()  
        # Database - O(log n)
        self.database = PostgreSQL()  
    
    # Cache expensive O(n²) operations aggressively
    def get_expensive_calculation(self, key: str) -> dict:
        """Cache expensive O(n²) operations aggressively"""
        
        # Check L1 cache first
        if key in self.l1_cache:
            return self.l1_cache[key]
        
        # Check L2 cache
        result = self.l2_cache.get(key)
        if result:
            self.l1_cache[key] = result  # Promote to L1
            return result
        
        # Expensive calculation - cache for long time
        result = self.perform_expensive_calculation(key)
        
        # Cache at all levels
        self.l1_cache[key] = result
        self.l2_cache.setex(key, 3600, result)  # 1 hour
        
        return result
    
    # O(n²) operation - minimize calls
    def perform_expensive_calculation(self, key: str) -> dict:
        """O(n²) operation - minimize calls"""
        # Complex ML model, graph analysis, etc.
        pass


### 3. **Load Balancing Strategy**
# 
# Route requests based on complexity:

# nginx.conf - Route by complexity
"""
upstream simple_service {
    server simple1:8000;
    server simple2:8000;
    server simple3:8000;
}

upstream complex_service {
    server complex1:8000 weight=3;
    server complex2:8000 weight=3;
    server complex3:8000 weight=3;
}

server {
    location /api/users/ {
        # Simple O(1) operations - lightweight servers
        proxy_pass http://simple_service;
    }
    
    location /api/recommendations/ {
        # Complex O(n log n) operations - powerful servers
        proxy_pass http://complex_service;
    }
}
"""


## Essential Libraries for Different Complexities

### **Data Structures & Algorithms**

#### **Python Libraries**

# For O(1) operations
import redis  # In-memory key-value store
import memcache  # Distributed caching
from collections import defaultdict, Counter, deque

# For O(log n) operations
import heapq  # Priority queue operations
import bisect  # Binary search operations
from sortedcontainers import SortedList, SortedDict

# For O(n) optimizations
import pandas as pd  # Vectorized operations
import numpy as np  # Numerical computations
import polars as pl  # Faster DataFrame operations

# For complex algorithms
import networkx as nx  # Graph algorithms
import sklearn  # Machine learning algorithms
import scipy  # Scientific computing

### **Database & Search**

#### **Search & Indexing (O(log n) to O(1))**

# Elasticsearch - Full-text search
from elasticsearch import Elasticsearch
es = Elasticsearch()

# Example: Product search
def search_products(query: str) -> list[dict]:
    """O(log n) search with proper indexing"""
    return es.search(
        index="products",
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["name^3", "description", "tags"]
                }
            }
        }
    )

# Solr - Alternative search engine
import pysolr
solr = pysolr.Solr('http://localhost:8983/solr/products')

# Whoosh - Pure Python search
from whoosh import index, fields, qparser


#### **Time-Series Data (O(1) writes, O(log n) reads)**

# InfluxDB - Time series database
from influxdb_client import InfluxDBClient

# Example: Metrics collection
def write_metrics(metric_name: str, value: float):
    """O(1) write operation"""
    point = Point(metric_name).field("value", value)
    write_api.write(bucket="metrics", record=point)

# TimescaleDB - PostgreSQL extension
import psycopg2
def write_sensor_data(sensor_id: str, temperature: float):
    """O(1) write with automatic partitioning"""
    cursor.execute(
        "INSERT INTO sensor_data (sensor_id, temperature, timestamp) VALUES (%s, %s, NOW())",
        (sensor_id, temperature)
    )


### **Caching & Memory**

#### **Redis (O(1) operations)**

import redis
import json

class RedisCache:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0)
    
    # Cache expensive O(n²) operations
    def cache_expensive_operation(self, key: str, ttl: int = 3600):
        """Decorator for caching O(n²) operations"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                cache_key = f"{key}:{hash(str(args) + str(kwargs))}"
                
                # O(1) lookup
                cached = self.redis.get(cache_key)
                if cached:
                    return json.loads(cached)
                
                # Expensive operation
                result = func(*args, **kwargs)
                
                # O(1) storage
                self.redis.setex(cache_key, ttl, json.dumps(result))
                return result
            return wrapper
        return decorator

# Usage
cache = RedisCache()

@cache.cache_expensive_operation("user_recommendations", ttl=1800)
def get_user_recommendations(user_id: str) -> list[dict]:
    """Complex O(n²) operation - cache results"""
    # Expensive ML computation here
    pass


#### **Memcached (O(1) operations)**

import memcache

class MemcachedCache:
    def __init__(self):
        self.mc = memcache.Client(['127.0.0.1:11211'])
    
    # Cache O(n log n) database queries
    def cache_query_results(self, sql_query: str) -> list[dict]:
        """Cache O(n log n) database queries"""
        cache_key = f"query:{hash(sql_query)}"
        
        # O(1) lookup
        result = self.mc.get(cache_key)
        if result:
            return result
        
        # Expensive database query
        result = self.database.execute(sql_query)
        
        # O(1) storage
        self.mc.set(cache_key, result, time=3600)
        return result


### **Message Queues & Async Processing**

#### **For Breaking Down O(n²) Operations**

# Celery - Distributed task queue
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379')

@app.task
# Break O(n²) operation into smaller O(n) chunks
def process_user_batch(user_ids: list[str]):
    """Break O(n²) operation into smaller O(n) chunks"""
    for user_id in user_ids:
        # Process individual user - O(n) operation
        generate_recommendations_for_user(user_id)

# Usage: Instead of processing all users at once
def process_all_users():
    """Convert O(n²) to distributed O(n) operations"""
    all_users = get_all_users()
    batch_size = 100
    
    for i in range(0, len(all_users), batch_size):
        batch = all_users[i:i+batch_size]
        process_user_batch.delay([u['id'] for u in batch])

# RabbitMQ - Message broker
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Queue O(n²) operations for background processing
def queue_expensive_operation(user_id: str):
    """Queue O(n²) operations for background processing"""
    channel.basic_publish(
        exchange='',
        routing_key='heavy_computation',
        body=json.dumps({'user_id': user_id, 'operation': 'generate_recommendations'})
    )


### **Real-Time Processing**

#### **Apache Kafka (O(1) writes, O(log n) reads)**

from kafka import KafkaProducer, KafkaConsumer

# Producer - O(1) write
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# O(1) event tracking
def track_user_event(user_id: str, event_type: str, data: dict):
    """O(1) event tracking"""
    producer.send('user_events', {
        'user_id': user_id,
        'event_type': event_type,
        'data': data,
        'timestamp': time.time()
    })

# Consumer - Process events efficiently
consumer = KafkaConsumer(
    'user_events',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# Process events in O(1) per event
def process_events():
    """Process events in O(1) per event"""
    for message in consumer:
        event = message.value
        # Update user profile, trigger recommendations, etc.
        update_user_profile(event['user_id'], event['data'])


### **Vector Databases (O(log n) similarity search)**

# Pinecone - Vector database for ML
import pinecone

pinecone.init(api_key="your-api-key", environment="us-west1-gcp")
index = pinecone.Index("user-embeddings")

# O(log n) similarity search instead of O(n²) comparison
def find_similar_users(user_embedding: list[float], top_k: int = 10) -> list[dict]:
    """O(log n) similarity search instead of O(n²) comparison"""
    results = index.query(
        vector=user_embedding,
        top_k=top_k,
        include_metadata=True
    )
    return results['matches']

# Weaviate - Open source vector database
import weaviate

client = weaviate.Client("http://localhost:8080")

# O(log n) semantic search
def semantic_search(query: str) -> list[dict]:
    """O(log n) semantic search"""
    result = client.query.get("Product", ["name", "description"]).with_near_text({
        "concepts": [query]
    }).with_limit(10).do()
    
    return result['data']['Get']['Product']


## System Design Architecture Example

# Complete system architecture based on complexity requirements

class ECommerceSystemDesign:
    def __init__(self):
        # O(1) operations - Use Redis
        self.session_cache = redis.Redis(host='redis-sessions')
        self.cart_cache = redis.Redis(host='redis-carts')
        
        # O(log n) operations - Use PostgreSQL with indexes
        self.user_db = postgresql.connect(host='postgres-users')
        self.order_db = postgresql.connect(host='postgres-orders')
        
        # O(log n) search - Use Elasticsearch
        self.search_engine = elasticsearch.Elasticsearch(hosts=['es-cluster'])
        
        # O(n log n) recommendations - Use separate service
        self.recommendation_service = RecommendationService()
        
        # O(1) messaging - Use Kafka
        self.event_stream = kafka.KafkaProducer(bootstrap_servers=['kafka-cluster'])
    
    # Route requests based on complexity requirements
    def handle_user_request(self, request_type: str, user_id: str, data: dict):
        """Route requests based on complexity requirements"""
        
        if request_type == 'get_user':
            # O(1) - Use cache
            return self.session_cache.get(f"user:{user_id}")
        
        elif request_type == 'search_products':
            # O(log n) - Use search engine
            return self.search_engine.search({
                "query": {"match": {"name": data['query']}},
                "size": 20
            })
        
        elif request_type == 'get_recommendations':
            # O(n log n) - Queue for background processing
            self.event_stream.send('recommendation_requests', {
                'user_id': user_id,
                'context': data
            })
            # Return cached results immediately
            return self.recommendation_service.get_cached_recommendations(user_id)
        
        elif request_type == 'place_order':
            # O(log n) - Database with proper indexing
            return self.order_db.execute(
                "INSERT INTO orders (user_id, items, total) VALUES (%s, %s, %s)",
                (user_id, data['items'], data['total'])
            )


## Key Takeaways for System Design

#1. **O(1) operations** → Use caching (Redis, Memcached)
#2. **O(log n) operations** → Use indexed databases (PostgreSQL, Elasticsearch)
#3. **O(n) operations** → Use streaming/batch processing (Kafka, Celery)
#4. **O(n²) operations** → Break down, cache, or pre-compute
#5. **O(2ⁿ) operations** → Avoid in production, use heuristics instead

#**Remember**: System design is about choosing the right tool for the right complexity level. A simple O(1) lookup doesn't need a complex distributed system, but an O(n²) operation might need to be redesigned entirely!

# Code Complexity - Real World Use Cases

#Let me explain complexity using actual scenarios you encounter every day!

## E-commerce Platform Examples

### 1. Product Search - O(n) vs O(1)

#**Bad Approach - O(n): Linear Search**

# Amazon-like search - checking every product
def search_products_slow(query: str, products: list[dict]) -> list[dict]:
    """Like having an employee check every item in the warehouse"""
    results = []
    for product in products:  # 10 million products = 10 million checks
        if query.lower() in product['name'].lower():
            results.append(product)
    return results

# Real impact: 10 million products = 10 seconds search time


#**Good Approach - O(1): Indexed Search**

# Using search index (like Elasticsearch)
def search_products_fast(query: str, search_index: dict) -> list[dict]:
    """Like having a pre-organized catalog with instant lookup"""
    return search_index.get(query, [])  # Instant lookup

# Real impact: 10 million products = 0.001 seconds search time


#**Real Example**: Amazon processes 1.6 billion searches daily. Without optimization, each search would take 10+ seconds instead of milliseconds!

### 2. Shopping Cart Total - O(n²) vs O(n)

#**Bad Approach - O(n²): Recalculating Everything**

# Recalculating discounts for every item, every time
def calculate_cart_total_slow(cart_items: list[dict]) -> float:
    """Like recalculating all discounts from scratch every time"""
    total = 0
    for item in cart_items:  # 50 items
        item_total = item['price'] * item['quantity']
        
        # Check all discount rules for each item
        for discount_rule in get_all_discount_rules():  # 1000 rules
            if discount_applies(item, discount_rule):
                item_total *= (1 - discount_rule['percentage'])
        
        total += item_total
    return total

# Real impact: 50 items × 1000 rules = 50,000 calculations per cart update


#**Good Approach - O(n): Cached Calculations**

# Pre-calculate applicable discounts
def calculate_cart_total_fast(cart_items: list[dict]) -> float:
    """Like having pre-calculated discount tables"""
    total = 0
    for item in cart_items:  # 50 items only
        # Use pre-calculated discount (cached)
        applicable_discount = get_cached_discount(item['category'])
        discounted_price = item['price'] * (1 - applicable_discount)
        total += discounted_price * item['quantity']
    return total

# Real impact: 50 items = 50 calculations per cart update


#**Real Example**: Shopify processes millions of cart updates daily. Bad approach would crash their servers!

## Social Media Platform Examples

### 3. News Feed Generation - O(n²) vs O(n log n)

#**Bad Approach - O(n²): Checking Everyone's Everything**

# Instagram-like feed generation
def generate_feed_slow(user: dict) -> list[dict]:
    """Like manually asking each friend about every post they've made"""
    posts = []
    
    for friend in user['friends']:  # 500 friends
        for post in friend['all_posts']:  # Each friend has 1000 posts
            if post['timestamp'] > user['last_login']:
                posts.append(post)
    
    return sorted(posts, key=lambda x: x['timestamp'])

# Real impact: 500 friends × 1000 posts = 500,000 operations per feed load


#**Good Approach - O(n log n): Pre-computed Timeline**

# Using timeline/activity stream
def generate_feed_fast(user: dict) -> list[dict]:
    """Like having a pre-organized newspaper delivered to your door"""
    # Posts are pre-aggregated in user's timeline
    recent_posts = user['timeline'][:100]  # Get top 100
    return recent_posts

# Real impact: 100 operations per feed load


#**Real Example**: Facebook generates 4.5 billion feeds daily. Without optimization, each feed would take 30+ seconds to load!

### 4. Friend Suggestions - O(n³) vs O(n)

#**Bad Approach - O(n³): Triple Nested Loops**

# LinkedIn-like friend suggestions
def suggest_friends_slow(user: dict, all_users: list[dict]) -> list[dict]:
    """Like comparing every person with every other person's friends"""
    suggestions = []
    
    for potential_friend in all_users:  # 1 billion users
        if potential_friend['id'] == user['id']:
            continue
            
        mutual_friends = 0
        for user_friend in user['friends']:  # 500 friends
            for potential_friend_friend in potential_friend['friends']:  # 500 friends
                if user_friend['id'] == potential_friend_friend['id']:
                    mutual_friends += 1
        
        if mutual_friends > 0:
            suggestions.append(potential_friend)
    
    return suggestions

# Real impact: 1 billion × 500 × 500 = 250 trillion operations!


#**Good Approach - O(n): Friend-of-Friends Index**

# Using graph-based approach
def suggest_friends_fast(user: dict) -> list[dict]:
    """Like having a pre-built network map"""
    # Pre-computed friend-of-friends relationships
    return user['friend_suggestions_cache'][:10]

# Real impact: 10 operations per suggestion request


#**Real Example**: LinkedIn has 900+ million users. Bad approach would literally take years to compute!

## Streaming Service Examples

### 5. Video Recommendations - O(n²) vs O(n)

#**Bad Approach - O(n²): User-to-User Comparison**

# Netflix-like recommendations
def recommend_movies_slow(user: dict, all_users: list[dict]) -> list[dict]:
    """Like asking every Netflix user what they like"""
    recommendations = []
    
    for other_user in all_users:  # 230 million users
        if other_user['id'] == user['id']:
            continue
            
        similarity = calculate_similarity(user, other_user)  # Expensive calculation
        if similarity > 0.8:
            for movie in other_user['liked_movies']:
                if movie not in user['watched_movies']:
                    recommendations.append(movie)
    
    return recommendations

# Real impact: 230 million similarity calculations per recommendation


#**Good Approach - O(n): Clustering and Pre-computation**

# Using collaborative filtering with clusters
def recommend_movies_fast(user: dict) -> list[dict]:
    """Like having movie taste categories pre-organized"""
    # User is pre-assigned to taste clusters
    user_cluster = user['taste_cluster']  # e.g., "action_lovers"
    
    # Get recommendations from similar users in same cluster
    cluster_recommendations = get_cluster_recommendations(user_cluster)
    
    # Filter out already watched
    unwatched = [movie for movie in cluster_recommendations 
                if movie not in user['watched_movies']]
    
    return unwatched[:20]

# Real impact: ~1000 operations per recommendation


#**Real Example**: Netflix users watch 1+ billion hours daily. Bad approach would require supercomputers!

## Banking/Financial Examples

### 6. Transaction Fraud Detection - O(n²) vs O(log n)

#**Bad Approach - O(n²): Checking All Transactions**

# Credit card fraud detection
def detect_fraud_slow(new_transaction: dict, all_transactions: list[dict]) -> bool:
    """Like manually reviewing every transaction in bank history"""
    
    for transaction in all_transactions:  # 100 million transactions
        # Check for patterns with every other transaction
        for other_transaction in all_transactions:
            if is_suspicious_pattern(transaction, other_transaction, new_transaction):
                return True
    
    return False

# Real impact: 100 million × 100 million = 10 quadrillion comparisons per check


#**Good Approach - O(log n): Rule-based with Indexed Lookup**

# Using rules engine with indexed data
def detect_fraud_fast(new_transaction: dict, user_profile: dict) -> bool:
    """Like having smart rules that instantly flag anomalies"""
    
    # Check amount against user's typical spending (indexed lookup)
    if new_transaction['amount'] > user_profile['max_typical_amount'] * 3:
        return True
    
    # Check location against recent locations (indexed lookup)
    if new_transaction['location'] not in user_profile['recent_locations']:
        return True
    
    # Check merchant category (indexed lookup)
    if new_transaction['merchant_type'] in user_profile['never_used_categories']:
        return True
    
    return False

# Real impact: ~10 operations per fraud check


#**Real Example**: Visa processes 150 million transactions daily. Each must be checked in milliseconds!

## Gaming Examples

### 7. Matchmaking - O(n²) vs O(n log n)

#**Bad Approach - O(n²): Compare Every Player**

# Fortnite-like matchmaking
def find_match_slow(player: dict, all_players: list[dict]) -> list[dict]:
    """Like having every player fight every other player to find equal matches"""
    potential_matches = []
    
    for other_player in all_players:  # 10 million active players
        for comparison_player in all_players:  # Compare with everyone else too
            if players_are_similar_skill(player, other_player, comparison_player):
                potential_matches.append(other_player)
    
    return potential_matches[:99]  # 100 player battle royale

# Real impact: 10 million × 10 million = 100 trillion comparisons


#**Good Approach - O(n log n): Skill-based Buckets**

# Using skill rating buckets
def find_match_fast(player: dict) -> list[dict]:
    """Like having skill leagues where you only compete within your level"""
    
    # Players pre-sorted into skill buckets
    skill_range = player['skill_rating']
    bucket_min = skill_range - 100
    bucket_max = skill_range + 100
    
    # Get players from appropriate bucket (pre-filtered)
    eligible_players = skill_buckets[bucket_min:bucket_max]
    
    # Simple random selection from bucket
    return random.sample(eligible_players, 99)

# Real impact: ~1000 operations per match


#**Real Example**: Fortnite has 400+ million players. Bad approach would take hours to find a match!

## Real-World Impact Summary

## Why This Matters for Your Projects

### Django/DRF Backend

# Bad: N+1 queries problem
def get_orders_slow(request):
    orders = Order.objects.all()  # 1 query
    result = []
    for order in orders:  # N additional queries
        result.append({
            'id': order.id,
            'customer': order.customer.name,  # Database hit each time!
            'amount': order.amount
        })
    return JsonResponse(result)

# Good: Single query with JOIN
def get_orders_fast(request):
    orders = Order.objects.select_related('customer').all()  # 1 query only
    result = []
    for order in orders:
        result.append({
            'id': order.id,
            'customer': order.customer.name,  # No additional query
            'amount': order.amount
        })
    return JsonResponse(result)


#The key takeaway: **Complexity optimization isn't just academic - it's the difference between your app working and your app crashing under real-world load!**# Code Complexity - Real World Use Cases

#Let me explain complexity using actual scenarios you encounter every day!

## E-commerce Platform Examples

### 1. Product Search - O(n) vs O(1)

#**Bad Approach - O(n): Linear Search**

# Amazon-like search - checking every product
def search_products_slow(query: str, products: list[dict]) -> list[dict]:
    """Like having an employee check every item in the warehouse"""
    results = []
    for product in products:  # 10 million products = 10 million checks
        if query.lower() in product['name'].lower():
            results.append(product)
    return results

# Real impact: 10 million products = 10 seconds search time


#**Good Approach - O(1): Indexed Search**

# Using search index (like Elasticsearch)
def search_products_fast(query: str, search_index: dict) -> list[dict]:
    """Like having a pre-organized catalog with instant lookup"""
    return search_index.get(query, [])  # Instant lookup

# Real impact: 10 million products = 0.001 seconds search time


#**Real Example**: Amazon processes 1.6 billion searches daily. Without optimization, each search would take 10+ seconds instead of milliseconds!

### 2. Shopping Cart Total - O(n²) vs O(n)

#**Bad Approach - O(n²): Recalculating Everything**

# Recalculating discounts for every item, every time
def calculate_cart_total_slow(cart_items: list[dict]) -> float:
    """Like recalculating all discounts from scratch every time"""
    total = 0
    for item in cart_items:  # 50 items
        item_total = item['price'] * item['quantity']
        
        # Check all discount rules for each item
        for discount_rule in get_all_discount_rules():  # 1000 rules
            if discount_applies(item, discount_rule):
                item_total *= (1 - discount_rule['percentage'])
        
        total += item_total
    return total

# Real impact: 50 items × 1000 rules = 50,000 calculations per cart update


#**Good Approach - O(n): Cached Calculations**

# Pre-calculate applicable discounts
def calculate_cart_total_fast(cart_items: list[dict]) -> float:
    """Like having pre-calculated discount tables"""
    total = 0
    for item in cart_items:  # 50 items only
        # Use pre-calculated discount (cached)
        applicable_discount = get_cached_discount(item['category'])
        discounted_price = item['price'] * (1 - applicable_discount)
        total += discounted_price * item['quantity']
    return total

# Real impact: 50 items = 50 calculations per cart update


#**Real Example**: Shopify processes millions of cart updates daily. Bad approach would crash their servers!

## Social Media Platform Examples

### 3. News Feed Generation - O(n²) vs O(n log n)

#**Bad Approach - O(n²): Checking Everyone's Everything**

# Instagram-like feed generation
def generate_feed_slow(user: dict) -> list[dict]:
    """Like manually asking each friend about every post they've made"""
    posts = []
    
    for friend in user['friends']:  # 500 friends
        for post in friend['all_posts']:  # Each friend has 1000 posts
            if post['timestamp'] > user['last_login']:
                posts.append(post)
    
    return sorted(posts, key=lambda x: x['timestamp'])

# Real impact: 500 friends × 1000 posts = 500,000 operations per feed load


#**Good Approach - O(n log n): Pre-computed Timeline**

# Using timeline/activity stream
def generate_feed_fast(user: dict) -> list[dict]:
    """Like having a pre-organized newspaper delivered to your door"""
    # Posts are pre-aggregated in user's timeline
    recent_posts = user['timeline'][:100]  # Get top 100
    return recent_posts

# Real impact: 100 operations per feed load


#**Real Example**: Facebook generates 4.5 billion feeds daily. Without optimization, each feed would take 30+ seconds to load!

### 4. Friend Suggestions - O(n³) vs O(n)

#**Bad Approach - O(n³): Triple Nested Loops**

# LinkedIn-like friend suggestions
def suggest_friends_slow(user: dict, all_users: list[dict]) -> list[dict]:
    """Like comparing every person with every other person's friends"""
    suggestions = []
    
    for potential_friend in all_users:  # 1 billion users
        if potential_friend['id'] == user['id']:
            continue
            
        mutual_friends = 0
        for user_friend in user['friends']:  # 500 friends
            for potential_friend_friend in potential_friend['friends']:  # 500 friends
                if user_friend['id'] == potential_friend_friend['id']:
                    mutual_friends += 1
        
        if mutual_friends > 0:
            suggestions.append(potential_friend)
    
    return suggestions

# Real impact: 1 billion × 500 × 500 = 250 trillion operations!


**Good Approach - O(n): Friend-of-Friends Index**

# Using graph-based approach
def suggest_friends_fast(user: dict) -> list[dict]:
    """Like having a pre-built network map"""
    # Pre-computed friend-of-friends relationships
    return user['friend_suggestions_cache'][:10]

# Real impact: 10 operations per suggestion request


#**Real Example**: LinkedIn has 900+ million users. Bad approach would literally take years to compute!

## Streaming Service Examples

### 5. Video Recommendations - O(n²) vs O(n)

#**Bad Approach - O(n²): User-to-User Comparison**

# Netflix-like recommendations
def recommend_movies_slow(user: dict, all_users: list[dict]) -> list[dict]:
    """Like asking every Netflix user what they like"""
    recommendations = []
    
    for other_user in all_users:  # 230 million users
        if other_user['id'] == user['id']:
            continue
            
        similarity = calculate_similarity(user, other_user)  # Expensive calculation
        if similarity > 0.8:
            for movie in other_user['liked_movies']:
                if movie not in user['watched_movies']:
                    recommendations.append(movie)
    
    return recommendations

# Real impact: 230 million similarity calculations per recommendation


#**Good Approach - O(n): Clustering and Pre-computation**

# Using collaborative filtering with clusters
def recommend_movies_fast(user: dict) -> list[dict]:
    """Like having movie taste categories pre-organized"""
    # User is pre-assigned to taste clusters
    user_cluster = user['taste_cluster']  # e.g., "action_lovers"
    
    # Get recommendations from similar users in same cluster
    cluster_recommendations = get_cluster_recommendations(user_cluster)
    
    # Filter out already watched
    unwatched = [movie for movie in cluster_recommendations 
                if movie not in user['watched_movies']]
    
    return unwatched[:20]

# Real impact: ~1000 operations per recommendation


#**Real Example**: Netflix users watch 1+ billion hours daily. Bad approach would require supercomputers!

## Banking/Financial Examples

### 6. Transaction Fraud Detection - O(n²) vs O(log n)

#**Bad Approach - O(n²): Checking All Transactions**

# Credit card fraud detection
def detect_fraud_slow(new_transaction: dict, all_transactions: list[dict]) -> bool:
    """Like manually reviewing every transaction in bank history"""
    
    for transaction in all_transactions:  # 100 million transactions
        # Check for patterns with every other transaction
        for other_transaction in all_transactions:
            if is_suspicious_pattern(transaction, other_transaction, new_transaction):
                return True
    
    return False

# Real impact: 100 million × 100 million = 10 quadrillion comparisons per check


#**Good Approach - O(log n): Rule-based with Indexed Lookup**

# Using rules engine with indexed data
def detect_fraud_fast(new_transaction: dict, user_profile: dict) -> bool:
    """Like having smart rules that instantly flag anomalies"""
    
    # Check amount against user's typical spending (indexed lookup)
    if new_transaction['amount'] > user_profile['max_typical_amount'] * 3:
        return True
    
    # Check location against recent locations (indexed lookup)
    if new_transaction['location'] not in user_profile['recent_locations']:
        return True
    
    # Check merchant category (indexed lookup)
    if new_transaction['merchant_type'] in user_profile['never_used_categories']:
        return True
    
    return False

# Real impact: ~10 operations per fraud check


#**Real Example**: Visa processes 150 million transactions daily. Each must be checked in milliseconds!

## Gaming Examples

### 7. Matchmaking - O(n²) vs O(n log n)

#**Bad Approach - O(n²): Compare Every Player**

# Fortnite-like matchmaking
def find_match_slow(player: dict, all_players: list[dict]) -> list[dict]:
    """Like having every player fight every other player to find equal matches"""
    potential_matches = []
    
    for other_player in all_players:  # 10 million active players
        for comparison_player in all_players:  # Compare with everyone else too
            if players_are_similar_skill(player, other_player, comparison_player):
                potential_matches.append(other_player)
    
    return potential_matches[:99]  # 100 player battle royale

# Real impact: 10 million × 10 million = 100 trillion comparisons


#**Good Approach - O(n log n): Skill-based Buckets**

# Using skill rating buckets
def find_match_fast(player: dict) -> list[dict]:
    """Like having skill leagues where you only compete within your level"""
    
    # Players pre-sorted into skill buckets
    skill_range = player['skill_rating']
    bucket_min = skill_range - 100
    bucket_max = skill_range + 100
    
    # Get players from appropriate bucket (pre-filtered)
    eligible_players = skill_buckets[bucket_min:bucket_max]
    
    # Simple random selection from bucket
    return random.sample(eligible_players, 99)

# Real impact: ~1000 operations per match


#**Real Example**: Fortnite has 400+ million players. Bad approach would take hours to find a match!

## Real-World Impact Summary

## Why This Matters for Your Projects

### Django/DRF Backend

# Bad: N+1 queries problem
def get_orders_slow(request):
    orders = Order.objects.all()  # 1 query
    result = []
    for order in orders:  # N additional queries
        result.append({
            'id': order.id,
            'customer': order.customer.name,  # Database hit each time!
            'amount': order.amount
        })
    return JsonResponse(result)

# Good: Single query with JOIN
def get_orders_fast(request):
    orders = Order.objects.select_related('customer').all()  # 1 query only
    result = []
    for order in orders:
        result.append({
            'id': order.id,
            'customer': order.customer.name,  # No additional query
            'amount': order.amount
        })
    return JsonResponse(result)


#The key takeaway: **Complexity optimization isn't just academic - it's the difference between your app working and your app crashing under real-world load!**# Code Complexity - Simple Explanation

#Think of code complexity like asking: **"How much slower/more memory does my code use when I give it more data?"**

## The Big Idea

#Imagine you're organizing books:
#- **Time Complexity**: How much longer it takes as you add more books
#- **Space Complexity**: How much extra space you need as you add more books

## Big O Notation - The Report Card

#Big O notation describes the upper bound of an algorithm's growth rate. It focuses on the dominant term and ignores constants and lower-order terms.

### Common Time Complexities (Best to Worst):

#1. **O(1) - Constant Time**
#   - Performance doesn't change with input size
#   - Example: Array access by index, hash table lookup


def get_first_element(arr: list[int]) -> int:
    """O(1) - Always one operation regardless of array size"""
    return arr[0]


#2. **O(log n) - Logarithmic Time**
#   - Reduces problem size by half each step
#   - Example: Binary search, balanced tree operations


def binary_search(arr: list[int], target: int, left: int = 0, right: int = None) -> int:
    """O(log n) - Eliminates half the search space each iteration"""
    if right is None:
        right = len(arr) - 1
    
    if left > right:
        return -1
    
    mid = (left + right) // 2
    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binary_search(arr, target, mid + 1, right)
    else:
        return binary_search(arr, target, left, mid - 1)


#3. **O(n) - Linear Time**
#   - Performance scales directly with input size
#   - Example: Single loop through array, linear search


def find_max(arr: list[int]) -> int:
    """O(n) - Must check every element once"""
    max_val = arr[0]
    for num in arr:  # n iterations
        if num > max_val:
            max_val = num
    return max_val


#4. **O(n log n) - Linearithmic Time**
#   - Efficient sorting algorithms
#   - Example: Merge sort, heap sort, efficient sorting


def merge_sort(arr: list[int]) -> list[int]:
    """O(n log n) - Divide and conquer approach"""
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])    # log n divisions
    right = merge_sort(arr[mid:])   # log n divisions
    
    return merge(left, right)       # O(n) merge operation

def merge(left: list[int], right: list[int]) -> list[int]:
    """Helper function for merging - O(n) time"""
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result


#5. **O(n²) - Quadratic Time**
#   - Nested loops over input
#   - Example: Bubble sort, selection sort, naive string matching


def bubble_sort(arr: list[int]) -> list[int]:
    """O(n²) - Nested loops create quadratic complexity"""
    n = len(arr)
    for i in range(n):          # n iterations
        for j in range(0, n - i - 1):  # n iterations (worst case)
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


#6. **O(2ⁿ) - Exponential Time**
#   - Recursive algorithms with multiple recursive calls
#   - Example: Naive Fibonacci, subset generation


def fibonacci_naive(n: int) -> int:
    """O(2^n) - Each call spawns two more calls"""
    if n <= 1:
        return n
    return fibonacci_naive(n - 1) + fibonacci_naive(n - 2)


## Space Complexity Analysis

#Space complexity includes:
#- **Auxiliary Space** - Extra space used by algorithm
#- **Input Space** - Space to store input data

### Examples:


def reverse_array_inplace(arr: list[int]) -> list[int]:
    """O(1) space - Only using a few variables"""
    left, right = 0, len(arr) - 1
    while left < right:
        arr[left], arr[right] = arr[right], arr[left]
        left += 1
        right -= 1
    return arr

def reverse_array_new(arr: list[int]) -> list[int]:
    """O(n) space - Creating new array"""
    return arr[::-1]

def fibonacci_memoized(n: int, memo: dict[int, int] = None) -> int:
    """O(n) space - Storing results in memo dictionary"""
    if memo is None:
        memo = {}
    
    if n in memo:
        return memo[n]
    
    if n <= 1:
        return n
    
    memo[n] = fibonacci_memoized(n - 1, memo) + fibonacci_memoized(n - 2, memo)
    return memo[n]


## Real-World Examples and Applications

### 1. Database Query Optimization

# O(n²) - Inefficient nested loop join
def find_user_orders_naive(users: list[dict], orders: list[dict]) -> dict:
    """Bad approach - checking every order for every user"""
    result = {}
    for user in users:          # n users
        user_orders = []
        for order in orders:    # m orders - O(n*m)
            if order['user_id'] == user['id']:
                user_orders.append(order)
        result[user['id']] = user_orders
    return result

# O(n + m) - Using hash map for efficient lookup
def find_user_orders_optimized(users: list[dict], orders: list[dict]) -> dict:
    """Optimized approach using dictionary grouping"""
    from collections import defaultdict
    
    # Group orders by user_id - O(m)
    orders_by_user = defaultdict(list)
    for order in orders:
        orders_by_user[order['user_id']].append(order)
    
    # Create result - O(n)
    result = {}
    for user in users:
        result[user['id']] = orders_by_user[user['id']]
    
    return result


### 3. API Optimization (Django/DRF)

# O(n) - N+1 query problem
class InefficeintOrderViewSet(viewsets.ModelViewSet):
    """Each order triggers separate user query"""
    serializer_class = OrderSerializer
    
    def list(self, request):
        orders = Order.objects.all()  # 1 query
        serialized = []
        for order in orders:  # n queries for users
            serialized.append({
                'id': order.id,
                'user_name': order.user.name,  # Database hit for each order
                'amount': order.amount
            })
        return Response(serialized)

# O(1) - Optimized with select_related
class OptimizedOrderViewSet(viewsets.ModelViewSet):
    """Single query with JOIN"""
    serializer_class = OrderSerializer
    
    def list(self, request):
        # Single query with JOIN - O(1) database calls
        orders = Order.objects.select_related('user').all()
        serialized = []
        for order in orders:
            serialized.append({
                'id': order.id,
                'user_name': order.user.name,  # No additional query
                'amount': order.amount
            })
        return Response(serialized)


## How to Determine Complexity

### Step-by-Step Analysis:

#1. **Identify the input size** - What parameter determines the "size" of your problem?
#2. **Count operations** - How many basic operations are performed?
#3. **Look for loops** - Each nested loop usually multiplies complexity
#4. **Analyze recursive calls** - Use recurrence relations
#5. **Focus on worst-case** - Big O describes the upper bound

### Example Analysis:

def find_duplicates(arr: list[int]) -> list[int]:
    """Let's analyze this step by step"""
    duplicates = []                    # O(1)
    seen = set()                       # O(1)
    
    for num in arr:                    # O(n) - loop through n elements
        if num in seen:                # O(1) - set lookup
            duplicates.append(num)     # O(1) - append operation
        else:
            seen.add(num)              # O(1) - set add
    
    return duplicates                  # O(1)

# Overall: O(n) time, O(n) space


## Optimization Strategies

### 1. Use Appropriate Data Structures

# Bad: O(n) lookup in list
def check_membership_list(items: list[int], targets: list[int]) -> list[bool]:
    """O(n*m) - checking each target in list"""
    return [target in items for target in targets]

# Good: O(1) lookup in set
def check_membership_set(items: list[int], targets: list[int]) -> list[bool]:
    """O(n + m) - using set for O(1) lookup"""
    item_set = set(items)  # O(n)
    return [target in item_set for target in targets]  # O(m)


### 2. Memoization/Caching

from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci_optimized(n: int) -> int:
    """O(n) time, O(n) space - each number calculated once"""
    if n <= 1:
        return n
    return fibonacci_optimized(n - 1) + fibonacci_optimized(n - 2)


### 3. Early Termination

def linear_search_optimized(arr: list[int], target: int) -> int:
    """Stop as soon as target is found"""
    for i, num in enumerate(arr):
        if num == target:
            return i  # Early termination
    return -1

def all_positive(arr: list[int]) -> bool:
    """Stop at first negative number"""
    for num in arr:
        if num <= 0:
            return False  # Early termination
    return True


## Security Considerations

#When optimizing algorithms, always consider security implications:


# Potential timing attack vulnerability
def unsafe_password_check(stored_hash: str, provided_password: str) -> bool:
    """Vulnerable to timing attacks - comparison time varies"""
    return stored_hash == hash(provided_password)

# Secure constant-time comparison
def secure_password_check(stored_hash: str, provided_password: str) -> bool:
    """Secure comparison - constant time regardless of input"""
    import hmac
    provided_hash = hash(provided_password)
    return hmac.compare_digest(stored_hash, provided_hash)


## Advanced Concepts

### Amortized Analysis
#Some operations have different costs over time:

class DynamicArray:
    """Array that grows dynamically - amortized O(1) append"""
    def __init__(self):
        self.capacity = 1
        self.size = 0
        self.data = [None] * self.capacity
    
    def append(self, item):
        if self.size >= self.capacity:
            self._resize()  # O(n) occasionally
        
        self.data[self.size] = item
        self.size += 1
    
    def _resize(self):
        """Double the capacity - expensive but rare"""
        self.capacity *= 2
        new_data = [None] * self.capacity
        for i in range(self.size):
            new_data[i] = self.data[i]
        self.data = new_data


#Understanding complexity helps you make informed decisions about algorithm choice, data structure selection, and system architecture. Always profile your code in real-world scenarios to validate theoretical analysis!

#Code complexity analysis and optimization is fundamental for writing efficient, scalable applications. Let me break this down systematically with practical examples from your tech stack.

## Understanding Code Complexity

### Time Complexity Analysis
#Time complexity measures how execution time grows with input size. Here's how to analyze it:

# O(1) - Constant time
def get_user_by_id(user_id: int) -> Optional[User]:
    """
    Database lookup with primary key - always constant time
    regardless of table size due to indexing
    """
    return User.objects.get(pk=user_id)

# O(n) - Linear time
def filter_active_users(users: List[User]) -> List[User]:
    """
    Must check every user - time grows linearly with input
    """
    return [user for user in users if user.is_active]

# O(n²) - Quadratic time (avoid this!)
def find_duplicate_emails(users: List[User]) -> List[str]:
    """
    Nested loops - performance degrades quickly with large datasets
    """
    duplicates = []
    for i, user1 in enumerate(users):
        for j, user2 in enumerate(users[i+1:], i+1):
            if user1.email == user2.email:
                duplicates.append(user1.email)
    return duplicates

### Space Complexity Analysis
#Space complexity measures additional memory usage:

# O(1) - Constant space
def sum_array(arr: List[int]) -> int:
    """
    Only uses a single variable regardless of input size
    """
    total = 0
    for num in arr:
        total += num
    return total

# O(n) - Linear space
def reverse_array(arr: List[int]) -> List[int]:
    """
    Creates new array of same size as input
    """
    return arr[::-1]

# O(log n) - Logarithmic space (recursion stack)
def binary_search(arr: List[int], target: int, left: int = 0, right: int = None) -> int:
    """
    Recursive calls create stack frames - depth is log(n)
    """
    if right is None:
        right = len(arr) - 1
    
    if left > right:
        return -1
    
    mid = (left + right) // 2
    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binary_search(arr, target, mid + 1, right)
    else:
        return binary_search(arr, target, left, mid - 1)

## Real-World Optimization Examples

### Django Backend Optimization

# BAD: N+1 Query Problem
def get_user_posts_bad(request):
    """
    This creates N+1 database queries - very inefficient!
    """
    users = User.objects.all()  # 1 query
    result = []
    for user in users:
        posts = user.posts.all()  # N queries (one per user)
        result.append({
            'user': user.username,
            'post_count': posts.count()
        })
    return JsonResponse(result, safe=False)

# GOOD: Optimized with select_related/prefetch_related
def get_user_posts_optimized(request):
    """
    Single query with JOIN - O(1) database calls
    """
    users = User.objects.prefetch_related('posts').all()  # 1 query
    result = []
    for user in users:
        result.append({
            'user': user.username,
            'post_count': user.posts.count()  # No additional query
        })
    return JsonResponse(result, safe=False)

# SECURITY NOTE: Always validate and sanitize input
def search_users(request):
    """
    Secure search with pagination and input validation
    """
    query = request.GET.get('q', '').strip()
    
    # Input validation prevents SQL injection
    if not query or len(query) < 2:
        return JsonResponse({'error': 'Query too short'}, status=400)
    
    # Use Q objects for complex queries, limit results
    users = User.objects.filter(
        Q(username__icontains=query) | Q(email__icontains=query)
    ).select_related('profile')[:50]  # Limit results for performance
    
    return JsonResponse([{
        'id': user.id,
        'username': user.username,
        'email': user.email  # Be careful about exposing sensitive data
    } for user in users], safe=False)


## Advanced Optimization Techniques

### 1. Caching Strategies

# Django with Redis caching
from django.core.cache import cache
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def expensive_computation(request):
    """
    Cache expensive operations to avoid recomputation
    """
    cache_key = f"expensive_data_{request.user.id}"
    result = cache.get(cache_key)
    
    if result is None:
        # Expensive operation here
        result = perform_complex_calculation()
        cache.set(cache_key, result, 60 * 15)  # 15 minutes
    
    return JsonResponse(result)

### 2. Algorithm Optimization

# BAD: Brute force approach - O(n²)
def find_pair_with_sum_bad(arr: List[int], target: int) -> Optional[Tuple[int, int]]:
    """
    Checks every pair - inefficient for large arrays
    """
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] + arr[j] == target:
                return (arr[i], arr[j])
    return None

# GOOD: Hash table approach - O(n)
def find_pair_with_sum_optimized(arr: List[int], target: int) -> Optional[Tuple[int, int]]:
    """
    Uses hash table for O(1) lookups - much faster!
    """
    seen = set()
    for num in arr:
        complement = target - num
        if complement in seen:
            return (complement, num)
        seen.add(num)
    return None

# Real-world example: User recommendation system
def get_user_recommendations(user_id: int, limit: int = 10) -> List[Dict]:
    """
    Optimized recommendation algorithm using precomputed similarities
    """
    # Use precomputed similarity matrix instead of calculating on-demand
    similar_users = cache.get(f"similar_users_{user_id}")
    
    if similar_users is None:
        # Fallback to database query with proper indexing
        similar_users = UserSimilarity.objects.filter(
            user_id=user_id
        ).select_related('similar_user').order_by('-similarity_score')[:50]
        
        cache.set(f"similar_users_{user_id}", similar_users, 3600)
    
    recommendations = []
    for similarity in similar_users[:limit]:
        recommendations.append({
            'user': similarity.similar_user.username,
            'score': similarity.similarity_score,
            'common_interests': similarity.common_interests
        })
    
    return recommendations


## System Design Optimization Principles

### 1. Database Design
#- **Indexing Strategy**: Create indexes on frequently queried columns
#- **Normalization vs Denormalization**: Balance between data integrity and query performance
#- **Sharding**: Distribute data across multiple databases for horizontal scaling

### 2. API Design
#- **Pagination**: Always limit response sizes
#- **Rate Limiting**: Prevent abuse and ensure fair usage
#- **Compression**: Use gzip for large responses
#- **Caching Headers**: Implement proper HTTP caching

### 3. Frontend Performance
#- **Code Splitting**: Load only necessary JavaScript
#- **Lazy Loading**: Defer non-critical resources
#- **Bundle Analysis**: Monitor and optimize bundle sizes
#- **CDN Usage**: Serve static assets from edge locations

#The key is to measure first, optimize second. Use profiling tools, monitor real-world performance, and always consider the trade-offs between code complexity and performance gains. Security should never be compromised for performance - always validate inputs, sanitize outputs, and use parameterized queries.