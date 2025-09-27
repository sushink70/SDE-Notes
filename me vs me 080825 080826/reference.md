Keshav's "three-pass approach" is a method for efficiently reading academic research papers, involving three distinct passes to gain progressively deeper understanding. The first pass provides a high-level overview by skimming the title, abstract, introduction, and conclusion. The second pass offers a comprehensive grasp of the paper's content by reading more carefully, but ignoring the detailed proofs and equations. The third pass is the most in-depth, requiring a thorough analysis of the paper to truly understand its contributions, identify any potential flaws, and even to attempt to recreate the work. [1, 2, 3, 4, 5]  
Pass 1: The Quick Scan (5-10 minutes) 

• Goal: Get a general idea of the paper's topic and significance. [1, 4]  
• What to read: Title, abstract, introduction, headings, conclusion, and references. [1, 5]  
• Outcome: Decide if the paper is relevant and what its main contribution is. [5]  

Pass 2: Grasping the Content (Up to 1 hour) [1, 5]  

• Goal: Understand the paper's main arguments and findings without getting bogged down in details. 
• What to read: Read the paper more carefully, focusing on figures, tables, and equations, but skip the detailed proofs. 
• Outcome: Achieve a comprehensive understanding of the paper's core ideas. 

Pass 3: In-depth Analysis (1-5 hours) [1, 5]  

• Goal: Understand the paper in its entirety, including any potential flaws and the details of its experimental work. [5]  
• What to do: Recreate the paper's work or experimental setup, check the statistical tests, and assess the generalizability of the results. [2, 5]  
• Outcome: Fully understand the paper's contributions and limitations. [5]  

This method allows researchers to tailor their reading to their needs, efficiently evaluating papers for literature surveys, background research, or deep dives into specific topics. [2, 6]  

AI responses may include mistakes.

[1] https://www.kaggle.com/general/527494
[2] https://www.scribd.com/document/320203693/PRINT-How-to-Read-a-Paper-Keshav
[3] http://ccr.sigcomm.org/online/files/p83-keshavA.pdf
[4] https://medium.com/@aisuko/the-three-pass-approach-to-read-a-academic-paper-c174ce7ec2cb
[5] https://www.youtube.com/watch?v=Cq_jg4iQ4lk
[6] https://www.scribd.com/document/386345104/HowtoReadaPaper

Not all images can be exported from Search.

In Google's Site Reliability Engineering (SRE), an SLO (Service Level Objective) is a specific, measurable reliability target for a service, while the Error Budget is the maximum acceptable level of unreliability for that service, calculated as 100% minus the SLO. The error budget provides a data-driven mechanism for managing the inherent tension between launching new features and maintaining reliability, allowing development teams to take calculated risks while ensuring overall service stability. When the error budget is depleted, changes are frozen until it can be replenished, promoting innovation within defined limits.  [1, 2, 3, 4]  
Service Level Objectives (SLOs) [2]  

• Purpose: To define a specific, measurable target for a service's performance or reliability, such as 99.9% availability for an API endpoint over 30 days. 
• Internal vs. External: SLOs are typically internal targets agreed upon by teams, which are often more ambitious than external Service Level Agreements (SLAs). 
• Examples: An SLO could specify that 99.9% of requests are successfully processed, or that a service maintains 99.99% availability. 

Error Budgets 

• Definition: The amount of acceptable unreliability for a service, calculated as (1 - SLO). [1, 5]  
• Example: A service with a 99.9% availability SLO has a 0.1% error budget, which represents the allowed downtime or error rate over a specific period. [1, 2]  
• Purpose: 
	• Innovation: Allows development teams to spend the budget on risky actions like launching new features or updates, provided the service doesn't exceed its budget. [3, 4]  
	• Stability: When the error budget is nearly exhausted, it signals that the service is becoming unreliable, and changes should be halted until the budget is replenished. [3, 6]  
	• Alignment: Creates a common goal between SRE and product development, fostering a culture where both teams work together to balance innovation and reliability. [3, 4]  

How They Work Together 

• Data-Driven Decisions: SLOs and error budgets provide a shared, data-driven framework for deciding when and how to launch changes. [3]  
• Risk Management: Teams can assess the risk of new deployments against the available error budget, ensuring that feature velocity doesn't come at the cost of essential stability. [4]  
• Flexibility: The error budget offers flexibility to take chances and innovate, but also sets clear limits to prevent excessive risk and potential outages. [4]  

AI responses may include mistakes.

[1] https://sre.google/workbook/error-budget-policy/
[2] https://www.netdata.cloud/academy/error-budget/
[3] https://sre.google/sre-book/service-best-practices/
[4] https://sre.google/sre-book/introduction/
[5] https://medium.com/google-cloud/google-cloud-adoption-site-reliability-engineering-sre-and-best-practices-for-sli-slo-sla-6670c864c96b
[6] https://cloud.google.com/service-mesh/docs/observability/design-slo

Prompts like "how would you improve your solution?" and peer code reviews are forms of constructive feedback designed to enhance code quality and software development by identifying defects and promoting better design, maintainability, and efficiency. During peer code reviews, reviewers examine code for adherence to conventions, optimal design, correct functionality, and potential complexity, while authors can improve their code by embracing coding standards, using linters, leaving clear comments, and annotating source code before the review. [1, 2, 3]  
How to improve your solution (for code authors): 

• Embrace coding standards: Follow development team guidelines to ensure consistency and readability. [1]  
• Use linters and static analysis tools: These tools can automatically detect potential issues in your code. [1, 4, 5, 6, 7]  
• Leave helpful comments: Explain complex parts of your code to make it easier for others to understand. [1, 8, 9]  
• Annotate your source code: Before a peer review, provide explanations or context for your code changes. [10, 11, 12]  

What to look for in a peer code review (for reviewers): 

• Design and architecture: Check if the code is well-designed and follows good architectural principles. [3, 13, 14]  
• Functionality: Verify that the code works correctly and provides the intended user functionality. [3]  
• Complexity: Ensure the code is not more complex than necessary and that there are no unnecessary parts. [3]  
• Readability: Look for clear variable names, well-structured functions, and adherence to coding conventions. [1, 3, 15, 16, 17]  
• Maintainability: Assess if the code is easy to understand, modify, and extend in the future. [2, 3, 18, 19, 20]  
• Potential defects: Identify bugs or logical errors that could cause problems. [2, 21, 22, 23]  

Best practices for peer code reviews: [10, 24, 25, 26, 27, 28]  

• Set goals and capture metrics: Define what you want to achieve with the review process. 
• Limit review size: Avoid reviewing more than 400 lines of code at a time to maintain focus. 
• Take regular breaks: Don't review for more than 60 minutes at a time to prevent fatigue. 
• Use checklists: Employ checklists to ensure all critical aspects are covered during the review. 
• Establish a process for fixing defects: Have a clear process for addressing issues found during the review. 

==AI responses may include mistakes.==

[1] https://www.atlassian.com/blog/add-ons/4-tips-to-improve-code-quality
[2] https://www.browserstack.com/guide/what-is-peer-testing
[3] https://google.github.io/eng-practices/review/reviewer/looking-for.html
[4] https://moldstud.com/articles/p-the-importance-of-code-refactoring-in-software-maintenance
[5] https://www.linkedin.com/pulse/best-practices-code-review-enhancing-collaboration-quality-kghtf
[6] https://arxiv.org/html/2405.13565v1
[7] https://graphite.dev/guides/code-review-techniques-software-engineering
[8] https://dev.to/hamitseyrek/whyhow-to-write-comment-what-is-cleancode-5hin
[9] https://hutchdatascience.org/AI_for_Efficient_Programming/annotating-your-code.html
[10] https://smartbear.com/learn/code-review/best-practices-for-peer-code-review/
[11] https://daily.dev/blog/software-engineering-best-practices-for-code-review
[12] https://www.merowing.info/code-review-best-practices/
[13] https://www.multitudes.com/blog/code-review-checklist
[14] https://www.servicenow.com/community/developer-blog/blog-5-5-steps-to-conduct-effective-code-reviews/ba-p/3084564
[15] https://www.alooba.com/skills/concepts/product-management/software-development-life-cycle/peer-reviews/
[16] https://bigohtech.com/code-review-for-ios-app
[17] https://google.github.io/eng-practices/review/
[18] https://www.wrike.com/blog/code-review-process/
[19] https://frogslayer.com/blog/code-reviews-as-an-actually-useful-exercise/
[20] https://arxiv.org/html/2406.12655v1
[21] https://medium.com/@shubhadeepchat/best-practices-of-code-review-b4fff998c610
[22] https://softwaremind.com/blog/agile-is-not-enough-learn-about-the-modern-approach-to-product-development/
[23] https://www.drupal.org/case-study/bugs-and-website-breakdowns-how-to-protect-your-project-from-the-most-frequent-errors
[24] https://moldstud.com/articles/p-strategies-for-effective-debugging-in-programming
[25] https://www.wiz.io/academy/code-review-best-practices
[26] https://savvycomsoftware.com/blog/code-review-best-practices-process/
[27] https://www.coderabbit.ai/blog/code-reviews-made-easy-how-to-improve-code-quality
[28] https://savvycomsoftware.com/blog/code-review-best-practices-process/

