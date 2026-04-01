# What backend platform is AWS built on?

[Amazon Web Services (AWS)](https://aws.amazon.com/) is not built on a single "backend platform" in the way a typical app might use a single framework. Instead, it is a massive collection of [distributed microservices](https://en.wikipedia.org/wiki/Amazon_Web_Services) that Amazon developed internally to manage its own e-commerce infrastructure. [1, 2, 3, 4] 

The core backend of AWS is built using several primary technologies: [5] 

* Java: This is the most dominant language used across Amazon and AWS for business logic and the majority of backend services.
* C/C++: Used for performance-critical components, such as internal networking, payment processing, and checkout systems.
* Rust: Increasingly used for modern, performance-sensitive infrastructure, such as powering microVMs (e.g., Firecracker) and Bottlerocket.
* Python: Extensively used for internal tools, automation (like the AWS CLI and SAM), and many Lambda functions.
* Linux: The underlying operating system for AWS infrastructure is a highly customized version of Linux, similar to CentOS/RHEL.
* Custom Hypervisors: AWS originally used Xen for its [EC2](https://aws.amazon.com/ec2/) virtual machine service but has transitioned to a KVM-based system as part of its AWS Nitro System. [6, 7, 8, 9] 

In short, AWS is built on AWS itself; it uses its own "basic building blocks" like [S3](https://aws.amazon.com/s3/), EC2, and [Route 53](https://aws.amazon.com/about-aws/) to run and scale its newer services. [7] 
Would you like to know which programming languages are best for building your own backend on AWS?

AWS primarily uses internally developed, proprietary frameworks rather than standard public ones like Spring Boot or Django for its core infrastructure. Because AWS operates at a scale beyond typical applications, most of its backend "frameworks" are custom-built to handle massive distributed systems and ensure high reliability. [1, 2, 3] 
The key frameworks and internal systems that power AWS include:
## Internal Development Frameworks

* Brazil: Amazon's primary internal build and package management system. It handles dependencies, builds, and versioning across thousands of microservices, similar to a combination of Maven, Gradle, and NPM but specialized for Amazon's ecosystem.
* LPT (Live Pipeline Templates): A Ruby-based internal framework used to generate AWS CloudFormation or AWS CodeDeploy templates. It automates the "scaffolding" (the basic structure) needed for new services, including setting up accounts and deployment pipelines.
* Apollo: A legacy internal deployment framework used to deploy code to servers. While older, it was the precursor to many modern automated deployment systems at Amazon.
* Coral: A widely used internal service framework (primarily for Java) that standardizes how different AWS microservices talk to each other via [APIs](https://aws.amazon.com/what-is/framework/). [2, 3] 

## Operational & Infrastructure Frameworks

* The AWS Nitro System: A custom-designed hardware and software framework that offloads virtualization functions (like networking and storage) to dedicated hardware, which significantly improves EC2 performance.
* Firecracker: An open-source virtualization technology (built in Rust) that functions as a framework for launching lightweight MicroVMs used in services like [AWS Lambda](https://aws.amazon.com/lambda/) and AWS Fargate.
* Isengard/Conduit: Internal systems used for managing and isolating millions of AWS accounts for different services and development stages. [1, 2, 3, 4] 

## External Frameworks Used for Specific Tools
While the core "engines" of AWS are proprietary, some user-facing tools use well-known languages and lightweight libraries: [5] 

* Python (Boto3): The framework for the [AWS CLI](https://aws.amazon.com/cdk/) and AWS SDK for Python.
* TypeScript/JavaScript: Used heavily in the AWS Cloud Development Kit (CDK), which is a framework for defining cloud infrastructure as code. [1, 6, 7] 

Would you like to explore how you can use AWS CDK or AWS SAM as a framework to build your own applications on top of this infrastructure?
