# Python Best Practices Guide

## Code Organization

### Project Structure
A well-organized Python project separates concerns into distinct modules and packages. Each module should have a single responsibility, and packages should group related modules together.

### Module Design
Follow the principle of least surprise: functions and classes should do what their names suggest. Use clear, descriptive names for variables, functions, and classes. Avoid abbreviations unless they are universally understood.

### Import Organization
Organize imports in three groups separated by blank lines:
1. Standard library imports
2. Third-party library imports
3. Local application imports

## Type Hints

### Why Use Type Hints
Type hints improve code readability, enable better IDE support, and catch bugs early. Python's typing module provides tools for expressing complex types including generics, unions, and optional types.

### Pydantic Models
Pydantic provides data validation using Python type annotations. It's particularly useful for:
- API request/response schemas
- Configuration management
- Data serialization/deserialization

## Error Handling

### Exception Hierarchy
Create custom exception classes that inherit from appropriate base exceptions. This allows callers to catch specific errors while still supporting generic error handling.

### Context Managers
Use context managers (with statements) for resource management. They ensure resources like file handles, database connections, and network sockets are properly cleaned up, even when exceptions occur.

## Testing

### Unit Testing with Pytest
Pytest is the most popular Python testing framework. It provides:
- Simple test discovery based on naming conventions
- Powerful assertion introspection
- Fixtures for setup and teardown
- Parametrized tests for testing multiple inputs

### Test Coverage
Aim for meaningful test coverage rather than arbitrary percentages. Focus on testing:
- Business logic and algorithms
- Edge cases and error conditions
- Integration points between components

## Performance

### Profiling
Use cProfile or py-spy to identify performance bottlenecks. Optimize the hot paths identified by profiling rather than guessing.

### Memory Management
Python's garbage collector handles most memory management, but be aware of:
- Circular references
- Large data structures that persist longer than needed
- Generator expressions for processing large datasets

### Caching
Use `functools.lru_cache` for memoizing expensive pure functions. For more complex caching needs, consider Redis or Memcached.

## Virtual Environments

### Why Virtual Environments
Virtual environments isolate project dependencies, preventing conflicts between different projects. They also make it easy to reproduce the exact same environment on different machines.

### Best Practices
- Always use a virtual environment for each project
- Pin dependency versions in requirements.txt
- Use `pip freeze` to capture exact versions
- Consider using tools like Poetry or pip-tools for dependency management

## Documentation

### Docstrings
Write docstrings for all public modules, functions, classes, and methods. Use the Google or NumPy docstring format for consistency.

### README Files
Every project should have a README that explains:
- What the project does
- How to install and run it
- How to contribute
- License information

## Security

### Environment Variables
Never hardcode secrets, API keys, or passwords in source code. Use environment variables and .env files (excluded from version control) for sensitive configuration.

### Input Validation
Always validate and sanitize user input. Use Pydantic models for API input validation and parameterized queries for database operations to prevent SQL injection.

### Dependency Security
Regularly audit dependencies for known vulnerabilities using tools like `pip-audit` or `safety`. Keep dependencies updated but test thoroughly after updates.
