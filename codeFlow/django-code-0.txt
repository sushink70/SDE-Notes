# DJ-Rest-Auth Documentation Data Structure for AI Training

## MongoDB Collections Schema

### 1. Documentation Pages Collection (`documentation_pages`)

```javascript
{
  _id: ObjectId,
  page_id: "string", // unique identifier like "introduction", "installation"
  title: "string",
  url: "string",
  version: "string", // e.g., "5.0.1", "latest"
  content_type: "string", // "page", "api_reference", "configuration"
  
  // Main content structure
  content: {
    raw_html: "string", // original HTML content
    markdown: "string", // converted markdown
    plain_text: "string", // cleaned text for training
    sections: [
      {
        heading: "string",
        level: "number", // h1=1, h2=2, etc.
        content: "string",
        subsections: [
          {
            heading: "string",
            level: "number",
            content: "string"
          }
        ]
      }
    ],
    code_blocks: [
      {
        language: "string", // python, javascript, bash, etc.
        code: "string",
        description: "string",
        context: "string" // surrounding explanation
      }
    ]
  },
  
  // Metadata for AI training
  metadata: {
    word_count: "number",
    reading_time: "number", // estimated minutes
    difficulty_level: "string", // beginner, intermediate, advanced
    topics: ["string"], // ["authentication", "JWT", "serializers"]
    keywords: ["string"], // extracted keywords
    last_updated: "date",
    crawled_at: "date"
  },
  
  // Navigation and relationships
  navigation: {
    parent_page: "string", // parent page_id
    child_pages: ["string"], // array of child page_ids
    next_page: "string",
    previous_page: "string",
    breadcrumb: ["string"] // navigation path
  },
  
  // AI training specific fields
  training_data: {
    question_answer_pairs: [
      {
        question: "string",
        answer: "string",
        context: "string",
        confidence: "number"
      }
    ],
    summary: "string",
    key_concepts: ["string"],
    examples: [
      {
        title: "string",
        description: "string",
        code: "string",
        output: "string"
      }
    ]
  }
}
```

### 2. Configuration Options Collection (`config_options`)

```javascript
{
  _id: ObjectId,
  option_name: "string", // e.g., "LOGIN_SERIALIZER"
  category: "string", // "serializers", "jwt", "general"
  data_type: "string", // "string", "boolean", "class_path"
  default_value: "mixed",
  description: "string",
  
  usage_examples: [
    {
      code: "string",
      description: "string",
      use_case: "string"
    }
  ],
  
  related_options: ["string"], // array of related config option names
  version_info: {
    introduced_in: "string",
    deprecated_in: "string",
    removed_in: "string"
  },
  
  // For AI training
  common_questions: ["string"],
  troubleshooting: [
    {
      issue: "string",
      solution: "string"
    }
  ]
}
```

### 3. API Endpoints Collection (`api_endpoints`)

```javascript
{
  _id: ObjectId,
  endpoint_path: "string", // "/dj-rest-auth/login/"
  method: "string", // "GET", "POST", "PUT", "DELETE"
  name: "string", // "Login"
  description: "string",
  
  parameters: {
    required: [
      {
        name: "string",
        type: "string",
        description: "string"
      }
    ],
    optional: [
      {
        name: "string",
        type: "string",
        description: "string",
        default: "mixed"
      }
    ]
  },
  
  request_format: {
    content_type: "string",
    example: "object"
  },
  
  response_format: {
    success: {
      status_code: "number",
      example: "object",
      schema: "object"
    },
    error: [
      {
        status_code: "number",
        description: "string",
        example: "object"
      }
    ]
  },
  
  authentication_required: "boolean",
  permissions: ["string"],
  
  code_examples: [
    {
      language: "string", // "curl", "python", "javascript"
      code: "string",
      description: "string"
    }
  ]
}
```

### 4. Code Examples Collection (`code_examples`)

```javascript
{
  _id: ObjectId,
  title: "string",
  description: "string",
  language: "string",
  framework: "string", // "django", "react", "vue"
  category: "string", // "setup", "authentication", "customization"
  
  code: "string",
  explanation: "string",
  use_case: "string",
  
  dependencies: ["string"],
  prerequisites: ["string"],
  
  related_pages: ["string"], // page_ids where this example appears
  tags: ["string"]
}
```

### 5. FAQ Collection (`faq`)

```javascript
{
  _id: ObjectId,
  question: "string",
  answer: "string",
  category: "string",
  difficulty: "string",
  
  related_pages: ["string"],
  related_config: ["string"],
  related_endpoints: ["string"],
  
  code_snippets: [
    {
      language: "string",
      code: "string",
      description: "string"
    }
  ],
  
  upvotes: "number",
  views: "number"
}
```

### 6. Versions Collection (`versions`)

```javascript
{
  _id: ObjectId,
  version: "string",
  release_date: "date",
  is_latest: "boolean",
  is_stable: "boolean",
  
  changelog: [
    {
      type: "string", // "feature", "bugfix", "breaking"
      description: "string"
    }
  ],
  
  documentation_pages: ["string"], // page_ids for this version
  deprecated_features: ["string"],
  new_features: ["string"]
}
```

## Data Extraction Strategy

### 1. Web Scraping Script Structure

```python
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from pymongo import MongoClient
import re
from datetime import datetime

class DjRestAuthScraper:
    def __init__(self, base_url, mongo_connection):
        self.base_url = base_url
        self.mongo = mongo_connection
        self.session = None
        
    async def scrape_documentation(self):
        # Implementation for scraping all pages
        pass
        
    def extract_content_structure(self, html):
        # Parse HTML and extract structured content
        pass
        
    def generate_training_data(self, content):
        # Generate Q&A pairs and summaries
        pass
```

### 2. Content Processing Pipeline

1. **HTML Parsing**: Extract text, code blocks, headings, links
2. **Content Cleaning**: Remove navigation, ads, irrelevant content
3. **Structure Analysis**: Identify sections, subsections, code examples
4. **Relationship Mapping**: Link related pages, configs, endpoints
5. **Training Data Generation**: Create Q&A pairs, summaries, examples

### 3. AI Training Data Preparation

```javascript
// Training dataset format
{
  input: "How do I configure JWT authentication in dj-rest-auth?",
  output: "To configure JWT authentication, set REST_USE_JWT = True in settings...",
  context: "Configuration documentation section",
  metadata: {
    source_page: "configuration",
    confidence: 0.95,
    topics: ["JWT", "authentication", "configuration"]
  }
}
```

## Documentation Generation System

### 1. Automated Documentation Builder

```python
class DocumentationBuilder:
    def __init__(self, mongo_client):
        self.db = mongo_client.dj_rest_auth_docs
        
    def generate_markdown_docs(self):
        # Generate markdown from MongoDB data
        pass
        
    def create_api_reference(self):
        # Generate API documentation
        pass
        
    def build_searchable_index(self):
        # Create search indexes
        pass
```

### 2. Documentation Templates

- **Installation Guide**: Step-by-step setup instructions
- **Configuration Reference**: All config options with examples
- **API Documentation**: Complete endpoint documentation
- **Examples Gallery**: Code examples by use case
- **Troubleshooting Guide**: Common issues and solutions

### 3. Search & Query System

```python
# MongoDB text search indexes
db.documentation_pages.create_index([
    ("content.plain_text", "text"),
    ("title", "text"),
    ("metadata.keywords", "text")
])

# Example query for AI training
def find_relevant_content(query):
    return db.documentation_pages.find({
        "$text": {"$search": query}
    }).sort([("score", {"$meta": "textScore"})])
```

## Implementation Steps

1. **Set up MongoDB with the above schema**
2. **Create web scraping script to collect all documentation**
3. **Implement content processing pipeline**
4. **Generate training datasets for AI model**
5. **Build documentation generation system**
6. **Create search and query interfaces**
7. **Set up automated updates for new versions**

This structure provides a comprehensive foundation for training an AI model on dj-rest-auth documentation while maintaining the ability to generate updated documentation from the stored data.

---

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from pymongo import MongoClient
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
import json
from typing import List, Dict, Optional
import hashlib

class DjRestAuthDocumentationScraper:
    def __init__(self, mongodb_connection_string: str, base_url: str = "https://dj-rest-auth.readthedocs.io/en/latest/"):
        self.base_url = base_url
        self.client = MongoClient(mongodb_connection_string)
        self.db = self.client.dj_rest_auth_docs
        self.session = None
        
        # Initialize collections
        self.pages_collection = self.db.documentation_pages
        self.config_collection = self.db.config_options
        self.api_collection = self.db.api_endpoints
        self.examples_collection = self.db.code_examples
        self.faq_collection = self.db.faq
        self.versions_collection = self.db.versions
        
        # Create indexes for better query performance
        self._create_indexes()
        
    def _create_indexes(self):
        """Create MongoDB indexes for efficient querying"""
        # Text search indexes
        self.pages_collection.create_index([
            ("content.plain_text", "text"),
            ("title", "text"),
            ("metadata.keywords", "text")
        ])
        
        # Unique indexes
        self.pages_collection.create_index("page_id", unique=True)
        self.config_collection.create_index("option_name", unique=True)
        self.api_collection.create_index([("endpoint_path", 1), ("method", 1)], unique=True)
        
        # Query optimization indexes
        self.pages_collection.create_index("metadata.topics")
        self.pages_collection.create_index("version")
        
    async def scrape_all_documentation(self):
        """Main method to scrape all documentation"""
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # Start with the main page
            main_page = await self._fetch_page(self.base_url)
            if main_page:
                await self._process_main_page(main_page)
                
            # Discover and scrape all linked pages
            await self._discover_and_scrape_pages()
            
            # Process special sections
            await self._process_configuration_options()
            await self._process_api_endpoints()
            await self._extract_code_examples()
            
        print("Documentation scraping completed!")
        
    async def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a single page"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    return BeautifulSoup(html, 'html.parser')
                else:
                    print(f"Failed to fetch {url}: {response.status}")
                    return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
            
    async def _process_main_page(self, soup: BeautifulSoup):
        """Process the main documentation page"""
        # Extract table of contents and navigation structure
        toc_links = soup.find_all('a', href=True)
        
        page_links = []
        for link in toc_links:
            href = link.get('href')
            if href and href.endswith('.html'):
                full_url = urljoin(self.base_url, href)
                page_links.append({
                    'url': full_url,
                    'title': link.get_text().strip(),
                    'page_id': href.replace('.html', '')
                })
                
        # Store discovered pages for processing
        self.discovered_pages = page_links
        
    async def _discover_and_scrape_pages(self):
        """Discover and scrape all documentation pages"""
        for page_info in self.discovered_pages:
            soup = await self._fetch_page(page_info['url'])
            if soup:
                await self._process_documentation_page(soup, page_info)
                
    async def _process_documentation_page(self, soup: BeautifulSoup, page_info: Dict):
        """Process a single documentation page"""
        # Extract main content area
        main_content = soup.find('div', class_='document') or soup.find('main') or soup.body
        
        if not main_content:
            return
            
        # Extract structured content
        content_data = self._extract_content_structure(main_content)
        
        # Generate page document
        page_doc = {
            '_id': self._generate_id(page_info['page_id']),
            'page_id': page_info['page_id'],
            'title': page_info['title'],
            'url': page_info['url'],
            'version': self._extract_version_from_url(page_info['url']),
            'content_type': self._determine_content_type(page_info['page_id']),
            'content': content_data,
            'metadata': self._generate_metadata(content_data),
            'navigation': self._extract_navigation(soup),
            'training_data': await self._generate_training_data(content_data),
            'crawled_at': datetime.utcnow()
        }
        
        # Store in MongoDB
        self.pages_collection.replace_one(
            {'page_id': page_info['page_id']},
            page_doc,
            upsert=True
        )
        
        print(f"Processed page: {page_info['title']}")
        
    def _extract_content_structure(self, content_element) -> Dict:
        """Extract structured content from HTML"""
        content_data = {
            'raw_html': str(content_element),
            'plain_text': content_element.get_text(),
            'sections': [],
            'code_blocks': []
        }
        
        # Extract sections and headings
        current_section = None
        for element in content_element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'code']):
            
            if element.name.startswith('h'):
                # New section
                if current_section:
                    content_data['sections'].append(current_section)
                    
                current_section = {
                    'heading': element.get_text().strip(),
                    'level': int(element.name[1]),
                    'content': '',
                    'subsections': []
                }
                
            elif element.name == 'p' and current_section:
                current_section['content'] += element.get_text() + '\n'
                
            elif element.name in ['pre', 'code']:
                # Extract code blocks
                code_text = element.get_text()
                if len(code_text.strip()) > 10:  # Filter out small code snippets
                    code_block = {
                        'language': self._detect_code_language(element),
                        'code': code_text,
                        'description': self._extract_code_description(element),
                        'context': current_section['heading'] if current_section else ''
                    }
                    content_data['code_blocks'].append(code_block)
                    
        # Add last section
        if current_section:
            content_data['sections'].append(current_section)
            
        # Generate markdown
        content_data['markdown'] = self._html_to_markdown(content_element)
        
        return content_data
        
    def _detect_code_language(self, code_element) -> str:
        """Detect programming language from code block"""
        # Check for class attributes that indicate language
        classes = code_element.get('class', [])
        for cls in classes:
            if cls.startswith('language-'):
                return cls.replace('language-', '')
            elif cls in ['python', 'javascript', 'bash', 'json', 'yaml']:
                return cls
                
        # Heuristic detection based on content
        code_text = code_element.get_text().lower()
        if 'def ' in code_text or 'import ' in code_text:
            return 'python'
        elif 'function' in code_text or 'const ' in code_text:
            return 'javascript'
        elif code_text.startswith('curl ') or code_text.startswith('$ '):
            return 'bash'
        elif code_text.startswith('{') and code_text.endswith('}'):
            return 'json'
            
        return 'text'
        
    def _extract_code_description(self, code_element) -> str:
        """Extract description for code block from surrounding text"""
        # Look for preceding paragraph or comment
        prev_sibling = code_element.find_previous_sibling(['p', 'div'])
        if prev_sibling:
            return prev_sibling.get_text().strip()[:200]  # Limit length
        return ''
        
    def _html_to_markdown(self, html_element) -> str:
        """Convert HTML to markdown"""
        # Simple conversion - can be enhanced with proper HTML to Markdown library
        text = html_element.get_text()
        # Basic markdown formatting
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Clean up whitespace
        return text.strip()
        
    def _generate_metadata(self, content_data: Dict) -> Dict:
        """Generate metadata for the page"""
        plain_text = content_data['plain_text']
        
        return {
            'word_count': len(plain_text.split()),
            'reading_time': max(1, len(plain_text.split()) // 200),  # Assume 200 WPM
            'difficulty_level': self._assess_difficulty(content_data),
            'topics': self._extract_topics(plain_text),
            'keywords': self._extract_keywords(plain_text),
            'last_updated': datetime.utcnow()
        }
        
    def _assess_difficulty(self, content_data: Dict) -> str:
        """Assess difficulty level based on content"""
        # Simple heuristic based on code complexity and technical terms
        code_blocks = len(content_data['code_blocks'])
        technical_terms = ['serializer', 'authentication', 'JWT', 'API', 'configuration']
        
        text = content_data['plain_text'].lower()
        technical_count = sum(1 for term in technical_terms if term in text)
        
        if code_blocks >= 3 or technical_count >= 5:
            return 'advanced'
        elif code_blocks >= 1 or technical_count >= 2:
            return 'intermediate'
        else:
            return 'beginner'
            
    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from text"""
        topics = []
        topic_keywords = {
            'authentication': ['auth', 'login', 'logout', 'token', 'session'],
            'JWT': ['jwt', 'json web token', 'bearer'],
            'configuration': ['config', 'setting', 'option'],
            'API': ['endpoint', 'request', 'response', 'api'],
            'serialization': ['serializer', 'serialize', 'json'],
            'registration': ['register', 'signup', 'account'],
            'social': ['social', 'oauth', 'github', 'google', 'facebook']
        }
        
        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
                
        return topics
        
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction - can be enhanced with NLP libraries
        words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
        word_freq = {}
        
        for word in words:
            if word not in ['with', 'this', 'that', 'have', 'will', 'from', 'they']:
                word_freq[word] = word_freq.get(word, 0) + 1
                
        # Return top keywords
        return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
    def _extract_navigation(self, soup: BeautifulSoup) -> Dict:
        """Extract navigation information"""
        nav_data = {
            'parent_page': None,
            'child_pages': [],
            'next_page': None,
            'previous_page': None,
            'breadcrumb': []
        }
        
        # Extract breadcrumb if available
        breadcrumb = soup.find('nav', class_='breadcrumb') or soup.find('ol', class_='breadcrumb')
        if breadcrumb:
            nav_data['breadcrumb'] = [link.get_text().strip() for link in breadcrumb.find_all('a')]
            
        # Extract next/previous links
        nav_links = soup.find_all('a', href=True)
        for link in nav_links:
            text = link.get_text().lower()
            if 'next' in text:
                nav_data['next_page'] = link.get('href')
            elif 'previous' in text or 'prev' in text:
                nav_data['previous_page'] = link.get('href')
                
        return nav_data
        
    async def _generate_training_data(self, content_data: Dict) -> Dict:
        """Generate training data for AI model"""
        training_data = {
            'question_answer_pairs': [],
            'summary': '',
            'key_concepts': [],
            'examples': []
        }
        
        # Generate Q&A pairs from sections
        for section in content_data['sections']:
            if len(section['content']) > 100:  # Only process substantial content
                # Generate questions based on section headings
                questions = self._generate_questions_from_heading(section['heading'])
                for question in questions:
                    training_data['question_answer_pairs'].append({
                        'question': question,
                        'answer': section['content'][:500],  # Limit answer length
                        'context': section['heading'],
                        'confidence': 0.8
                    })
                    
        # Generate summary
        training_data['summary'] = self._generate_summary(content_data['plain_text'])
        
        # Extract key concepts
        training_data['key_concepts'] = self._extract_key_concepts(content_data)
        
        # Process code examples
        for code_block in content_data['code_blocks']:
            if len(code_block['code']) > 50:
                training_data['examples'].append({
                    'title': f"{code_block['language'].title()} Example",
                    'description': code_block['description'],
                    'code': code_block['code'],
                    'output': ''  # Could be enhanced to include expected output
                })
                
        return training_data
        
    def _generate_questions_from_heading(self, heading: str) -> List[str]:
        """Generate potential questions from section headings"""
        questions = []
        heading_lower = heading.lower()
        
        # Template-based question generation
        if 'configuration' in heading_lower:
            questions.append(f"How do I configure {heading}?")
            questions.append(f"What are the configuration options for {heading}?")
        elif 'installation' in heading_lower:
            questions.append(f"How do I install {heading}?")
            questions.append(f"What are the installation steps for {heading}?")
        elif 'api' in heading_lower or 'endpoint' in heading_lower:
            questions.append(f"How do I use the {heading} API?")
            questions.append(f"What parameters does {heading} accept?")
        else:
            questions.append(f"What is {heading}?")
            questions.append(f"How does {heading} work?")
            
        return questions
        
    def _generate_summary(self, text: str) -> str:
        """Generate a summary of the content"""
        # Simple extractive summarization - first few sentences
        sentences = re.split(r'[.!?]+', text)
        summary_sentences = []
        
        for sentence in sentences[:3]:  # Take first 3 sentences
            if len(sentence.strip()) > 20:
                summary_sentences.append(sentence.strip())
                
        return ' '.join(summary_sentences)[:300]  # Limit summary length
        
    def _extract_key_concepts(self, content_data: Dict) -> List[str]:
        """Extract key concepts from content"""
        concepts = set()
        
        # Extract from headings
        for section in content_data['sections']:
            heading_words = section['heading'].split()
            concepts.update(word for word in heading_words if len(word) > 3)
            
        # Extract from code blocks
        for code_block in content_data['code_blocks']:
            if code_block['language'] == 'python':
                # Extract class and function names
                code_text = code_block['code']
                classes = re.findall(r'class\s+(\w+)', code_text)
                functions = re.findall(r'def\s+(\w+)', code_text)
                concepts.update(classes + functions)
                
        return list(concepts)[:10]  # Limit to top 10 concepts
        
    async def _process_configuration_options(self):
        """Extract and process configuration options"""
        # Find configuration pages
        config_pages = self.pages_collection.find({'content_type': 'configuration'})
        
        for page in config_pages:
            content = page['content']['plain_text']
            
            # Extract configuration options using regex
            config_pattern = r'([A-Z_]+)\s*[-=]\s*(.+?)(?=\n[A-Z_]+|\n\n|\Z)'
            matches = re.findall(config_pattern, content, re.DOTALL)
            
            for option_name, description in matches:
                if len(option_name) > 3:  # Filter out short matches
                    config_doc = {
                        '_id': self._generate_id(option_name),
                        'option_name': option_name,
                        'category': self._categorize_config_option(option_name),
                        'data_type': self._infer_data_type(description),
                        'default_value': self._extract_default_value(description),
                        'description': description.strip()[:500],
                        'usage_examples': [],
                        'related_options': [],
                        'version_info': {
                            'introduced_in': 'unknown',
                            'deprecated_in': None,
                            'removed_in': None
                        },
                        'common_questions': [],
                        'troubleshooting': []
                    }
                    
                    self.config_collection.replace_one(
                        {'option_name': option_name},
                        config_doc,
                        upsert=True
                    )
                    
    def _categorize_config_option(self, option_name: str) -> str:
        """Categorize configuration option"""
        name_lower = option_name.lower()
        if 'jwt' in name_lower:
            return 'jwt'
        elif 'serializer' in name_lower:
            return 'serializers'
        elif 'password' in name_lower:
            return 'password'
        elif 'token' in name_lower:
            return 'tokens'
        elif 'register' in name_lower:
            return 'registration'
        else:
            return 'general'
            
    def _infer_data_type(self, description: str) -> str:
        """Infer data type from description"""
        desc_lower = description.lower()
        if 'true' in desc_lower or 'false' in desc_lower or 'boolean' in desc_lower:
            return 'boolean'
        elif 'string' in desc_lower or 'path'
		
		---
		
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from pymongo import MongoClient
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
import json
from typing import List, Dict, Optional
import hashlib

class DjRestAuthDocumentationScraper:
    def __init__(self, mongodb_connection_string: str, base_url: str = "https://dj-rest-auth.readthedocs.io/en/latest/"):
        self.base_url = base_url
        self.client = MongoClient(mongodb_connection_string)
        self.db = self.client.dj_rest_auth_docs
        self.session = None
        
        # Initialize collections
        self.pages_collection = self.db.documentation_pages
        self.config_collection = self.db.config_options
        self.api_collection = self.db.api_endpoints
        self.examples_collection = self.db.code_examples
        self.faq_collection = self.db.faq
        self.versions_collection = self.db.versions
        
        # Create indexes for better query performance
        self._create_indexes()
        
    def _create_indexes(self):
        """Create MongoDB indexes for efficient querying"""
        # Text search indexes
        self.pages_collection.create_index([
            ("content.plain_text", "text"),
            ("title", "text"),
            ("metadata.keywords", "text")
        ])
        
        # Unique indexes
        self.pages_collection.create_index("page_id", unique=True)
        self.config_collection.create_index("option_name", unique=True)
        self.api_collection.create_index([("endpoint_path", 1), ("method", 1)], unique=True)
        
        # Query optimization indexes
        self.pages_collection.create_index("metadata.topics")
        self.pages_collection.create_index("version")
        
    async def scrape_all_documentation(self):
        """Main method to scrape all documentation"""
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # Start with the main page
            main_page = await self._fetch_page(self.base_url)
            if main_page:
                await self._process_main_page(main_page)
                
            # Discover and scrape all linked pages
            await self._discover_and_scrape_pages()
            
            # Process special sections
            await self._process_configuration_options()
            await self._process_api_endpoints()
            await self._extract_code_examples()
            
        print("Documentation scraping completed!")
        
    async def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a single page"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    return BeautifulSoup(html, 'html.parser')
                else:
                    print(f"Failed to fetch {url}: {response.status}")
                    return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
            
    async def _process_main_page(self, soup: BeautifulSoup):
        """Process the main documentation page"""
        # Extract table of contents and navigation structure
        toc_links = soup.find_all('a', href=True)
        
        page_links = []
        for link in toc_links:
            href = link.get('href')
            if href and href.endswith('.html'):
                full_url = urljoin(self.base_url, href)
                page_links.append({
                    'url': full_url,
                    'title': link.get_text().strip(),
                    'page_id': href.replace('.html', '')
                })
                
        # Store discovered pages for processing
        self.discovered_pages = page_links
        
    async def _discover_and_scrape_pages(self):
        """Discover and scrape all documentation pages"""
        for page_info in self.discovered_pages:
            soup = await self._fetch_page(page_info['url'])
            if soup:
                await self._process_documentation_page(soup, page_info)
                
    async def _process_documentation_page(self, soup: BeautifulSoup, page_info: Dict):
        """Process a single documentation page"""
        # Extract main content area
        main_content = soup.find('div', class_='document') or soup.find('main') or soup.body
        
        if not main_content:
            return
            
        # Extract structured content
        content_data = self._extract_content_structure(main_content)
        
        # Generate page document
        page_doc = {
            '_id': self._generate_id(page_info['page_id']),
            'page_id': page_info['page_id'],
            'title': page_info['title'],
            'url': page_info['url'],
            'version': self._extract_version_from_url(page_info['url']),
            'content_type': self._determine_content_type(page_info['page_id']),
            'content': content_data,
            'metadata': self._generate_metadata(content_data),
            'navigation': self._extract_navigation(soup),
            'training_data': await self._generate_training_data(content_data),
            'crawled_at': datetime.utcnow()
        }
        
        # Store in MongoDB
        self.pages_collection.replace_one(
            {'page_id': page_info['page_id']},
            page_doc,
            upsert=True
        )
        
        print(f"Processed page: {page_info['title']}")
        
    def _extract_content_structure(self, content_element) -> Dict:
        """Extract structured content from HTML"""
        content_data = {
            'raw_html': str(content_element),
            'plain_text': content_element.get_text(),
            'sections': [],
            'code_blocks': []
        }
        
        # Extract sections and headings
        current_section = None
        for element in content_element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'code']):
            
            if element.name.startswith('h'):
                # New section
                if current_section:
                    content_data['sections'].append(current_section)
                    
                current_section = {
                    'heading': element.get_text().strip(),
                    'level': int(element.name[1]),
                    'content': '',
                    'subsections': []
                }
                
            elif element.name == 'p' and current_section:
                current_section['content'] += element.get_text() + '\n'
                
            elif element.name in ['pre', 'code']:
                # Extract code blocks
                code_text = element.get_text()
                if len(code_text.strip()) > 10:  # Filter out small code snippets
                    code_block = {
                        'language': self._detect_code_language(element),
                        'code': code_text,
                        'description': self._extract_code_description(element),
                        'context': current_section['heading'] if current_section else ''
                    }
                    content_data['code_blocks'].append(code_block)
                    
        # Add last section
        if current_section:
            content_data['sections'].append(current_section)
            
        # Generate markdown
        content_data['markdown'] = self._html_to_markdown(content_element)
        
        return content_data
        
    def _detect_code_language(self, code_element) -> str:
        """Detect programming language from code block"""
        # Check for class attributes that indicate language
        classes = code_element.get('class', [])
        for cls in classes:
            if cls.startswith('language-'):
                return cls.replace('language-', '')
            elif cls in ['python', 'javascript', 'bash', 'json', 'yaml']:
                return cls
                
        # Heuristic detection based on content
        code_text = code_element.get_text().lower()
        if 'def ' in code_text or 'import ' in code_text:
            return 'python'
        elif 'function' in code_text or 'const ' in code_text:
            return 'javascript'
        elif code_text.startswith('curl ') or code_text.startswith('$ '):
            return 'bash'
        elif code_text.startswith('{') and code_text.endswith('}'):
            return 'json'
            
        return 'text'
        
    def _extract_code_description(self, code_element) -> str:
        """Extract description for code block from surrounding text"""
        # Look for preceding paragraph or comment
        prev_sibling = code_element.find_previous_sibling(['p', 'div'])
        if prev_sibling:
            return prev_sibling.get_text().strip()[:200]  # Limit length
        return ''
        
    def _html_to_markdown(self, html_element) -> str:
        """Convert HTML to markdown"""
        # Simple conversion - can be enhanced with proper HTML to Markdown library
        text = html_element.get_text()
        # Basic markdown formatting
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Clean up whitespace
        return text.strip()
        
    def _generate_metadata(self, content_data: Dict) -> Dict:
        """Generate metadata for the page"""
        plain_text = content_data['plain_text']
        
        return {
            'word_count': len(plain_text.split()),
            'reading_time': max(1, len(plain_text.split()) // 200),  # Assume 200 WPM
            'difficulty_level': self._assess_difficulty(content_data),
            'topics': self._extract_topics(plain_text),
            'keywords': self._extract_keywords(plain_text),
            'last_updated': datetime.utcnow()
        }
        
    def _assess_difficulty(self, content_data: Dict) -> str:
        """Assess difficulty level based on content"""
        # Simple heuristic based on code complexity and technical terms
        code_blocks = len(content_data['code_blocks'])
        technical_terms = ['serializer', 'authentication', 'JWT', 'API', 'configuration']
        
        text = content_data['plain_text'].lower()
        technical_count = sum(1 for term in technical_terms if term in text)
        
        if code_blocks >= 3 or technical_count >= 5:
            return 'advanced'
        elif code_blocks >= 1 or technical_count >= 2:
            return 'intermediate'
        else:
            return 'beginner'
            
    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from text"""
        topics = []
        topic_keywords = {
            'authentication': ['auth', 'login', 'logout', 'token', 'session'],
            'JWT': ['jwt', 'json web token', 'bearer'],
            'configuration': ['config', 'setting', 'option'],
            'API': ['endpoint', 'request', 'response', 'api'],
            'serialization': ['serializer', 'serialize', 'json'],
            'registration': ['register', 'signup', 'account'],
            'social': ['social', 'oauth', 'github', 'google', 'facebook']
        }
        
        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
                
        return topics
        
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction - can be enhanced with NLP libraries
        words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
        word_freq = {}
        
        for word in words:
            if word not in ['with', 'this', 'that', 'have', 'will', 'from', 'they']:
                word_freq[word] = word_freq.get(word, 0) + 1
                
        # Return top keywords
        return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
    def _extract_navigation(self, soup: BeautifulSoup) -> Dict:
        """Extract navigation information"""
        nav_data = {
            'parent_page': None,
            'child_pages': [],
            'next_page': None,
            'previous_page': None,
            'breadcrumb': []
        }
        
        # Extract breadcrumb if available
        breadcrumb = soup.find('nav', class_='breadcrumb') or soup.find('ol', class_='breadcrumb')
        if breadcrumb:
            nav_data['breadcrumb'] = [link.get_text().strip() for link in breadcrumb.find_all('a')]
            
        # Extract next/previous links
        nav_links = soup.find_all('a', href=True)
        for link in nav_links:
            text = link.get_text().lower()
            if 'next' in text:
                nav_data['next_page'] = link.get('href')
            elif 'previous' in text or 'prev' in text:
                nav_data['previous_page'] = link.get('href')
                
        return nav_data
        
    async def _generate_training_data(self, content_data: Dict) -> Dict:
        """Generate training data for AI model"""
        training_data = {
            'question_answer_pairs': [],
            'summary': '',
            'key_concepts': [],
            'examples': []
        }
        
        # Generate Q&A pairs from sections
        for section in content_data['sections']:
            if len(section['content']) > 100:  # Only process substantial content
                # Generate questions based on section headings
                questions = self._generate_questions_from_heading(section['heading'])
                for question in questions:
                    training_data['question_answer_pairs'].append({
                        'question': question,
                        'answer': section['content'][:500],  # Limit answer length
                        'context': section['heading'],
                        'confidence': 0.8
                    })
                    
        # Generate summary
        training_data['summary'] = self._generate_summary(content_data['plain_text'])
        
        # Extract key concepts
        training_data['key_concepts'] = self._extract_key_concepts(content_data)
        
        # Process code examples
        for code_block in content_data['code_blocks']:
            if len(code_block['code']) > 50:
                training_data['examples'].append({
                    'title': f"{code_block['language'].title()} Example",
                    'description': code_block['description'],
                    'code': code_block['code'],
                    'output': ''  # Could be enhanced to include expected output
                })
                
        return training_data
        
    def _generate_questions_from_heading(self, heading: str) -> List[str]:
        """Generate potential questions from section headings"""
        questions = []
        heading_lower = heading.lower()
        
        # Template-based question generation
        if 'configuration' in heading_lower:
            questions.append(f"How do I configure {heading}?")
            questions.append(f"What are the configuration options for {heading}?")
        elif 'installation' in heading_lower:
            questions.append(f"How do I install {heading}?")
            questions.append(f"What are the installation steps for {heading}?")
        elif 'api' in heading_lower or 'endpoint' in heading_lower:
            questions.append(f"How do I use the {heading} API?")
            questions.append(f"What parameters does {heading} accept?")
        else:
            questions.append(f"What is {heading}?")
            questions.append(f"How does {heading} work?")
            
        return questions
        
    def _generate_summary(self, text: str) -> str:
        """Generate a summary of the content"""
        # Simple extractive summarization - first few sentences
        sentences = re.split(r'[.!?]+', text)
        summary_sentences = []
        
        for sentence in sentences[:3]:  # Take first 3 sentences
            if len(sentence.strip()) > 20:
                summary_sentences.append(sentence.strip())
                
        return ' '.join(summary_sentences)[:300]  # Limit summary length
        
    def _extract_key_concepts(self, content_data: Dict) -> List[str]:
        """Extract key concepts from content"""
        concepts = set()
        
        # Extract from headings
        for section in content_data['sections']:
            heading_words = section['heading'].split()
            concepts.update(word for word in heading_words if len(word) > 3)
            
        # Extract from code blocks
        for code_block in content_data['code_blocks']:
            if code_block['language'] == 'python':
                # Extract class and function names
                code_text = code_block['code']
                classes = re.findall(r'class\s+(\w+)', code_text)
                functions = re.findall(r'def\s+(\w+)', code_text)
                concepts.update(classes + functions)
                
        return list(concepts)[:10]  # Limit to top 10 concepts
        
    async def _process_configuration_options(self):
        """Extract and process configuration options"""
        # Find configuration pages
        config_pages = self.pages_collection.find({'content_type': 'configuration'})
        
        for page in config_pages:
            content = page['content']['plain_text']
            
            # Extract configuration options using regex
            config_pattern = r'([A-Z_]+)\s*[-=]\s*(.+?)(?=\n[A-Z_]+|\n\n|\Z)'
            matches = re.findall(config_pattern, content, re.DOTALL)
            
            for option_name, description in matches:
                if len(option_name) > 3:  # Filter out short matches
                    config_doc = {
                        '_id': self._generate_id(option_name),
                        'option_name': option_name,
                        'category': self._categorize_config_option(option_name),
                        'data_type': self._infer_data_type(description),
                        'default_value': self._extract_default_value(description),
                        'description': description.strip()[:500],
                        'usage_examples': [],
                        'related_options': [],
                        'version_info': {
                            'introduced_in': 'unknown',
                            'deprecated_in': None,
                            'removed_in': None
                        },
                        'common_questions': [],
                        'troubleshooting': []
                    }
                    
                    self.config_collection.replace_one(
                        {'option_name': option_name},
                        config_doc,
                        upsert=True
                    )
                    
    def _categorize_config_option(self, option_name: str) -> str:
        """Categorize configuration option"""
        name_lower = option_name.lower()
        if 'jwt' in name_lower:
            return 'jwt'
        elif 'serializer' in name_lower:
            return 'serializers'
        elif 'password' in name_lower:
            return 'password'
        elif 'token' in name_lower:
            return 'tokens'
        elif 'register' in name_lower:
            return 'registration'
        else:
            return 'general'
            
    def _infer_data_type(self, description: str) -> str:
        """Infer data type from description"""
        desc_lower = description.lower()
        if 'true' in desc_lower or 'false' in desc_lower or 'boolean' in desc_lower:
            return 'boolean'
        elif 'string' in desc_lower or 'path' in desc_lower or 'name' in desc_lower:
            return 'string'
        elif 'number' in desc_lower or 'integer' in desc_lower or 'int' in desc_lower:
            return 'integer'
        elif 'list' in desc_lower or 'array' in desc_lower:
            return 'list'
        elif 'dict' in desc_lower or 'object' in desc_lower:
            return 'object'
        elif 'class' in desc_lower:
            return 'class_path'
        else:
            return 'string'  # Default to string
            
    def _extract_default_value(self, description: str):
        """Extract default value from description"""
        # Look for patterns like "Default: value" or "default is value"
        default_patterns = [
            r'default:?\s*([^\n.]+)',
            r'default\s+is\s+([^\n.]+)',
            r'defaults?\s+to\s+([^\n.]+)'
        ]
        
        for pattern in default_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                default_val = match.group(1).strip()
                # Try to convert to appropriate type
                if default_val.lower() in ['true', 'false']:
                    return default_val.lower() == 'true'
                elif default_val.isdigit():
                    return int(default_val)
                elif default_val in ['None', 'null', 'NULL']:
                    return None
                else:
                    return default_val
                    
        return None
        
    async def _process_api_endpoints(self):
        """Extract and process API endpoints"""
        # Find API documentation pages
        api_pages = self.pages_collection.find({'content_type': 'api_reference'})
        
        for page in api_pages:
            content = page['content']['plain_text']
            
            # Extract API endpoints using regex patterns
            endpoint_patterns = [
                r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-]+)',
                r'URL:\s*([/\w\-]+)',
                r'Endpoint:\s*([/\w\-]+)'
            ]
            
            for pattern in endpoint_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                
                for match in matches:
                    if isinstance(match, tuple) and len(match) == 2:
                        method, endpoint = match
                    else:
                        method = 'GET'  # Default method
                        endpoint = match if isinstance(match, str) else match[0]
                        
                    if endpoint.startswith('/'):
                        api_doc = {
                            '_id': self._generate_id(f"{method}_{endpoint}"),
                            'endpoint_path': endpoint,
                            'method': method.upper(),
                            'name': self._generate_endpoint_name(endpoint),
                            'description': self._extract_endpoint_description(content, endpoint),
                            'parameters': self._extract_parameters(content, endpoint),
                            'request_format': self._extract_request_format(content, endpoint),
                            'response_format': self._extract_response_format(content, endpoint),
                            'authentication_required': self._check_auth_required(content, endpoint),
                            'permissions': self._extract_permissions(content, endpoint),
                            'code_examples': self._extract_endpoint_examples(content, endpoint)
                        }
                        
                        self.api_collection.replace_one(
                            {'endpoint_path': endpoint, 'method': method.upper()},
                            api_doc,
                            upsert=True
                        )
                        
    def _generate_endpoint_name(self, endpoint: str) -> str:
        """Generate a human-readable name for endpoint"""
        parts = endpoint.strip('/').split('/')
        if parts:
            return ' '.join(word.capitalize() for word in parts[-1].split('-'))
        return 'Unknown Endpoint'
        
    def _extract_endpoint_description(self, content: str, endpoint: str) -> str:
        """Extract description for an endpoint"""
        # Look for text near the endpoint definition
        lines = content.split('\n')
        endpoint_line_idx = None
        
        for i, line in enumerate(lines):
            if endpoint in line:
                endpoint_line_idx = i
                break
                
        if endpoint_line_idx is not None:
            # Get surrounding lines for description
            start_idx = max(0, endpoint_line_idx - 2)
            end_idx = min(len(lines), endpoint_line_idx + 3)
            context_lines = lines[start_idx:end_idx]
            return ' '.join(line.strip() for line in context_lines if line.strip())[:300]
            
        return ''
        
    def _extract_parameters(self, content: str, endpoint: str) -> Dict:
        """Extract parameters for an endpoint"""
        parameters = {'required': [], 'optional': []}
        
        # Look for parameter documentation patterns
        param_patterns = [
            r'(?:Parameters?|Fields?):\s*(.*?)(?=\n\n|\nResponse|\nExample|\Z)',
            r'Request\s+Body:\s*(.*?)(?=\n\n|\nResponse|\nExample|\Z)'
        ]
        
        for pattern in param_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                param_text = match.group(1)
                
                # Extract individual parameters
                param_lines = param_text.split('\n')
                for line in param_lines:
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            param_name = parts[0].strip()
                            param_desc = parts[1].strip()
                            
                            param_obj = {
                                'name': param_name,
                                'type': self._infer_param_type(param_desc),
                                'description': param_desc
                            }
                            
                            if 'required' in param_desc.lower() or 'mandatory' in param_desc.lower():
                                parameters['required'].append(param_obj)
                            else:
                                parameters['optional'].append(param_obj)
                                
        return parameters
        
    def _infer_param_type(self, description: str) -> str:
        """Infer parameter type from description"""
        desc_lower = description.lower()
        if 'string' in desc_lower:
            return 'string'
        elif 'integer' in desc_lower or 'number' in desc_lower:
            return 'integer'
        elif 'boolean' in desc_lower:
            return 'boolean'
        elif 'array' in desc_lower or 'list' in desc_lower:
            return 'array'
        elif 'object' in desc_lower:
            return 'object'
        else:
            return 'string'  # Default
            
    def _extract_request_format(self, content: str, endpoint: str) -> Dict:
        """Extract request format information"""
        request_format = {'content_type': 'application/json', 'example': {}}
        
        # Look for request examples
        request_patterns = [
            r'Request.*?Example:\s*(.*?)(?=\n\n|\nResponse|\Z)',
            r'POST\s+data:\s*(.*?)(?=\n\n|\nResponse|\Z)'
        ]
        
        for pattern in request_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                example_text = match.group(1).strip()
                try:
                    # Try to parse as JSON
                    request_format['example'] = json.loads(example_text)
                except:
                    # Store as text if not valid JSON
                    request_format['example'] = example_text
                    
        return request_format
        
    def _extract_response_format(self, content: str, endpoint: str) -> Dict:
        """Extract response format information"""
        response_format = {
            'success': {'status_code': 200, 'example': {}, 'schema': {}},
            'error': []
        }
        
        # Look for response examples
        response_patterns = [
            r'Response.*?Example:\s*(.*?)(?=\n\n|\nError|\Z)',
            r'Success\s+Response:\s*(.*?)(?=\n\n|\nError|\Z)'
        ]
        
        for pattern in response_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                example_text = match.group(1).strip()
                try:
                    response_format['success']['example'] = json.loads(example_text)
                except:
                    response_format['success']['example'] = example_text
                    
        # Look for error responses
        error_patterns = [
            r'Error\s+Response:\s*(.*?)(?=\n\n|\nExample|\Z)',
            r'(?:400|401|403|404|500)\s*:?\s*(.*?)(?=\n\n|\Z)'
        ]
        
        for pattern in error_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                response_format['error'].append({
                    'status_code': 400,  # Default error code
                    'description': match.strip(),
                    'example': {}
                })
                
        return response_format
        
    def _check_auth_required(self, content: str, endpoint: str) -> bool:
        """Check if authentication is required for endpoint"""
        auth_keywords = ['authentication', 'auth', 'token', 'login', 'authorized']
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in auth_keywords)
        
    def _extract_permissions(self, content: str, endpoint: str) -> List[str]:
        """Extract required permissions for endpoint"""
        permissions = []
        
        # Look for permission-related text
        perm_patterns = [
            r'Permission(?:s?):\s*(.*?)(?=\n\n|\Z)',
            r'Requires?\s+permission(?:s?):\s*(.*?)(?=\n\n|\Z)'
        ]
        
        for pattern in perm_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                perm_text = match.group(1).strip()
                # Split by common delimiters
                permissions = [p.strip() for p in re.split(r'[,;]', perm_text) if p.strip()]
                
        return permissions
        
    def _extract_endpoint_examples(self, content: str, endpoint: str) -> List[Dict]:
        """Extract code examples for endpoint"""
        examples = []
        
        # Look for curl examples
        curl_pattern = r'curl\s+.*?' + re.escape(endpoint) + r'.*?(?=\n\n|\n[A-Z]|\Z)'
        curl_matches = re.findall(curl_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for curl_match in curl_matches:
            examples.append({
                'language': 'curl',
                'code': curl_match.strip(),
                'description': 'cURL example'
            })
            
        # Look for Python examples
        python_pattern = r'```python(.*?)```'
        python_matches = re.findall(python_pattern, content, re.DOTALL)
        
        for python_match in python_matches:
            if endpoint in python_match:
                examples.append({
                    'language': 'python',
                    'code': python_match.strip(),
                    'description': 'Python example'
                })
                
        return examples
        
    async def _extract_code_examples(self):
        """Extract and categorize all code examples"""
        all_pages = self.pages_collection.find({})
        
        for page in all_pages:
            for code_block in page['content']['code_blocks']:
                if len(code_block['code']) > 30:  # Filter out very short examples
                    example_doc = {
                        '_id': self._generate_id(f"example_{page['page_id']}_{hash(code_block['code'])}"),
                        'title': self._generate_example_title(code_block),
                        'description': code_block['description'],
                        'language': code_block['language'],
                        'framework': self._detect_framework(code_block['code']),
                        'category': self._categorize_example(code_block['code'], code_block['context']),
                        'code': code_block['code'],
                        'explanation': self._generate_code_explanation(code_block['code']),
                        'use_case': code_block['context'],
                        'dependencies': self._extract_dependencies(code_block['code']),
                        'prerequisites': [],
                        'related_pages': [page['page_id']],
                        'tags': self._generate_example_tags(code_block['code'])
                    }
                    
                    self.examples_collection.replace_one(
                        {'_id': example_doc['_id']},
                        example_doc,
                        upsert=True
                    )
                    
    def _generate_example_title(self, code_block: Dict) -> str:
        """Generate title for code example"""
        if code_block['description']:
            return code_block['description'][:50]
        elif code_block['context']:
            return f"{code_block['language'].title()} - {code_block['context']}"
        else:
            return f"{code_block['language'].title()} Example"
            
    def _detect_framework(self, code: str) -> str:
        """Detect framework from code"""
        code_lower = code.lower()
        if 'django' in code_lower or 'rest_framework' in code_lower:
            return 'django'
        elif 'react' in code_lower or 'jsx' in code_lower:
            return 'react'
        elif 'vue' in code_lower:
            return 'vue'
        elif 'angular' in code_lower:
            return 'angular'
        elif 'requests' in code_lower:
            return 'requests'
        else:
            return 'unknown'
            
    def _categorize_example(self, code: str, context: str) -> str:
        """Categorize code example"""
        code_lower = code.lower()
        context_lower = context.lower() if context else ''
        
        if 'install' in context_lower or 'pip install' in code_lower:
            return 'setup'
        elif 'login' in code_lower or 'auth' in code_lower:
            return 'authentication'
        elif 'register' in code_lower or 'signup' in code_lower:
            return 'registration'
        elif 'config' in context_lower or 'setting' in context_lower:
            return 'configuration'
        elif 'test' in code_lower:
            return 'testing'
        else:
            return 'general'
            
    def _generate_code_explanation(self, code: str) -> str:
        """Generate explanation for code"""
        # Simple explanation based on code analysis
        explanations = []
        
        if 'import' in code:
            explanations.append("Imports necessary modules and dependencies.")
        if 'class' in code:
            explanations.append("Defines a class with custom functionality.")
        if 'def' in code:
            explanations.append("Contains function definitions.")
        if 'settings' in code.lower():
            explanations.append("Configures application settings.")
        if 'request' in code.lower():
            explanations.append("Makes HTTP requests to the API.")
            
        return ' '.join(explanations) if explanations else "Code example for implementation."
        
    def _extract_dependencies(self, code: str) -> List[str]:
        """Extract dependencies from code"""
        dependencies = []
        
        # Python imports
        import_pattern = r'(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_.]*)'
        imports = re.findall(import_pattern, code)
        
        for imp in imports:
            if '.' in imp:
                dependencies.append(imp.split('.')[0])
            else:
                dependencies.append(imp)
                
        # Package installations
        pip_pattern = r'pip install\s+([a-zA-Z0-9\-_]+)'
        pip_packages = re.findall(pip_pattern, code)
        dependencies.extend(pip_packages)
        
        return list(set(dependencies))  # Remove duplicates
        
    def _generate_example_tags(self, code: str) -> List[str]:
        """Generate tags for code example"""
        tags = []
        code_lower = code.lower()
        
        tag_keywords = {
            'authentication': ['auth', 'login', 'token'],
            'api': ['request', 'response', 'endpoint'],
            'configuration': ['config', 'setting'],
            'testing': ['test', 'assert'],
            'serialization': ['serialize', 'json'],
            'database': ['model', 'query', 'db'],
            'frontend': ['react', 'vue', 'html', 'javascript'],
            'backend': ['django', 'python', 'server']
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in code_lower for keyword in keywords):
                tags.append(tag)
                
        return tags
        
    def _determine_content_type(self, page_id: str) -> str:
        """Determine content type based on page ID"""
        if 'api' in page_id or 'endpoint' in page_id:
            return 'api_reference'
        elif 'config' in page_id or 'setting' in page_id:
            return 'configuration'
        elif 'install' in page_id:
            return 'installation'
        elif 'faq' in page_id:
            return 'faq'
        elif 'demo' in page_id or 'example' in page_id:
            return 'example'
        else:
            return 'page'
            
    def _extract_version_from_url(self, url: str) -> str:
        """Extract version from URL"""
        version_pattern = r'/(v?\d+\.\d+(?:\.\d+)?|latest)/'
        match = re.search(version_pattern, url)
        return match.group(1) if match else 'latest'
        
    def _generate_id(self, text: str) -> str:
        """Generate consistent ID from text"""
        return hashlib.md5(text.encode()).hexdigest()
        
    def create_search_indexes(self):
        """Create additional search indexes for better performance"""
        # Full-text search indexes
        self.pages_collection.create_index([
            ("content.plain_text", "text"),
            ("title", "text"),
            ("metadata.keywords", "text"),
            ("training_data.key_concepts", "text")
        ], name="full_text_search")
        
        # Topic-based indexes
        self.pages_collection.create_index("metadata.topics")
        self.pages_collection.create_index("metadata.difficulty_level")
        
        # Configuration search
        self.config_collection.create_index([
            ("option_name", "text"),
            ("description", "text"),
            ("category", 1)
        ])
        
        # API endpoint search
        self.api_collection.create_index([
            ("endpoint_path", 1),
            ("method", 1),
            ("name", "text")
        ])
        
    def export_training_dataset(self, output_file: str = 'training_dataset.json'):
        """Export processed data as training dataset"""
        training_data = []
        
        # Export Q&A pairs from all pages
        for page in self.pages_collection.find({}):
            for qa_pair in page.get('training_data', {}).get('question_answer_pairs', []):
                training_data.append({
                    'input': qa_pair['question'],
                    'output': qa_pair['answer'],
                    'context': qa_pair['context'],
                    'source_page': page['page_id'],
                    'metadata': {
                        'topics': page['metadata']['topics'],
                        'difficulty': page['metadata']['difficulty_level'],
                        'confidence': qa_pair['confidence']
                    }
                })
                
        # Export configuration Q&A
        for config in self.config_collection.find({}):
            training_data.append({
                'input': f"How do I configure {config['option_name']}?",
                'output': config['description'],
                'context': 'Configuration',
                'source_page': 'configuration',
                'metadata': {
                    'topics': ['configuration'],
                    'difficulty': 'intermediate',
                    'confidence': 0.9
                }
            })
            
        # Export API endpoint Q&A
        for endpoint in self.api_collection.find({}):
            training_data.append({
                'input': f"How do I use the {endpoint['name']} API endpoint?",
                'output': f"{endpoint['description']} The endpoint is {endpoint['endpoint_path']} using {endpoint['method']} method.",
                'context': 'API Reference',
                'source_page': 'api_endpoints',
                'metadata': {
                    'topics': ['api'],
                    'difficulty': 'intermediate',
                    'confidence': 0.85
                }
            })
            
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(training_data, f, indent=2, default=str)
            
        print(f"Training dataset exported to {output_file} with {len(training_data)} entries")
        
    def generate_documentation_site(self, output_dir: str = 'generated_docs'):
        """Generate documentation site from stored data"""
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate index page
        self._generate_index_page(output_dir)
        
        # Generate individual pages
        for page in self.pages_collection.find({}):
            self._generate_page_file(page, output_dir)
            
        # Generate API reference
        self._generate_api_reference(output_dir)
        
        # Generate configuration reference
        self._generate_config_reference(output_dir)
        
        print(f"Documentation site generated in {output_dir}")
        
    def _generate_index_page(self, output_dir: str):
        """Generate main index page"""
        pages = list(self.pages_collection.find({}).sort('title', 1))
        
        index_content = """# DJ-Rest-Auth Documentation

This documentation is automatically generated from the official dj-rest-auth documentation.

## Table of Contents

"""
        
        for page in pages:
            index_content += f"- [{page['title']}]({page['page_id']}.md)\n"
            
        with open(f"{output_dir}/index.md", 'w') as f:
            f.write(index_content)
            
    def _generate_page_file(self, page: Dict, output_dir: str):
        """Generate individual page file"""
        content = f"# {page['title']}\n\n"
        
        # Add metadata
        content += f"**Topics:** {', '.join(page['metadata']['topics'])}\n"
        content += f"**Difficulty:** {page['metadata']['difficulty_level']}\n"
        content += f"**Reading Time:** {page['metadata']['reading_time']} minutes\n\n"
        
        # Add sections
        for section in page['content']['sections']:
            content += f"{'#' * (section['level'] + 1)} {section['heading']}\n\n"
            content += f"{section['content']}\n\n"
            
        # Add code examples
        if page['content']['code_blocks']:
            content += "## Code Examples\n\n"
            for i, code_block in enumerate(page['content']['code_blocks']):
                content += f"### Example {i + 1}: {code_block['language'].title()}\n\n"
                if code_block['description']:
                    content += f"{code_block['description']}\n\n"
                content += f"```{code_block['language']}\n{code_block['code']}\n```\n\n"
                
        with open(f"{output_dir}/{page['page_id']}.md", 'w') as f:
            f.write(content)
            
    def _generate_api_reference(self, output_dir: str):
        """Generate API reference documentation"""
        endpoints = list(self.api_collection.find({}).sort('endpoint_path', 1))
        
        content = "# API Reference\n\n"
        
        for endpoint in endpoints:
            content += f"## {endpoint['method']} {endpoint['endpoint_path']}\n\n"
            content += f"{endpoint['description']}\n\n"
            
            if endpoint['parameters']['required']:
                content += "### Required Parameters\n\n"
                for param in endpoint['parameters']['required']:
                    content += f"- **{param['name']}** ({param['type']}): {param['description']}\n"
                content += "\n"
                
            if endpoint['parameters']['optional']:
                content += "### Optional Parameters\n\n"
                for param in endpoint['parameters']['optional']:
                    content += f"- **{param['name']}** ({param['type']}): {param['description']}\n"
                content += "\n"
                
            # Add code examples
            if endpoint['code_examples']:
                content += "### Examples\n\n"
                for example in endpoint['code_examples']:
                    content += f"#### {example['language'].title()}\n\n"
                    content += f"```{example['language']}\n{example['code']}\n```\n\n"
                    
        with open(f"{output_dir}/api_reference.md", 'w') as f:
            f.write(content)
            
    def _generate_config_reference(self, output_dir: str):
        """Generate configuration reference documentation"""
        configs = list(self.config_collection.find({}).sort('option_name', 1))
        
        content = "# Configuration Reference\n\n"
        
        # Group by category
        categories = {}
        for config in configs:
            category = config['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(config)
            
        for category, config_list in categories.items():
            content += f"## {category.title()} Configuration\n\n"
            
            for config in config_list:
                content += f"### {config['option_name']}\n\n"
                content += f"**Type:** {config['data_type']}\n"
                if config['default_value'] is not None:
                    content += f"**Default:** `{config['default_value']}`\n"
                content += f"\n{config['description']}\n\n"
                
        with open(f"{output_dir}/configuration.md", 'w') as f:
            f.write(content)


# Usage example
if __name__ == "__main__":
    # Initialize scraper
    scraper = DjRestAuthDocumentationScraper(
        mongodb_connection_string="mongodb://localhost:27017/",
        base_url="https://dj-rest-auth.readthedocs.io/en/latest/"
    )
    
    # Run scraping
    asyncio.run(scraper.scrape_all_documentation())
    
    # Create search indexes
    scraper.create_search_indexes()
    
    # Export training dataset
    scraper.export_training_dataset('dj_rest_auth_training_data.json')
    
    # Generate documentation site
    scraper.generate_documentation_site('dj_rest_auth_docs')

---

# DJ-Rest-Auth AI Training Setup Guide

## Prerequisites

### Required Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
aiohttp>=3.8.0
beautifulsoup4>=4.11.0
pymongo>=4.3.0
asyncio
lxml>=4.9.0
requests>=2.28.0
```

### MongoDB Setup

1. **Install MongoDB:**
```bash
# Ubuntu/Debian
sudo apt-get install mongodb-community

# macOS
brew install mongodb-community

# Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

2. **Start MongoDB:**
```bash
sudo systemctl start mongod
# or with Docker
docker start mongodb
```

## Quick Start

### 1. Basic Scraping

```python
import asyncio
from scraper_implementation import DjRestAuthDocumentationScraper

# Initialize scraper
scraper = DjRestAuthDocumentationScraper(
    mongodb_connection_string="mongodb://localhost:27017/",
    base_url="https://dj-rest-auth.readthedocs.io/en/latest/"
)

# Run complete scraping process
async def main():
    await scraper.scrape_all_documentation()
    scraper.create_search_indexes()
    scraper.export_training_dataset()
    scraper.generate_documentation_site()

asyncio.run(main())
```

### 2. Customized Scraping

```python
# Custom configuration
scraper = DjRestAuthDocumentationScraper(
    mongodb_connection_string="mongodb://username:password@localhost:27017/mydb",
    base_url="https://dj-rest-auth.readthedocs.io/en/latest/"
)

# Scrape specific versions
versions = ['v5.0.1', 'v4.2.3', 'latest']
for version in versions:
    version_url = f"https://dj-rest-auth.readthedocs.io/en/{version}/"
    scraper.base_url = version_url
    await scraper.scrape_all_documentation()
```

## Data Analysis and Querying

### MongoDB Queries for Training Data

```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.dj_rest_auth_docs

# 1. Find all configuration options
configs = db.config_options.find({})
for config in configs:
    print(