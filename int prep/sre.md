Google's Site Reliability Engineering (SRE) interview process is legendary for its depth, covering everything from the way a kernel manages memory to how a global system might fail under the laws of physics. [1, 2, 3] 
The questions typically fall into five main categories:
## 1. Unix/Linux Internals [4] 
Google expects a deep understanding of what happens "under the hood". [4, 5] 

* Process Management: What is a zombie process? What happens when a process enters a "D-state" (uninterruptible sleep)?
* System Calls: Explain how ls -l works at the kernel level. How does a shell execute a command like rm?
* Memory & Storage: What are inodes, and why are they important? Explain the difference between hard and soft links.
* Boot Process: Describe the Linux boot sequence from power-on to login prompt. [2, 6, 7, 8, 9] 

## 2. Troubleshooting & Debugging
These rounds test your systematic reasoning rather than just your knowledge of commands. [2, 4] 

* Latency Spikes: "The site is slow, but CPU is at 40%. How would you investigate?"
* Network Failure: "A service cannot reach its database. Walk me through your diagnosis".
* Resource Exhaustion: "The system says there are no more process IDs (PIDs) available. How do you detect and stop the issue?" [2, 6, 10, 11, 12] 

## 3. Non-Abstract Large System Design (NALSD)
Unlike standard software design, NALSD requires you to account for physical constraints like bandwidth and latency. [2, 13, 14] 

* Global Pipelines: Design a metrics collection pipeline that handles 10 million events per second.
* Disaster Recovery: "Design a plan to replicate 5PB of data with a 4-hour recovery objective" (Note: This often tests if you realize 10Gbps isn't fast enough for that much data).
* Availability: How would you ensure a 99.99% uptime for a global chat system with 10 million users? [2, 7, 15, 16, 17] 

## 4. Operational Coding
SRE coding is less about "LeetCode" algorithms and more about writing safe, efficient scripts for infrastructure. [2, 4] 

* Log Parsing: "Write a script to parse a 100GB log file to find p99 latency without causing an Out-of-Memory (OOM) crash".
* Concurrency: "Write a tool to check the health of 10,000 servers in parallel with a strict rate limit".
* Data Structures: Design a structure to find the maximum temperature from a stream over the last 24 hours. [2, 7, 18, 19, 20] 

## 5. Googleyness & Leadership
These questions evaluate how you handle stress and work with others. [7, 21] 

* "Tell me about the most severe outage you ever handled".
* "How do you prioritize reliability improvements against new feature development?"
* "Describe a time you disagreed with a software engineer on a production decision". [18, 22] 

For a deep dive into the official principles, you can read the [Google SRE Book](https://sre.google/sre-book/table-of-contents/) online for free. [18, 23, 24, 25] 
Would you like to focus on a specific track (like SRE-SWE vs. SRE-SE) or do a mock troubleshooting scenario?

Preparing for a Google SRE interview requires deep knowledge in five areas: Linux Internals, Networking, Troubleshooting, Coding/Algorithms, and Non-Abstract Large System Design (NALSD). [1, 2, 3] 
Here is a comprehensive list of 100 interview questions categorized by these core domains.
## Unix/Linux Internals

   1. What happens at the kernel level when you type ls -l?
   2. Explain the difference between a hard link and a soft link.
   3. What is a zombie process, and how is it reaped?
   4. Explain the Linux boot process from BIOS/UEFI to the login prompt.
   5. What are inodes, and why might a disk be "full" even if it has free space?
   6. Describe the difference between process and thread memory management.
   7. What is a file descriptor?
   8. Explain the purpose of /proc and name three useful files within it.
   9. What does the "D-state" (uninterruptible sleep) mean for a process?
   10. How do cgroups and namespaces facilitate containerization?
   11. Explain context switching and its impact on performance.
   12. How does a shell execute a command like rm?
   13. What is the difference between SIGKILL and SIGTERM?
   14. Explain virtual memory, the MMU, and page tables.
   15. What is the OOM Killer, and how does it choose which process to kill?
   16. Describe RAID levels (0, 1, 5, 10) and their trade-offs.
   17. What are system calls, and how do they differ from library calls?
   18. Explain copy-on-write (COW) in the context of fork().
   19. What is a mutex vs. a semaphore?
   20. How do you find which process is using a specific port? [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] 

## Networking & Load Balancing

   1. Walk through the TCP 3-way handshake.
   2. Explain the step-by-step process of DNS resolution.
   3. What is the difference between L4 (Transport) and L7 (Application) load balancing?
   4. How does HTTPS/TLS establish a secure connection?
   5. Explain ARP (Address Resolution Protocol) and its stages.
   6. What is the TCP Congestion Control mechanism?
   7. Describe the purpose of BGP in internet routing.
   8. What is the difference between TCP and UDP?
   9. Explain DHCP and how it assigns IP addresses.
   10. What is Anycast, and how is it used in CDNs?
   11. Describe MTU and the consequences of IP fragmentation.
   12. What is a Reverse Proxy, and how does it differ from a forward proxy?
   13. Explain the CAP Theorem in distributed systems.
   14. What is ICMP, and which common tools use it?
   15. Describe SNAT vs. DNAT.
   16. How do you troubleshoot a "Connection Refused" vs. "Connection Timeout"?
   17. Explain VLAN tagging and its use in large networks.
   18. What is Quic/HTTP3, and how does it improve over HTTP2?
   19. Describe Sticky Sessions (Session Affinity) and when to avoid them.
   20. Explain Consistent Hashing and its importance in distributed caching. [1, 5, 6, 7, 8, 9, 12, 13, 16] 

## Troubleshooting & Observability

   1. A server has high I/O Wait. How do you diagnose the root cause?
   2. Define the Four Golden Signals: Latency, Traffic, Errors, Saturation.
   3. What is the difference between SLI, SLO, and SLA?
   4. Explain White-box vs. Black-box monitoring.
   5. How do you investigate a "No space left on device" error when df -h shows plenty of space?
   6. Describe your process for debugging a latency spike that only affects 1% of users.
   7. What is Alert Fatigue, and how do you prevent it?
   8. Explain distributed tracing (e.g., Jaeger) and its necessity in microservices.
   9. How do you distinguish between an application bug and an infrastructure failure during an outage?
   10. What is a blameless postmortem?
   11. Explain the USE method (Utilization, Saturation, Errors) vs. the RED method (Rate, Errors, Duration).
   12. How do you handle a cascading failure in a distributed system?
   13. What is Chaos Engineering, and what are some tools used for it?
   14. How do you troubleshoot a memory leak in a running process?
   15. Explain MTTR (Mean Time to Repair) vs. MTBF (Mean Time Between Failures).
   16. What is Log Aggregation, and how does the ELK stack work?
   17. How would you monitor a service that currently has no monitoring?
   18. Describe a time you used strace or tcpdump to solve a production issue.
   19. What are synthetic transactions, and why are they useful?
   20. How do you manage on-call burnout? [2, 6, 9, 10, 12, 15, 16, 17, 18, 19] 

## Coding & Algorithms

   1. Implement a Rate Limiter (e.g., Token Bucket or Leaky Bucket).
   2. Write a script to find the top 10 IP addresses from a 100GB log file.
   3. Design a data structure to find the max temperature in a stream over the last 24 hours.
   4. Reverse a Linked List.
   5. Given an array of integers, find if any two numbers sum up to a target value.
   6. Implement a Thread-safe Queue.
   7. Write a function to check for balanced parentheses in an expression.
   8. Implement Binary Search and explain its time complexity.
   9. Shuffle an array so that no element remains in its original position.
   10. Write a script to restart a service automatically if it crashes.
   11. Merge two sorted arrays efficiently.
   12. Find the k-th largest element in an unsorted array.
   13. Implement a basic Stack or Queue using lists.
   14. Write a program to detect a cycle in a directed graph.
   15. Design a system to store and retrieve metrics (time-series data).
   16. Calculate the height of a Binary Search Tree.
   17. Write a script to check disk usage across 1,000 servers in parallel.
   18. Implement a Sorted Hash Table.
   19. How do you handle idempotency in automation scripts?
   20. Write a function to merge overlapping intervals. [5, 9, 10, 12, 18] 

## System Design (NALSD)

   1. Design a Global Metrics Pipeline handling 10M events per second.
   2. Explain Horizontal vs. Vertical Scaling.
   3. Design a distributed Cron system.
   4. How would you design a system to achieve 99.999% availability?
   5. Explain Database Sharding and its pros/cons.
   6. Design a Rate Limiting system for a global API gateway.
   7. What is Eventual Consistency vs. Strong Consistency?
   8. Design a log processing system that can handle multi-region failures.
   9. How would you migrate 1PB of data with zero downtime?
   10. Explain the Sidecar pattern and its role in a Service Mesh.
   11. Design a system for copying large files to 100,000 remote servers.
   12. What are Circuit Breakers, and how do they prevent system failure?
   13. Design a Feature Flag system for global rollouts.
   14. Explain Backpressure and how to implement it in a distributed system.
   15. How do you handle Data Replication across three different continents?
   16. Design an Identity and Access Management (IAM) system.
   17. Explain Blue-Green vs. Canary deployment strategies.
   18. What is Infrastructure as Code (IaC), and how does it help SREs?
   19. Design a Disaster Recovery plan for a multi-tier web application.
   20. How do you manage Secret Management (passwords/keys) at scale? [2, 5, 6, 7, 8, 9, 11, 12, 13, 16, 17, 20, 21] 

For detailed preparation, Google's [SRE Books](https://sre.google/books/) are the primary source for the philosophy and technical rigor expected in these interviews. [2] 
Would you like a deep dive into one of these specific sections?

[1] [https://www.youtube.com](https://www.youtube.com/watch?v=gAFbdDVnT7I&t=141)
[2] [https://aceinterviews.hashnode.dev](https://aceinterviews.hashnode.dev/google-sre-interview-questions-2026-and-beyond-guide-what-google-really-tests-and-how-to-prepare)
[3] [https://igotanoffer.com](https://igotanoffer.com/blogs/tech/google-site-reliability-engineer-interview)
[4] [https://igotanoffer.com](https://igotanoffer.com/blogs/tech/google-site-reliability-engineer-interview)
[5] [https://igotanoffer.com](https://igotanoffer.com/blogs/tech/google-site-reliability-engineer-interview)
[6] [https://pagertree.com](https://pagertree.com/blog/site-reliability-engineer-sre-interview-questions)
[7] [https://www.interviewbit.com](https://www.interviewbit.com/sre-interview-questions/)
[8] [https://github.com](https://github.com/mxssl/sre-interview-prep-guide)
[9] [https://techwithhuz.com](https://techwithhuz.com/top-100-sre-interview-questions-answers/)
[10] [https://www.naukri.com](https://www.naukri.com/code360/library/sre-interview-questions)
[11] [https://medium.com](https://medium.com/@sre-devops-interview/sre-interview-questions-for-faang-companies-28e06dbebf2d)
[12] [https://medium.com](https://medium.com/@sre-devops-interview/sre-interview-questions-for-faang-companies-28e06dbebf2d)
[13] [https://mindmajix.com](https://mindmajix.com/sre-interview-questions)
[14] [https://interviewthoughts.quora.com](https://interviewthoughts.quora.com/My-Site-Reliability-Engineer-Interview-with-Google-Dublin)
[15] [https://techwithhuz.com](https://techwithhuz.com/top-100-sre-interview-questions-answers/)
[16] [https://www.youtube.com](https://www.youtube.com/watch?v=xQYWPjJOhNg)
[17] [https://github.com](https://github.com/rohitg00/devops-interview-questions)
[18] [https://www.gremlin.com](https://www.gremlin.com/site-reliability-engineering/sre-interview-questions-and-job-descriptions)
[19] [https://www.interviewbit.com](https://www.interviewbit.com/sre-interview-questions/)
[20] [https://pagertree.com](https://pagertree.com/blog/site-reliability-engineer-sre-interview-questions)
[21] [https://www.novelvista.com](https://www.novelvista.com/blogs/devops/top-sre-interview-question-answer)
