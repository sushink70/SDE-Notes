# The Complete Terraform Mastery Guide
## From Zero to Infrastructure as Code Expert

---

## **PART 1: FOUNDATIONAL CONCEPTS**

### **What is Terraform?**

Terraform is an **Infrastructure as Code (IaC)** tool created by HashiCorp. It allows you to define, provision, and manage infrastructure using declarative configuration files rather than manual processes or imperative scripts.

**Key Mental Model**: Think of Terraform as a "desired state manager" for infrastructure. You declare *what* you want (the end state), and Terraform figures out *how* to get there.

---

### **Core Philosophy: Declarative vs Imperative**

```
IMPERATIVE (How):                    DECLARATIVE (What):
"Create a server"                    state: {
"Set memory to 4GB"          →         server: exists
"Install nginx"                        memory: 4GB
"Start nginx"                          nginx: running
                                     }
```

**Declarative approach benefits:**
- Idempotent (running twice produces same result)
- Self-documenting
- Easier to reason about
- Predictable outcomes

---

### **Why Terraform Matters**

Traditional infrastructure management problems:
1. **Manual processes** → error-prone, not reproducible
2. **Snowflake servers** → each configured differently
3. **No version control** → can't track changes
4. **Difficult to replicate** → production ≠ staging

Terraform solutions:
1. **Codified infrastructure** → version controlled, reviewed
2. **Consistent environments** → same code = same result
3. **Audit trail** → every change tracked
4. **Easy replication** → spin up identical environments

---

## **PART 2: FUNDAMENTAL BUILDING BLOCKS**

### **1. Providers**

**Concept**: A provider is a plugin that allows Terraform to interact with APIs of cloud platforms, SaaS services, or other systems.

**Mental Model**: Providers are "translators" that speak Terraform language on one side and the target platform's API on the other.

```
┌─────────────┐
│  Terraform  │
│   Config    │
└──────┬──────┘
       │
   ┌───▼────┐
   │Provider│ (AWS Plugin)
   └───┬────┘
       │
   ┌───▼────────┐
   │  AWS API   │
   └────────────┘
```

**Example providers:**
- `aws` - Amazon Web Services
- `google` - Google Cloud Platform
- `azurerm` - Microsoft Azure
- `kubernetes` - Kubernetes clusters
- `github` - GitHub repositories
- `local` - Local filesystem operations

**Configuration anatomy:**

```hcl
# Provider block structure
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"  # Registry location
      version = "~> 5.0"          # Version constraint
    }
  }
}

provider "aws" {
  region = "us-west-2"  # Provider-specific config
}
```

---

### **2. Resources**

**Concept**: Resources are the most important element. They represent infrastructure objects (servers, databases, networks, DNS records, etc.).

**Mental Model**: If providers are "translators," resources are the "nouns" - the actual things you're creating.

```
Resource Lifecycle:
┌──────────┐
│  Create  │ ← terraform apply (first time)
└────┬─────┘
     │
┌────▼─────┐
│  Update  │ ← terraform apply (when changed)
└────┬─────┘
     │
┌────▼─────┐
│  Destroy │ ← terraform destroy
└──────────┘
```

**Resource syntax anatomy:**

```hcl
resource "provider_type" "local_name" {
  # ↑         ↑            ↑
  # |         |            └─ Your custom identifier
  # |         └────────────── Resource type from provider
  # └──────────────────────── Provider prefix

  argument1 = "value1"
  argument2 = "value2"
  
  nested_block {
    nested_arg = "value"
  }
}
```

**Concrete example:**

```hcl
resource "aws_instance" "web_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  
  tags = {
    Name = "MyWebServer"
    Environment = "production"
  }
}
```

**Resource addressing:**
- Full address: `aws_instance.web_server`
- This becomes the unique identifier across your Terraform configuration

---

### **3. Data Sources**

**Concept**: Data sources allow you to *fetch* information about existing infrastructure that was created outside Terraform or in a different Terraform workspace.

**Key distinction**: 
- **Resources** = things Terraform manages (CRUD operations)
- **Data Sources** = read-only queries to existing things

**Mental Model**: Data sources are like "SELECT" queries in SQL - you're reading, not writing.

```
┌──────────────────┐
│ Existing AWS     │
│ Infrastructure   │
│                  │
│ • VPCs           │
│ • AMIs           │
│ • Subnets        │
└────────┬─────────┘
         │
    ┌────▼─────┐
    │   Data   │ (Read-only)
    │  Source  │
    └────┬─────┘
         │
    ┌────▼──────┐
    │ Terraform │
    │   Uses    │
    │   Data    │
    └───────────┘
```

**Example:**

```hcl
# Query for the latest Ubuntu AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical's AWS account
  
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }
}

# Use the queried data in a resource
resource "aws_instance" "app" {
  ami           = data.aws_ami.ubuntu.id  # ← Reference data source
  instance_type = "t2.micro"
}
```

**When to use data sources:**
- Looking up dynamic values (latest AMI IDs)
- Referencing infrastructure managed elsewhere
- Getting information about the account/environment
- Avoiding hardcoded values

---

### **4. Variables**

**Concept**: Variables make configurations reusable and parameterizable. They're inputs to your Terraform modules.

**Mental Model**: Variables are function parameters for your infrastructure code.

```
Input Variables → [Terraform Processing] → Infrastructure
    ↓
  values.tfvars
  CLI flags
  Environment vars
```

**Variable declaration syntax:**

```hcl
variable "variable_name" {
  description = "Human-readable description"
  type        = string  # or number, bool, list, map, object, etc.
  default     = "default_value"  # Optional
  sensitive   = false   # Hide in logs if true
  validation {
    condition     = can(regex("^[a-z]+$", var.variable_name))
    error_message = "Must contain only lowercase letters."
  }
}
```

**Type system deep dive:**

```hcl
# Primitive types
variable "instance_count" {
  type = number
}

variable "enable_monitoring" {
  type = bool
}

# Collection types
variable "availability_zones" {
  type = list(string)
  # Example: ["us-west-2a", "us-west-2b"]
}

variable "tags" {
  type = map(string)
  # Example: { Environment = "prod", Team = "platform" }
}

# Structural types
variable "server_config" {
  type = object({
    instance_type = string
    volume_size   = number
    monitoring    = bool
  })
  # Example: { instance_type = "t2.micro", volume_size = 20, monitoring = true }
}

# Complex nested
variable "applications" {
  type = list(object({
    name = string
    ports = list(number)
    config = map(string)
  }))
}
```

**Providing variable values:**

```hcl
# Method 1: terraform.tfvars (auto-loaded)
instance_count = 3
region = "us-west-2"

# Method 2: Custom .tfvars file
# terraform apply -var-file="production.tfvars"

# Method 3: Command line
# terraform apply -var="instance_count=3"

# Method 4: Environment variables
# export TF_VAR_instance_count=3

# Precedence (highest to lowest):
# CLI -var flags > *.auto.tfvars > terraform.tfvars > Environment vars > defaults
```

---

### **5. Outputs**

**Concept**: Outputs are return values from your Terraform configuration. They export information about your infrastructure.

**Mental Model**: Outputs are like return statements in functions - they make internal values available externally.

```
[Terraform Config]
       ↓
   Resources Created
       ↓
   Output Values → • Display to user
                   • Pass to other modules
                   • Query via CLI
```

**Output syntax:**

```hcl
output "output_name" {
  description = "What this output represents"
  value       = resource.type.name.attribute
  sensitive   = false  # Hide in console output if true
}
```

**Practical examples:**

```hcl
# Simple value output
output "instance_ip" {
  description = "Public IP of the web server"
  value       = aws_instance.web.public_ip
}

# Complex object output
output "database_connection" {
  description = "Database connection details"
  value = {
    endpoint = aws_db_instance.main.endpoint
    port     = aws_db_instance.main.port
    username = aws_db_instance.main.username
  }
  sensitive = true  # Contains sensitive info
}

# List output
output "subnet_ids" {
  value = aws_subnet.private[*].id
  # Results in: ["subnet-abc123", "subnet-def456", "subnet-ghi789"]
}
```

**Using outputs:**

```bash
# View all outputs after apply
terraform output

# Get specific output value
terraform output instance_ip

# Get output in JSON format (for scripting)
terraform output -json

# In another module/configuration
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "my-terraform-state"
    key    = "network/terraform.tfstate"
  }
}

# Reference outputs from other state
resource "aws_instance" "app" {
  subnet_id = data.terraform_remote_state.network.outputs.subnet_id
}
```

---

### **6. Local Values**

**Concept**: Local values are like internal variables - they simplify expressions and avoid repetition within a module.

**Key distinction**:
- **Variables** = external inputs
- **Locals** = internal computed values

**Mental Model**: Locals are like intermediate variables in a function - they make code more readable and maintainable.

```hcl
locals {
  # Simple computed value
  environment_prefix = "${var.environment}-${var.project_name}"
  
  # Conditional logic
  instance_type = var.environment == "production" ? "t3.large" : "t3.micro"
  
  # Complex transformations
  common_tags = merge(
    var.tags,
    {
      ManagedBy   = "Terraform"
      Environment = var.environment
      Timestamp   = timestamp()
    }
  )
  
  # Data processing
  enabled_regions = [for region in var.all_regions : region if region.enabled]
}

# Usage in resources
resource "aws_instance" "app" {
  instance_type = local.instance_type
  tags          = local.common_tags
}
```

**When to use locals:**
- Avoiding repetition of complex expressions
- Computing derived values
- Making configurations more readable
- Centralizing common values

---

## **PART 3: CONFIGURATION LANGUAGE (HCL)**

### **HCL Syntax Deep Dive**

HCL (HashiCorp Configuration Language) is designed to be both human-readable and machine-friendly.

**Basic syntax rules:**

```hcl
# Comments
// Single line comment
# Another single line comment
/* Multi-line
   comment */

# Arguments: key = value
argument_name = "value"
number_arg = 42
boolean_arg = true

# Blocks: type "label" { }
block_type "label" {
  nested_argument = "value"
  
  nested_block {
    # ...
  }
}

# Identifiers (valid names)
valid_name
valid_name_2
valid-name-with-dashes
```

---

### **Expressions and Functions**

**String interpolation:**

```hcl
# Basic interpolation
name = "server-${var.environment}"

# Complex expressions
description = "Server ${var.index + 1} of ${var.total_count}"

# Conditional
status = "Server is ${var.enabled ? "enabled" : "disabled"}"

# Directives
config = <<-EOT
  Server: ${aws_instance.web.public_ip}
  %{~ if var.enable_ssl ~}
  SSL: enabled
  %{~ endif ~}
EOT
```

**Operators:**

```hcl
# Arithmetic: + - * / %
size = var.base_size * 2

# Comparison: == != < > <= >=
is_production = var.environment == "production"

# Logical: && || !
deploy = var.approved && !var.maintenance_mode

# Null coalescing: ??
value = var.optional_value != null ? var.optional_value : "default"
```

**Essential functions** (Terraform has 100+ built-in functions):

```hcl
# String functions
upper("hello")           # "HELLO"
lower("HELLO")           # "hello"
title("hello world")     # "Hello World"
trim("  spaces  ")       # "spaces"
replace("hello", "l", "L") # "heLLo"
format("Server-%03d", 5)   # "Server-005"
join(",", ["a", "b", "c"]) # "a,b,c"
split(",", "a,b,c")      # ["a", "b", "c"]

# Collection functions
length([1, 2, 3])        # 3
concat([1, 2], [3, 4])   # [1, 2, 3, 4]
merge({a=1}, {b=2})      # {a=1, b=2}
contains(["a", "b"], "a") # true
distinct([1, 2, 2, 3])   # [1, 2, 3]
flatten([[1, 2], [3, 4]]) # [1, 2, 3, 4]
keys({a=1, b=2})         # ["a", "b"]
values({a=1, b=2})       # [1, 2]

# Numeric functions
min(1, 2, 3)            # 1
max(1, 2, 3)            # 3
ceil(1.1)               # 2
floor(1.9)              # 1
abs(-5)                 # 5

# Encoding functions
base64encode("data")
jsonencode({key = "value"})
yamlencode({key = "value"})

# Filesystem functions
file("path/to/file")         # Read file content
templatefile("template.tpl", {var = "value"})

# Date/time
timestamp()              # Current time
formatdate("YYYY-MM-DD", timestamp())

# Type conversion
tostring(42)
tonumber("42")
tobool("true")
tolist(["a", "b"])
tomap({a = 1})

# Cryptographic
md5("data")
sha256("data")
bcrypt("password")
```

---

### **Conditional Expressions**

**Ternary operator:**

```hcl
# Syntax: condition ? true_value : false_value

instance_type = var.environment == "prod" ? "t3.large" : "t3.micro"

# Chained conditions
size = (
  var.environment == "prod" ? "large" :
  var.environment == "staging" ? "medium" :
  "small"
)

# With functions
count = var.enabled ? length(var.instances) : 0
```

---

### **For Expressions**

**Concept**: For expressions transform collections (like map/filter in functional programming).

**List transformation:**

```hcl
# Transform list
[for item in var.list : upper(item)]
# Input: ["a", "b", "c"]
# Output: ["A", "B", "C"]

# Filter list
[for item in var.numbers : item if item > 5]
# Input: [1, 3, 5, 7, 9]
# Output: [7, 9]

# Transform with index
[for i, item in var.list : "${i}: ${item}"]
# Output: ["0: a", "1: b", "2: c"]
```

**Map transformation:**

```hcl
# Transform map values
{for k, v in var.map : k => upper(v)}
# Input: {name = "john", city = "nyc"}
# Output: {name = "JOHN", city = "NYC"}

# Filter map
{for k, v in var.map : k => v if v != null}

# Create map from list
{for item in var.list : item.id => item}
# Input: [{id="a", val=1}, {id="b", val=2}]
# Output: {a = {id="a", val=1}, b = {id="b", val=2}}
```

**Practical examples:**

```hcl
# Create multiple resources from list
resource "aws_instance" "servers" {
  for_each = toset(var.server_names)
  
  ami           = var.ami_id
  instance_type = "t2.micro"
  
  tags = {
    Name = each.key
  }
}

# Transform subnet configurations
locals {
  subnet_configs = {
    for idx, cidr in var.subnet_cidrs :
    "subnet-${idx}" => {
      cidr_block = cidr
      az         = var.availability_zones[idx % length(var.availability_zones)]
    }
  }
}
```

---

### **Splat Expressions**

**Concept**: Splat (`[*]`) is shorthand for extracting attributes from all elements in a list.

```hcl
# Instead of: [for instance in aws_instance.servers : instance.id]
# Use splat: aws_instance.servers[*].id

# Get all IDs
instance_ids = aws_instance.web[*].id

# Get nested attributes
private_ips = aws_instance.web[*].private_ip

# With for_each resources
server_names = [for server in aws_instance.servers : server.tags.Name]
# Or with values()
server_names = values(aws_instance.servers)[*].tags.Name
```

---

## **PART 4: RESOURCE META-ARGUMENTS**

These special arguments can be used with any resource to control behavior.

### **1. depends_on**

**Concept**: Explicitly define dependency between resources when Terraform can't infer it automatically.

**When to use**: Terraform automatically detects dependencies through resource references, but sometimes you need to enforce ordering for non-obvious dependencies.

```
Normal dependency (auto-detected):
┌──────────┐
│ Security │
│  Group   │
└────┬─────┘
     │ (referenced in instance)
     ▼
┌────────────┐
│  Instance  │
└────────────┘

Explicit dependency (depends_on):
┌──────────┐
│IAM Policy│
└────┬─────┘
     │ (no direct reference, but needed)
     ▼
┌────────────┐
│    API     │
│  Call      │
└────────────┘
```

**Example:**

```hcl
# IAM role must exist before EC2 tries to assume it
resource "aws_iam_role" "instance_role" {
  name = "instance-role"
  # ... role definition
}

resource "aws_iam_role_policy_attachment" "policy_attach" {
  role       = aws_iam_role.instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

resource "aws_instance" "app" {
  ami           = "ami-12345"
  instance_type = "t2.micro"
  iam_instance_profile = aws_iam_instance_profile.profile.name
  
  # Ensure policy is attached before instance starts
  depends_on = [
    aws_iam_role_policy_attachment.policy_attach
  ]
}
```

---

### **2. count**

**Concept**: Create multiple identical resources.

**Mental Model**: Like a for-loop that creates N copies of a resource.

```
count = 3 →  [0] Resource Instance 0
             [1] Resource Instance 1
             [2] Resource Instance 2
```

**Syntax:**

```hcl
resource "aws_instance" "servers" {
  count = 3  # Creates 3 instances
  
  ami           = "ami-12345"
  instance_type = "t2.micro"
  
  tags = {
    Name = "server-${count.index}"  # count.index = 0, 1, 2
  }
}

# Addressing specific instances:
# aws_instance.servers[0]
# aws_instance.servers[1]
# aws_instance.servers[2]

# Reference all instances:
# aws_instance.servers[*].id
```

**Conditional resource creation:**

```hcl
resource "aws_instance" "monitoring" {
  count = var.enable_monitoring ? 1 : 0  # Create if true, skip if false
  
  # ... configuration
}

# Accessing (must check if exists):
output "monitoring_ip" {
  value = length(aws_instance.monitoring) > 0 ? aws_instance.monitoring[0].public_ip : null
}
```

**Limitations of count:**
- Elements are referenced by index (brittle if order changes)
- Removing element from middle causes renumbering
- No built-in way to reference by meaningful key

---

### **3. for_each**

**Concept**: Create multiple resources with distinct configurations, referenced by key.

**Mental Model**: Like iterating over a map/set where each key represents a unique resource.

```
for_each = {        →  ["web"]  Resource with key "web"
  web = {...}          ["api"]  Resource with key "api"
  api = {...}          ["db"]   Resource with key "db"
  db  = {...}
}
```

**Syntax:**

```hcl
# With a map
resource "aws_instance" "servers" {
  for_each = {
    web = { type = "t2.small", az = "us-west-2a" }
    api = { type = "t2.micro", az = "us-west-2b" }
    db  = { type = "t2.medium", az = "us-west-2c" }
  }
  
  ami               = "ami-12345"
  instance_type     = each.value.type
  availability_zone = each.value.az
  
  tags = {
    Name = "server-${each.key}"  # "server-web", "server-api", "server-db"
  }
}

# Accessing specific instances:
# aws_instance.servers["web"]
# aws_instance.servers["api"].id

# With a set (for identical resources with different names)
resource "aws_s3_bucket" "buckets" {
  for_each = toset(["logs", "data", "backups"])
  
  bucket = "${var.project}-${each.key}"  # each.key = each.value for sets
}
```

**for_each vs count decision tree:**

```
Need multiple resources?
        │
        ├─ Yes → All identical?
        │        │
        │        ├─ Yes → count
        │        │
        │        └─ No → Different configs?
        │                │
        │                └─ Yes → for_each with map
        │
        └─ No → No meta-argument needed

Order matters? → count
Order doesn't matter? → for_each
Need to reference by name? → for_each
Simple numeric sequence? → count
```

---

### **4. provider**

**Concept**: Specify which provider configuration to use when multiple exist.

**Use case**: Multiple AWS regions, multiple cloud accounts, or different credentials.

```hcl
# Define multiple provider configurations
provider "aws" {
  alias  = "us_west"
  region = "us-west-2"
}

provider "aws" {
  alias  = "us_east"
  region = "us-east-1"
}

# Use specific provider
resource "aws_instance" "west_server" {
  provider = aws.us_west  # Uses us-west-2
  
  ami           = "ami-12345"
  instance_type = "t2.micro"
}

resource "aws_instance" "east_server" {
  provider = aws.us_east  # Uses us-east-1
  
  ami           = "ami-67890"
  instance_type = "t2.micro"
}
```

---

### **5. lifecycle**

**Concept**: Control resource lifecycle behavior.

**Available options:**

```hcl
resource "aws_instance" "app" {
  # ... resource config
  
  lifecycle {
    # Prevent resource from being destroyed
    prevent_destroy = true
    
    # Create replacement before destroying old
    create_before_destroy = true
    
    # Ignore changes to specific attributes
    ignore_changes = [
      tags,
      user_data,
    ]
    
    # Ignore all attribute changes
    ignore_changes = all
    
    # Replace resource when specific attributes change
    replace_triggered_by = [
      aws_security_group.app.id
    ]
  }
}
```

**Deep dive on each option:**

**create_before_destroy:**
```
Normal behavior:          With create_before_destroy:
1. Destroy old            1. Create new
2. Create new             2. Update references
                          3. Destroy old

Use when: Downtime is unacceptable (databases, load balancers)
```

**prevent_destroy:**
```hcl
resource "aws_db_instance" "production" {
  # ... config
  
  lifecycle {
    prevent_destroy = true  # terraform destroy will error
  }
}

# Useful for: Production databases, stateful resources
```

**ignore_changes:**
```hcl
resource "aws_instance" "app" {
  ami           = "ami-12345"
  instance_type = "t2.micro"
  
  tags = {
    Name = "app-server"
  }
  
  lifecycle {
    ignore_changes = [
      tags,        # Ignore tag changes (maybe managed externally)
      user_data,   # Ignore user_data changes
    ]
  }
}

# Use when: External systems modify resources, want to prevent drift detection
```

---

## **PART 5: STATE MANAGEMENT**

### **What is Terraform State?**

**Concept**: State is Terraform's database - it maps your configuration to real-world resources.

**Mental Model**: State is a snapshot of your infrastructure at a point in time.

```
Configuration (what you want)
        ↓
    [State File] ← Current reality mapping
        ↓
Real Infrastructure (what exists)
```

**State file contents:**

```json
{
  "version": 4,
  "terraform_version": "1.6.0",
  "resources": [
    {
      "mode": "managed",
      "type": "aws_instance",
      "name": "web",
      "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
      "instances": [
        {
          "attributes": {
            "id": "i-1234567890abcdef0",
            "public_ip": "54.123.45.67",
            "instance_type": "t2.micro"
          }
        }
      ]
    }
  ]
}
```

---

### **Why State Exists**

1. **Mapping**: Links configuration to real resources
2. **Metadata**: Stores resource dependencies
3. **Performance**: Caching avoids querying APIs every time
4. **Collaboration**: Shared source of truth

**What happens without state?**
- Terraform can't track what it manages
- Can't detect drift
- Can't safely destroy resources
- Can't update existing resources

---

### **State Backends**

**Concept**: Backend determines where state is stored.

**Local backend (default):**
```hcl
# Implicit - stores state in terraform.tfstate locally
# ⚠️ NOT recommended for teams
```

**Remote backends:**

```hcl
# S3 Backend (AWS)
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "terraform-locks"  # For state locking
  }
}

# Azure Backend
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-rg"
    storage_account_name = "tfstate"
    container_name       = "state"
    key                  = "prod.terraform.tfstate"
  }
}

# GCS Backend (Google Cloud)
terraform {
  backend "gcs" {
    bucket = "my-terraform-state"
    prefix = "prod"
  }
}

# Terraform Cloud
terraform {
  backend "remote" {
    organization = "my-org"
    
    workspaces {
      name = "production"
    }
  }
}
```

**Backend configuration workflow:**

```
1. Add backend block to configuration
2. Run: terraform init -migrate-state
3. Confirm migration
4. Local state is uploaded to remote backend
```

---

### **State Locking**

**Concept**: Prevents concurrent modifications that could corrupt state.

```
User A starts apply →  [Acquires Lock]
                            ↓
User B tries apply →  [Blocked - waits for lock]
                            ↓
User A completes   →  [Releases Lock]
                            ↓
User B proceeds    →  [Acquires Lock]
```

**DynamoDB locking configuration (AWS):**

```hcl
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"
  
  attribute {
    name = "LockID"
    type = "S"
  }
}

terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "terraform-locks"  # Enables locking
  }
}
```

**Force unlock (emergency):**
```bash
terraform force-unlock LOCK_ID
# Use cautiously - only when sure no other process is running
```

---

### **State Commands**

**Essential state operations:**

```bash
# List resources in state
terraform state list

# Show details of specific resource
terraform state show aws_instance.web

# Remove resource from state (doesn't destroy resource)
terraform state rm aws_instance.web

# Move/rename resource in state
terraform state mv aws_instance.web aws_instance.app

# Pull remote state to local file
terraform state pull > backup.tfstate

# Push local state to remote
terraform state push backup.tfstate

# Replace provider in state (after provider refactor)
terraform state replace-provider hashicorp/aws registry.terraform.io/hashicorp/aws
```

**Import existing resources:**

```bash
# Import syntax: terraform import ADDRESS ID

# Import EC2 instance
terraform import aws_instance.web i-1234567890abcdef0

# Import with for_each
terraform import 'aws_instance.servers["web"]' i-1234567890abcdef0

