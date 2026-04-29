# Resource-Oriented vs Procedure-Oriented Communication

Let me build this from **absolute zero** — no assumptions.

---

## 🧱 First, What is an API?

Before anything, understand this:

> **API (Application Programming Interface)** = A way for two programs to **talk to each other**.

Think of it like a **waiter** in a restaurant:
- You (client) don't go into the kitchen directly
- You tell the waiter what you want
- The waiter talks to the kitchen (server) and brings back the result

The **style** of how you communicate with that waiter — that's what REST and gRPC define differently.

---

## 🌍 Mental Model: The World vs The Action

Imagine a **library system**. There are two ways to think about it:

```
WAY 1 — Think in THINGS (Nouns):
  "There is a Book. I want to GET it, UPDATE it, DELETE it."

WAY 2 — Think in ACTIONS (Verbs):
  "BorrowBook(), ReturnBook(), SearchCatalog()"
```

This is the **core philosophical difference**.

---

## 📦 REST — Resource-Oriented (Noun-First Thinking)

### What is a "Resource"?

A **resource** is a **thing** — an entity in your system that has:
- An **identity** (a URL/address)
- A **state** (data inside it)
- **Standard operations** you can do on it (GET, POST, PUT, DELETE)

> REST says: *"Everything in your system is a resource. You manipulate resources using standard HTTP verbs."*

### The 4 Standard Operations (HTTP Verbs)

```
VERB        MEANING             ANALOGY
-------     -------             -------
GET         Read a resource     "Show me the book"
POST        Create a resource   "Add a new book"
PUT/PATCH   Update a resource   "Edit the book's details"
DELETE      Remove a resource   "Remove the book"
```

### REST URL Structure

```
https://api.library.com/books          → The "books" resource collection
https://api.library.com/books/42       → A specific book (id=42)
https://api.library.com/books/42/reviews → Reviews belonging to book 42
```

### REST Communication Flow

```
CLIENT                          SERVER
  |                               |
  |   GET /books/42               |
  |------------------------------>|
  |                               |  "Find resource: book with id=42"
  |                               |  "Return its current state"
  |   200 OK { id:42, title:... } |
  |<------------------------------|
  |                               |
  |   DELETE /books/42            |
  |------------------------------>|
  |                               |  "Find resource: book with id=42"
  |                               |  "Destroy it"
  |   204 No Content              |
  |<------------------------------|
```

### Key Insight About REST

REST **doesn't care** what you want to *do* — it only cares about **what thing** you're acting on.

```
The URL   = WHAT (the noun — the resource)
The verb  = HOW (GET/POST/PUT/DELETE)
Together  = "Do THIS to THAT THING"
```

---

## ⚙️ gRPC — Procedure-Oriented (Verb-First Thinking)

### What is a "Procedure"?

A **procedure** (or function/method) is an **action** — something you want to **do**.

> gRPC says: *"Define functions on the server. The client calls those functions directly — as if they were local functions in its own code."*

This is called **RPC = Remote Procedure Call**.

```
"Remote"    = The function lives on another machine (server)
"Procedure" = It's a function/action
"Call"      = You invoke it like a local function
```

### The Mental Model: Calling a Function Remotely

```
WITHOUT RPC (normal):
  result = myLocalFunction(arg1, arg2)   ← function is on YOUR machine

WITH RPC:
  result = server.SomeFunction(arg1, arg2) ← function is on ANOTHER machine
                                             but FEELS like a local call
```

### gRPC Service Definition (`.proto` file)

```proto
// You define PROCEDURES (functions), not resources
service LibraryService {
    rpc BorrowBook(BorrowRequest) returns (BorrowResponse);
    rpc ReturnBook(ReturnRequest) returns (ReturnResponse);
    rpc SearchCatalog(SearchRequest) returns (SearchResponse);
    rpc GetRecommendations(UserRequest) returns (BookList);
}
```

Notice: **Verbs everywhere** — Borrow, Return, Search, GetRecommendations.

### gRPC Communication Flow

```
CLIENT                              SERVER
  |                                   |
  |  BorrowBook(userId=5, bookId=42)  |
  |---------------------------------->|
  |                                   |  "Execute BorrowBook procedure"
  |                                   |  "with these specific inputs"
  |  BorrowResponse{success: true}    |
  |<----------------------------------|
  |                                   |
  |  GetRecommendations(userId=5)     |
  |---------------------------------->|
  |                                   |  "Execute GetRecommendations"
  |  BookList{books: [...]}           |
  |<----------------------------------|
```

---

## ⚖️ Side-by-Side Comparison

```
DIMENSION           REST (Resource)             gRPC (Procedure)
-----------         ---------------             ----------------
Core idea           Manipulate THINGS           Call ACTIONS
Vocabulary          Nouns (book, user)          Verbs (BorrowBook, Login)
Address style       URL paths (/books/42)       Function names (BorrowBook)
Operations          Fixed: GET/POST/PUT/DELETE  Unlimited custom functions
Data format         JSON (human-readable)       Protobuf (binary, compact)
Transport           HTTP/1.1                    HTTP/2
Speed               Slower (text-based)         Faster (binary)
Streaming           Limited                     Native support
Learning curve      Easier                      Steeper
Use case            Public APIs, web apps       Microservices, internal APIs
```

---

## 🔍 Where the Philosophy Breaks Down in Real Life

REST has a well-known problem — **what about actions that don't fit the noun model?**

```
How do you model these in REST? (They're ACTIONS, not THINGS)

  - Login a user
  - Send an email
  - Resize an image
  - Checkout a cart
  - BorrowBook
```

REST forces you to **fake** them as nouns:

```
POST /sessions          ← login (creating a "session" resource)
POST /emails            ← sending (creating an "email" resource)
POST /checkouts         ← checkout (creating a "checkout" resource)
POST /borrows           ← borrow (awkward!)
```

> This is called **"resource gymnastics"** — bending your actions into nouns artificially.

gRPC **avoids this entirely**:

```
Login(credentials)       → clean
SendEmail(emailData)     → clean
ResizeImage(params)      → clean
BorrowBook(userId, bookId) → clean
```

---

## 🌊 Decision Tree: When to Use Which?

```
Is your API public-facing (browsers, mobile apps)?
├── YES → REST (universal HTTP support, easier for external devs)
└── NO → Continue...
    │
    Do you need very high performance / low latency?
    ├── YES → gRPC (binary protocol, HTTP/2, streaming)
    └── NO → Continue...
        │
        Is your domain naturally action-heavy (complex workflows)?
        ├── YES → gRPC (procedures map naturally)
        └── NO → REST (simple CRUD on clear entities)
```

---

## 🧠 Expert Mental Model to Lock This In

```
REST thinks like a DATABASE:
  "Here are tables (resources). Read, write, update, delete rows."

gRPC thinks like a PROGRAM:
  "Here are functions. Call them with arguments. Get results."
```

---

## 🏋️ Cognitive Principle — **Conceptual Chunking**

Your brain learns faster by grouping related ideas into a single "chunk":

```
REST chunk:   [ URL = identity of a thing ] + [ HTTP verb = what to do ]
gRPC chunk:   [ Function name + args ] → [ Result ]
```

Once you own these two chunks deeply, every API design decision becomes clear — you're just choosing which mental model fits your domain better.

---

## Summary

| | REST | gRPC |
|---|---|---|
| **Asks** | *"What thing am I touching?"* | *"What action am I performing?"* |
| **Philosophy** | The world is **nouns** | The world is **verbs** |
| **Strength** | Clear, universal, stateless | Fast, typed, action-rich |

REST is like **managing files in a folder**.
gRPC is like **calling functions in a program**.

Both are valid. The art is knowing **which lens fits your problem**.