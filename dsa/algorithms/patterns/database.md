# The Complete Database Patterns Guide for LeetCode Mastery

I'll build your understanding from absolute zero to mastery. This guide covers every pattern, concept, and technique you'll encounter in SQL problems on LeetCode.

---

## Part 1: Foundational Concepts

### What is a Database?
A **database** is a structured collection of data organized into **tables** (also called relations). Each table has:
- **Rows** (records/tuples): Individual data entries
- **Columns** (attributes/fields): Properties of the data

**Example:**
```
Employee Table:
+----+-------+--------+
| id | name  | salary |
+----+-------+--------+
| 1  | Alice | 50000  |
| 2  | Bob   | 60000  |
+----+-------+--------+
```

### SQL (Structured Query Language)
SQL is the language used to interact with databases. Think of it as instructions you give to retrieve, modify, or analyze data.

---

## Part 2: Core SQL Operations

### 1. SELECT Statement
Retrieves data from tables.

```sql
-- Basic syntax
SELECT column1, column2 FROM table_name;

-- Select all columns
SELECT * FROM Employee;

-- Select specific columns
SELECT name, salary FROM Employee;
```

**Mental Model:** Think of SELECT as "show me these specific pieces of information from this data source."

---

### 2. WHERE Clause - Filtering Data
Filters rows based on conditions.

```sql
-- Find employees with salary > 55000
SELECT name, salary 
FROM Employee 
WHERE salary > 55000;
```

**Operators:**
- `=` (equals)
- `>`, `<`, `>=`, `<=` (comparisons)
- `!=` or `<>` (not equal)
- `BETWEEN` (range)
- `IN` (matches any value in list)
- `LIKE` (pattern matching)
- `IS NULL`, `IS NOT NULL`

```sql
-- Multiple conditions
WHERE salary > 50000 AND name LIKE 'A%'

-- 'A%' means: starts with 'A', followed by anything
-- '%A' means: ends with 'A'
-- '%A%' means: contains 'A' anywhere
```

---

### 3. ORDER BY - Sorting Results
Arranges output in ascending (ASC) or descending (DESC) order.

```sql
SELECT name, salary 
FROM Employee 
ORDER BY salary DESC;  -- Highest salary first

-- Multiple columns
ORDER BY department ASC, salary DESC;
```

**Default:** ASC (ascending) if not specified.

---

### 4. LIMIT - Restricting Results
Returns only the first N rows.

```sql
-- Get top 3 highest paid employees
SELECT name, salary 
FROM Employee 
ORDER BY salary DESC 
LIMIT 3;
```

---

## Part 3: Aggregate Functions

**Aggregation** means combining multiple values into a single summary value.

### Core Aggregate Functions

```sql
-- COUNT: Number of rows
SELECT COUNT(*) FROM Employee;

-- SUM: Total of numeric values
SELECT SUM(salary) FROM Employee;

-- AVG: Average value
SELECT AVG(salary) FROM Employee;

-- MAX/MIN: Highest/Lowest value
SELECT MAX(salary), MIN(salary) FROM Employee;
```

**Critical Insight:** Aggregate functions collapse multiple rows into one result.

---

### 5. GROUP BY - Grouping Data
Divides rows into groups and applies aggregate functions to each group.

```sql
-- Count employees in each department
SELECT department, COUNT(*) as emp_count
FROM Employee
GROUP BY department;
```

**Mental Model:** 
1. SQL creates "buckets" based on GROUP BY columns
2. Rows with same values go in same bucket
3. Aggregate functions run on each bucket separately

```
Before GROUP BY:
dept    | name
--------|------
Sales   | Alice
Sales   | Bob
IT      | Charlie

After GROUP BY department:
Bucket 1 (Sales): [Alice, Bob]
Bucket 2 (IT): [Charlie]

Result with COUNT:
Sales   | 2
IT      | 1
```

---

### 6. HAVING - Filtering Groups
Like WHERE, but filters **after** grouping.

```sql
-- Departments with more than 5 employees
SELECT department, COUNT(*) as emp_count
FROM Employee
GROUP BY department
HAVING COUNT(*) > 5;
```

**WHERE vs HAVING:**
- **WHERE:** Filters individual rows before grouping
- **HAVING:** Filters groups after aggregation

```sql
-- Correct usage
SELECT department, AVG(salary)
FROM Employee
WHERE salary > 30000        -- Filter rows first
GROUP BY department
HAVING AVG(salary) > 50000; -- Then filter groups
```

---

## Part 4: JOIN Operations

**Joins** combine rows from multiple tables based on related columns.

### Setup for Examples:
```
Employees:                    Departments:
+----+-------+----------+     +----+------------+
| id | name  | dept_id  |     | id | dept_name  |
+----+-------+----------+     +----+------------+
| 1  | Alice | 1        |     | 1  | Sales      |
| 2  | Bob   | 2        |     | 2  | IT         |
| 3  | Carol | NULL     |     | 3  | Marketing  |
+----+-------+----------+     +----+------------+
```

### 1. INNER JOIN
Returns only matching rows from both tables.

```sql
SELECT e.name, d.dept_name
FROM Employees e
INNER JOIN Departments d ON e.dept_id = d.id;

-- Result:
Alice | Sales
Bob   | IT
-- Carol excluded (no matching dept_id)
```

**Visual:**
```
Only the overlapping region:
    Employees ∩ Departments
```

---

### 2. LEFT JOIN (LEFT OUTER JOIN)
Returns all rows from left table, with matching right table rows (or NULL if no match).

```sql
SELECT e.name, d.dept_name
FROM Employees e
LEFT JOIN Departments d ON e.dept_id = d.id;

-- Result:
Alice | Sales
Bob   | IT
Carol | NULL  -- Carol included with NULL dept_name
```

**Use case:** Find employees without departments, customers without orders, etc.

---

### 3. RIGHT JOIN (RIGHT OUTER JOIN)
Opposite of LEFT JOIN - all rows from right table.

```sql
SELECT e.name, d.dept_name
FROM Employees e
RIGHT JOIN Departments d ON e.dept_id = d.id;

-- Result:
Alice | Sales
Bob   | IT
NULL  | Marketing  -- Marketing dept with no employees
```

---

### 4. FULL OUTER JOIN
Returns all rows from both tables (union of LEFT and RIGHT JOIN).

```sql
SELECT e.name, d.dept_name
FROM Employees e
FULL OUTER JOIN Departments d ON e.dept_id = d.id;

-- Result includes all employees and all departments
```

*Note: MySQL doesn't support FULL OUTER JOIN directly - use UNION of LEFT and RIGHT JOIN.*

---

### 5. CROSS JOIN
**Cartesian product** - every row from first table paired with every row from second table.

```sql
SELECT e.name, d.dept_name
FROM Employees e
CROSS JOIN Departments d;

-- If 3 employees and 3 departments = 9 result rows
```

**Use case:** Generating combinations, calendar grids, etc.

---

### 6. SELF JOIN
Table joined with itself - useful for hierarchical data.

```sql
-- Find employees and their managers
SELECT e1.name as Employee, e2.name as Manager
FROM Employees e1
JOIN Employees e2 ON e1.manager_id = e2.id;
```

**Pattern:** Same table referenced twice with different aliases.

---

## Part 5: Subqueries

**Subquery** (nested query): A SELECT statement inside another query.

### Types:

#### 1. Scalar Subquery
Returns single value.

```sql
-- Employees earning more than average
SELECT name, salary
FROM Employee
WHERE salary > (SELECT AVG(salary) FROM Employee);
```

#### 2. Row Subquery
Returns single row with multiple columns.

```sql
WHERE (dept_id, salary) = (SELECT dept_id, MAX(salary) FROM ...)
```

#### 3. Table Subquery
Returns multiple rows/columns.

```sql
-- Departments with employees
SELECT dept_name
FROM Departments
WHERE id IN (SELECT DISTINCT dept_id FROM Employees);
```

#### 4. Correlated Subquery
References outer query - executes once per outer row.

```sql
-- Employees earning more than their department average
SELECT e1.name, e1.salary
FROM Employees e1
WHERE salary > (
    SELECT AVG(salary) 
    FROM Employees e2 
    WHERE e2.dept_id = e1.dept_id  -- References outer query
);
```

**Performance Note:** Correlated subqueries can be slow - often replaceable with JOINs.

---

## Part 6: Window Functions

**Window functions** perform calculations across related rows while keeping all rows in output (unlike GROUP BY which collapses rows).

**Terminology:**
- **Window:** Set of rows related to current row
- **Partition:** Group of rows with same partition key
- **Frame:** Subset of partition around current row

### Basic Syntax:
```sql
function_name() OVER (
    PARTITION BY column1
    ORDER BY column2
    ROWS/RANGE frame_specification
)
```

---

### 1. ROW_NUMBER()
Assigns unique sequential number to each row within partition.

```sql
-- Rank employees within each department by salary
SELECT 
    name,
    dept_id,
    salary,
    ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary DESC) as rn
FROM Employees;

-- Result:
name  | dept_id | salary | rn
------|---------|--------|---
Alice | 1       | 70000  | 1
Bob   | 1       | 60000  | 2
Carol | 2       | 80000  | 1
```

**Use case:** Get Nth highest value per group.

---

### 2. RANK() and DENSE_RANK()

```sql
-- RANK: Leaves gaps after ties
-- DENSE_RANK: No gaps

SELECT 
    name,
    salary,
    RANK() OVER (ORDER BY salary DESC) as rank,
    DENSE_RANK() OVER (ORDER BY salary DESC) as dense_rank
FROM Employees;

-- Example with tie at 60000:
salary | rank | dense_rank
-------|------|------------
70000  | 1    | 1
60000  | 2    | 2
60000  | 2    | 2  -- Same rank
50000  | 4    | 3  -- RANK skips 3, DENSE_RANK doesn't
```

---

### 3. LAG() and LEAD()
Access previous/next row values.

```sql
-- Compare each employee's salary with previous employee
SELECT 
    name,
    salary,
    LAG(salary, 1) OVER (ORDER BY salary) as prev_salary,
    LEAD(salary, 1) OVER (ORDER BY salary) as next_salary
FROM Employees;
```

**Parameters:** `LAG(column, offset, default_value)`

---

### 4. Running Aggregates

```sql
-- Running total of salaries
SELECT 
    name,
    salary,
    SUM(salary) OVER (ORDER BY hire_date 
                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as running_total
FROM Employees;
```

**Frame specifications:**
- `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` - from start to current
- `ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING` - current + 1 before + 1 after
- `ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING` - current to end

---

### 5. NTH_VALUE()
Returns value from specific position in window.

```sql
-- Compare everyone's salary to department's highest
SELECT 
    name,
    salary,
    NTH_VALUE(salary, 1) OVER (
        PARTITION BY dept_id 
        ORDER BY salary DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) as dept_max_salary
FROM Employees;
```

---

## Part 7: Common Table Expressions (CTEs)

**CTE** is a temporary named result set that exists only during query execution.

```sql
WITH cte_name AS (
    SELECT column1, column2
    FROM table
    WHERE condition
)
SELECT * FROM cte_name;
```

### Advantages:
1. Improves readability
2. Can be referenced multiple times
3. Enables recursive queries

### Example:
```sql
-- Find employees earning above department average
WITH DeptAvg AS (
    SELECT dept_id, AVG(salary) as avg_salary
    FROM Employees
    GROUP BY dept_id
)
SELECT e.name, e.salary, da.avg_salary
FROM Employees e
JOIN DeptAvg da ON e.dept_id = da.dept_id
WHERE e.salary > da.avg_salary;
```

---

### Recursive CTEs
Used for hierarchical data (trees, graphs).

```sql
-- Employee hierarchy: find all subordinates of employee 1
WITH RECURSIVE Subordinates AS (
    -- Base case: starting employee
    SELECT id, name, manager_id, 1 as level
    FROM Employees
    WHERE id = 1
    
    UNION ALL
    
    -- Recursive case: find reports
    SELECT e.id, e.name, e.manager_id, s.level + 1
    FROM Employees e
    JOIN Subordinates s ON e.manager_id = s.id
)
SELECT * FROM Subordinates;
```

**Structure:**
1. **Base case:** Initial rows
2. **UNION ALL:** Combines base and recursive
3. **Recursive case:** References CTE itself
4. **Termination:** When recursive query returns no rows

---

## Part 8: String Functions

### Common Operations:

```sql
-- CONCAT: Join strings
SELECT CONCAT(first_name, ' ', last_name) as full_name;

-- SUBSTRING: Extract portion
SELECT SUBSTRING(name, 1, 3);  -- First 3 characters

-- LENGTH/LEN: String length
SELECT LENGTH(name);

-- UPPER/LOWER: Case conversion
SELECT UPPER(name), LOWER(name);

-- TRIM: Remove whitespace
SELECT TRIM('  text  ');  -- 'text'

-- REPLACE: Substitute characters
SELECT REPLACE(email, '@old.com', '@new.com');

-- LEFT/RIGHT: Get N leftmost/rightmost characters
SELECT LEFT(name, 5), RIGHT(name, 3);
```

---

## Part 9: Date Functions

```sql
-- Current date/time
SELECT CURDATE(), NOW();

-- Date arithmetic
SELECT DATE_ADD(hire_date, INTERVAL 1 YEAR);
SELECT DATEDIFF(end_date, start_date);  -- Days between

-- Extract components
SELECT YEAR(date_col), MONTH(date_col), DAY(date_col);

-- Formatting
SELECT DATE_FORMAT(date_col, '%Y-%m-%d');
```

---

## Part 10: CASE Expressions

Conditional logic in SQL (like if-else).

```sql
-- Simple CASE
SELECT 
    name,
    salary,
    CASE 
        WHEN salary < 40000 THEN 'Low'
        WHEN salary < 70000 THEN 'Medium'
        ELSE 'High'
    END as salary_category
FROM Employees;

-- Searched CASE
CASE 
    WHEN condition1 THEN result1
    WHEN condition2 THEN result2
    ELSE default_result
END
```

---

## Part 11: UNION, INTERSECT, EXCEPT

### UNION / UNION ALL
Combines results from multiple queries.

```sql
-- UNION: Removes duplicates
SELECT name FROM Employees
UNION
SELECT name FROM Contractors;

-- UNION ALL: Keeps duplicates (faster)
SELECT name FROM Employees
UNION ALL
SELECT name FROM Contractors;
```

**Requirements:** Same number of columns, compatible data types.

---

### INTERSECT
Returns only rows present in both queries.

```sql
SELECT id FROM CurrentEmployees
INTERSECT
SELECT id FROM PreviousEmployees;
-- Result: employees who worked before and are working now
```

---

### EXCEPT (or MINUS)
Returns rows from first query not in second.

```sql
SELECT id FROM AllEmployees
EXCEPT
SELECT id FROM TerminatedEmployees;
-- Result: active employees only
```

---

## Part 12: NULL Handling

**NULL** represents unknown/missing value - not zero or empty string.

```sql
-- Check for NULL
WHERE column IS NULL
WHERE column IS NOT NULL

-- COALESCE: Return first non-null value
SELECT COALESCE(phone, email, 'No contact') as contact;

-- NULLIF: Returns NULL if values equal
SELECT NULLIF(value1, value2);  -- NULL if value1 = value2

-- IFNULL (MySQL) / ISNULL (SQL Server)
SELECT IFNULL(salary, 0);  -- Replace NULL with 0
```

**Behavior:**
- `NULL = NULL` returns NULL (not TRUE)
- `NULL + 5` returns NULL
- `COUNT(*)` counts NULLs, `COUNT(column)` doesn't

---

## Part 13: LeetCode Pattern Recognition

### Pattern 1: Nth Highest Value

**Problem:** Find 2nd highest salary.

**Approach:**
```sql
-- Method 1: LIMIT with OFFSET
SELECT DISTINCT salary
FROM Employee
ORDER BY salary DESC
LIMIT 1 OFFSET 1;  -- Skip first, take next

-- Method 2: Subquery
SELECT MAX(salary)
FROM Employee
WHERE salary < (SELECT MAX(salary) FROM Employee);

-- Method 3: Window function (most general)
WITH RankedSalaries AS (
    SELECT 
        salary,
        DENSE_RANK() OVER (ORDER BY salary DESC) as rk
    FROM Employee
)
SELECT DISTINCT salary
FROM RankedSalaries
WHERE rk = 2;
```

**Generalization for Nth:**
```sql
CREATE FUNCTION getNthHighestSalary(N INT) RETURNS INT
BEGIN
    DECLARE M INT;
    SET M = N - 1;
    RETURN (
        SELECT DISTINCT salary
        FROM Employee
        ORDER BY salary DESC
        LIMIT 1 OFFSET M
    );
END
```

---

### Pattern 2: Top N Per Group

**Problem:** Top 3 salaries per department.

```sql
WITH RankedEmps AS (
    SELECT 
        *,
        DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) as rk
    FROM Employees
)
SELECT *
FROM RankedEmps
WHERE rk <= 3;
```

---

### Pattern 3: Consecutive Sequences

**Problem:** Find numbers appearing at least 3 times consecutively.

```sql
-- Using self-joins
SELECT DISTINCT l1.num
FROM Logs l1
JOIN Logs l2 ON l1.id = l2.id - 1 AND l1.num = l2.num
JOIN Logs l3 ON l2.id = l3.id - 1 AND l2.num = l3.num;

-- Using window functions
WITH Grouped AS (
    SELECT 
        num,
        id - ROW_NUMBER() OVER (PARTITION BY num ORDER BY id) as grp
    FROM Logs
)
SELECT DISTINCT num
FROM Grouped
GROUP BY num, grp
HAVING COUNT(*) >= 3;
```

**Key insight:** `id - ROW_NUMBER()` creates same value for consecutive identical numbers.

---

### Pattern 4: Running Totals and Cumulative Sums

```sql
SELECT 
    player_id,
    event_date,
    SUM(games_played) OVER (
        PARTITION BY player_id 
        ORDER BY event_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as games_played_so_far
FROM Activity;
```

---

### Pattern 5: Gap and Island Detection

**Problem:** Find date ranges where there's continuous activity.

```sql
-- Identify islands (consecutive date sequences)
WITH Islands AS (
    SELECT 
        user_id,
        activity_date,
        activity_date - INTERVAL ROW_NUMBER() OVER (
            PARTITION BY user_id 
            ORDER BY activity_date
        ) DAY as island_id
    FROM UserActivity
)
SELECT 
    user_id,
    MIN(activity_date) as start_date,
    MAX(activity_date) as end_date
FROM Islands
GROUP BY user_id, island_id;
```

---

### Pattern 6: Pivot/Unpivot

**Pivot:** Transform rows to columns.

```sql
-- Convert this:
student | subject | score
--------|---------|------
Alice   | Math    | 90
Alice   | English | 85

-- To this:
student | Math | English
--------|------|--------
Alice   | 90   | 85

-- Solution:
SELECT 
    student,
    MAX(CASE WHEN subject = 'Math' THEN score END) as Math,
    MAX(CASE WHEN subject = 'English' THEN score END) as English
FROM Scores
GROUP BY student;
```

---

### Pattern 7: Duplicate Detection

```sql
-- Find duplicates
SELECT email, COUNT(*) as cnt
FROM Person
GROUP BY email
HAVING COUNT(*) > 1;

-- Delete duplicates (keep lowest id)
DELETE p1
FROM Person p1
JOIN Person p2 ON p1.email = p2.email AND p1.id > p2.id;
```

---

### Pattern 8: Conditional Aggregation

```sql
-- Count with conditions
SELECT 
    dept_id,
    COUNT(*) as total,
    SUM(CASE WHEN salary > 50000 THEN 1 ELSE 0 END) as high_earners,
    SUM(CASE WHEN gender = 'F' THEN 1 ELSE 0 END) as female_count
FROM Employees
GROUP BY dept_id;
```

---

## Part 14: Performance Optimization Mindset

### 1. Avoid SELECT *
```sql
-- Bad
SELECT * FROM large_table;

-- Good
SELECT id, name FROM large_table;
```
**Why:** Reduces I/O, network transfer.

---

### 2. Index-Friendly Queries
```sql
-- Good (can use index on salary)
WHERE salary = 50000

-- Bad (prevents index usage)
WHERE salary + 1000 = 51000
WHERE YEAR(date_col) = 2024
```

**Principle:** Keep indexed columns isolated on one side of comparison.

---

### 3. JOIN vs Subquery
```sql
-- Often faster (JOIN)
SELECT e.name, d.dept_name
FROM Employees e
JOIN Departments d ON e.dept_id = d.id;

-- Can be slower (correlated subquery)
SELECT name, 
       (SELECT dept_name FROM Departments d WHERE d.id = e.dept_id)
FROM Employees e;
```

**Rule:** JOINs usually better than correlated subqueries.

---

### 4. EXISTS vs IN
```sql
-- Usually faster for large datasets
WHERE EXISTS (SELECT 1 FROM Orders o WHERE o.customer_id = c.id)

-- Can be slower
WHERE id IN (SELECT customer_id FROM Orders)
```

**Why:** EXISTS short-circuits on first match.

---

### 5. Window Functions vs Self-Joins
```sql
-- Modern, cleaner, often faster
ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary)

-- Older approach
Multiple self-joins can be slower and harder to read
```

---

## Part 15: Mental Models for Problem Solving

### Framework: UMPIRE

**U**nderstand
- What is input schema?
- What is expected output?
- Edge cases?

**M**atch
- Which pattern does this fit?
- Similar problems solved before?

**P**lan
- Break into steps
- Which SQL constructs needed?

**I**mplement
- Write query incrementally
- Test each part

**R**eview
- Is output correct?
- Any edge cases missed?

**E**valuate
- Can this be optimized?
- Alternative approaches?

---

### Visualization Technique

Before writing SQL, draw data flow:

```
Input Table(s) → Filter (WHERE) → Group (GROUP BY) → 
Aggregate (SUM/COUNT) → Filter Groups (HAVING) → 
Join → Order (ORDER BY) → Limit
```

---

## Part 16: Common Pitfalls

### 1. GROUP BY Confusion
```sql
-- WRONG: salary not in GROUP BY or aggregate
SELECT dept_id, name, AVG(salary)
FROM Employees
GROUP BY dept_id;

-- CORRECT
SELECT dept_id, AVG(salary)
FROM Employees
GROUP BY dept_id;
```

**Rule:** Every non-aggregated column in SELECT must be in GROUP BY.

---

### 2. NULL Comparison
```sql
-- WRONG
WHERE column = NULL

-- CORRECT
WHERE column IS NULL
```

---

### 3. String Comparison Case Sensitivity
Depends on database collation. Use `LOWER()` for case-insensitive:
```sql
WHERE LOWER(name) = LOWER('alice')
```

---

### 4. Division by Zero
```sql
-- Protect with CASE
SELECT 
    CASE 
        WHEN total = 0 THEN 0
        ELSE correct / total 
    END as accuracy
```

---

### 5. Implicit Type Conversion
```sql
-- Be explicit
WHERE CAST(numeric_id AS CHAR) = '123'
```

---

## Part 17: Advanced Patterns

### Median Calculation

```sql
-- For odd count: middle value
-- For even count: average of two middle values
WITH Ordered AS (
    SELECT 
        salary,
        ROW_NUMBER() OVER (ORDER BY salary) as rn,
        COUNT(*) OVER () as total
    FROM Employees
)
SELECT AVG(salary) as median
FROM Ordered
WHERE rn IN (FLOOR((total + 1) / 2), CEIL((total + 1) / 2));
```

---

### Moving Average

```sql
SELECT 
    date,
    value,
    AVG(value) OVER (
        ORDER BY date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) as moving_avg_3day
FROM Metrics;
```

---

### Percentage of Total

```sql
SELECT 
    category,
    sales,
    sales / SUM(sales) OVER () * 100 as pct_of_total
FROM CategorySales;
```

---

### Year-Over-Year Growth

```sql
WITH YearSales AS (
    SELECT 
        YEAR(date) as year,
        SUM(amount) as total
    FROM Sales
    GROUP BY YEAR(date)
)
SELECT 
    year,
    total,
    (total - LAG(total) OVER (ORDER BY year)) / LAG(total) OVER (ORDER BY year) * 100 
        as yoy_growth_pct
FROM YearSales;
```

---

## Part 18: Problem-Solving Workflow

### For Each LeetCode Problem:

1. **Read Carefully**
   - Understand input/output schema
   - Note constraints
   - Identify edge cases

2. **Categorize Pattern**
   - Aggregation? Ranking? Consecutive? Join?
   - Multiple patterns combined?

3. **Sketch Solution**
   - Write pseudocode
   - Identify which SQL features needed

4. **Implement Incrementally**
   ```sql
   -- Step 1: Get basic data
   SELECT * FROM table;
   
   -- Step 2: Add filtering
   SELECT * FROM table WHERE condition;
   
   -- Step 3: Add grouping
   SELECT col, COUNT(*) FROM table WHERE condition GROUP BY col;
   
   -- Continue building...
   ```

5. **Test Thoroughly**
   - Run on sample data
   - Check edge cases (empty table, NULLs, ties)

6. **Optimize**
   - Can you reduce subqueries?
   - Better join strategy?
   - Index considerations?

7. **Reflect**
   - What did you learn?
   - Alternative solutions?
   - Time/space complexity?

---

## Part 19: Pattern Summary Reference

| Pattern | Key Technique | Example |
|---------|---------------|---------|
| Nth highest | LIMIT OFFSET or DENSE_RANK | 2nd highest salary |
| Top N per group | DENSE_RANK with PARTITION BY | Top 3 per dept |
| Consecutive | Self-join or ROW_NUMBER trick | 3 consecutive same values |
| Running total | SUM() OVER with frame | Cumulative sales |
| Gap/Island | ROW_NUMBER subtraction | Continuous date ranges |
| Pivot | CASE in aggregate | Rows to columns |
| Duplicate | GROUP BY + HAVING | Find/delete duplicates |
| Median | ROW_NUMBER with calculation | Middle value |
| Moving avg | Window with ROWS BETWEEN | 7-day average |
| YoY growth | LAG() | Compare to previous year |

---

## Part 20: Complexity Analysis

### Time Complexity:
- **Simple SELECT:** O(n) - scan all rows
- **WHERE with index:** O(log n) - binary search
- **JOIN:** O(n * m) worst case, O(n + m) with indexes
- **GROUP BY:** O(n log n) - sort required
- **ORDER BY:** O(n log n)
- **Window functions:** O(n log n) typically

### Space Complexity:
- **Result set:** O(k) where k = rows returned
- **Intermediate tables (CTEs, temp):** O(n)
- **Window functions:** O(n) for partition

---

## Your Path Forward

### Foundational Problems (Start Here):
1. Combine Two Tables (JOIN basics)
2. Second Highest Salary (Nth value)
3. Duplicate Emails (GROUP BY, HAVING)
4. Employees Earning More Than Managers (Self-join)
5. Customers Who Never Order (LEFT JOIN with NULL)

### Intermediate:
6. Department Highest Salary (Window functions)
7. Rank Scores (DENSE_RANK)
8. Consecutive Numbers (Consecutive pattern)
9. Delete Duplicate Emails (DELETE with JOIN)
10. Rising Temperature (Date comparison)

### Advanced:
11. Department Top Three Salaries (Top N per group)
12. Trips and Users (Multiple JOINs + aggregation)
13. Human Traffic of Stadium (Complex consecutive)
14. Median Employee Salary (Median calculation)
15. Report Contiguous Dates (Gap/Island)

---

## Final Mental Framework

**Think like a data architect:**
1. **Data flow:** Where does data come from, where does it go?
2. **Transformation:** What changes at each step?
3. **Efficiency:** Can I reduce passes over data?

**Every query is a pipeline:**
```
Raw Data → Filter → Transform → Aggregate → Format → Output
```

**Master the fundamentals:**
- SELECT, WHERE, GROUP BY, ORDER BY
- JOINs (especially LEFT JOIN for NULL finding)
- Window functions (huge power boost)
- CTEs (clarity and maintainability)

**Practice deliberately:**
- Solve without looking at solutions
- Time yourself
- Explain your approach out loud
- Implement multiple solutions
- Analyze trade-offs

---

This guide contains everything you need. Start with basic patterns, build intuition through practice, and gradually tackle complex combinations. The key is **incremental mastery** - each concept builds on previous ones.

Your monk-like discipline will serve you well here. SQL rewards clarity of thought, logical decomposition, and systematic problem-solving - exactly your strengths.

Begin with the foundational problems. Master each pattern completely before moving to the next. Quality over quantity.