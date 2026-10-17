Complete Guide to gRPC .proto Schema (Protocol Buffers)



This guide covers Protocol Buffers (.proto files) comprehensively, from basic syntax to advanced topics used in production gRPC systems.



1\. What is a .proto File?



A .proto file is the schema definition language for Protocol Buffers (protobuf).



It defines:



Data structures (messages)

Enumerations

Services (RPC APIs)

Field rules

Options

Imports

Extensions

Package namespaces



Example:



syntax = "proto3";



package user.v1;



message User {

&#x20; int64 id = 1;

&#x20; string name = 2;

}





The protobuf compiler (protoc) generates code from this schema.



2\. Protocol Buffer Versions



There are two major versions still encountered:



Proto2

syntax = "proto2";





Supports:



required

optional

extensions

explicit field presence



Example:



required string name = 1;

optional int32 age = 2;



Proto3

syntax = "proto3";





Most commonly used with gRPC.



Removed:



required field



Added:



Simpler defaults

Better language support



Example:



string name = 1;



3\. File Structure



Typical structure:



syntax = "proto3";



package company.user.v1;



import "google/protobuf/timestamp.proto";



option java\_package = "com.company.user";



message User {}



service UserService {}





Common sections:



Syntax

Package

Imports

Options

Enums

Messages

Services

4\. Package Declaration



Defines namespace.



package ecommerce.order.v1;





Benefits:



Avoid naming conflicts

API versioning



Example:



package user.v1;

package user.v2;





Different APIs can coexist.



5\. Imports



Import other proto files.



import "user.proto";



Public Import



Re-export another schema.



import public "common.proto";





Consumers automatically gain access.



Weak Import



Mostly legacy.



import weak "legacy.proto";





Rarely used today.



6\. Comments



Single line:



// user identifier

int64 id = 1;





Multi-line:



/\*

&#x20;User information

\*/

message User {}





Documentation generators consume comments.



7\. Messages



Messages are protobuf objects.



message User {

&#x20; int64 id = 1;

&#x20; string name = 2;

}





Generated into language-specific classes/structs.



8\. Field Numbers



Each field requires a unique tag.



string name = 1;

int32 age = 2;





The number is part of the serialized wire format.



Reserved Ranges



Avoid:



19000–19999





Reserved internally by protobuf.



Recommended



Use stable numbering.



Never renumber fields.



9\. Scalar Types

Integer Types

int32

int64

uint32

uint64

sint32

sint64

fixed32

fixed64

sfixed32

sfixed64



int32

int32 age = 1;





Variable-length encoding.



uint32



Unsigned only.



uint32 count = 1;



sint32



Uses ZigZag encoding.



Efficient for negative values.



sint32 delta = 1;



fixed32



Always 4 bytes.



Good when values are consistently large.



fixed32 hash = 1;



10\. Floating Types

float

double





Example:



double balance = 1;



11\. Boolean

bool is\_active = 1;



12\. String



UTF-8 encoded.



string name = 1;



13\. Bytes



Raw binary data.



bytes avatar = 1;





Common uses:



Images

Files

Cryptographic material

14\. Field Presence



Proto3 originally lacked field presence for primitive types.



Modern proto3 supports:



optional string nickname = 1;





Generated APIs can determine:



not set





versus



empty string



15\. Repeated Fields



Arrays/lists.



repeated string tags = 1;





Generated as:



Vec (Rust)

List (Java)

slice (Go)



Example:



message User {

&#x20; repeated string skills = 1;

}



16\. Packed Repeated Fields



More compact wire representation.



repeated int32 nums = 1 \[packed=true];





Proto3 automatically packs numeric repeated fields.



17\. Maps



Dictionary structure.



map<string, string> labels = 1;





Generated as:



HashMap<String, String>





Example:



message Config {

&#x20; map<string, string> values = 1;

}



18\. Nested Messages

message User {

&#x20; message Address {

&#x20;   string city = 1;

&#x20; }



&#x20; Address address = 1;

}





Referenced as:



User.Address



19\. Enumerations

enum UserStatus {

&#x20; USER\_STATUS\_UNSPECIFIED = 0;

&#x20; ACTIVE = 1;

&#x20; BLOCKED = 2;

}



Enum Rules



Proto3 requires:



0





value.



UNKNOWN = 0;





is common.



20\. Aliased Enum Values

enum Status {

&#x20; option allow\_alias = true;



&#x20; ACTIVE = 1;

&#x20; ENABLED = 1;

}



21\. Reserved Fields



Protect compatibility.



message User {

&#x20; reserved 2;

&#x20; reserved "email";

}





or



reserved 5 to 10;





Prevents future reuse.



22\. Oneof



Mutually exclusive fields.



message Payment {

&#x20; oneof method {

&#x20;   string card = 1;

&#x20;   string paypal = 2;

&#x20; }

}





Only one can exist.



Wire format keeps last one received.



Generated APIs

enum Method {

&#x20;   Card(String),

&#x20;   Paypal(String)

}



23\. Any Type



Stores arbitrary protobuf messages.



import "google/protobuf/any.proto";



google.protobuf.Any data = 1;





Example:



message Event {

&#x20;   Any payload = 1;

}





Useful for event systems.



24\. Wrapper Types



Legacy nullable primitives.



import "google/protobuf/wrappers.proto";



Int32Value age = 1;





Modern proto3 usually prefers:



optional int32 age = 1;



25\. Common Built-in Types

Timestamp

import "google/protobuf/timestamp.proto";



Timestamp created\_at = 1;





Represents UTC time.



Duration

Duration timeout = 1;



Empty

import "google/protobuf/empty.proto";



rpc Ping(Empty) returns (Empty);



Struct



Dynamic JSON-like object.



Struct metadata = 1;



Value



Represents any JSON value.



Value data = 1;



26\. Service Definitions



Core gRPC API definition.



service UserService {

&#x20; rpc GetUser(GetUserRequest)

&#x20;     returns (User);

}



27\. Unary RPC



One request → one response.



rpc GetUser(GetUserRequest)

&#x20;   returns (User);





Similar to REST GET.



28\. Server Streaming



One request → many responses.



rpc StreamUsers(Request)

&#x20;   returns (stream User);





Server continuously sends users.



29\. Client Streaming



Many requests → one response.



rpc UploadUsers(stream User)

&#x20;   returns (UploadResult);





Client uploads multiple messages.



30\. Bidirectional Streaming



Many requests ↔ many responses.



rpc Chat(stream ChatMessage)

&#x20;   returns (stream ChatMessage);





Full duplex.



31\. Request and Response Messages



Convention:



message GetUserRequest {

&#x20; int64 id = 1;

}



message GetUserResponse {

&#x20; User user = 1;

}





Even for simple methods.



Avoid primitives directly.



32\. Options



Options customize generated code.



File Options

option java\_multiple\_files = true;



option java\_package = "com.example";



option go\_package = "github.com/example/user";



option csharp\_namespace = "Example.User";



33\. Message Options

message User {

&#x20; option deprecated = true;

}



34\. Field Options

string email = 1 \[deprecated = true];



35\. Service Options

service UserService {

&#x20; option deprecated = true;

}



36\. RPC Options

rpc CreateUser(CreateUserRequest)

returns(User) {

&#x20; option deprecated = true;

}



37\. Custom Options



Advanced feature.



Extend descriptor objects.



extend google.protobuf.FieldOptions {

&#x20; string validation = 50001;

}





Usage:



string email = 1 \[(validation)="email"];





Often used by validation frameworks.



38\. Extensions (Proto2)



Allows third-party extensions.



extend MyMessage {

&#x20; optional string extra = 100;

}





Rare in modern proto3.



39\. Extension Ranges

message User {

&#x20; extensions 100 to 999;

}





Proto2 feature.



40\. Proto Evolution Rules



One of the most important topics.



Safe Changes

Add field

string email = 10;





Safe.



Add enum value

PREMIUM = 3;





Safe.



Add service method



Safe.



Dangerous Changes

Renumber field



BAD.



name = 1





to



name = 5





Breaks compatibility.



Remove field without reservation



Bad practice.



Use:



reserved 3;



Change type



Dangerous.



string





→



int32





may break decoding.



41\. Unknown Fields



Older clients may receive newer fields.



Unknown fields:



ignored

preserved

forwarded





depending on implementation.



Critical for compatibility.



42\. JSON Mapping



Example:



Proto:



message User {

&#x20; string full\_name = 1;

}





JSON:



{

&#x20; "fullName": "John"

}





snake\_case converts to camelCase.



43\. Default Values



Proto3 defaults:



string -> ""

int32 -> 0

bool -> false

enum -> first value



44\. Naming Conventions

Package

company.product.v1



Service

UserService



Message

CreateUserRequest



Fields

full\_name

created\_at





snake\_case.



45\. Versioning Strategies



Common:



package user.v1;

package user.v2;





Do NOT version messages individually:



UserV1

UserV2





unless absolutely required.



46\. Validation Patterns



Often implemented using tools like:



string email = 1;

string phone = 2;





with generated validators.



Popular frameworks:



protoc-gen-validate

protovalidate

47\. Protobuf Well-Known Types



Frequently used:



Any

Timestamp

Duration

Struct

Value

ListValue

FieldMask

Empty





Learn all of them.



48\. FieldMask



Partial updates.



message UpdateUserRequest {

&#x20; User user = 1;

&#x20; FieldMask update\_mask = 2;

}





Example:



name,email





Only specified fields updated.



49\. API Design Best Practices



Always:



CreateUserRequest

CreateUserResponse





Avoid:



rpc GetUser(int64)





Prefer:



message GetUserRequest {

&#x20; int64 id = 1;

}



50\. Enterprise gRPC Design Pattern

service UserService {



&#x20; rpc CreateUser(CreateUserRequest)

&#x20;     returns (CreateUserResponse);



&#x20; rpc GetUser(GetUserRequest)

&#x20;     returns (GetUserResponse);



&#x20; rpc UpdateUser(UpdateUserRequest)

&#x20;     returns (UpdateUserResponse);



&#x20; rpc DeleteUser(DeleteUserRequest)

&#x20;     returns (DeleteUserResponse);



&#x20; rpc ListUsers(ListUsersRequest)

&#x20;     returns (ListUsersResponse);

}





Supports:



Pagination

Filtering

Metadata

Future additions

51\. Advanced Topics

Descriptor API



Schemas are themselves represented as protobufs.



FileDescriptorProto

DescriptorProto

FieldDescriptorProto





Used by:



Dynamic clients

Reflection

Documentation generators

Reflection Service



Allows clients to inspect schema at runtime.



Useful for:



grpcurl

Postman

Dynamic testing tools

Dynamic Messages



Create protobuf messages without generated code.



Used in:



Gateways

Message brokers

Tooling

Custom Code Generation



Plugins:



protoc \\

&#x20; --plugin





can generate:



Rust

Go

TypeScript

OpenAPI

Validators

Docs

52\. Production Schema Checklist



✅ Use proto3



✅ Use packages with versions



✅ Reserve removed fields



✅ Never renumber tags



✅ Use request/response messages



✅ Use Timestamp



✅ Use FieldMask for updates



✅ Prefer optional over wrapper types



✅ Include UNSPECIFIED=0 enum values



✅ Document everything



✅ Keep backward compatibility



✅ Enable reflection in development



✅ Adopt validation rules



✅ Design for schema evolution



Mental Model



A .proto file serves three roles simultaneously:



Data contract (message definitions)

API contract (gRPC service definitions)

Code generation blueprint (client/server stubs)



Everything in a gRPC system ultimately revolves around these core schema constructs:



.proto

&#x20;├── package

&#x20;├── imports

&#x20;├── options

&#x20;├── enums

&#x20;├── messages

&#x20;│    ├── fields

&#x20;│    ├── maps

&#x20;│    ├── repeated

&#x20;│    ├── oneof

&#x20;│    ├── Any

&#x20;│    └── nested types

&#x20;└── services

&#x20;     ├── unary

&#x20;     ├── server stream

&#x20;     ├── client stream

&#x20;     └── bidirectional stream





If you master message evolution, field numbering, oneof, well-known types, streaming RPCs, options, and backward compatibility rules, you'll understand the vast majority of production-grade gRPC schema design.



When designing a gRPC schema for a microservice, there isn't just one way to write .proto files. Different organizations use different patterns depending on service size, domain complexity, versioning strategy, and API governance.



Think of a .proto schema as the API contract of a microservice.



1\. Single File Approach (Small Services)



Suitable for:



PoC

Internal tools

Small microservices

syntax = "proto3";



package user.v1;



service UserService {

&#x20; rpc GetUser(GetUserRequest)

&#x20;     returns (GetUserResponse);



&#x20; rpc CreateUser(CreateUserRequest)

&#x20;     returns (CreateUserResponse);

}



message User {

&#x20; string id = 1;

&#x20; string name = 2;

}



message GetUserRequest {

&#x20; string id = 1;

}



message GetUserResponse {

&#x20; User user = 1;

}



message CreateUserRequest {

&#x20; string name = 1;

}



message CreateUserResponse {

&#x20; User user = 1;

}





Everything lives in one file.



Pros



Simple

Easy to understand



Cons



Becomes huge

Difficult to maintain

2\. Service-Oriented Structure



Common in microservices.



user/

├── user.proto

├── user\_messages.proto

├── common.proto



user.proto

syntax = "proto3";



package user.v1;



import "user\_messages.proto";



service UserService {

&#x20; rpc GetUser(GetUserRequest)

&#x20;     returns (GetUserResponse);

}



user\_messages.proto

message User {

&#x20; string id = 1;

&#x20; string name = 2;

}



message GetUserRequest {

&#x20; string id = 1;

}



message GetUserResponse {

&#x20; User user = 1;

}





This separates API from DTOs.



3\. Google API Style (Recommended)



Large production systems often follow this.



Structure:



user/

├── user\_service.proto

├── user.proto

├── request.proto

├── response.proto





Example:



user.proto

message User {

&#x20; string user\_id = 1;

&#x20; string email = 2;

&#x20; string name = 3;

}



request.proto

message GetUserRequest {

&#x20; string user\_id = 1;

}



response.proto

message GetUserResponse {

&#x20;  User user = 1;

}



user\_service.proto

service UserService {

&#x20;  rpc GetUser(GetUserRequest)

&#x20;      returns (GetUserResponse);

}





Large teams prefer this because each concern is isolated.



4\. Domain-Driven Design (DDD) Pattern



Best for enterprise microservices.



Example:



inventory/

├── product.proto

├── stock.proto

├── warehouse.proto

├── inventory\_service.proto



product.proto

message Product {

&#x20;  string product\_id = 1;

&#x20;  string name = 2;

}



stock.proto

message Stock {

&#x20;  string product\_id = 1;

&#x20;  int32 quantity = 2;

}



inventory\_service.proto

service InventoryService {

&#x20;  rpc GetStock(GetStockRequest)

&#x20;      returns (GetStockResponse);

}





Schemas are organized around domain concepts.



5\. Resource-Oriented Design (Google-style APIs)



Treats messages as resources.



Example:



message User {

&#x20;  string id = 1;

&#x20;  string name = 2;

&#x20;  string email = 3;

}





CRUD service:



service UserService {



&#x20;  rpc CreateUser(CreateUserRequest)

&#x20;      returns (User);



&#x20;  rpc GetUser(GetUserRequest)

&#x20;      returns (User);



&#x20;  rpc UpdateUser(UpdateUserRequest)

&#x20;      returns (User);



&#x20;  rpc DeleteUser(DeleteUserRequest)

&#x20;      returns (DeleteUserResponse);



&#x20;  rpc ListUsers(ListUsersRequest)

&#x20;      returns (ListUsersResponse);

}





This is the most common style today.



6\. CQRS Style



For event-driven microservices.



Separate commands and queries.



service UserCommandService {



&#x20;  rpc CreateUser(CreateUserCommand)

&#x20;      returns (CreateUserResult);



&#x20;  rpc UpdateUser(UpdateUserCommand)

&#x20;      returns (UpdateUserResult);

}



service UserQueryService {



&#x20;  rpc GetUser(GetUserQuery)

&#x20;      returns (UserView);



&#x20;  rpc SearchUsers(SearchUsersQuery)

&#x20;      returns (SearchUsersResult);

}





Useful when reads and writes scale differently.



7\. CRUD Microservice Example



A realistic User Service:



syntax = "proto3";



package users.v1;



service UserService {



&#x20; rpc CreateUser(CreateUserRequest)

&#x20;     returns (CreateUserResponse);



&#x20; rpc GetUser(GetUserRequest)

&#x20;     returns (GetUserResponse);



&#x20; rpc UpdateUser(UpdateUserRequest)

&#x20;     returns (UpdateUserResponse);



&#x20; rpc DeleteUser(DeleteUserRequest)

&#x20;     returns (DeleteUserResponse);



&#x20; rpc ListUsers(ListUsersRequest)

&#x20;     returns (ListUsersResponse);

}



Resource

message User {

&#x20;  string user\_id = 1;

&#x20;  string email = 2;

&#x20;  string name = 3;

}



Create

message CreateUserRequest {

&#x20;  string email = 1;

&#x20;  string name = 2;

}



message CreateUserResponse {

&#x20;  User user = 1;

}



Read

message GetUserRequest {

&#x20;  string user\_id = 1;

}



message GetUserResponse {

&#x20;  User user = 1;

}



Update

message UpdateUserRequest {

&#x20;  User user = 1;

}



Delete

message DeleteUserRequest {

&#x20;  string user\_id = 1;

}



List

message ListUsersRequest {

&#x20;  int32 page\_size = 1;

&#x20;  string page\_token = 2;

}



message ListUsersResponse {

&#x20;  repeated User users = 1;

&#x20;  string next\_page\_token = 2;

}



8\. Event-Driven Microservice Schema



Suppose Order Service publishes events.



message OrderCreated {

&#x20;   string order\_id = 1;

&#x20;   string customer\_id = 2;

}



message OrderPaid {

&#x20;   string order\_id = 1;

&#x20;   double amount = 2;

}



message OrderCancelled {

&#x20;   string order\_id = 1;

&#x20;   string reason = 2;

}





Sometimes wrapped in:



message Event {

&#x20;   string event\_type = 1;



&#x20;   oneof payload {

&#x20;       OrderCreated order\_created = 2;

&#x20;       OrderPaid order\_paid = 3;

&#x20;       OrderCancelled order\_cancelled = 4;

&#x20;   }

}





Very common in Kafka-based systems.



9\. API Gateway Friendly Design



Avoid primitive parameters.



❌ Bad



rpc GetUser(string)

&#x20;   returns (User);





✅ Good



rpc GetUser(GetUserRequest)

&#x20;   returns (GetUserResponse);





Why?



Tomorrow you may add:



message GetUserRequest {

&#x20;  string user\_id = 1;

&#x20;  bool include\_roles = 2;

&#x20;  bool include\_permissions = 3;

}





No breaking change.



10\. Production Folder Structure



A structure often seen in large microservice platforms:



proto/

└── company/

&#x20;   └── user/

&#x20;       └── v1/

&#x20;           ├── user.proto

&#x20;           ├── user\_service.proto

&#x20;           ├── requests.proto

&#x20;           ├── responses.proto

&#x20;           └── common.proto



&#x20;   └── order/

&#x20;       └── v1/

&#x20;           ├── order.proto

&#x20;           ├── order\_service.proto

&#x20;           └── events.proto





Versioning is built into the package path.



11\. Best Practices for Microservices

Use versioned packages

package company.user.v1;



Model resources explicitly

message User {}

message Order {}

message Product {}



Use Request/Response messages

GetUserRequest

GetUserResponse



Support pagination from day one

page\_size

page\_token



Use timestamps

import "google/protobuf/timestamp.proto";



google.protobuf.Timestamp created\_at = 1;



Use FieldMask for updates

message UpdateUserRequest {

&#x20;   User user = 1;

&#x20;   google.protobuf.FieldMask update\_mask = 2;

}



Reserve removed fields

reserved 5;

reserved "email";



Never renumber field tags

string email = 2;





must remain 2 forever.



What Most Companies Actually Use



For modern production microservices, the most common pattern looks like:



package company.user.v1;



service UserService {

&#x20;   rpc CreateUser(CreateUserRequest)

&#x20;       returns (CreateUserResponse);



&#x20;   rpc GetUser(GetUserRequest)

&#x20;       returns (GetUserResponse);



&#x20;   rpc UpdateUser(UpdateUserRequest)

&#x20;       returns (UpdateUserResponse);



&#x20;   rpc DeleteUser(DeleteUserRequest)

&#x20;       returns (DeleteUserResponse);



&#x20;   rpc ListUsers(ListUsersRequest)

&#x20;       returns (ListUsersResponse);

}



message User {

&#x20;   string user\_id = 1;

&#x20;   string email = 2;

&#x20;   string name = 3;

&#x20;   google.protobuf.Timestamp created\_at = 4;

}





This resource-oriented, versioned, request/response-based design scales well from a single microservice to hundreds of services and is the de facto enterprise gRPC schema style.



When people say "working with gRPC", they usually mean interacting with gRPC in different architectural and implementation styles.



You can think of it at 4 levels:



1\. Service Design

2\. Communication Pattern

3\. Client Interaction Style

4\. Infrastructure \& Operations



1\. Unary RPC (Most Common)



Request → Response



Equivalent to:



GET /users/123





gRPC:



service UserService {

&#x20; rpc GetUser(GetUserRequest)

&#x20;     returns (GetUserResponse);

}





Client:



Client ----Request----> Server

Client <---Response---- Server





Use for:



CRUD APIs

User services

Inventory services

Payment APIs



Example:



rpc CreateOrder(CreateOrderRequest)

&#x20;   returns (CreateOrderResponse);



2\. Server Streaming



One request → many responses



rpc WatchOrders(WatchOrdersRequest)

&#x20;   returns (stream OrderEvent);





Flow:



Client ----Request----> Server



Client <---Event 1-----

Client <---Event 2-----

Client <---Event 3-----





Use for:



Notifications

Log streaming

Market data

Real-time monitoring



Example:



rpc StreamLogs(LogRequest)

&#x20;   returns (stream LogEvent);



3\. Client Streaming



Many requests → one response



rpc UploadFiles(stream FileChunk)

&#x20;   returns (UploadResult);





Flow:



Client ---> Chunk1

Client ---> Chunk2

Client ---> Chunk3



Server ---> Result





Use for:



File upload

Bulk import

Data ingestion



Example:



rpc ImportUsers(stream User)

&#x20;   returns (ImportResult);



4\. Bidirectional Streaming



Many requests ↔ many responses



rpc Chat(stream ChatMessage)

&#x20;   returns (stream ChatMessage);





Flow:



Client <---> Server





Both sides communicate simultaneously.



Use for:



Chat applications

Multiplayer games

Trading systems

Event streams

5\. Request/Response Microservices



Most enterprise systems use gRPC this way.



service UserService {

&#x20; rpc CreateUser(...)

&#x20; rpc GetUser(...)

&#x20; rpc UpdateUser(...)

&#x20; rpc DeleteUser(...)

}





Architecture:



API Gateway

&#x20;     |

&#x20;     v

User Service

Order Service

Payment Service





Service-to-service communication occurs over gRPC.



6\. Resource-Oriented APIs



Like REST but using gRPC.



service ProductService {



&#x20; rpc CreateProduct(...)

&#x20;     returns (...);



&#x20; rpc GetProduct(...)

&#x20;     returns (...);



&#x20; rpc UpdateProduct(...)

&#x20;     returns (...);



&#x20; rpc DeleteProduct(...)

&#x20;     returns (...);



&#x20; rpc ListProducts(...)

&#x20;     returns (...);

}





Very popular.



7\. Domain-Oriented Services



Instead of CRUD, organize by business capability.



Example:



service PaymentService {



&#x20; rpc AuthorizePayment(...)

&#x20;     returns (...);



&#x20; rpc CapturePayment(...)

&#x20;     returns (...);



&#x20; rpc RefundPayment(...)

&#x20;     returns (...);

}





This aligns better with Domain-Driven Design (DDD).



8\. Event-Driven Systems



gRPC can behave like an event bus.



rpc SubscribeOrderEvents(

&#x20;       SubscribeRequest)

&#x20;   returns (stream OrderEvent);





Example events:



message OrderCreated {}

message OrderPaid {}

message OrderCancelled {}





Use for:



CQRS

Event sourcing

Real-time updates

9\. CQRS Pattern



Separate:



Commands

service UserCommandService {



&#x20; rpc CreateUser(...)

&#x20;     returns (...);



&#x20; rpc UpdateUser(...)

&#x20;     returns (...);

}



Queries

service UserQueryService {



&#x20; rpc GetUser(...)

&#x20;     returns (...);



&#x20; rpc SearchUsers(...)

&#x20;     returns (...);

}





Useful for high-scale applications.



10\. API Gateway + gRPC



External clients:



Browser

Mobile App

Partner APIs





Call:



REST

GraphQL





Gateway converts:



REST -> gRPC





Example:



Client

&#x20;  |

&#x20;REST

&#x20;  |

Gateway

&#x20;  |

&#x20;gRPC

&#x20;  |

Microservices





Very common in Kubernetes deployments.



11\. gRPC-Web



Browsers cannot directly use native gRPC easily.



Solution:



Browser

&#x20;  |

gRPC-Web

&#x20;  |

Envoy

&#x20;  |

gRPC Service





Proto:



service UserService {

&#x20;  rpc GetUser(GetUserRequest)

&#x20;      returns (GetUserResponse);

}





Frontend gets generated TypeScript code.



12\. Internal Service-to-Service Communication



One service calls another.



Example:



Order Service

&#x20;     |

&#x20;     v

Inventory Service

&#x20;     |

&#x20;     v

Payment Service





Proto:



service InventoryService {

&#x20;  rpc ReserveStock(...)

&#x20;      returns (...);

}





Common microservice usage.



13\. Aggregator Pattern



One service orchestrates others.



Order API

&#x20;  |

&#x20;  +--> User Service

&#x20;  |

&#x20;  +--> Inventory Service

&#x20;  |

&#x20;  +--> Payment Service





The aggregator makes multiple gRPC calls and combines results.



14\. Batch Processing

rpc CreateUsers(BatchCreateUsersRequest)

&#x20;   returns (BatchCreateUsersResponse);





Example:



message BatchCreateUsersRequest {

&#x20;  repeated User users = 1;

}





Efficient for bulk operations.



15\. Long-Running Jobs



Start a job:



rpc GenerateReport(...)

&#x20;   returns (JobResponse);





Check status:



rpc GetJobStatus(...)

&#x20;   returns (...);





Or stream progress:



rpc GenerateReport(...)

&#x20;   returns (stream JobStatus);



16\. Pub/Sub Style



Using streaming.



rpc SubscribeMetrics(

&#x20;       MetricsRequest)

&#x20;   returns (stream Metric);





Client subscribes.



Server pushes continuously.



Looks similar to:



Kafka Consumer

RabbitMQ Consumer





but over gRPC.



17\. Mesh Communication



With service meshes.



Service A

Service B

Service C





Connected through:



Istio

Linkerd

Consul





All communication occurs via gRPC.



18\. Synchronous vs Asynchronous

Synchronous

rpc CreateInvoice(...)

&#x20;   returns (...);





Client waits.



Request

Response



Asynchronous (Streaming)

rpc WatchInvoices(...)

&#x20;   returns (stream InvoiceEvent);





Client listens continuously.



19\. Polyglot Communication



One of gRPC's biggest strengths.



Same proto:



service UserService {

&#x20; rpc GetUser(...)

&#x20;     returns (...);

}





Generated code:



Go

Rust

Java

Python

C#

Node.js

Kotlin

Swift





All communicate seamlessly.



20\. Contract-First Development



Many companies start with:



.proto first





Workflow:



Design API

&#x20;     |

Write proto

&#x20;     |

Generate code

&#x20;     |

Implement server

&#x20;     |

Implement client





Example:



protoc --go\_out=.

protoc --rust\_out=.

protoc --java\_out=.





This is often considered the most scalable way to work with gRPC.



In Real Microservices, These Are the Most Common Approaches

CRUD Service

UserService

ProductService

CustomerService



Business Capability Service

PaymentService

ShippingService

BillingService



Streaming Service

NotificationService

MarketDataService

TelemetryService



Event Service

OrderEventService

AuditEventService



Internal Service Mesh Communication

Service A -> Service B -> Service C





using unary gRPC calls.



A useful mental model is:



gRPC = HTTP/2 + Protocol Buffers + RPC



Ways to work with it:



1\. Unary RPC

2\. Server Streaming

3\. Client Streaming

4\. Bidirectional Streaming



Architectural styles:



1\. CRUD APIs

2\. Resource-Oriented APIs

3\. Domain Services

4\. CQRS

5\. Event-Driven Systems

6\. Service-to-Service Communication

7\. API Gateway Backends

8\. gRPC-Web Frontends

9\. Pub/Sub Streaming

10\. Service Mesh Communication





In modern microservice platforms (Kubernetes, Istio, cloud-native systems), the most common combination is contract-first development using .proto files, unary gRPC calls for service-to-service communication, and server-streaming for real-time events.



When building systems with gRPC and .proto schemas, there is a clear separation of responsibilities:



.proto = Contract/Schema Definition

gRPC = Communication Framework



Think of it as:



.proto  --> Defines WHAT can be sent

gRPC    --> Defines HOW it is sent



What Does .proto Usually Do?



A .proto file defines the API contract.



1\. Define Data Models



Example:



message User {

&#x20; string id = 1;

&#x20; string name = 2;

&#x20; string email = 3;

}





This acts like a DTO, model, or contract.



Equivalent to:



struct User {

&#x20;   id: String,

&#x20;   name: String,

&#x20;   email: String,

}



2\. Define API Requests

message GetUserRequest {

&#x20; string user\_id = 1;

}





Describes what the client must send.



3\. Define API Responses

message GetUserResponse {

&#x20; User user = 1;

}





Describes what the server returns.



4\. Define Services

service UserService {

&#x20; rpc GetUser(GetUserRequest)

&#x20;     returns (GetUserResponse);

}





Declares available operations.



5\. Define Streaming Contracts

rpc StreamUsers(UsersRequest)

&#x20;   returns (stream User);





Specifies streaming behavior.



6\. Define Enums

enum UserStatus {

&#x20; USER\_STATUS\_UNSPECIFIED = 0;

&#x20; ACTIVE = 1;

&#x20; INACTIVE = 2;

}





For fixed values.



7\. Define API Versioning

package user.v1;





or



package company.user.v2;





Allows multiple API versions to coexist.



8\. Define Validation Metadata



Using options:



string email = 1;





Many organizations add validation rules through custom options or validation generators.



9\. Define Event Contracts

message OrderCreated {

&#x20; string order\_id = 1;

}





Even when using Kafka, RabbitMQ, or NATS, teams often use protobuf to define event payloads.



What Does gRPC Usually Do?



Once the schema exists, gRPC uses it to communicate between services.



1\. Generate Client Code



From:



service UserService {

&#x20; rpc GetUser(GetUserRequest)

&#x20;     returns (GetUserResponse);

}





gRPC generates:



client.get\_user(...)



client.getUser(...)



client.GetUser(...)



2\. Generate Server Stubs



Instead of manually parsing requests:



impl UserService for UserServiceImpl {

&#x20;   async fn get\_user(...)

}





The framework generates interfaces to implement.



3\. Serialize Data



Transforms:



message User {

&#x20; string id = 1;

}





Into efficient binary bytes.



Example:



User Object

&#x20;     ↓

Protobuf Binary

&#x20;     ↓

Network



4\. Deserialize Data



Receives bytes and reconstructs:



Binary Data

&#x20;     ↓

User Object





Automatically.



5\. Handle Network Communication



Without gRPC you'd write:



TCP sockets

HTTP requests

serialization logic

retry logic





gRPC handles most of this.



6\. Service-to-Service Communication



Example:



Order Service

&#x20;     |

&#x20;     v

User Service





Order Service calls:



GetUser()





through generated gRPC clients.



7\. Streaming



gRPC manages:



Server Streaming

returns (stream User)



Client Streaming

rpc Upload(stream Chunk)



Bidirectional Streaming

rpc Chat(stream Message)

&#x20;   returns (stream Message);



8\. Deadline Handling



Client:



timeout = 2 seconds





If server exceeds timeout:



DEADLINE\_EXCEEDED





Useful in microservices.



9\. Load Balancing



Clients can distribute calls across:



User Service Pod 1

User Service Pod 2

User Service Pod 3



10\. Authentication



Commonly:



JWT

OAuth

mTLS





via gRPC metadata and interceptors.



11\. Error Handling



Standardized errors.



NOT\_FOUND

INVALID\_ARGUMENT

UNAVAILABLE





Instead of custom HTTP error parsing.



Example:



User not found





returns:



NOT\_FOUND



12\. Reflection



Allows tools to inspect services dynamically.



Useful for:



grpcurl



grpcui





Without needing source code.



What Are Teams Usually Using .proto For?



Typical enterprise usage:



Resource Definitions

message User {}

message Product {}

message Order {}



Request/Response Contracts

GetUserRequest

GetUserResponse



Internal APIs

service UserService



Event Schemas

OrderCreated

OrderPaid

OrderCancelled



Shared Contracts

Auth Service

Order Service

Inventory Service





All understand the same schema.



What Are Teams Usually Using gRPC For?



Most common scenarios:



Service-to-Service Calls

API Gateway

&#x20;     ↓

User Service

&#x20;     ↓

Inventory Service

&#x20;     ↓

Payment Service



Microservice Communication

Order → User

Order → Inventory

Order → Payment



Streaming Data

Logs

Notifications

Market Data

Metrics



Real-Time Systems

Chat

Games

Trading

IoT



Multi-Language Systems

Rust Service

Go Service

Java Service

Python Service





All communicate through the same .proto contract.



Real-World Example



For a User microservice:



.proto

syntax = "proto3";



package company.user.v1;



service UserService {

&#x20; rpc GetUser(GetUserRequest)

&#x20;     returns (GetUserResponse);

}



message GetUserRequest {

&#x20; string user\_id = 1;

}



message GetUserResponse {

&#x20; User user = 1;

}



message User {

&#x20; string user\_id = 1;

&#x20; string name = 2;

&#x20; string email = 3;

}



What .proto provides



✅ Data structure definitions



✅ Service contract



✅ Request/response schemas



✅ Versioning



✅ Code generation blueprint



What gRPC provides



✅ Client generation



✅ Server generation



✅ Binary serialization



✅ Networking



✅ HTTP/2 transport



✅ Streaming



✅ Authentication hooks



✅ Retries and deadlines



✅ Error handling



Simple Mental Model

Database Schema

&#x20;       |

&#x20;       v

&#x20;     .proto

&#x20;       |

&#x20;       v

&#x20;  API Contract

&#x20;       |

&#x20;       v

&#x20;     gRPC

&#x20;       |

&#x20;       v

Client <----> Server





In practice, the .proto file describes your microservice API and data contracts, while gRPC uses those contracts to generate code and enable fast, strongly typed communication between services.

