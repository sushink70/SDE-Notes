"""don't provide unwanted code. 
how search bar works? in nextjs app router setup by the help of react hook useDeferredValue. I am using mongodb as backend with multiple database and collections. via nextjs app router api the search will go to the mongodb engine and get the results. what are the libraries and tools can help to secure the search queries. if user got the search results, how to process that? our web is SPA, so how to navigate them to search results? if user click on the search icon, a modal using nextui will popup with search bar. 
provide only SearchBar.tsx,route.ts, mongodb handler code that import from @/lib/mongodb/mongodbhandler to route.ts.
do Input Validation and Sanitization using zod, sanitize-html or DUMPurify or isomorphic-dompurify (which is most best), Helmet, Rate Limiting, validator
Store MongoDB credentials in .env using dotenv. Configure CORS in Next.js API routes to allow only trusted origins.
Next.js caching to store frequent search queries if needed.
implement infinite scroll or pagination on the search results page using libraries like tanstack useinfinityquery.
Use router.push for client-side transitions to avoid full page reloads.
consider this - Authentication and Authorization (Next.js Middleware/API Routes):
NextAuth.js: For full-stack authentication. If your search results are user-specific or require certain permissions, NextAuth.js can help secure your API routes. You can check if a user is authenticated and authorized to perform a search or access specific data.(Note: authentication is optional now, but provide code and comment that for future use.)
JSON Web Tokens (JWT) / Session Management: If not using NextAuth.js, implement secure JWTs or session management to verify the user's identity on each API request. Store JWTs securely (e.g., HTTP-only cookies).
Role-Based Access Control (RBAC): In your MongoDB query logic, ensure that only data the authenticated user is permitted to see is returned. This might involve adding filters based on user roles or ownership.
Transport Layer Security (TLS/SSL):
Always serve your Next.js application over HTTPS. This encrypts all communication between the client and your server, protecting the search queries (and results) from eavesdropping. Vercel (Next.js's creator) provides HTTPS by default.
Rate Limiting:
https://github.com/express-rate-limit/express-rate-limit
Prevent abuse (e.g., denial-of-service attacks, brute-force searches) by implementing rate limiting on your search API endpoint.
Next.js Middleware: You can implement basic rate limiting using Next.js Middleware.
Dedicated libraries/services: For more robust solutions, consider libraries like express-rate-limit (if you were using Express, but concepts apply) or cloud provider services (e.g., AWS WAF, Cloudflare).
Error Handling and Logging:
Implement robust error handling in your API routes to catch unexpected issues and prevent sensitive information from being leaked in error messages.
Log all search queries and any errors to a secure logging system. This helps in auditing, debugging, and identifying potential security incidents."""

import bs4 from "bs4";
import axios from "axios";
import cheerio from "cheerio";

def function_chaining(url):
  try:  
    response = axios.get(url)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    for script in soup(["script", "style"]):
      script.extract()
      text = soup.get_text()
      lines = (line.strip() for line in text.splitlines())
      chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
      text = '\n'.join(chunk for chunk in chunks if chunk)
      return text
  except Exception as e:
    return str(e)
    