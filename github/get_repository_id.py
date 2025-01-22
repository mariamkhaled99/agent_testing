from .execute_github_graphql_query import execute_github_graphql_query

async def get_repository_id(REPO_OWNER, REPO_NAME, GITHUB_TOKEN):
    """
    Retrieves the ID of a GitHub repository.

    Args:
    REPO_OWNER (str): The owner of the repository.
    REPO_NAME (str): The name of the repository.
    GITHUB_TOKEN (str): A valid GitHub token.

    Returns:
    str: The ID of the repository.

    Raises:
    Exception: If the query returns errors or if the repository information cannot be retrieved.
    """

    query = """
    query($owner: String!, $repo_name: String!) {
      repository(owner: $owner, name: $repo_name) {
        id
      }
    }
    """
    variables = {"owner": REPO_OWNER, "repo_name": REPO_NAME}
    
    # Ensure execute_github_graphql_query is an async function
    response = await execute_github_graphql_query(query, variables, GITHUB_TOKEN)
    
    if 'errors' in response:
        raise Exception(f"Query returned errors: {response['errors']}")

    data = response.get("data", {}).get("repository")
    if data is None:
        raise Exception("Failed to retrieve repository information. Please check the repository details and try again.")
    
    return data["id"]