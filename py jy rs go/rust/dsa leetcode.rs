// fn main() {
//     let num = 10;
//     let binary_str = format!("{:b}", num); // "1010"
//     println!("{}", binary_str);
// }

// fn main() {
//     let binary_str = "1010";
//     let num = u32::from_str_radix(binary_str, 2).unwrap(); // Converts "1010" to 10
//     println!("{}", num); // Output: 10
// }

// class Solution:
//     def addBinary(self, a: str, b: str) -> str:
//         v = 0 if a < b else 1
//         a = int(a, 2)
//         b = int(b, 2)
//         c = a + b
//         result = bin(c)[2:]
//         return result

// # Input: a = "1010", b = "1011"
// # Output: "10101"
// a = "1010"
// b = "1011"
// s = Solution()
// result = s.addBinary(a, b)
// print("result: ", result)


impl Solution {
    pub fn add_binary(a: String, b: String) -> String {
    let a_num = u32::from_str_radix(&a, 2).unwrap();
    let b_num = u32::from_str_radix(&b, 2).unwrap();
    let sum = a_num + b_num;
    format!("{:b}", sum)
    }
}