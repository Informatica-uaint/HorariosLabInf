#!/usr/bin/env python3
"""
Improved Test Runner for HorariosLabInf Back-end APIs
Runs comprehensive unit tests for estudiantes, ayudantes, and lector APIs
"""

import unittest
import sys
import os
import time
import json
from io import StringIO
from datetime import datetime
import tempfile
import subprocess

class TestRunner:
    def __init__(self):
        self.start_time = time.time()
        self.results = {
            'total_tests': 0,
            'total_failures': 0,
            'total_errors': 0,
            'total_skipped': 0,
            'modules': {}
        }
        
    def setup_environment(self):
        """Set up test environment and paths"""
        # Add current directory to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # Set minimal environment variables for testing
        test_env = {
            'SECRET_KEY': 'test-secret-key-for-unit-tests',
            'JWT_SECRET': 'test-jwt-secret-for-unit-tests',
            'MYSQL_HOST': 'localhost',
            'MYSQL_USER': 'test_user',
            'MYSQL_PASSWORD': 'test_password',
            'MYSQL_DB': 'test_database',
            'MYSQL_PORT': '3306',
            'FLASK_ENV': 'testing',
            'LOG_LEVEL': 'ERROR'
        }
        
        for key, value in test_env.items():
            if key not in os.environ:
                os.environ[key] = value
        
        print("🔧 Environment configured for testing")
    
    def discover_test_modules(self):
        """Discover available test modules"""
        test_modules = []
        
        # Look for test files in current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        potential_modules = [
            'test_estudiantes_api',
            'test_ayudantes_api', 
            'test_lector_api',
            # Legacy modules for backward compatibility
            'test_estudiantes',
            'test_ayudantes',
            'test_lector'
        ]
        
        for module_name in potential_modules:
            module_path = os.path.join(current_dir, f"{module_name}.py")
            if os.path.exists(module_path):
                test_modules.append(module_name)
        
        return test_modules
    
    def run_module_tests(self, module_name):
        """Run tests for a specific module"""
        print(f"\n📋 Running tests for: {module_name}")
        print("-" * 50)
        
        module_result = {
            'tests_run': 0,
            'failures': 0,
            'errors': 0,
            'skipped': 0,
            'success': False,
            'duration': 0,
            'details': []
        }
        
        start_time = time.time()
        
        try:
            # Import the test module
            test_module = __import__(module_name)
            
            # Create test suite
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(test_module)
            
            # Count total tests
            test_count = suite.countTestCases()
            if test_count == 0:
                print(f"⚠️  No tests found in {module_name}")
                return module_result
            
            # Run tests with custom result handler
            stream = StringIO()
            runner = unittest.TextTestRunner(
                stream=stream,
                verbosity=2,
                failfast=False,
                buffer=True
            )
            
            result = runner.run(suite)
            
            # Capture results
            module_result['tests_run'] = result.testsRun
            module_result['failures'] = len(result.failures)
            module_result['errors'] = len(result.errors)
            module_result['skipped'] = len(result.skipped)
            module_result['success'] = result.wasSuccessful()
            module_result['duration'] = time.time() - start_time
            
            # Show output
            output = stream.getvalue()
            if output:
                print(output)
            
            # Show summary for this module
            if result.wasSuccessful():
                print(f"✅ {module_name}: ALL {test_count} TESTS PASSED")
            else:
                print(f"❌ {module_name}: {len(result.failures)} failures, {len(result.errors)} errors")
            
            # Show failure details
            if result.failures:
                print(f"\n📝 FAILURES in {module_name}:")
                for i, (test, traceback) in enumerate(result.failures, 1):
                    test_name = str(test).split()[0]
                    # Extract error message
                    error_lines = traceback.split('\n')
                    error_msg = "Unknown failure"
                    for line in error_lines:
                        if 'AssertionError:' in line:
                            error_msg = line.split('AssertionError:')[-1].strip()
                            break
                        elif 'assert' in line.lower() and ('false' in line.lower() or 'true' in line.lower()):
                            error_msg = line.strip()
                            break
                    
                    print(f"  {i}. {test_name}: {error_msg}")
                    module_result['details'].append(f"FAIL: {test_name} - {error_msg}")
            
            # Show error details
            if result.errors:
                print(f"\n💥 ERRORS in {module_name}:")
                for i, (test, traceback) in enumerate(result.errors, 1):
                    test_name = str(test).split()[0]
                    # Extract error type
                    error_lines = traceback.split('\n')
                    error_msg = "Unknown error"
                    for line in error_lines:
                        if 'Error:' in line or 'Exception:' in line:
                            error_msg = line.strip()
                            break
                    
                    print(f"  {i}. {test_name}: {error_msg}")
                    module_result['details'].append(f"ERROR: {test_name} - {error_msg}")
            
            # Show skipped tests
            if result.skipped:
                print(f"\n⏭️  SKIPPED in {module_name}: {len(result.skipped)} tests")
                for test, reason in result.skipped:
                    if "not available" in reason:
                        module_result['details'].append(f"SKIP: {test} - {reason}")
        
        except ImportError as e:
            print(f"⚠️  Could not import {module_name}: {e}")
            print("   (This is normal if dependencies are missing)")
            module_result['details'].append(f"IMPORT ERROR: {str(e)}")
        
        except Exception as e:
            print(f"💥 Unexpected error in {module_name}: {e}")
            module_result['errors'] = 1
            module_result['details'].append(f"UNEXPECTED ERROR: {str(e)}")
        
        return module_result
    
    def run_all_tests(self):
        """Run all discovered tests"""
        print("🧪 RUNNING COMPREHENSIVE UNIT TESTS FOR HORARIOS LAB INF")
        print("=" * 70)
        
        self.setup_environment()
        
        # Discover test modules
        test_modules = self.discover_test_modules()
        
        if not test_modules:
            print("❌ No test modules found!")
            return False
        
        print(f"🔍 Discovered {len(test_modules)} test modules:")
        for module in test_modules:
            print(f"   - {module}")
        
        # Run tests for each module
        for module_name in test_modules:
            module_result = self.run_module_tests(module_name)
            self.results['modules'][module_name] = module_result
            
            # Update totals
            self.results['total_tests'] += module_result['tests_run']
            self.results['total_failures'] += module_result['failures'] 
            self.results['total_errors'] += module_result['errors']
            self.results['total_skipped'] += module_result['skipped']
        
        # Generate final summary
        self.generate_summary()
        
        # Return overall success
        return self.results['total_failures'] == 0 and self.results['total_errors'] == 0
    
    def run_specific_test(self, test_name):
        """Run tests for a specific API"""
        print(f"🎯 Running tests for: {test_name}")
        print("-" * 50)
        
        self.setup_environment()
        
        # Map friendly names to module names
        module_mapping = {
            'estudiantes': ['test_estudiantes_api', 'test_estudiantes'],
            'ayudantes': ['test_ayudantes_api', 'test_ayudantes'],
            'lector': ['test_lector_api', 'test_lector']
        }
        
        possible_modules = module_mapping.get(test_name, [f'test_{test_name}_api', f'test_{test_name}'])
        
        # Find the first available module
        module_to_run = None
        for module_name in possible_modules:
            module_path = os.path.join(os.path.dirname(__file__), f"{module_name}.py")
            if os.path.exists(module_path):
                module_to_run = module_name
                break
        
        if not module_to_run:
            print(f"❌ No test module found for '{test_name}'")
            print(f"   Looked for: {', '.join(possible_modules)}")
            return False
        
        module_result = self.run_module_tests(module_to_run)
        self.results['modules'][module_to_run] = module_result
        self.results['total_tests'] = module_result['tests_run']
        self.results['total_failures'] = module_result['failures']
        self.results['total_errors'] = module_result['errors']
        self.results['total_skipped'] = module_result['skipped']
        
        self.generate_summary()
        
        return module_result['success']
    
    def generate_summary(self):
        """Generate final test summary"""
        duration = time.time() - self.start_time
        
        print("\n" + "=" * 70)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 70)
        
        print(f"🕒 Total execution time: {duration:.2f} seconds")
        print(f"📝 Total tests executed: {self.results['total_tests']}")
        print(f"✅ Tests passed: {self.results['total_tests'] - self.results['total_failures'] - self.results['total_errors']}")
        print(f"❌ Tests failed: {self.results['total_failures']}")
        print(f"💥 Test errors: {self.results['total_errors']}")
        print(f"⏭️  Tests skipped: {self.results['total_skipped']}")
        
        if self.results['total_tests'] > 0:
            success_rate = ((self.results['total_tests'] - self.results['total_failures'] - self.results['total_errors']) / self.results['total_tests']) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")
        
        # Module breakdown
        print(f"\n📋 Module Breakdown:")
        for module_name, result in self.results['modules'].items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"   {module_name}: {status} ({result['tests_run']} tests, {result['duration']:.2f}s)")
        
        # Overall result
        if self.results['total_failures'] == 0 and self.results['total_errors'] == 0:
            print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
        else:
            print(f"\n⚠️  SOME TESTS FAILED OR HAD ERRORS")
            print(f"   Review the details above for specific issues")
        
        print("\n" + "=" * 70)
    
    def generate_junit_xml(self, output_file="test-results.xml"):
        """Generate JUnit XML report for CI/CD"""
        try:
            # Simple XML generation
            xml_content = ['<?xml version="1.0" encoding="UTF-8"?>']
            xml_content.append('<testsuites>')
            
            for module_name, result in self.results['modules'].items():
                xml_content.append(f'  <testsuite name="{module_name}" tests="{result["tests_run"]}" '
                                 f'failures="{result["failures"]}" errors="{result["errors"]}" '
                                 f'skipped="{result["skipped"]}" time="{result["duration"]:.3f}">')
                
                # Add individual test details if available
                for detail in result['details']:
                    if detail.startswith('FAIL:'):
                        test_name, message = detail[5:].split(' - ', 1)
                        xml_content.append(f'    <testcase classname="{module_name}" name="{test_name}">')
                        xml_content.append(f'      <failure message="{message}"></failure>')
                        xml_content.append('    </testcase>')
                    elif detail.startswith('ERROR:'):
                        test_name, message = detail[6:].split(' - ', 1)
                        xml_content.append(f'    <testcase classname="{module_name}" name="{test_name}">')
                        xml_content.append(f'      <error message="{message}"></error>')
                        xml_content.append('    </testcase>')
                
                xml_content.append('  </testsuite>')
            
            xml_content.append('</testsuites>')
            
            with open(output_file, 'w') as f:
                f.write('\n'.join(xml_content))
            
            print(f"📄 JUnit XML report generated: {output_file}")
            
        except Exception as e:
            print(f"⚠️  Could not generate XML report: {e}")
    
    def check_dependencies(self):
        """Check if required dependencies are available"""
        print("🔍 Checking dependencies...")
        
        dependencies = {
            'unittest': 'Built-in Python module',
            'json': 'Built-in Python module',
            'datetime': 'Built-in Python module',
            'time': 'Built-in Python module',
            'os': 'Built-in Python module',
            'sys': 'Built-in Python module'
        }
        
        missing_deps = []
        for dep, description in dependencies.items():
            try:
                __import__(dep)
                print(f"  ✅ {dep}: {description}")
            except ImportError:
                missing_deps.append(dep)
                print(f"  ❌ {dep}: Missing - {description}")
        
        # Check optional dependencies
        optional_deps = {
            'pymysql': 'MySQL database connector',
            'flask': 'Web framework',
            'unittest.mock': 'Mocking library'
        }
        
        print("\n🔍 Optional dependencies:")
        for dep, description in optional_deps.items():
            try:
                __import__(dep)
                print(f"  ✅ {dep}: {description}")
            except ImportError:
                print(f"  ⚠️  {dep}: Not available - {description} (tests will be skipped)")
        
        if missing_deps:
            print(f"\n❌ Missing critical dependencies: {', '.join(missing_deps)}")
            return False
        
        print("\n✅ All critical dependencies available")
        return True

def main():
    """Main entry point"""
    runner = TestRunner()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command in ['help', '--help', '-h']:
            print("🔧 HORARIOS LAB INF TEST RUNNER")
            print("=" * 40)
            print("Usage:")
            print("  python test_runner.py                    - Run all tests")
            print("  python test_runner.py estudiantes        - Run estudiantes API tests")
            print("  python test_runner.py ayudantes          - Run ayudantes API tests")
            print("  python test_runner.py lector             - Run lector QR API tests")
            print("  python test_runner.py check-deps         - Check dependencies")
            print("  python test_runner.py junit              - Run all tests and generate XML")
            print("  python test_runner.py help               - Show this help")
            print("\nTest modules:")
            print("  - test_estudiantes_api.py  (Students API)")
            print("  - test_ayudantes_api.py    (Helpers API)")
            print("  - test_lector_api.py       (QR Reader API)")
            return
        
        elif command == 'check-deps':
            runner.check_dependencies()
            return
        
        elif command == 'junit':
            success = runner.run_all_tests()
            runner.generate_junit_xml()
            sys.exit(0 if success else 1)
        
        elif command in ['estudiantes', 'ayudantes', 'lector']:
            success = runner.run_specific_test(command)
            sys.exit(0 if success else 1)
        
        else:
            print(f"❌ Unknown command: {command}")
            print("Use 'python test_runner.py help' for usage information")
            sys.exit(1)
    
    else:
        # Run all tests
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
