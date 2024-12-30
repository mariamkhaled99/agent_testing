# Agent Testing with Git Ingest and LangChain

This project is a proof of concept (PoC) for creating an agent that analyzes code repositories. The agent uses **GitIngest** and **LangChain** to perform the following tasks:
- Identify programming languages and frameworks used in the repository.
- Analyze the repository to define classes, functions, and models that can be covered with unit testing.

## Table of Contents

- [Features](#features)
- [Installation](#installation)


---

## Features

- **Repository Analysis**:
  - Detect programming languages and frameworks used in the codebase.
  - List all classes, functions, and models suitable for unit testing.
- **Streamlit Integration**: An interactive web app for analyzing repositories and displaying results.
- **Git Integration**: Uses GitIngest for efficient repository analysis.
- **AI-Powered Insights**: Leverages LangChain for natural language processing and reasoning.

---

## Installation

Follow these steps to set up the project locally:

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/agent_testing.git
   cd agent_testing
   

2. Set up a virtual environment:
    ```bash
    python -m venv venv
    venv\Scripts\activate

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt


4. Run the Streamlit app:
    ```bash
    streamlit run app.py

    
    