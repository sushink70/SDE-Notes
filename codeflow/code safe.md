Write [language] code that is efficient, secure, scalable, and easy to maintain. 
Avoid unnecessary complexity and follow industry best practices. Add comments for clarity. 
Ensure the code is optimized for performance and free from common vulnerabilities (e.g., SQL injection, XSS, buffer overflow). 
Use appropriate error handling, logging, and modular design. Also, suggest unit tests and performance tips after the code.


Write a scalable, secure, and well-typed React component or API route using Next.js App Router and TypeScript. 
Follow best practices for performance (e.g., code-splitting, memoization, SSR/ISR/CSR as needed), accessibility (ARIA roles, keyboard support), and security (e.g., input sanitization, proper headers). 
Use reusable hooks, modular architecture, and Tailwind CSS (if styling is needed). 
Include type safety with interfaces/types, proper error handling, and suggestions for testing with Jest/React Testing Library. 
Add comments to explain the logic and suggest performance or security optimizations after the code.

Write a production-grade component or API route using React.js (with appropriate built-in hooks like useState, useEffect, useMemo, useCallback, etc.) and Next.js App Router with TypeScript. 
Use only official Next.js features for routing (app directory), data fetching (fetch, getServerSideProps, generateStaticParams, revalidateTag, etc.), and API handling (app/api). 
Follow best practices for performance (lazy loading, memoization), security (input validation, HTTP headers, edge middleware if needed), and maintainability (typed interfaces, reusable components, clear folder structure). 
Use Tailwind CSS (optional), proper accessibility (ARIA), and error boundaries. Include comments, test suggestions (Jest/RTL), and performance tips at the end.

React built-ins: useState, useEffect, useMemo, useCallback, useContext, useRef, etc.
Next.js built-ins:
Routing: app/, dynamic routes [slug]/page.tsx, layout.tsx
Data fetching: fetch, revalidatePath, generateMetadata
API Routes: app/api/[...]/route.ts
Metadata: metadata export
TypeScript: interfaces, type inference
Error handling: error.tsx, try/catch, status codes
Code splitting: dynamic() from Next.js
Testing suggestions: Jest/RTL
Security: Input validation (Zod or manual), headers, sanitization

Write a modern, scalable, and secure component or API route using React (with hooks), Next.js App Router, and TypeScript. 
Use built-in features where possible, and include libraries like TanStack Query for data fetching, React Spring or GSAP for animations (when applicable), and Tailwind CSS for styling. 
Ensure high performance (memoization, lazy loading), accessibility (ARIA), and security (input validation, proper HTTP headers). 
Use modular architecture, typed interfaces, and SSR/ISR/CSR appropriately. Add comments, testing suggestions (Jest/RTL), and optimization tips at the end.

Build a performant and interactive [carousel / coverflow / infinite scroll / notification roster / ad banner] component in a React SPA using Next.js App Router and TypeScript. 
Use only essential and lightweight libraries (e.g., keen-slider, react-spring, react-intersection-observer) when necessary. 
Use TanStack Query for client-side data fetching from a DRF API (e.g., MongoDB content). 
Ensure lazy loading, smooth animation, accessibility (keyboard + ARIA), and responsive design (Tailwind CSS). Add error boundaries, memoization, and proper cleanup in effects. 
Include TypeScript types, comments, test suggestions, and performance tips.

Perfect based on your tech stack (React, Next.js App Router, TypeScript, Django + DRF + Allauth + PostgreSQL, MongoDB, Razorpay, NextAuth), here are 20 AI coding prompts tailored to real-world features using modern libraries, best practices, and high-performance UI/UX components.

---

  Backend-Connected Prompts (Django, DRF, PostgreSQL, MongoDB)

1. Build a secure Django Rest Framework API endpoint to return subscription details for a logged-in user. 
Use PostgreSQL, JWT auth with Django Allauth, and DRF serializers. Include type hints, pagination, and permissions.

2. Create a DRF API that fetches and filters user analytics data from a PostgreSQL database. 
Use Django filters, annotate counts, and return structured JSON. Add input validation and rate limiting.

3. Build a DRF endpoint to log ad impressions and clicks in MongoDB for analytics purposes. 
Implement proper schema validation and suggest index strategies for high write throughput.

4. Create a DRF API that triggers a Razorpay payment initiation and returns the order ID. 
Validate user session with Allauth and restrict to active subscribers.

5. Design a Django Celery task to periodically update ad performance stats stored in MongoDB and cache results using Redis. 
Include retry logic and monitoring best practices.

---

  Frontend UI Prompts (Next.js App Router, React, TS, Tailwind)

6. Build a responsive carousel for featured ads using `keen-slider` in a React SPA. Use TypeScript, Tailwind, and lazy load images for performance. 
Animate with Framer Motion.

7. Create a notification roster component that cycles through messages using `setInterval` and `react-transition-group` for animations. 
Support manual pause/play and auto-dismiss.

8. Implement infinite scroll with TanStack Query and `react-intersection-observer` to load blog posts from a MongoDB-backed DRF API. 
Debounce loading and include error handling.

9. Build a coverflow-style testimonial slider using `react-spring`. Add navigation controls, ARIA accessibility, and dynamic sizing.

10. Create a user dashboard layout with a sticky sidebar, conditional rendering based on subscription status (fetched via TanStack Query), and skeleton loaders.

---

  Authentication & Session Prompts (NextAuth, Allauth)

11. Set up authentication in a Next.js App Router app using NextAuth with JWT strategy. 
Connect to Django Allauth backend to sync sessions. Handle token refresh and secure cookies.

12. Create a protected route in Next.js (App Router) that only allows users with active subscriptions. 
Use middleware for auth checks and redirect unauthenticated users.

13. Build a login page in Next.js using NextAuth and Tailwind CSS. 
Show social login options and redirect users after successful login with a smooth transition.

---

  Payments & Subscriptions (Razorpay, PostgreSQL, DRF)

14. Implement a Razorpay checkout flow in a React component. 
Fetch the Razorpay order from a Django API, collect payment, and verify on the server.

15. Build a DRF webhook endpoint to handle Razorpay payment success and update the user subscription in PostgreSQL. 
Ensure HMAC validation and error logging.

16. Create a Next.js pricing page using static generation and Tailwind CSS. 
Include dynamic plan data from MongoDB and animate price card selection.

---

  Reusable Components & State Management

17. Create a global notification system using Zustand or Jotai for state management. 
Allow triggering toast-like alerts from anywhere in the app. Use Framer Motion for animations.

18. Build a reusable modal component with Headless UI and Tailwind. 
Trigger the modal for ads, payments, or alerts with smooth entry/exit animations.

19. Create a hook (`useUserSubscription`) that fetches and caches subscription status from the backend using TanStack Query.
Auto-refetch on login or subscription change.

20. Implement a dynamic ad placement system where banners rotate every X seconds and fetch ad data from a MongoDB API. 
Track impressions and clicks with useEffect + IntersectionObserver.

---

 1. Hardened Authentication & Authorization

Create a Next.js App Router authentication flow using NextAuth with JWT, integrating Django Allauth as the identity provider. 
Enforce multi-factor authentication (MFA) via TOTP (e.g., Authenticator apps). Include CSRF protection, secure cookie flags, and robust session handling. 
Provide production-grade error handling and security headers. 

 2. Role-Based Access Control (RBAC)

Implement RBAC in Django Rest Framework: define `Admin`, `Editor`, and `Viewer` roles in PostgreSQL, enforce permissions in DRF viewsets, and generate signed JWTs with custom claims. 
Use Django-Guardian for object-level permissions and include unit tests for each role s access. 

 3. OAuth2 with External Providers

Build OAuth2 login in Next.js using NextAuth and Auth0 as the provider. Configure PKCE, refresh tokens, rotating secrets via HashiCorp Vault, and secure token storage. 
Include middleware to validate scopes on API routes. 

 4. Input Validation & Sanitization

Create a DRF endpoint that accepts HTML content (user comments). Use Django-Clean-Fields and Bleach (or DOMPurify in Next.js) to sanitize input against XSS. 
Include automated tests to verify malicious payloads are stripped. 

 5. API Rate Limiting & Throttling

Set up API rate limiting in Django with `drf-extensions` or `django-ratelimit`, and in Next.js using `express-rate-limit` on a custom server or middleware. 
Return standardized `429 Too Many Requests` responses and include Redis for counter storage. 

 6. Secure Headers & Content Security Policy

Configure HTTP security headers in Next.js using `helmet` (via a custom server or middleware): HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, and a strict CSP. 
Show how to report CSP violations to a monitoring endpoint. 

 7. Encryption at Rest & In Transit

Demonstrate how to encrypt sensitive fields (e.g., user PII, payment tokens) in PostgreSQL using `pgcrypto`, and how to enforce TLS 1.2+ for all Django/Next.js endpoints. 
Include certificate rotation via AWS ACM or Let s Encrypt. 

 8. Secrets Management

Integrate HashiCorp Vault (or AWS Secrets Manager) to store Django `SECRET_KEY`, database credentials, and Razorpay API keys. 
Show how to fetch secrets at runtime in Django settings and Next.js using environment variable injection in Vercel. 

 9. Dependency Scanning & SCA

Add Snyk (or GitHub Dependabot) to CI/CD to scan Python and npm dependencies for known vulnerabilities. 
Configure pull-request alerts and automatic PRs for patching. Include a failing build on high-severity findings. 

 10. Automated Security Testing

Create a GitHub Actions pipeline step that runs `bandit` for Python and `npm audit` for JavaScript. 
Then run OWASP ZAP against your staging environment to detect common web vulnerabilities. Fail the pipeline on medium-or-higher issues. 

 11. Secure File Uploads

Implement a file upload endpoint in DRF that stores images to AWS S3 with presigned URLs. Validate MIME types, limit file sizes, sanitize filenames, and scan uploads with ClamAV before saving. 

 12. Cross-Origin & CORS Configuration

Configure CORS in Django using `django-cors-headers` and in Next.js via custom headers to only allow your SPA s domain. 
Reject all other origins and include support for credentials when needed. 

 13. Database Security & Auditing

Set up PostgreSQL roles with least-privilege access for your Django app. Enable `pgaudit` to log DDL and DML changes. 
Rotate DB passwords monthly via Vault and configure a leak-proof backup process. 

 14. Secure WebSockets & Real-Time

Build a secure WebSocket endpoint in Next.js (or using Pusher) for notification rosters. 
Authenticate via a signed JWT, enforce origin checks, and use SSL/TLS. Throttle connections and log suspicions. 

 15. Payment Security & PCI Compliance

Implement Razorpay checkout in React, then verify payments in DRF using HMAC signature verification. 
Do not store card data on your servers; use only tokenized keys. Document PCI-DSS considerations and server-side logging. 

 16. OAuth Scopes & API Gateways

Use AWS API Gateway (or Kong) in front of your DRF APIs. Configure OAuth scopes, request validation, IP whitelisting, and usage plans. 
Include usage-based throttling via API keys. 

 17. Web Application Firewall (WAF)

Demonstrate how to set up AWS WAF (or Cloudflare WAF) rules to protect against SQLi, XSS, and bots. 
Integrate with CloudFront in front of your Next.js app. Show metrics and alerting in AWS CloudWatch. 

 18. Static Code Analysis & Linting

Configure ESLint with security plugins (`eslint-plugin-security`, `jsx-a11y`) for the Next.js codebase, and Flake8 + Bandit for Django. 
Integrate pre-commit hooks using `pre-commit` to enforce style and catch vulnerabilities. 

 19. Secure CI/CD & Infrastructure as Code

Write Terraform modules to provision your Django+PostgreSQL stack on AWS EKS, using Pod Security Policies, Network Policies (Calico), and Secrets in Kubernetes via Sealed Secrets. Enforce GitOps with FluxCD. 

 20. Monitoring, Logging & Incident Response

Implement structured logging in Django (using `structlog`) and Next.js (winston or pino). Centralize logs in ELK or Datadog, set up security alerts for suspicious activity, and document an incident response playbook. 

---

