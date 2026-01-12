#include <iomanip>
#include <iostream>
#include BLAZINGIO

int main() {
#ifndef cout
    std::cout << std::setprecision(16);
#endif
    float x;
    while (std::cin >> x) {
        std::cout << x << std::endl;
    }
    return 0;
}
