import streamlit as st
import json
import os
import subprocess
import re
import shutil
import stat
import os
import sys

# Function to install a Python package
def install_package(package_name):
    try:
        os.system(f"pip install {package_name}")
        print(f"Successfully installed {package_name}!")
        st.info(f"Successfully installed {package_name}!")

        
    except Exception as e:
        print(f"Failed to install {package_name}: {e}")

def clone_repo(repo_url):
    """Clone the repository."""
    try:
        os.system(f"git clone {repo_url}")
        print(f"Successfully cloned repository: {repo_url}")
        st.info(f"Successfully cloned repository: {repo_url}")
    except Exception as e:
        print(f"Failed to clone repository: {e}")
        sys.exit(1)

def navigate_into_repo_folder(repo_name):
    """Navigate into the repository folder."""
    try:
        os.chdir(repo_name)
        print(f"Navigated into repository folder: {repo_name}")
        st.info(f"Navigated into repository folder: {repo_name}")
    except FileNotFoundError:
        print(f"Repository folder not found: {repo_name}")
        sys.exit(1)

def create_virtual_environment():
    """Create a virtual environment."""
    try:
        os.system("python -m venv venv")
        print("Virtual environment created successfully.")
        st.info("Virtual environment created successfully.")
    except Exception as e:
        print(f"Failed to create virtual environment: {e}")
        sys.exit(1)

def activate_virtual_environment():
    """Activate the virtual environment."""
    try:
        # Determine the activation script path based on the operating system
        if os.name == "nt":  # Windows
            activate_script = os.path.join("venv", "Scripts", "activate.bat")
            command = f"call {activate_script}"  # Use 'call' to execute the batch file
        else:  # macOS and Linux
            activate_script = os.path.join("venv", "bin", "activate")
            command = f"source {activate_script}"  # Use 'source' to execute the shell script

        # Run the activation command in the shell
        os.system(command)
        print("Virtual environment activated successfully.")
        st.info("Virtual environment activated successfully.")
    except Exception as e:
        print(f"Failed to activate virtual environment: {e}")
        sys.exit(1)

def install_requirements():
    """Install requirements from requirements.txt if it exists."""
    if os.path.exists("requirements.txt"):
        try:
            os.system("pip install -r requirements.txt")
            print("Requirements installed successfully.")
            st.info("Requirements installed successfully.")
        except Exception as e:
            print(f"Failed to install requirements: {e}")
            sys.exit(1)
    else:
        print("requirements.txt not found. Skipping requirements installation.")

def install_testing_library():
    """Install the testing library (pytest)."""
    try:
        os.system("pip install pytest")
        print("pytest installed successfully.")
        st.info("pytest installed successfully.")
    except Exception as e:
        print(f"Failed to install pytest: {e}")
        sys.exit(1)

def create_tests_folder():
    """Create a tests folder for unit tests."""
    if not os.path.exists("tests"):
        os.makedirs("tests")
        print("Created tests folder.")
        st.info("Created tests folder.")
    else:
        print("Tests folder already exists.")

def create_pytest_ini():
    """Create a pytest.ini file with the specified configuration."""
    pytest_ini_content = """[pytest]
# Look for tests in the custom_tests folder
testpaths = tests
pythonpath = .

# Match files named test_*.py or *_test.py
python_files = test_*.py *_test.py

# Match functions named test_* or check_*
python_functions = test_* check_*
"""
    with open("pytest.ini", "w") as f:
        f.write(pytest_ini_content)
    print("Created pytest.ini file.")
    st.info("Created pytest.ini file.")



def run_django_tests_and_capture_results():
    try:
        # Run `python manage.py test` and redirect output to a file
        command = "python manage.py test tests --verbosity=2 > test_output.txt 2>&1"
        print(f"Running command: {command}")

        # Execute the command and capture output in the test_output.txt file
        os.system(command)

        # Now, read the contents of the file to get the test results
        with open('test_output.txt', 'r') as file:
            test_output = file.read()

        # Debug: Print raw test output
        print("Raw Django test output:")
        print("====================================================")
        print(test_output)
        print("====================================================")

        return test_output

    except Exception as e:
        print(f"Error running Django tests: {e}")
        return {}

def run_pytest_and_capture_results(file_path):
    try:
        # Construct the full path to the test file
        full_path = os.path.join("tests", file_path)
        
        # Run pytest with the --collect-only flag to list all test methods
        collect_output = os.popen(f"pytest {full_path} --collect-only").read()
        
        # Check if the command was successful
        if "ERROR" in collect_output or "FAILED" in collect_output:
            print("Error collecting test methods.")
            return {}

        # Extract test method names from the output
        test_methods = re.findall(r"<Function\s+(test_\w+)>", collect_output)

        # Run pytest and capture the results
        pytest_output = os.popen(f"pytest {full_path} -v").read()

        # Debug: Print raw pytest output
        print("Raw pytest output:")
        print(pytest_output)

        # Parse the results to determine which tests passed or failed
        test_results = {}
        for line in pytest_output.splitlines():
            if "PASSED" in line or "FAILED" in line or "ERROR" in line:
                # Match the test name more precisely
                match = re.search(r"(\w+::test_\w+)", line)
                if match:
                    test_name = match.group(1).replace('::', '')
                    if test_name not in test_results:  # Ensure each test is only added once
                        if "PASSED" in line:
                            test_results[test_name] = "✅"
                        elif "FAILED" in line or "ERROR" in line:
                            test_results[test_name] = "❌"

        return test_results

    except Exception as e:
        print(f"Error running pytest: {e}")
        return {}
# Function to extract test method names from the code
def extract_test_methods(code):
    # Use regex to find all test method names
    test_methods = re.findall(r"def\s+(test_\w+)", code)
    return test_methods


def run_tests():
    """Run the tests using pytest."""
    # Run pytest using os.system
    return_code = os.system("pytest")
    
    # Check the return code
    if return_code != 0:
        print("Tests failed.")
        sys.exit(1)
    else:
        print("All tests passed!")

# Function to save unit test code to a file
def save_test_file(file_path, code):
    # Ensure the 'tests' folder exists
    os.makedirs("tests", exist_ok=True)
    
    # Construct the full path to the test file
    full_path = os.path.join("tests", file_path)
    
    # Save the test file
    with open(full_path, "w") as f:
        f.write(code)
    st.success(f"Saved test file: {full_path}")

# Function to extract the function being tested from the code
def extract_tested_function(code):
    # Use regex to find the function being tested
    match = re.search(r"from\s+[\w\.]+\s+import\s+(\w+)", code)
    if match:
        return match.group(1)
    return None

def extract_tested_function_django(unit_test_code):
    # Example implementation to extract tested function (you can replace it with your logic)
    # You can use regex or other methods to get the function name being tested
    match = re.search(r"def (\w+)\(", unit_test_code)
    if match:
        return match.group(1)
    return None


def create_test_files_for_functions_django(data):
    for item in data:
        code = item["unit_test_code"]
        tested_function = extract_tested_function_django(code)
        print(f"tested_function name:{tested_function}")
        if tested_function:
            # Create a test file named test_<function_name>.py
            test_file_name = f"test_{tested_function}.py"
            save_test_file(test_file_name, code)
        else:
            st.warning(f"Could not determine the function being tested in: {item['unit_test_id']}")

# Function to create a separate test file for each function
def create_test_files_for_functions(data):
    for item in data:
        code = item["unit_test_code"]
        tested_function = extract_tested_function(code)
        print(f"tested_function name:{tested_function}")
        if tested_function:
            # Create a test file named test_<function_name>.py
            test_file_name = f"test_{tested_function}.py"
            save_test_file(test_file_name, code)
        else:
            st.warning(f"Could not determine the function being tested in: {item['unit_test_id']}")
            
            

# Function to install Jest (JavaScript-specific)
def install_jest():
    try:
        # Check if npm is installed
        os.system("npm -v")
        
        # Install Jest
        os.system("npm install --save-dev jest")
        print("Jest installed successfully.")
    except Exception as e:
        print(f"Failed to install Jest: {e}")
        print("Ensure Node.js and npm are installed and added to the system PATH.")
        exit(1)

# Function to run Jest and capture results (JavaScript-specific)
def run_jest_and_capture_results():
    try:
        # Run Jest and output results to a JSON file
        os.system("npx jest --json --outputFile=test-results.json")
        
        # Read the Jest results from the output file
        with open("test-results.json", "r") as f:
            jest_results = json.load(f)

        # Parse the results to determine which tests passed or failed
        test_results = {}
        for test in jest_results["testResults"]:
            for assertion in test["assertionResults"]:
                test_name = assertion["fullName"]
                status = "✅" if assertion["status"] == "passed" else "❌"
                test_results[test_name] = status

        return test_results
    except Exception as e:
        st.error(f"Error running Jest: {e}")
        return {}

# Function to save unit test code to a file
def save_js_test_file(file_path, code):
    os.makedirs("__tests__", exist_ok=True)
    full_path = os.path.join("__tests__", file_path)
    with open(full_path, "w") as f:
        f.write(code)
    st.success(f"Saved test file: {full_path}")

# Function to extract the function being tested from the code
def extract_js_tested_function(code):
    match = re.search(r"from\s+\w+\s+import\s+(\w+)", code)
    if match:
        return match.group(1)
    return None

# Function to create a separate test file for each function
def create_js_test_files_for_functions(data):
    for item in data:
        code = item["unit_test_code"]
        tested_function = extract_js_tested_function(code)
        if tested_function:
            test_file_name = f"test_{tested_function}.js"
            save_js_test_file(test_file_name, code)
        else:
            st.warning(f"Could not determine the function being tested in: {item['unit_test_id']}")


def delete_repo(repo_name):
    """Delete the cloned repository."""
    def handle_remove_readonly(func, path, exc_info):
        """
        Clear the readonly bit and reattempt the removal.
        This is used when a file cannot be deleted due to permission issues.
        """
        os.chmod(path, stat.S_IWRITE)
        func(path)
    
    try:
        # Ensure the current working directory is not inside the repo folder
        if os.getcwd().endswith(repo_name):
            os.chdir("..")
        
        # Delete the repository folder
        if os.path.exists(repo_name):
            shutil.rmtree(repo_name, onerror=handle_remove_readonly)
            print(f"Repository '{repo_name}' deleted successfully.")
        else:
            print(f"Repository '{repo_name}' not found. No deletion performed.")
    except Exception as e:
        print(f"An error occurred while deleting the repository: {e}")
        
        
def navigate_to_root_folder(root_folder_path):
    """Navigate to the specified root folder."""
    print("i am in navigate django root where mange.py exist ...")
    
    try:
        os.chdir(root_folder_path)  # Change to the root folder path provided
        print(f"Navigated to root folder: {root_folder_path}")
    except FileNotFoundError:
        print(f"Root folder not found: {root_folder_path}")
        sys.exit(1)
    except PermissionError:
        print(f"Permission denied while accessing: {root_folder_path}")
        sys.exit(1)


def extract_test_results(output):
    # Define a pattern that matches from the "System check identified no issues" to the end of the tests.
    pattern = r"(System check identified no issues \(0 silenced\).+?)(test_.+?)(?=\n\n|$)"
    
    match = re.search(pattern, output, re.DOTALL)
    
    if match:
        return match.group(2).strip()  # Extract the test results
    return None


def run_test(repo_url, repo_name, json_input, language,framework):
    st.title("Unit Test Runner with Streamlit")
    
   
    
    # Parse JSON input
    data = json.loads(json_input)
    project_root_path = data[0]['project_root_path']
    
    # Clone the repo and navigate into it
    clone_repo(repo_url=repo_url)
    

    try:
        if 'Python' in language or 'python' in language:
            if 'Django' in framework or 'django' in framework:
                print("i am in django ....")
                print(f"project_root_path:{project_root_path}")
                navigate_to_root_folder(project_root_path)
                create_virtual_environment()
                activate_virtual_environment()
                install_requirements()
                create_test_files_for_functions_django(data)
                test_results = run_django_tests_and_capture_results()
                    
                if test_results:
                    print(f"test_results in django: {test_results}")

                    # Extract number of tests found
                    match_summary = re.search(r"Found (\d+) test\(s\)", test_results)
                    num_tests = int(match_summary.group(1)) if match_summary else 0
                    print(f"Found: {num_tests} tests")
                    st.write(f"Found: {num_tests} tests")
                    test_cases = re.findall(r"(test_[^\s]+) \(([^)]+)\) \.\.\. (\w+)", test_results)
                     # Loop through the extracted test cases and display formatted results
                    for test_name, test_location, test_status in test_cases:
                        # Define the status symbols
                        if test_status == "ok":
                            status_symbol = "✅"  # Success
                        elif test_status == "FAIL":
                            status_symbol = "❌"  # Failure
                        elif test_status == "ERROR":
                            status_symbol = "❗"  # Error
                        else:
                            status_symbol = "❔"  # Unknown

                        # Format the result to show the symbol and test information
                        formatted_result = f"{test_name} → {test_status} {status_symbol} )"
                        print(formatted_result)
                        st.write(formatted_result)
                else:
                    print("No test results found.")
                    st.write("No test results found.")

                    

                
            else:
                print(f"Python in list: {language}")
                navigate_into_repo_folder(repo_name=repo_name)
                create_virtual_environment()
                activate_virtual_environment()
                install_package("pytest")
                install_requirements()
                create_pytest_ini()
                create_test_files_for_functions(data)

                # Run tests and display results
                for item in data:
                    tested_function = extract_tested_function(item["unit_test_code"])
                    
                    if tested_function:
                        test_file_name = f"test_{tested_function}.py"
                        test_results = run_pytest_and_capture_results(test_file_name)
                        print(f"test_results:{test_results}")
                        st.write(f"Test Results for {tested_function}:")
                        
                        for test_name, result in test_results.items():
                            st.write(f"{result} {test_name}")
                    else:
                        st.warning(f"Could not determine the function being tested in: {item['unit_test_id']}")
        
        elif 'JavaScript' in language or 'javascript' in language:
            print(f"JavaScript in list: {language}")
            install_jest()
            create_js_test_files_for_functions(data)
            test_results = run_jest_and_capture_results()
            st.write("Test Results:")
            for test_name, result in test_results.items():
                st.write(f"{result} {test_name}")

    except Exception as e:
        st.error(f"An error occurred: {e}")
     

    # finally:
    #     # Cleanup: Delete the cloned repo
    #     delete_repo(repo_name)

    

   
    