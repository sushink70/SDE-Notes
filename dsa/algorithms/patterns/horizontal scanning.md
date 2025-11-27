# Comprehensive Guide to Horizontal Scanning

## What is Horizontal Scanning?

Horizontal scanning is a fundamental pattern-matching technique used in lexical analysis, text processing, and parsing. It involves moving through a text input character by character from left to right (horizontally), examining each character to identify tokens, patterns, or specific sequences.

This technique is the foundation of:
- **Lexical analyzers (lexers)** in compilers
- **Text parsers** and tokenizers
- **Regular expression engines**
- **Network protocol parsers**
- **Data validation systems**

## ASCII Diagram: Horizontal Scanning Concept

```
Input String: "int x = 42;"
              
Position:     0   1   2   3   4   5   6   7   8   9   10
              ↓   ↓   ↓   ↓   ↓   ↓   ↓   ↓   ↓   ↓   ↓
Characters:   i   n   t       x       =       4   2   ;
              
Scan pointer: →   →   →   →   →   →   →   →   →   →   →

Tokens identified:
┌─────────┐
│ "int"   │ ← Keyword (positions 0-2)
└─────────┘
           ┌───┐
           │"x"│ ← Identifier (position 4)
           └───┘
               ┌───┐
               │"="│ ← Operator (position 6)
               └───┘
                   ┌──────┐
                   │ "42" │ ← Number (positions 8-9)
                   └──────┘
                           ┌───┐
                           │";"│ ← Delimiter (position 10)
                           └───┘
```

## Detailed Process Flow

```
START
  ↓
┌─────────────────────┐
│ Initialize pointer  │
│ at position 0       │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ Read current char   │
└─────────┬───────────┘
          ↓
     ┌────┴────┐
     │ Analyze │
     │  char   │
     └────┬────┘
          ↓
    ┌─────┴─────┐
    │ Is it a   │ ← Character classification
    │ letter?   │
    │ digit?    │
    │ operator? │
    │ space?    │
    └─────┬─────┘
          ↓
┌─────────────────────┐
│ Accumulate token    │
│ Continue scanning   │
│ similar chars       │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ Token complete?     │
│ (delimiter found)   │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ Store/process token │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ Move pointer right  │
│ pointer++           │
└─────────┬───────────┘
          ↓
     ┌────┴────┐
     │   End   │ NO
     │ of text?├────┐
     └────┬────┘    │
          │ YES     │
          ↓         │
        END    ←────┘
```

## Implementation Examples## Key Concepts Explained

### 1. **Core Algorithm**

The horizontal scanning algorithm follows these steps:

```
1. Initialize position pointer at 0
2. While not at end of input:
   a. Read character at current position
   b. Classify character type (letter, digit, operator, etc.)
   c. Accumulate similar characters into token
   d. When delimiter found, complete token
   e. Move position pointer forward
3. Return collected tokens
```

### 2. **State Management**

Each implementation maintains:
- **Current position**: Index in input string
- **Input text**: The string being scanned
- **Token accumulator**: Temporary storage for current token
- **Keyword set**: For identifying reserved words

### 3. **Character Classification**

The scanner categorizes characters into:
- **Letters/underscore** → Start of identifier/keyword
- **Digits** → Start of number
- **Operators** → `+`, `-`, `*`, `/`, `=`, `<`, `>`, etc.
- **Delimiters** → `(`, `)`, `{`, `}`, `;`, `,`, etc.
- **Whitespace** → Usually skipped
- **Unknown** → Everything else

### 4. **Lookahead Mechanism**

```
Current position: i
Lookahead: peek at position i+1, i+2, ...

Example: Scanning "=="
Position 0: See '='
Peek at 1: See '='
Result: Two-character operator "=="
```

### 5. **Language-Specific Features**

**Python**: Dynamic typing, easy string manipulation, list comprehensions

**Rust**: Memory safety, zero-cost abstractions, ownership system prevents buffer overflows

**Go**: Concurrent scanning with goroutines, simple syntax, efficient string handling

**C**: Manual memory management, direct pointer manipulation, maximum control

**C++**: STL containers, RAII, templates for generic programming, smart pointers

### 6. **Performance Characteristics**

- **Time Complexity**: O(n) where n is input length
- **Space Complexity**: O(t) where t is number of tokens
- **Single pass**: No backtracking required
- **Linear scanning**: Cache-friendly memory access

### 7. **Common Use Cases**

1. **Compiler front-ends**: Lexical analysis phase
2. **Text editors**: Syntax highlighting
3. **Log parsers**: Extracting structured data
4. **Network protocols**: Parsing message formats
5. **Configuration files**: Reading structured text

### 8. **Optimization Techniques**

- **Buffering**: Read multiple characters at once
- **State machines**: Faster character classification
- **Lookup tables**: O(1) character type checking
- **Parallel scanning**: Split input into chunks (Go example)
- **Zero-copy**: Reference original string (Rust)

All five implementations demonstrate the same fundamental concept with language-appropriate idioms and optimizations!

/**
 * Horizontal Scanner Implementation in C++
 * Demonstrates modern C++ with STL, smart pointers, and templates
 */

#include <iostream>
#include <string>
#include <vector>
#include <unordered_set>
#include <memory>
#include <chrono>
#include <cctype>
#include <sstream>

enum class TokenType {
    Keyword,
    Identifier,
    Number,
    Operator,
    Delimiter,
    Whitespace,
    Unknown
};

std::string token_type_to_string(TokenType type) {
    switch(type) {
        case TokenType::Keyword: return "KEYWORD";
        case TokenType::Identifier: return "IDENTIFIER";
        case TokenType::Number: return "NUMBER";
        case TokenType::Operator: return "OPERATOR";
        case TokenType::Delimiter: return "DELIMITER";
        case TokenType::Whitespace: return "WHITESPACE";
        case TokenType::Unknown: return "UNKNOWN";
        default: return "INVALID";
    }
}

struct Token {
    TokenType type;
    std::string value;
    size_t position;
    size_t length;
    
    Token(TokenType t, const std::string& v, size_t pos)
        : type(t), value(v), position(pos), length(v.length()) {}
    
    friend std::ostream& operator<<(std::ostream& os, const Token& token) {
        os << "Token(" << token_type_to_string(token.type) 
           << ", '" << token.value << "', pos=" << token.position << ")";
        return os;
    }
};

class HorizontalScanner {
private:
    std::string text;
    size_t position;
    std::unordered_set<std::string> keywords;
    
public:
    explicit HorizontalScanner(const std::string& input) 
        : text(input), position(0) {
        keywords = {"int", "float", "if", "else", "while", "for", "return"};
    }
    
    // Get current character without advancing
    char current_char() const {
        if (position < text.length()) {
            return text[position];
        }
        return '\0';
    }
    
    // Look ahead at character without advancing
    char peek_char(size_t offset = 1) const {
        size_t pos = position + offset;
        if (pos < text.length()) {
            return text[pos];
        }
        return '\0';
    }
    
    // Move to next character
    void advance() {
        position++;
    }
    
    // Check if at end of input
    bool is_at_end() const {
        return position >= text.length();
    }
    
    // Scan an identifier or keyword
    Token scan_identifier(size_t start_pos) {
        std::string value;
        
        while (!is_at_end()) {
            char ch = current_char();
            if (std::isalnum(ch) || ch == '_') {
                value += ch;
                advance();
            } else {
                break;
            }
        }
        
        TokenType type = keywords.count(value) ? TokenType::Keyword : TokenType::Identifier;
        return Token(type, value, start_pos);
    }
    
    // Scan a numeric literal
    Token scan_number(size_t start_pos) {
        std::string value;
        bool has_dot = false;
        
        while (!is_at_end()) {
            char ch = current_char();
            if (std::isdigit(ch)) {
                value += ch;
                advance();
            } else if (ch == '.' && !has_dot) {
                has_dot = true;
                value += ch;
                advance();
            } else {
                break;
            }
        }
        
        return Token(TokenType::Number, value, start_pos);
    }
    
    // Scan an operator (handles multi-char operators)
    Token scan_operator(size_t start_pos) {
        char ch = current_char();
        std::string value(1, ch);
        advance();
        
        // Check for two-character operators
        char next = current_char();
        if ((ch == '=' || ch == '!' || ch == '<' || ch == '>') && next == '=') {
            value += next;
            advance();
        } else if ((ch == '+' || ch == '-' || ch == '&' || ch == '|') && next == ch) {
            value += next;
            advance();
        }
        
        return Token(TokenType::Operator, value, start_pos);
    }
    
    // Main scanning loop - horizontal scan through entire input
    std::vector<Token> scan_tokens() {
        std::vector<Token> tokens;
        
        while (!is_at_end()) {
            size_t start_pos = position;
            char ch = current_char();
            
            // Whitespace
            if (std::isspace(ch)) {
                advance();
                continue;
            }
            
            // Identifiers and keywords
            if (std::isalpha(ch) || ch == '_') {
                tokens.push_back(scan_identifier(start_pos));
            }
            // Numbers
            else if (std::isdigit(ch)) {
                tokens.push_back(scan_number(start_pos));
            }
            // Operators
            else if (std::string("+-*/%=<>!&|").find(ch) != std::string::npos) {
                tokens.push_back(scan_operator(start_pos));
            }
            // Delimiters
            else if (std::string("(){}[];,").find(ch) != std::string::npos) {
                tokens.emplace_back(TokenType::Delimiter, std::string(1, ch), start_pos);
                advance();
            }
            // Unknown
            else {
                tokens.emplace_back(TokenType::Unknown, std::string(1, ch), start_pos);
                advance();
            }
        }
        
        return tokens;
    }
    
    // Visualize the scanning process
    void visualize_scan() {
        std::cout << "Input: " << text << std::endl;
        std::cout << "Length: " << text.length() << " characters\n" << std::endl;
        
        // Reset position for fresh scan
        position = 0;
        auto tokens = scan_tokens();
        
        std::cout << "Scanning visualization:" << std::endl;
        std::cout << text << std::endl;
        std::cout << std::string(text.length(), '^') << std::endl;
        
        for (size_t i = 0; i < text.length(); i++) {
            std::cout << "Position " << std::setw(2) << i << ": '" 
                     << text[i] << "' ";
            
            // Find token at this position
            bool found = false;
            for (const auto& token : tokens) {
                if (token.position <= i && i < token.position + token.length) {
                    std::cout << "→ " << token_type_to_string(token.type) << std::endl;
                    found = true;
                    break;
                }
            }
            if (!found) {
                std::cout << std::endl;
            }
        }
        
        std::cout << "\nExtracted Tokens:" << std::endl;
        for (const auto& token : tokens) {
            std::cout << "  " << token << std::endl;
        }
    }
    
    // Reset scanner for reuse
    void reset() {
        position = 0;
    }
};

// Template function for performance testing
template<typename Func>
double measure_time_ms(Func func) {
    auto start = std::chrono::high_resolution_clock::now();
    func();
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> elapsed = end - start;
    return elapsed.count();
}

int main() {
    // Test case 1: Simple assignment
    std::cout << std::string(70, '=') << std::endl;
    std::cout << "Test 1: Simple variable assignment" << std::endl;
    std::cout << std::string(70, '=') << std::endl;
    HorizontalScanner scanner1("int x = 42;");
    scanner1.visualize_scan();
    
    // Test case 2: Complex expression
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "Test 2: Complex expression" << std::endl;
    std::cout << std::string(70, '=') << std::endl;
    HorizontalScanner scanner2("if (count >= 10) { result = count + 1; }");
    scanner2.visualize_scan();
    
    // Test case 3: Multiple operators
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "Test 3: Multi-character operators" << std::endl;
    std::cout << std::string(70, '=') << std::endl;
    HorizontalScanner scanner3("x == y && a != b");
    scanner3.visualize_scan();
    
    // Performance demonstration
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "Performance test" << std::endl;
    std::cout << std::string(70, '=') << std::endl;
    
    std::ostringstream oss;
    for (int i = 0; i < 1000; i++) {
        oss << "int x = 42; ";
    }
    std::string large_input = oss.str();
    
    HorizontalScanner scanner4(large_input);
    std::vector<Token> tokens;
    
    double elapsed = measure_time_ms([&]() {
        tokens = scanner4.scan_tokens();
    });
    
    std::cout << "Scanned " << large_input.length() << " characters" << std::endl;
    std::cout << "Found " << tokens.size() << " tokens" << std::endl;
    std::cout << "Time: " << std::fixed << std::setprecision(2) 
              << elapsed << "ms" << std::endl;
    
    // Demonstrate RAII with smart pointers
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "Smart pointer demonstration" << std::endl;
    std::cout << std::string(70, '=') << std::endl;
    
    auto smart_scanner = std::make_unique<HorizontalScanner>("return x + y;");
    auto smart_tokens = smart_scanner->scan_tokens();
    std::cout << "Tokens found with smart pointer: " << smart_tokens.size() << std::endl;
    
    return 0;
}

/**
 * Horizontal Scanner Implementation in C
 * Demonstrates low-level, manual memory management scanning
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <time.h>

typedef enum {
    TOKEN_KEYWORD,
    TOKEN_IDENTIFIER,
    TOKEN_NUMBER,
    TOKEN_OPERATOR,
    TOKEN_DELIMITER,
    TOKEN_WHITESPACE,
    TOKEN_UNKNOWN
} TokenType;

const char* token_type_str(TokenType type) {
    switch(type) {
        case TOKEN_KEYWORD: return "KEYWORD";
        case TOKEN_IDENTIFIER: return "IDENTIFIER";
        case TOKEN_NUMBER: return "NUMBER";
        case TOKEN_OPERATOR: return "OPERATOR";
        case TOKEN_DELIMITER: return "DELIMITER";
        case TOKEN_WHITESPACE: return "WHITESPACE";
        case TOKEN_UNKNOWN: return "UNKNOWN";
        default: return "INVALID";
    }
}

typedef struct {
    TokenType type;
    char* value;
    int position;
    int length;
} Token;

typedef struct {
    Token* tokens;
    int count;
    int capacity;
} TokenList;

typedef struct {
    const char* text;
    int position;
    int length;
} HorizontalScanner;

// Initialize scanner
HorizontalScanner* scanner_create(const char* text) {
    HorizontalScanner* scanner = (HorizontalScanner*)malloc(sizeof(HorizontalScanner));
    scanner->text = text;
    scanner->position = 0;
    scanner->length = strlen(text);
    return scanner;
}

// Free scanner
void scanner_destroy(HorizontalScanner* scanner) {
    free(scanner);
}

// Get current character without advancing
char scanner_current_char(HorizontalScanner* scanner) {
    if (scanner->position < scanner->length) {
        return scanner->text[scanner->position];
    }
    return '\0';
}

// Look ahead at character without advancing
char scanner_peek_char(HorizontalScanner* scanner, int offset) {
    int pos = scanner->position + offset;
    if (pos < scanner->length) {
        return scanner->text[pos];
    }
    return '\0';
}

// Move to next character
void scanner_advance(HorizontalScanner* scanner) {
    scanner->position++;
}

// Check if at end of input
int scanner_is_at_end(HorizontalScanner* scanner) {
    return scanner->position >= scanner->length;
}

// Check if string is a keyword
int is_keyword(const char* str) {
    const char* keywords[] = {"int", "float", "if", "else", "while", "for", "return"};
    int num_keywords = sizeof(keywords) / sizeof(keywords[0]);
    
    for (int i = 0; i < num_keywords; i++) {
        if (strcmp(str, keywords[i]) == 0) {
            return 1;
        }
    }
    return 0;
}

// Create token
Token token_create(TokenType type, const char* value, int position) {
    Token token;
    token.type = type;
    token.value = strdup(value);
    token.position = position;
    token.length = strlen(value);
    return token;
}

// Free token
void token_destroy(Token* token) {
    if (token->value) {
        free(token->value);
        token->value = NULL;
    }
}

// Initialize token list
TokenList* token_list_create() {
    TokenList* list = (TokenList*)malloc(sizeof(TokenList));
    list->capacity = 16;
    list->count = 0;
    list->tokens = (Token*)malloc(list->capacity * sizeof(Token));
    return list;
}

// Add token to list
void token_list_add(TokenList* list, Token token) {
    if (list->count >= list->capacity) {
        list->capacity *= 2;
        list->tokens = (Token*)realloc(list->tokens, list->capacity * sizeof(Token));
    }
    list->tokens[list->count++] = token;
}

// Free token list
void token_list_destroy(TokenList* list) {
    for (int i = 0; i < list->count; i++) {
        token_destroy(&list->tokens[i]);
    }
    free(list->tokens);
    free(list);
}

// Scan an identifier or keyword
Token scanner_scan_identifier(HorizontalScanner* scanner, int start_pos) {
    char buffer[256];
    int buf_pos = 0;
    
    while (!scanner_is_at_end(scanner)) {
        char ch = scanner_current_char(scanner);
        if (isalnum(ch) || ch == '_') {
            buffer[buf_pos++] = ch;
            scanner_advance(scanner);
        } else {
            break;
        }
    }
    buffer[buf_pos] = '\0';
    
    TokenType type = is_keyword(buffer) ? TOKEN_KEYWORD : TOKEN_IDENTIFIER;
    return token_create(type, buffer, start_pos);
}

// Scan a numeric literal
Token scanner_scan_number(HorizontalScanner* scanner, int start_pos) {
    char buffer[256];
    int buf_pos = 0;
    int has_dot = 0;
    
    while (!scanner_is_at_end(scanner)) {
        char ch = scanner_current_char(scanner);
        if (isdigit(ch)) {
            buffer[buf_pos++] = ch;
            scanner_advance(scanner);
        } else if (ch == '.' && !has_dot) {
            has_dot = 1;
            buffer[buf_pos++] = ch;
            scanner_advance(scanner);
        } else {
            break;
        }
    }
    buffer[buf_pos] = '\0';
    
    return token_create(TOKEN_NUMBER, buffer, start_pos);
}

// Scan an operator
Token scanner_scan_operator(HorizontalScanner* scanner, int start_pos) {
    char buffer[3];
    char ch = scanner_current_char(scanner);
    buffer[0] = ch;
    buffer[1] = '\0';
    scanner_advance(scanner);
    
    // Check for two-character operators
    char next = scanner_current_char(scanner);
    if ((ch == '=' || ch == '!' || ch == '<' || ch == '>') && next == '=') {
        buffer[1] = next;
        buffer[2] = '\0';
        scanner_advance(scanner);
    } else if ((ch == '+' || ch == '-' || ch == '&' || ch == '|') && next == ch) {
        buffer[1] = next;
        buffer[2] = '\0';
        scanner_advance(scanner);
    }
    
    return token_create(TOKEN_OPERATOR, buffer, start_pos);
}

// Main scanning loop - horizontal scan through entire input
TokenList* scanner_scan_tokens(HorizontalScanner* scanner) {
    TokenList* tokens = token_list_create();
    
    while (!scanner_is_at_end(scanner)) {
        int start_pos = scanner->position;
        char ch = scanner_current_char(scanner);
        
        // Whitespace
        if (isspace(ch)) {
            scanner_advance(scanner);
            continue;
        }
        
        // Identifiers and keywords
        if (isalpha(ch) || ch == '_') {
            token_list_add(tokens, scanner_scan_identifier(scanner, start_pos));
        }
        // Numbers
        else if (isdigit(ch)) {
            token_list_add(tokens, scanner_scan_number(scanner, start_pos));
        }
        // Operators
        else if (strchr("+-*/%=<>!&|", ch)) {
            token_list_add(tokens, scanner_scan_operator(scanner, start_pos));
        }
        // Delimiters
        else if (strchr("(){}[];,", ch)) {
            char buf[2] = {ch, '\0'};
            token_list_add(tokens, token_create(TOKEN_DELIMITER, buf, start_pos));
            scanner_advance(scanner);
        }
        // Unknown
        else {
            char buf[2] = {ch, '\0'};
            token_list_add(tokens, token_create(TOKEN_UNKNOWN, buf, start_pos));
            scanner_advance(scanner);
        }
    }
    
    return tokens;
}

// Visualize the scanning process
void scanner_visualize_scan(const char* input) {
    printf("Input: %s\n", input);
    printf("Length: %lu characters\n\n", strlen(input));
    
    HorizontalScanner* scanner = scanner_create(input);
    TokenList* tokens = scanner_scan_tokens(scanner);
    
    printf("Scanning visualization:\n");
    printf("%s\n", input);
    for (size_t i = 0; i < strlen(input); i++) {
        printf("^");
    }
    printf("\n");
    
    for (int i = 0; i < scanner->length; i++) {
        printf("Position %2d: '%c' ", i, input[i]);
        // Find token at this position
        int found = 0;
        for (int j = 0; j < tokens->count; j++) {
            Token* token = &tokens->tokens[j];
            if (token->position <= i && i < token->position + token->length) {
                printf("→ %s\n", token_type_str(token->type));
                found = 1;
                break;
            }
        }
        if (!found) {
            printf("\n");
        }
    }
    
    printf("\nExtracted Tokens:\n");
    for (int i = 0; i < tokens->count; i++) {
        Token* token = &tokens->tokens[i];
        printf("  Token(%s, '%s', pos=%d)\n", 
               token_type_str(token->type), token->value, token->position);
    }
    
    token_list_destroy(tokens);
    scanner_destroy(scanner);
}

int main() {
    // Test case 1: Simple assignment
    printf("%s\n", "======================================================================");
    printf("Test 1: Simple variable assignment\n");
    printf("%s\n", "======================================================================");
    scanner_visualize_scan("int x = 42;");
    
    // Test case 2: Complex expression
    printf("\n%s\n", "======================================================================");
    printf("Test 2: Complex expression\n");
    printf("%s\n", "======================================================================");
    scanner_visualize_scan("if (count >= 10) { result = count + 1; }");
    
    // Test case 3: Multiple operators
    printf("\n%s\n", "======================================================================");
    printf("Test 3: Multi-character operators\n");
    printf("%s\n", "======================================================================");
    scanner_visualize_scan("x == y && a != b");
    
    // Performance demonstration
    printf("\n%s\n", "======================================================================");
    printf("Performance test\n");
    printf("%s\n", "======================================================================");
    
    // Create large input
    const char* unit = "int x = 42; ";
    int unit_len = strlen(unit);
    int repetitions = 1000;
    char* large_input = (char*)malloc(unit_len * repetitions + 1);
    large_input[0] = '\0';
    for (int i = 0; i < repetitions; i++) {
        strcat(large_input, unit);
    }
    
    clock_t start = clock();
    HorizontalScanner* scanner = scanner_create(large_input);
    TokenList* tokens = scanner_scan_tokens(scanner);
    clock_t end = clock();
    
    double elapsed_ms = ((double)(end - start) / CLOCKS_PER_SEC) * 1000.0;
    printf("Scanned %lu characters\n", strlen(large_input));
    printf("Found %d tokens\n", tokens->count);
    printf("Time: %.2fms\n", elapsed_ms);
    
    token_list_destroy(tokens);
    scanner_destroy(scanner);
    free(large_input);
    
    return 0;
}

// Horizontal Scanner Implementation in Go
// Demonstrates efficient scanning with goroutines and channels

package main

import (
	"fmt"
	"strings"
	"time"
	"unicode"
)

type TokenType int

const (
	Keyword TokenType = iota
	Identifier
	Number
	Operator
	Delimiter
	Whitespace
	Unknown
)

func (t TokenType) String() string {
	return [...]string{"KEYWORD", "IDENTIFIER", "NUMBER", "OPERATOR", "DELIMITER", "WHITESPACE", "UNKNOWN"}[t]
}

type Token struct {
	Type     TokenType
	Value    string
	Position int
	Length   int
}

func (t Token) String() string {
	return fmt.Sprintf("Token(%s, '%s', pos=%d)", t.Type, t.Value, t.Position)
}

type HorizontalScanner struct {
	text     []rune
	position int
	keywords map[string]bool
}

func NewHorizontalScanner(text string) *HorizontalScanner {
	keywords := map[string]bool{
		"int":    true,
		"float":  true,
		"if":     true,
		"else":   true,
		"while":  true,
		"for":    true,
		"return": true,
	}
	
	return &HorizontalScanner{
		text:     []rune(text),
		position: 0,
		keywords: keywords,
	}
}

// CurrentChar gets current character without advancing
func (s *HorizontalScanner) CurrentChar() (rune, bool) {
	if s.position < len(s.text) {
		return s.text[s.position], true
	}
	return 0, false
}

// PeekChar looks ahead at character without advancing
func (s *HorizontalScanner) PeekChar(offset int) (rune, bool) {
	pos := s.position + offset
	if pos < len(s.text) {
		return s.text[pos], true
	}
	return 0, false
}

// Advance moves to next character
func (s *HorizontalScanner) Advance() {
	s.position++
}

// IsAtEnd checks if we've reached end of input
func (s *HorizontalScanner) IsAtEnd() bool {
	return s.position >= len(s.text)
}

// ScanIdentifier scans an identifier or keyword
func (s *HorizontalScanner) ScanIdentifier(startPos int) Token {
	var value strings.Builder
	
	for !s.IsAtEnd() {
		ch, ok := s.CurrentChar()
		if !ok {
			break
		}
		if unicode.IsLetter(ch) || unicode.IsDigit(ch) || ch == '_' {
			value.WriteRune(ch)
			s.Advance()
		} else {
			break
		}
	}
	
	val := value.String()
	tokenType := Identifier
	if s.keywords[val] {
		tokenType = Keyword
	}
	
	return Token{
		Type:     tokenType,
		Value:    val,
		Position: startPos,
		Length:   len(val),
	}
}

// ScanNumber scans a numeric literal
func (s *HorizontalScanner) ScanNumber(startPos int) Token {
	var value strings.Builder
	hasDot := false
	
	for !s.IsAtEnd() {
		ch, ok := s.CurrentChar()
		if !ok {
			break
		}
		if unicode.IsDigit(ch) {
			value.WriteRune(ch)
			s.Advance()
		} else if ch == '.' && !hasDot {
			hasDot = true
			value.WriteRune(ch)
			s.Advance()
		} else {
			break
		}
	}
	
	val := value.String()
	return Token{
		Type:     Number,
		Value:    val,
		Position: startPos,
		Length:   len(val),
	}
}

// ScanOperator scans an operator (handles multi-char operators)
func (s *HorizontalScanner) ScanOperator(startPos int) Token {
	ch, _ := s.CurrentChar()
	value := string(ch)
	s.Advance()
	
	// Check for two-character operators
	if next, ok := s.CurrentChar(); ok {
		if (ch == '=' || ch == '!' || ch == '<' || ch == '>') && next == '=' {
			value += string(next)
			s.Advance()
		} else if (ch == '+' || ch == '-' || ch == '&' || ch == '|') && next == ch {
			value += string(next)
			s.Advance()
		}
	}
	
	return Token{
		Type:     Operator,
		Value:    value,
		Position: startPos,
		Length:   len(value),
	}
}

// ScanTokens performs the main horizontal scan through entire input
func (s *HorizontalScanner) ScanTokens() []Token {
	tokens := make([]Token, 0)
	
	for !s.IsAtEnd() {
		startPos := s.position
		ch, ok := s.CurrentChar()
		if !ok {
			break
		}
		
		// Whitespace
		if unicode.IsSpace(ch) {
			s.Advance()
			continue
		}
		
		// Identifiers and keywords
		if unicode.IsLetter(ch) || ch == '_' {
			tokens = append(tokens, s.ScanIdentifier(startPos))
		} else if unicode.IsDigit(ch) {
			// Numbers
			tokens = append(tokens, s.ScanNumber(startPos))
		} else if strings.ContainsRune("+-*/%=<>!&|", ch) {
			// Operators
			tokens = append(tokens, s.ScanOperator(startPos))
		} else if strings.ContainsRune("(){}[];,", ch) {
			// Delimiters
			tokens = append(tokens, Token{
				Type:     Delimiter,
				Value:    string(ch),
				Position: startPos,
				Length:   1,
			})
			s.Advance()
		} else {
			// Unknown
			tokens = append(tokens, Token{
				Type:     Unknown,
				Value:    string(ch),
				Position: startPos,
				Length:   1,
			})
			s.Advance()
		}
	}
	
	return tokens
}

// VisualizeScan visualizes the scanning process
func (s *HorizontalScanner) VisualizeScan(input string) {
	fmt.Printf("Input: %s\n", input)
	fmt.Printf("Length: %d characters\n\n", len(s.text))
	
	// Reset position for fresh scan
	s.position = 0
	tokens := s.ScanTokens()
	
	fmt.Println("Scanning visualization:")
	fmt.Println(input)
	fmt.Println(strings.Repeat("^", len(input)))
	
	for i, ch := range s.text {
		fmt.Printf("Position %2d: '%c' ", i, ch)
		// Find token at this position
		found := false
		for _, token := range tokens {
			if token.Position <= i && i < token.Position+token.Length {
				fmt.Printf("→ %s\n", token.Type)
				found = true
				break
			}
		}
		if !found {
			fmt.Println()
		}
	}
	
	fmt.Println("\nExtracted Tokens:")
	for _, token := range tokens {
		fmt.Printf("  %s\n", token)
	}
}

// ScanTokensConcurrent demonstrates concurrent scanning (for very large inputs)
func (s *HorizontalScanner) ScanTokensConcurrent(chunkSize int) []Token {
	totalLen := len(s.text)
	if totalLen < chunkSize*2 {
		return s.ScanTokens() // Not worth parallelizing
	}
	
	numChunks := (totalLen + chunkSize - 1) / chunkSize
	resultChan := make(chan []Token, numChunks)
	
	for i := 0; i < numChunks; i++ {
		start := i * chunkSize
		end := start + chunkSize
		if end > totalLen {
			end = totalLen
		}
		
		go func(chunk []rune, offset int) {
			scanner := &HorizontalScanner{
				text:     chunk,
				position: 0,
				keywords: s.keywords,
			}
			tokens := scanner.ScanTokens()
			// Adjust positions
			for i := range tokens {
				tokens[i].Position += offset
			}
			resultChan <- tokens
		}(s.text[start:end], start)
	}
	
	// Collect results
	allTokens := make([]Token, 0)
	for i := 0; i < numChunks; i++ {
		tokens := <-resultChan
		allTokens = append(allTokens, tokens...)
	}
	
	return allTokens
}

func main() {
	// Test case 1: Simple assignment
	fmt.Println(strings.Repeat("=", 70))
	fmt.Println("Test 1: Simple variable assignment")
	fmt.Println(strings.Repeat("=", 70))
	input1 := "int x = 42;"
	scanner1 := NewHorizontalScanner(input1)
	scanner1.VisualizeScan(input1)
	
	// Test case 2: Complex expression
	fmt.Printf("\n%s\n", strings.Repeat("=", 70))
	fmt.Println("Test 2: Complex expression")
	fmt.Println(strings.Repeat("=", 70))
	input2 := "if (count >= 10) { result = count + 1; }"
	scanner2 := NewHorizontalScanner(input2)
	scanner2.VisualizeScan(input2)
	
	// Test case 3: Multiple operators
	fmt.Printf("\n%s\n", strings.Repeat("=", 70))
	fmt.Println("Test 3: Multi-character operators")
	fmt.Println(strings.Repeat("=", 70))
	input3 := "x == y && a != b"
	scanner3 := NewHorizontalScanner(input3)
	scanner3.VisualizeScan(input3)
	
	// Performance demonstration
	fmt.Printf("\n%s\n", strings.Repeat("=", 70))
	fmt.Println("Performance test")
	fmt.Println(strings.Repeat("=", 70))
	largeInput := strings.Repeat("int x = 42; ", 1000)
	scanner4 := NewHorizontalScanner(largeInput)
	start := time.Now()
	tokens := scanner4.ScanTokens()
	elapsed := time.Since(start)
	fmt.Printf("Scanned %d characters\n", len(largeInput))
	fmt.Printf("Found %d tokens\n", len(tokens))
	fmt.Printf("Time: %.2fms\n", float64(elapsed.Nanoseconds())/1e6)
}

/// Horizontal Scanner Implementation in Rust
/// Demonstrates safe, zero-copy scanning with strong typing

use std::collections::HashSet;

#[derive(Debug, Clone, PartialEq)]
enum TokenType {
    Keyword,
    Identifier,
    Number,
    Operator,
    Delimiter,
    Whitespace,
    Unknown,
}

#[derive(Debug, Clone)]
struct Token {
    token_type: TokenType,
    value: String,
    position: usize,
    length: usize,
}

impl Token {
    fn new(token_type: TokenType, value: String, position: usize) -> Self {
        let length = value.len();
        Token {
            token_type,
            value,
            position,
            length,
        }
    }
}

struct HorizontalScanner {
    text: Vec<char>,
    position: usize,
    keywords: HashSet<String>,
}

impl HorizontalScanner {
    fn new(text: &str) -> Self {
        let keywords: HashSet<String> = ["int", "float", "if", "else", "while", "for", "return"]
            .iter()
            .map(|s| s.to_string())
            .collect();
        
        HorizontalScanner {
            text: text.chars().collect(),
            position: 0,
            keywords,
        }
    }
    
    /// Get current character without advancing
    fn current_char(&self) -> Option<char> {
        self.text.get(self.position).copied()
    }
    
    /// Look ahead at character without advancing
    fn peek_char(&self, offset: usize) -> Option<char> {
        self.text.get(self.position + offset).copied()
    }
    
    /// Move to next character
    fn advance(&mut self) {
        self.position += 1;
    }
    
    /// Check if at end of input
    fn is_at_end(&self) -> bool {
        self.position >= self.text.len()
    }
    
    /// Scan an identifier or keyword
    fn scan_identifier(&mut self, start_pos: usize) -> Token {
        let mut value = String::new();
        
        while let Some(ch) = self.current_char() {
            if ch.is_alphanumeric() || ch == '_' {
                value.push(ch);
                self.advance();
            } else {
                break;
            }
        }
        
        let token_type = if self.keywords.contains(&value) {
            TokenType::Keyword
        } else {
            TokenType::Identifier
        };
        
        Token::new(token_type, value, start_pos)
    }
    
    /// Scan a numeric literal
    fn scan_number(&mut self, start_pos: usize) -> Token {
        let mut value = String::new();
        let mut has_dot = false;
        
        while let Some(ch) = self.current_char() {
            if ch.is_ascii_digit() {
                value.push(ch);
                self.advance();
            } else if ch == '.' && !has_dot {
                has_dot = true;
                value.push(ch);
                self.advance();
            } else {
                break;
            }
        }
        
        Token::new(TokenType::Number, value, start_pos)
    }
    
    /// Scan an operator (handles multi-char operators)
    fn scan_operator(&mut self, start_pos: usize) -> Token {
        let ch = self.current_char().unwrap();
        let mut value = String::from(ch);
        self.advance();
        
        // Check for two-character operators
        if let Some(next) = self.current_char() {
            if (ch == '=' || ch == '!' || ch == '<' || ch == '>') && next == '=' {
                value.push(next);
                self.advance();
            } else if (ch == '+' || ch == '-' || ch == '&' || ch == '|') && next == ch {
                value.push(next);
                self.advance();
            }
        }
        
        Token::new(TokenType::Operator, value, start_pos)
    }
    
    /// Main scanning loop - horizontal scan through entire input
    fn scan_tokens(&mut self) -> Vec<Token> {
        let mut tokens = Vec::new();
        
        while !self.is_at_end() {
            let start_pos = self.position;
            
            if let Some(ch) = self.current_char() {
                // Whitespace
                if ch.is_whitespace() {
                    self.advance();
                    continue;
                }
                
                // Identifiers and keywords
                if ch.is_alphabetic() || ch == '_' {
                    tokens.push(self.scan_identifier(start_pos));
                }
                // Numbers
                else if ch.is_ascii_digit() {
                    tokens.push(self.scan_number(start_pos));
                }
                // Operators
                else if "+-*/%=<>!&|".contains(ch) {
                    tokens.push(self.scan_operator(start_pos));
                }
                // Delimiters
                else if "(){}[];,".contains(ch) {
                    tokens.push(Token::new(TokenType::Delimiter, ch.to_string(), start_pos));
                    self.advance();
                }
                // Unknown
                else {
                    tokens.push(Token::new(TokenType::Unknown, ch.to_string(), start_pos));
                    self.advance();
                }
            }
        }
        
        tokens
    }
    
    /// Visualize the scanning process
    fn visualize_scan(&mut self, input: &str) {
        println!("Input: {}", input);
        println!("Length: {} characters\n", self.text.len());
        
        // Reset position for fresh scan
        self.position = 0;
        let tokens = self.scan_tokens();
        
        println!("Scanning visualization:");
        println!("{}", input);
        println!("{}", "^".repeat(input.len()));
        
        for (i, ch) in self.text.iter().enumerate() {
            print!("Position {:2}: '{}' ", i, ch);
            // Find token at this position
            for token in &tokens {
                if token.position <= i && i < token.position + token.length {
                    println!("→ {:?}", token.token_type);
                    break;
                }
            }
        }
        
        println!("\nExtracted Tokens:");
        for token in &tokens {
            println!("  Token({:?}, '{}', pos={})", token.token_type, token.value, token.position);
        }
    }
}

fn main() {
    // Test case 1: Simple assignment
    println!("{}", "=".repeat(70));
    println!("Test 1: Simple variable assignment");
    println!("{}", "=".repeat(70));
    let input1 = "int x = 42;";
    let mut scanner1 = HorizontalScanner::new(input1);
    scanner1.visualize_scan(input1);
    
    // Test case 2: Complex expression
    println!("\n{}", "=".repeat(70));
    println!("Test 2: Complex expression");
    println!("{}", "=".repeat(70));
    let input2 = "if (count >= 10) { result = count + 1; }";
    let mut scanner2 = HorizontalScanner::new(input2);
    scanner2.visualize_scan(input2);
    
    // Test case 3: Multiple operators
    println!("\n{}", "=".repeat(70));
    println!("Test 3: Multi-character operators");
    println!("{}", "=".repeat(70));
    let input3 = "x == y && a != b";
    let mut scanner3 = HorizontalScanner::new(input3);
    scanner3.visualize_scan(input3);
    
    // Performance demonstration
    println!("\n{}", "=".repeat(70));
    println!("Performance test");
    println!("{}", "=".repeat(70));
    let large_input = "int x = 42; ".repeat(1000);
    let start = std::time::Instant::now();
    let mut scanner4 = HorizontalScanner::new(&large_input);
    let tokens = scanner4.scan_tokens();
    let elapsed = start.elapsed();
    println!("Scanned {} characters", large_input.len());
    println!("Found {} tokens", tokens.len());
    println!("Time: {:.2}ms", elapsed.as_secs_f64() * 1000.0);
}

"""
Horizontal Scanner Implementation in Python
Demonstrates character-by-character text scanning with token extraction
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class TokenType(Enum):
    KEYWORD = "KEYWORD"
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    OPERATOR = "OPERATOR"
    DELIMITER = "DELIMITER"
    WHITESPACE = "WHITESPACE"
    UNKNOWN = "UNKNOWN"

@dataclass
class Token:
    type: TokenType
    value: str
    position: int
    length: int
    
    def __repr__(self):
        return f"Token({self.type.value}, '{self.value}', pos={self.position})"

class HorizontalScanner:
    def __init__(self, text: str):
        self.text = text
        self.position = 0
        self.length = len(text)
        self.keywords = {'int', 'float', 'if', 'else', 'while', 'for', 'return'}
        
    def current_char(self) -> Optional[str]:
        """Get current character without advancing"""
        if self.position < self.length:
            return self.text[self.position]
        return None
    
    def peek_char(self, offset: int = 1) -> Optional[str]:
        """Look ahead at character without advancing"""
        pos = self.position + offset
        if pos < self.length:
            return self.text[pos]
        return None
    
    def advance(self) -> Optional[str]:
        """Move to next character and return it"""
        self.position += 1
        return self.current_char()
    
    def is_at_end(self) -> bool:
        """Check if we've reached end of input"""
        return self.position >= self.length
    
    def scan_identifier(self, start_pos: int) -> Token:
        """Scan an identifier or keyword"""
        value = ""
        while not self.is_at_end():
            ch = self.current_char()
            if ch.isalnum() or ch == '_':
                value += ch
                self.advance()
            else:
                break
        
        token_type = TokenType.KEYWORD if value in self.keywords else TokenType.IDENTIFIER
        return Token(token_type, value, start_pos, len(value))
    
    def scan_number(self, start_pos: int) -> Token:
        """Scan a numeric literal"""
        value = ""
        has_dot = False
        
        while not self.is_at_end():
            ch = self.current_char()
            if ch.isdigit():
                value += ch
                self.advance()
            elif ch == '.' and not has_dot:
                has_dot = True
                value += ch
                self.advance()
            else:
                break
        
        return Token(TokenType.NUMBER, value, start_pos, len(value))
    
    def scan_operator(self, start_pos: int) -> Token:
        """Scan an operator (handles multi-char operators)"""
        ch = self.current_char()
        value = ch
        self.advance()
        
        # Check for two-character operators
        if ch in '=!<>' and self.current_char() == '=':
            value += self.current_char()
            self.advance()
        elif ch in '+-&|' and self.current_char() == ch:
            value += self.current_char()
            self.advance()
        
        return Token(TokenType.OPERATOR, value, start_pos, len(value))
    
    def scan_tokens(self) -> List[Token]:
        """Main scanning loop - horizontal scan through entire input"""
        tokens = []
        
        while not self.is_at_end():
            start_pos = self.position
            ch = self.current_char()
            
            # Whitespace
            if ch.isspace():
                self.advance()
                # Optionally skip whitespace or create token
                # tokens.append(Token(TokenType.WHITESPACE, ch, start_pos, 1))
                continue
            
            # Identifiers and keywords
            elif ch.isalpha() or ch == '_':
                tokens.append(self.scan_identifier(start_pos))
            
            # Numbers
            elif ch.isdigit():
                tokens.append(self.scan_number(start_pos))
            
            # Operators
            elif ch in '+-*/%=<>!&|':
                tokens.append(self.scan_operator(start_pos))
            
            # Delimiters
            elif ch in '(){}[];,':
                tokens.append(Token(TokenType.DELIMITER, ch, start_pos, 1))
                self.advance()
            
            # Unknown character
            else:
                tokens.append(Token(TokenType.UNKNOWN, ch, start_pos, 1))
                self.advance()
        
        return tokens
    
    def visualize_scan(self):
        """Visualize the scanning process"""
        print(f"Input: {self.text}")
        print(f"Length: {self.length} characters\n")
        
        tokens = self.scan_tokens()
        
        print("Scanning visualization:")
        print(self.text)
        print("^" * len(self.text))
        
        for i, ch in enumerate(self.text):
            print(f"Position {i:2d}: '{ch}' ", end="")
            # Find token at this position
            for token in tokens:
                if token.position <= i < token.position + token.length:
                    print(f"→ {token.type.value}")
                    break
            else:
                print()
        
        print("\nExtracted Tokens:")
        for token in tokens:
            print(f"  {token}")
        
        return tokens

# Example usage and demonstration
if __name__ == "__main__":
    # Test case 1: Simple assignment
    print("=" * 70)
    print("Test 1: Simple variable assignment")
    print("=" * 70)
    scanner1 = HorizontalScanner("int x = 42;")
    scanner1.visualize_scan()
    
    # Test case 2: Complex expression
    print("\n" + "=" * 70)
    print("Test 2: Complex expression")
    print("=" * 70)
    scanner2 = HorizontalScanner("if (count >= 10) { result = count + 1; }")
    scanner2.visualize_scan()
    
    # Test case 3: Multiple operators
    print("\n" + "=" * 70)
    print("Test 3: Multi-character operators")
    print("=" * 70)
    scanner3 = HorizontalScanner("x == y && a != b")
    scanner3.visualize_scan()
    
    # Performance demonstration
    print("\n" + "=" * 70)
    print("Performance test")
    print("=" * 70)
    import time
    large_input = "int x = 42; " * 1000
    start = time.time()
    scanner4 = HorizontalScanner(large_input)
    tokens = scanner4.scan_tokens()
    elapsed = time.time() - start
    print(f"Scanned {len(large_input)} characters")
    print(f"Found {len(tokens)} tokens")
    print(f"Time: {elapsed*1000:.2f}ms")