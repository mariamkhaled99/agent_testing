from .execute_github_graphql_query import execute_github_graphql_query

async def list_branches(REPO_OWNER, REPO_NAME, GITHUB_TOKEN):
    """
    Retrieves a list of branches in a GitHub repository.

    Args:
    REPO_OWNER (str): The owner of the repository.
    REPO_NAME (str): The name of the repository.
    GITHUB_TOKEN (str): A valid GitHub token.

    Returns:
    list: A list of branch names.

    Raises:
    Exception: If the query returns errors.
    """

    query = """
    query($owner: String!, $repo_name: String!) {
      repository(owner: $owner, name: $repo_name) {
        refs(refPrefix: "refs/heads/", first: 100) {
          edges {
            node {
              name
            }
          }
        }
      }
    }
    """
    variables = {"owner": REPO_OWNER, "repo_name": REPO_NAME}
    
    # Ensure execute_github_graphql_query is an async function
    response = await execute_github_graphql_query(query, variables, GITHUB_TOKEN)
    
    if 'errors' in response:
        raise Exception(f"Query returned errors: {response['errors']}")

    branches = response.get("data", {}).get("repository", {}).get("refs", {}).get("edges", [])
    return [branch["node"]["name"] for branch in branches]