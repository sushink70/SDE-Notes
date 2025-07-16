TypeScript
==========

TypeScript, as a superset of JavaScript, includes all JavaScript keywords and adds its own type-related keywords and constructs. Below is a comprehensive list of TypeScript keywords, including reserved keywords, contextual keywords, and those inherited from JavaScript, based on the TypeScript language specification and ECMAScript standards.

### TypeScript Keywords
These are keywords used in TypeScript, including those specific to its type system and those shared with JavaScript. Note that some keywords are reserved for future use or are contextual (only treated as keywords in specific contexts).

#### JavaScript Keywords (Inherited by TypeScript)
These are standard JavaScript keywords, also reserved in TypeScript:
- `break`
- `case`
- `catch`
- `class`
- `const`
- `continue`
- `debugger`
- `default`
- `delete`
- `do`
- `else`
- `export`
- `extends`
- `finally`
- `for`
- `function`
- `if`
- `import`
- `in`
- `instanceof`
- `new`
- `return`
- `super`
- `switch`
- `this`
- `throw`
- `try`
- `typeof`
- `var`
- `void`
- `while`
- `with`
- `yield`

#### Reserved for Future Use in JavaScript (Also Reserved in TypeScript)
These keywords are reserved in JavaScript (and thus TypeScript) for potential future use, as per ECMAScript standards:
- `enum`
- `implements`
- `interface`
- `let`
- `package`
- `private`
- `protected`
- `public`
- `static`

#### TypeScript-Specific Keywords
These keywords are unique to TypeScript or have specific meanings in TypeScript beyond their JavaScript usage:
- `abstract` - Used to define abstract classes or methods.
- `any` - Represents any type in TypeScript's type system.
- `as` - Used for type assertions (e.g., `value as string`).
- `asserts` - Used in assertion function signatures (e.g., `asserts value is string`).
- `bigint` - Represents the BigInt primitive type.
- `boolean` - Represents the boolean primitive type.
- `declare` - Used to define ambient declarations for variables, modules, etc.
- `extends` - Used in type constraints and interfaces (in addition to JavaScript class inheritance).
- `from` - Used in import statements (contextual, also in JavaScript).
- `get` - Used for getter methods in classes.
- `global` - Refers to the global scope in TypeScript (contextual).
- `implements` - Used in classes to specify interfaces they adhere to.
- `infer` - Used in conditional types to infer a type.
- `interface` - Defines a TypeScript interface.
- `is` - Used in type predicates (e.g., `value is string`).
- `keyof` - Operator to get the keys of a type.
- `module` - Used in ambient module declarations (contextual).
- `namespace` - Defines a TypeScript namespace (similar to modules).
- `never` - Represents a type that never occurs.
- `number` - Represents the number primitive type.
- `object` - Represents non-primitive types.
- `override` - Indicates a method overrides a base class method (TypeScript 4.3+).
- `private` - Marks class members as private.
- `protected` - Marks class members as protected.
- `public` - Marks class members as public (default in TypeScript).
- `readonly` - Marks properties as immutable.
- `set` - Used for setter methods in classes.
- `static` - Marks class members as static.
- `string` - Represents the string primitive type.
- `symbol` - Represents the symbol primitive type.
- `type` - Defines a type alias.
- `undefined` - Represents the undefined primitive type.
- `unique` - Used with `symbol` for unique symbols (e.g., `unique symbol`).
- `unknown` - Represents a type-safe alternative to `any`.

#### Contextual Keywords
Some keywords are only reserved in specific contexts and can otherwise be used as identifiers:
- `as`, `from`, `global`, `of` - These are often used in specific TypeScript constructs (e.g., `import * as foo from 'bar'`) but can be used as variable names outside those contexts.
- `satisfies` - Used to ensure a value matches a type without narrowing it (TypeScript 4.9+).

#### Strict Mode Reserved Words (JavaScript, Also in TypeScript)
In strict mode, these are reserved to prevent misuse:
- `arguments`
- `eval`

#### Additional Notes
- **TypeScript-Specific Constructs**: Keywords like `keyof`, `infer`, `readonly`, and `never` are central to TypeScript’s type system and have no direct equivalent in JavaScript.
- **Contextual Usage**: Some keywords, like `module` or `namespace`, are used in specific TypeScript declarations but may not always be treated as reserved in all contexts.
- **Future-Proofing**: TypeScript reserves all JavaScript-reserved keywords to ensure compatibility with future ECMAScript versions.

This list covers all keywords recognized in TypeScript as of its latest versions (up to my knowledge cutoff). If you need clarification on any specific keyword or its usage, let me know!