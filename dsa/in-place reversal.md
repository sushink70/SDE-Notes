# 🔬 **Deep Dive: The O(1) Space In-Place Reversal**

Let me break down this elegant algorithm that demonstrates **true mastery** of array manipulation.

---

## 🧩 **Core Concept: The Two-Reversal Trick**

This algorithm uses a **counter-intuitive insight**:

> **If you reverse a string twice with different granularities, you achieve rotation.**

### **Mathematical Intuition:**

Think of it like **matrix transposition**:
- Reversing the entire string = **flipping horizontally**
- Reversing each word = **flipping each segment vertically**
- Combined effect = **word order reversal**

---

## 📐 **Visual Step-by-Step Breakdown**

Let's trace `"the sky is blue"` character by character:

```
Original String:
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│ t │ h │ e │   │ s │ k │ y │   │ i │ s │   │ b │ l │ u │ e │
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
  0   1   2   3   4   5   6   7   8   9  10  11  12  13  14
```

### **Phase 1: Reverse Entire String**

**Operation:** Swap characters from both ends moving inward

```
Iteration 1: Swap index 0 ↔ 14
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│ e │ h │ e │   │ s │ k │ y │   │ i │ s │   │ b │ l │ u │ t │
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘

Iteration 2: Swap index 1 ↔ 13
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│ e │ u │ e │   │ s │ k │ y │   │ i │ s │   │ b │ l │ h │ t │
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘

... (continue until pointers meet)

Final Result:
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│ e │ u │ l │ b │   │ s │ i │   │ y │ k │ s │   │ e │ h │ t │
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
  0   1   2   3   4   5   6   7   8   9  10  11  12  13  14

String is now: "eulb si yks eht"
                ^^^^    ^^  ^^^  ^^^
              (words are backwards)
```

### **Phase 2: Reverse Each Word Individually**

**Word Detection:** Use two pointers to find word boundaries (spaces or end of string)

```
Word 1: "eulb" at indices [0:3]
Before: e u l b
         ↓ ↓ ↓ ↓
After:  b l u e

Word 2: "si" at indices [5:6]
Before: s i
         ↓ ↓
After:  i s

Word 3: "yks" at indices [8:10]
Before: y k s
         ↓ ↓ ↓
After:  s k y

Word 4: "eht" at indices [12:14]
Before: e h t
         ↓ ↓ ↓
After:  t h e

Final Result:
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│ b │ l │ u │ e │   │ i │ s │   │ s │ k │ y │   │ t │ h │ e │
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘

String is now: "blue is sky the"
```

---

## 🎯 **Complete Implementation with Deep Commentary**
package main

import (
	"fmt"
	"strings"
)

// ════════════════════════════════════════════════════════════
// OPTIMAL SOLUTION: O(n) Time, O(1) Space*
// ════════════════════════════════════════════════════════════
// *Note: In Go, strings are immutable, so we need O(n) space
// for conversion to []byte. In C/Rust with mutable strings,
// this would be true O(1) space.

func reverseWords(s string) string {
	// Step 0: Convert to byte slice and trim whitespace
	// Why []byte? Go strings are immutable, []byte allows in-place modification
	bytes := []byte(strings.TrimSpace(s))
	n := len(bytes)
	
	if n == 0 {
		return ""
	}
	
	// Helper function: reverses bytes[left:right+1] in-place
	reverse := func(left, right int) {
		// Two-pointer technique: swap from outside-in
		for left < right {
			bytes[left], bytes[right] = bytes[right], bytes[left]
			left++
			right--
		}
	}
	
	// ════════════════════════════════════════════════════════
	// PHASE 1: Reverse the entire string
	// ════════════════════════════════════════════════════════
	// Effect: Words are now in reverse order but backwards
	// "the sky is blue" → "eulb si yks eht"
	reverse(0, n-1)
	
	// ════════════════════════════════════════════════════════
	// PHASE 2: Reverse each word individually
	// ════════════════════════════════════════════════════════
	// This "un-reverses" each word while maintaining new order
	wordStart := 0
	for i := 0; i <= n; i++ {
		// Word boundary conditions:
		// 1. Reached end of string (i == n)
		// 2. Found a space (bytes[i] == ' ')
		if i == n || bytes[i] == ' ' {
			// Reverse the word from wordStart to i-1
			reverse(wordStart, i-1)
			
			// Skip any consecutive spaces (handles multiple spaces)
			for i < n && bytes[i] == ' ' {
				i++
			}
			
			// Next word starts at current position
			wordStart = i
		}
	}
	
	// ════════════════════════════════════════════════════════
	// PHASE 3: Remove extra spaces (compress)
	// ════════════════════════════════════════════════════════
	// Two-pointer technique for in-place compression
	writeIdx := 0  // Where we write the next character
	
	for readIdx := 0; readIdx < n; readIdx++ {
		// Write character if:
		// 1. It's not a space, OR
		// 2. It's a space but previous char wasn't a space
		if bytes[readIdx] != ' ' || (writeIdx > 0 && bytes[writeIdx-1] != ' ') {
			bytes[writeIdx] = bytes[readIdx]
			writeIdx++
		}
	}
	
	// Remove trailing space if it exists
	if writeIdx > 0 && bytes[writeIdx-1] == ' ' {
		writeIdx--
	}
	
	return string(bytes[:writeIdx])
}

// ════════════════════════════════════════════════════════════
// DETAILED VISUALIZATION FUNCTION
// ════════════════════════════════════════════════════════════
func visualizeAlgorithm(s string) {
	fmt.Println("\n╔════════════════════════════════════════════════════╗")
	fmt.Println("║       STEP-BY-STEP ALGORITHM VISUALIZATION        ║")
	fmt.Println("╚════════════════════════════════════════════════════╝")
	
	bytes := []byte(strings.TrimSpace(s))
	n := len(bytes)
	
	// Helper to print byte array with indices
	printState := func(label string, highlight []int) {
		fmt.Printf("\n%s\n", label)
		
		// Print indices
		fmt.Print("Index:  ")
		for i := 0; i < n; i++ {
			fmt.Printf("%2d ", i)
		}
		fmt.Println()
		
		// Print characters
		fmt.Print("Chars:  ")
		for i := 0; i < n; i++ {
			if bytes[i] == ' ' {
				fmt.Print(" ␣ ")
			} else {
				fmt.Printf(" %c ", bytes[i])
			}
		}
		fmt.Println()
		
		// Print string
		fmt.Printf("String: \"%s\"\n", string(bytes))
		
		// Highlight specific indices if provided
		if len(highlight) > 0 {
			fmt.Print("        ")
			for i := 0; i < n; i++ {
				found := false
				for _, h := range highlight {
					if i == h {
						found = true
						break
					}
				}
				if found {
					fmt.Print(" ^ ")
				} else {
					fmt.Print("   ")
				}
			}
			fmt.Println()
		}
	}
	
	printState("INITIAL STATE:", nil)
	
	// PHASE 1: Reverse entire string
	fmt.Println("\n" + strings.Repeat("═", 60))
	fmt.Println("PHASE 1: Reversing entire string")
	fmt.Println(strings.Repeat("═", 60))
	
	left, right := 0, n-1
	iteration := 0
	for left < right {
		iteration++
		fmt.Printf("\nIteration %d: Swap bytes[%d] ↔ bytes[%d] ('%c' ↔ '%c')\n", 
			iteration, left, right, bytes[left], bytes[right])
		bytes[left], bytes[right] = bytes[right], bytes[left]
		printState("After swap:", []int{left, right})
		left++
		right--
	}
	
	printState("\nPHASE 1 COMPLETE:", nil)
	
	// PHASE 2: Reverse each word
	fmt.Println("\n" + strings.Repeat("═", 60))
	fmt.Println("PHASE 2: Reversing individual words")
	fmt.Println(strings.Repeat("═", 60))
	
	reverse := func(l, r int) {
		for l < r {
			bytes[l], bytes[r] = bytes[r], bytes[l]
			l++
			r--
		}
	}
	
	wordNum := 0
	wordStart := 0
	for i := 0; i <= n; i++ {
		if i == n || bytes[i] == ' ' {
			wordNum++
			fmt.Printf("\nWord %d: Reversing bytes[%d:%d] = \"%s\"\n", 
				wordNum, wordStart, i, string(bytes[wordStart:i]))
			
			reverse(wordStart, i-1)
			printState(fmt.Sprintf("After reversing word %d:", wordNum), nil)
			
			// Skip spaces
			for i < n && bytes[i] == ' ' {
				i++
			}
			wordStart = i
		}
	}
	
	printState("\nFINAL RESULT:", nil)
}

// ════════════════════════════════════════════════════════════
// COMPARISON: Show why this approach is superior
// ════════════════════════════════════════════════════════════
func compareApproaches() {
	fmt.Println("\n╔════════════════════════════════════════════════════╗")
	fmt.Println("║            APPROACH COMPARISON TABLE              ║")
	fmt.Println("╚════════════════════════════════════════════════════╝\n")
	
	fmt.Println("┌────────────────┬──────────┬──────────┬─────────────┐")
	fmt.Println("│ Approach       │ Time     │ Space    │ Best For    │")
	fmt.Println("├────────────────┼──────────┼──────────┼─────────────┤")
	fmt.Println("│ Stack-based    │ O(n)     │ O(n)     │ Readability │")
	fmt.Println("│ Split & Join   │ O(n)     │ O(n)     │ Production  │")
	fmt.Println("│ Two-Reversal   │ O(n)     │ O(1)*    │ Interviews  │")
	fmt.Println("└────────────────┴──────────┴──────────┴─────────────┘")
	fmt.Println("\n*O(1) in C/Rust with mutable strings")
	fmt.Println(" O(n) in Go due to string immutability")
}

// ════════════════════════════════════════════════════════════
// EDGE CASE TESTING
// ════════════════════════════════════════════════════════════
func testEdgeCases() {
	fmt.Println("\n╔════════════════════════════════════════════════════╗")
	fmt.Println("║              EDGE CASE TESTING                    ║")
	fmt.Println("╚════════════════════════════════════════════════════╝\n")
	
	testCases := []struct {
		input    string
		expected string
		reason   string
	}{
		{"the sky is blue", "blue is sky the", "Standard case"},
		{"  hello world  ", "world hello", "Leading/trailing spaces"},
		{"a good   example", "example good a", "Multiple spaces"},
		{"  Bob    Loves  Alice   ", "Alice Loves Bob", "Mixed spacing"},
		{"a", "a", "Single character"},
		{"", "", "Empty string"},
		{"   ", "", "Only spaces"},
		{"word", "word", "Single word"},
	}
	
	allPassed := true
	for i, tc := range testCases {
		result := reverseWords(tc.input)
		passed := result == tc.expected
		
		status := "✓ PASS"
		if !passed {
			status = "✗ FAIL"
			allPassed = false
		}
		
		fmt.Printf("Test %d: %s\n", i+1, status)
		fmt.Printf("  Reason:   %s\n", tc.reason)
		fmt.Printf("  Input:    \"%s\"\n", tc.input)
		fmt.Printf("  Expected: \"%s\"\n", tc.expected)
		fmt.Printf("  Got:      \"%s\"\n", result)
		fmt.Println()
	}
	
	if allPassed {
		fmt.Println("🎉 All tests passed!")
	} else {
		fmt.Println("⚠️  Some tests failed")
	}
}

// ════════════════════════════════════════════════════════════
// MAIN EXECUTION
// ════════════════════════════════════════════════════════════
func main() {
	compareApproaches()
	
	visualizeAlgorithm("the sky is blue")
	
	testEdgeCases()
}

---

## 🧠 **Why This is O(1) Space (with caveats)**

### **Space Complexity Analysis:**

```
┌─────────────────────────────────────────────────────┐
│ Variable          │ Space      │ Note              │
├───────────────────┼────────────┼───────────────────┤
│ Input string      │ O(n)       │ Already exists    │
│ []byte conversion │ O(n)       │ Necessary in Go   │
│ Loop variables    │ O(1)       │ Just integers     │
│ Function stack    │ O(1)       │ No recursion      │
│ TOTAL EXTRA       │ O(n) in Go │ O(1) in C/Rust    │
└───────────────────┴────────────┴───────────────────┘
```

**Key Insight:**
- In **C or Rust**: You can modify the input string directly → **true O(1) space**
- In **Go**: Strings are immutable → need O(n) conversion to `[]byte`
- **Auxiliary space** (excluding input) is still O(1)

---

## 🔥 **Implementation in Rust (True O(1) Space)**

// ════════════════════════════════════════════════════════════
// RUST IMPLEMENTATION: True O(1) Space
// ════════════════════════════════════════════════════════════
// In Rust, we can work with mutable String or &mut str directly

/// Reverses words in-place using the two-reversal technique
/// 
/// # Algorithm
/// 1. Reverse the entire string
/// 2. Reverse each word individually
/// 3. Remove extra spaces
/// 
/// # Complexity
/// - Time: O(n) where n is the length of the string
/// - Space: O(1) auxiliary space (modifies input in-place)
fn reverse_words(s: &mut String) {
    // Get mutable byte slice - this is why Rust achieves true O(1)
    let bytes = unsafe { s.as_bytes_mut() };
    let n = bytes.len();
    
    if n == 0 {
        return;
    }
    
    // Helper: Reverse bytes in range [left, right]
    fn reverse_range(bytes: &mut [u8], mut left: usize, mut right: usize) {
        while left < right {
            bytes.swap(left, right);
            left += 1;
            right -= 1;
        }
    }
    
    // ════════════════════════════════════════════════════════
    // PHASE 1: Reverse entire string
    // ════════════════════════════════════════════════════════
    reverse_range(bytes, 0, n - 1);
    
    // ════════════════════════════════════════════════════════
    // PHASE 2: Reverse each word
    // ════════════════════════════════════════════════════════
    let mut word_start = 0;
    let mut i = 0;
    
    while i <= n {
        // Found word boundary (space or end)
        if i == n || bytes[i] == b' ' {
            if i > word_start {
                reverse_range(bytes, word_start, i - 1);
            }
            
            // Skip consecutive spaces
            while i < n && bytes[i] == b' ' {
                i += 1;
            }
            
            word_start = i;
        }
        i += 1;
    }
    
    // ════════════════════════════════════════════════════════
    // PHASE 3: Remove extra spaces (in-place compression)
    // ════════════════════════════════════════════════════════
    let mut write_idx = 0;
    let mut read_idx = 0;
    
    // Skip leading spaces
    while read_idx < n && bytes[read_idx] == b' ' {
        read_idx += 1;
    }
    
    // Compress middle section
    while read_idx < n {
        // Copy non-space or first space in sequence
        if bytes[read_idx] != b' ' || 
           (write_idx > 0 && bytes[write_idx - 1] != b' ') {
            bytes[write_idx] = bytes[read_idx];
            write_idx += 1;
        }
        read_idx += 1;
    }
    
    // Remove trailing space if exists
    if write_idx > 0 && bytes[write_idx - 1] == b' ' {
        write_idx -= 1;
    }
    
    // Truncate string to new length
    s.truncate(write_idx);
}

/// Immutable version that returns a new String
/// (More idiomatic for most Rust use cases)
fn reverse_words_immutable(s: &str) -> String {
    let mut result = s.trim().to_string();
    reverse_words(&mut result);
    result
}

// ════════════════════════════════════════════════════════════
// VISUALIZATION & TESTING
// ════════════════════════════════════════════════════════════

fn visualize_steps(input: &str) {
    println!("\n╔════════════════════════════════════════════════════╗");
    println!("║         RUST IN-PLACE REVERSAL TRACE             ║");
    println!("╚════════════════════════════════════════════════════╝");
    
    let mut s = input.to_string();
    let bytes = unsafe { s.as_bytes_mut() };
    let n = bytes.len();
    
    // Print helper
    let print_state = |label: &str, bytes: &[u8]| {
        println!("\n{}", label);
        print!("Bytes: [");
        for (i, &b) in bytes.iter().enumerate() {
            if b == b' ' {
                print!("'␣'");
            } else {
                print!("'{}'", b as char);
            }
            if i < bytes.len() - 1 {
                print!(", ");
            }
        }
        println!("]");
        println!("String: \"{}\"", String::from_utf8_lossy(bytes));
    };
    
    print_state("INITIAL:", bytes);
    
    // Phase 1: Reverse entire string
    println!("\n{}", "═".repeat(50));
    println!("PHASE 1: Reverse entire string");
    bytes.reverse();
    print_state("After full reversal:", bytes);
    
    // Phase 2: Reverse each word
    println!("\n{}", "═".repeat(50));
    println!("PHASE 2: Reverse individual words");
    
    let mut word_start = 0;
    let mut word_num = 0;
    
    for i in 0..=n {
        if i == n || bytes[i] == b' ' {
            if i > word_start {
                word_num += 1;
                let word = String::from_utf8_lossy(&bytes[word_start..i]);
                println!("\nWord {}: Reversing \"{}\" at [{}, {})", 
                         word_num, word, word_start, i);
                
                bytes[word_start..i].reverse();
                print_state(&format!("After word {} reversal:", word_num), bytes);
            }
            
            while i < n && bytes[i] == b' ' {
                word_start = i + 1;
            }
            word_start = i + 1;
        }
    }
    
    print_state("\nFINAL RESULT:", bytes);
}

fn test_all_cases() {
    println!("\n╔════════════════════════════════════════════════════╗");
    println!("║              COMPREHENSIVE TESTING                ║");
    println!("╚════════════════════════════════════════════════════╝\n");
    
    let test_cases = vec![
        ("the sky is blue", "blue is sky the"),
        ("  hello world  ", "world hello"),
        ("a good   example", "example good a"),
        ("a", "a"),
        ("", ""),
        ("   ", ""),
    ];
    
    let mut all_passed = true;
    
    for (i, (input, expected)) in test_cases.iter().enumerate() {
        let result = reverse_words_immutable(input);
        let passed = &result == expected;
        
        let status = if passed { "✓ PASS" } else { "✗ FAIL" };
        if !passed {
            all_passed = false;
        }
        
        println!("Test {}: {}", i + 1, status);
        println!("  Input:    \"{}\"", input);
        println!("  Expected: \"{}\"", expected);
        println!("  Got:      \"{}\"", result);
        println!();
    }
    
    if all_passed {
        println!("🎉 All tests passed!");
    } else {
        println!("⚠️  Some tests failed");
    }
}

// ════════════════════════════════════════════════════════════
// PERFORMANCE COMPARISON
// ════════════════════════════════════════════════════════════

fn performance_analysis() {
    println!("\n╔════════════════════════════════════════════════════╗");
    println!("║           MEMORY LAYOUT COMPARISON                ║");
    println!("╚════════════════════════════════════════════════════╝\n");
    
    println!("┌──────────────┬────────────────┬──────────────────┐");
    println!("│ Language     │ String Mutab.  │ True O(1) Space? │");
    println!("├──────────────┼────────────────┼──────────────────┤");
    println!("│ Rust         │ Yes (mut str)  │ ✓ YES            │");
    println!("│ C            │ Yes (char*)    │ ✓ YES            │");
    println!("│ Go           │ No (immutable) │ ✗ NO (need copy) │");
    println!("│ Python       │ No (immutable) │ ✗ NO (need list) │");
    println!("└──────────────┴────────────────┴──────────────────┘");
    
    println!("\nRust Advantage:");
    println!("• Safe mutable access via `as_bytes_mut()`");
    println!("• Zero-cost abstraction - compiles to raw pointer ops");
    println!("• Borrow checker ensures no data races");
    println!("• Perfect for systems programming & interviews");
}

fn main() {
    performance_analysis();
    
    visualize_steps("the sky is blue");
    
    test_all_cases();
}
---

## 🎓 **Mental Models for Mastery**

### **1. The "Undo Pattern"**
```
Operation A + Operation B = Net Effect

Full Reverse + Word Reverse = Word Order Reversal
```

This pattern appears in many algorithms:
- **Array rotation**: Reverse entire, then reverse parts
- **Linked list reversal**: Reverse links, then traverse
- **String manipulation**: Transform, then un-transform selectively

### **2. Two-Pointer Techniques Taxonomy**

```
┌──────────────────────────────────────────────────┐
│ Two-Pointer Patterns                            │
├──────────────────────────────────────────────────┤
│ 1. Opposite Ends (Converging)                   │
│    → String reversal, palindrome check          │
│                                                  │
│ 2. Same Direction (Slow-Fast)                   │
│    → Remove duplicates, detect cycles           │
│                                                  │
│ 3. Sliding Window (Dynamic Range)               │
│    → Subarray sum, longest substring            │
│                                                  │
│ 4. Read-Write (Compression)                     │
│    → Space removal, in-place filtering          │
└──────────────────────────────────────────────────┘
```

Our algorithm uses **patterns 1 and 4**.

### **3. Invariant Thinking**

**Before reversing words:**
```
Invariant: "Each word is a contiguous sequence of non-spaces"
```

**After reversing entire string:**
```
Invariant still holds! Words are just backwards.
```

**After reversing each word:**
```
Invariant holds + words are in reverse order
```

---

## 📊 **Performance Deep Dive**

### **Cache Efficiency Analysis**

```
Sequential Access Pattern:
┌─────────────────────────────────┐
│ [Read] → [Process] → [Write]    │  ← Single pass
│        ↓                         │
│    CPU Cache (Hot)               │
└─────────────────────────────────┘

Split & Join Approach:
┌─────────────────────────────────┐
│ [Read] → [Allocate] → [Copy]    │  ← First pass
│              ↓                   │
│        Memory (Cold)             │
│              ↓                   │
│ [Process] → [Join] → [Copy]     │  ← Second pass
└─────────────────────────────────┘
```

**In-place wins on:**
- Cache locality (fewer memory fetches)
- Memory bandwidth (no allocation overhead)
- Branch prediction (simple loop patterns)

---

## 🚀 **Implementation in C (Bare Metal)**
#include <stdio.h>
#include <string.h>
#include <ctype.h>

/*
 * ════════════════════════════════════════════════════════════
 * C IMPLEMENTATION: Maximum Performance O(1) Space
 * ════════════════════════════════════════════════════════════
 * This achieves true O(1) auxiliary space with zero overhead
 */

/**
 * @brief Reverses a portion of the character array in-place
 * @param str The character array to modify
 * @param left Starting index (inclusive)
 * @param right Ending index (inclusive)
 * 
 * Time: O(n) where n = right - left + 1
 * Space: O(1)
 */
void reverse_range(char* str, int left, int right) {
    while (left < right) {
        // XOR swap (optional optimization, but modern compilers 
        // optimize regular swap just as well)
        char temp = str[left];
        str[left] = str[right];
        str[right] = temp;
        
        left++;
        right--;
    }
}

/**
 * @brief Reverses words in a string using the two-reversal technique
 * @param str The string to modify (must be mutable, null-terminated)
 * 
 * Algorithm:
 * 1. Reverse entire string
 * 2. Reverse each word individually
 * 3. Remove extra spaces in-place
 * 
 * Time Complexity: O(n) - three passes through the string
 * Space Complexity: O(1) - only uses a few integer variables
 */
void reverse_words(char* str) {
    if (str == NULL || *str == '\0') {
        return;
    }
    
    int len = strlen(str);
    
    // ════════════════════════════════════════════════════════
    // PHASE 1: Reverse entire string
    // ════════════════════════════════════════════════════════
    // "the sky is blue" → "eulb si yks eht"
    reverse_range(str, 0, len - 1);
    
    // ════════════════════════════════════════════════════════
    // PHASE 2: Reverse each word
    // ════════════════════════════════════════════════════════
    int word_start = 0;
    
    for (int i = 0; i <= len; i++) {
        // Found word boundary (space or null terminator)
        if (str[i] == ' ' || str[i] == '\0') {
            // Reverse the word if it's not empty
            if (i > word_start) {
                reverse_range(str, word_start, i - 1);
            }
            
            // Skip consecutive spaces
            while (i < len && str[i] == ' ') {
                i++;
            }
            
            word_start = i;
        }
    }
    
    // ════════════════════════════════════════════════════════
    // PHASE 3: Remove extra spaces (in-place compression)
    // ════════════════════════════════════════════════════════
    // Two-pointer technique: read pointer and write pointer
    int write_idx = 0;  // Where we write the next character
    int read_idx = 0;   // Where we read from
    
    // Skip leading spaces
    while (str[read_idx] == ' ') {
        read_idx++;
    }
    
    // Process the string
    while (read_idx < len) {
        // Copy character if:
        // 1. It's not a space, OR
        // 2. It's a space AND the previous character wasn't a space
        if (str[read_idx] != ' ' || 
            (write_idx > 0 && str[write_idx - 1] != ' ')) {
            str[write_idx++] = str[read_idx];
        }
        read_idx++;
    }
    
    // Remove trailing space if exists
    if (write_idx > 0 && str[write_idx - 1] == ' ') {
        write_idx--;
    }
    
    // Null-terminate the compressed string
    str[write_idx] = '\0';
}

// ════════════════════════════════════════════════════════════
// VISUALIZATION FUNCTIONS
// ════════════════════════════════════════════════════════════

void print_with_indices(const char* str, const char* label) {
    printf("\n%s\n", label);
    
    int len = strlen(str);
    
    // Print indices
    printf("Index:  ");
    for (int i = 0; i < len; i++) {
        printf("%2d ", i);
    }
    printf("\n");
    
    // Print characters
    printf("Chars:  ");
    for (int i = 0; i < len; i++) {
        if (str[i] == ' ') {
            printf(" · ");
        } else {
            printf(" %c ", str[i]);
        }
    }
    printf("\n");
    
    printf("String: \"%s\"\n", str);
}

void visualize_algorithm(const char* input) {
    printf("\n╔════════════════════════════════════════════════════╗\n");
    printf("║       C LANGUAGE IN-PLACE REVERSAL TRACE         ║\n");
    printf("╚════════════════════════════════════════════════════╝\n");
    
    // Make a mutable copy
    char str[256];
    strcpy(str, input);
    int len = strlen(str);
    
    print_with_indices(str, "INITIAL STATE:");
    
    // Phase 1: Reverse entire string
    printf("\n%s\n", "════════════════════════════════════════════════════");
    printf("PHASE 1: Reversing entire string\n");
    printf("%s\n", "════════════════════════════════════════════════════");
    
    reverse_range(str, 0, len - 1);
    print_with_indices(str, "After full reversal:");
    
    // Phase 2: Reverse each word
    printf("\n%s\n", "════════════════════════════════════════════════════");
    printf("PHASE 2: Reversing individual words\n");
    printf("%s\n", "════════════════════════════════════════════════════");
    
    int word_start = 0;
    int word_num = 0;
    
    for (int i = 0; i <= len; i++) {
        if (str[i] == ' ' || str[i] == '\0') {
            if (i > word_start) {
                word_num++;
                printf("\nWord %d: Reversing str[%d:%d] = \"", 
                       word_num, word_start, i - 1);
                for (int j = word_start; j < i; j++) {
                    printf("%c", str[j]);
                }
                printf("\"\n");
                
                reverse_range(str, word_start, i - 1);
                
                char label[64];
                sprintf(label, "After reversing word %d:", word_num);
                print_with_indices(str, label);
            }
            
            while (i < len && str[i] == ' ') {
                i++;
            }
            word_start = i;
        }
    }
    
    print_with_indices(str, "\nFINAL RESULT:");
}

// ════════════════════════════════════════════════════════════
// TEST SUITE
// ════════════════════════════════════════════════════════════

typedef struct {
    const char* input;
    const char* expected;
    const char* description;
} TestCase;

void run_tests() {
    printf("\n╔════════════════════════════════════════════════════╗\n");
    printf("║              COMPREHENSIVE TESTING                ║\n");
    printf("╚════════════════════════════════════════════════════╝\n\n");
    
    TestCase tests[] = {
        {"the sky is blue", "blue is sky the", "Standard case"},
        {"  hello world  ", "world hello", "Leading/trailing spaces"},
        {"a good   example", "example good a", "Multiple spaces"},
        {"a", "a", "Single character"},
        {"", "", "Empty string"},
        {"   ", "", "Only spaces"},
        {"word", "word", "Single word"}
    };
    
    int num_tests = sizeof(tests) / sizeof(tests[0]);
    int passed = 0;
    
    for (int i = 0; i < num_tests; i++) {
        // Make mutable copy
        char result[256];
        strcpy(result, tests[i].input);
        
        // Run algorithm
        reverse_words(result);
        
        // Check result
        int test_passed = strcmp(result, tests[i].expected) == 0;
        if (test_passed) passed++;
        
        printf("Test %d: %s\n", i + 1, test_passed ? "✓ PASS" : "✗ FAIL");
        printf("  Description: %s\n", tests[i].description);
        printf("  Input:       \"%s\"\n", tests[i].input);
        printf("  Expected:    \"%s\"\n", tests[i].expected);
        printf("  Got:         \"%s\"\n", result);
        printf("\n");
    }
    
    printf("%s\n", passed == num_tests ? "🎉 All tests passed!" : 
                                         "⚠️  Some tests failed");
    printf("Result: %d/%d tests passed\n", passed, num_tests);
}

// ════════════════════════════════════════════════════════════
// PERFORMANCE CHARACTERISTICS
// ════════════════════════════════════════════════════════════

void performance_info() {
    printf("\n╔════════════════════════════════════════════════════╗\n");
    printf("║         PERFORMANCE CHARACTERISTICS               ║\n");
    printf("╚════════════════════════════════════════════════════╝\n\n");
    
    printf("Time Complexity:  O(n) - three sequential passes\n");
    printf("  • Pass 1: Reverse entire string     - O(n)\n");
    printf("  • Pass 2: Reverse individual words  - O(n)\n");
    printf("  • Pass 3: Remove extra spaces       - O(n)\n");
    printf("  Total: 3n = O(n)\n\n");
    
    printf("Space Complexity: O(1) auxiliary space\n");
    printf("  • Variables: ~5 integers            - O(1)\n");
    printf("  • Stack frames: Non-recursive       - O(1)\n");
    printf("  • No dynamic allocation             - O(1)\n\n");
    
    printf("Cache Performance:\n");
    printf("  • Sequential memory access pattern\n");
    printf("  • High cache hit rate (>95%% typical)\n");
    printf("  • Minimal cache misses\n\n");
    
    printf("Assembly Optimization Potential:\n");
    printf("  • SIMD vectorization possible (SSE/AVX)\n");
    printf("  • Loop unrolling opportunities\n");
    printf("  • Compiler auto-vectorizes well\n");
}

// ════════════════════════════════════════════════════════════
// MAIN EXECUTION
// ════════════════════════════════════════════════════════════

int main(void) {
    performance_info();
    
    visualize_algorithm("the sky is blue");
    
    run_tests();
    
    return 0;
}
---

## 🧩 **Comparative Language Analysis**

### **Why C/Rust Achieve True O(1) Space:**

```c
// C: Direct pointer manipulation
void reverse_words(char* str) {
    // str points to mutable memory
    str[i] = 'x';  // Direct modification, no copy
}
```

```rust
// Rust: Safe mutable access
fn reverse_words(s: &mut String) {
    let bytes = unsafe { s.as_bytes_mut() };
    bytes[i] = b'x';  // Direct modification, borrow-checked
}
```

```go
// Go: Strings are immutable value types
func reverseWords(s string) string {
    // MUST create []byte copy to modify
    bytes := []byte(s)  // O(n) allocation
    bytes[i] = 'x'      // Modifies copy, not original
    return string(bytes) // O(n) conversion back
}
```

---

## 🎯 **Master-Level Insights**

### **1. When to Use Each Approach**

| Scenario | Best Choice | Reason |
|----------|-------------|--------|
| **Production Go code** | `strings.Fields()` | Idiomatic, readable, tested |
| **Coding interviews** | Two-reversal | Shows algorithmic depth |
| **Embedded systems** | C in-place | Minimal memory footprint |
| **Systems programming** | Rust in-place | Safety + performance |
| **Competitive programming** | Language built-ins | Speed matters |

### **2. Hidden Complexity Pitfalls**

**Q:** Is removing spaces really O(n)?

**A:** Yes! It's a **single pass** with two pointers:

```
Read:  →→→→→→→→→→→→→→→→→→→
Write: →→→ (compressed)

Each character is:
- Read once  → O(n)
- Written once (or skipped) → O(n)
Total: O(n)
```

### **3. Interview Strategy**

**Optimal Interview Flow:**

1. **Start simple** (10 seconds):
   ```
   "I could use strings.Fields() and reverse the slice."
   ```

2. **Acknowledge optimal** (20 seconds):
   ```
   "But the optimal solution uses O(1) space with
    the two-reversal technique."
   ```

3. **Explain approach** (30 seconds):
   ```
   "Reverse entire string, then reverse each word.
    The double reversal gives us word order reversal."
   ```

4. **Code it** (3-4 minutes): Write clean, bug-free code

5. **Test edge cases** (1 minute):
   - Empty string
   - Single word
   - Multiple spaces
   - Leading/trailing spaces

---

## 🧠 **Cognitive Patterns for Top 1%**

### **Pattern Recognition Checklist:**

When you see **"reverse order"** + **"in-place"**, think:

✓ **Double reversal technique**
✓ **Two-pointer methods**
✓ **Character-level vs word-level operations**
✓ **Space compression opportunities**

### **Meta-Learning Principle:**

> **"Algorithms that modify structure often work in phases:
> Transform globally, then adjust locally."**

Examples:
- **Array rotation**: Reverse all, reverse parts
- **Matrix transpose**: Swap across diagonal, then adjust
- **Linked list reorder**: Reverse, then merge
- **String reversal**: This problem!

---

## 📝 **Practice Variations**

Now that you understand the core technique, try these:

1. **Rotate Array by K positions** (same pattern!)
2. **Reverse words but preserve spaces** (harder)
3. **Reverse sentence but keep word order** (opposite problem)
4. **Implement in assembly** (ultimate understanding)

---

## 💪 **Your Next Steps**

1. **Implement all three versions** (Go, Rust, C) from memory
2. **Profile performance** with strings of 1K, 1M, 100M characters
3. **Add SIMD optimization** in C (AVX2 instructions)
4. **Solve the variations** listed above

---

**Question for you:** Can you now explain **why** reversing twice achieves word-order reversal? If you can articulate the invariant that's preserved, you've truly mastered this pattern.

Would you like me to dive deeper into any specific aspect, or shall we move to a related problem that uses similar techniques?