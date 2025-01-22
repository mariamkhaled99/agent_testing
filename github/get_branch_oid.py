from .execute_github_graphql_query import execute_github_graphql_query

async def get_branch_oid(REPO_OWNER, REPO_NAME, branch_name, GITHUB_TOKEN):
    """
    Retrieves the OID of a branch in a GitHub repository.

    Args:
    REPO_OWNER (str): The owner of the repository.
    REPO_NAME (str): The name of the repository.
    branch_name (str): The name of the branch.
    GITHUB_TOKEN (str): A valid GitHub token.

    Returns:
    str: The OID of the branch.

    Raises:
    Exception: If the query returns errors or if the branch information cannot be retrieved.
    """

    query = """
    query($owner: String!, $repo_name: String!, $branch_name: String!) {
      repository(owner: $owner, name: $repo_name) {
        ref(qualifiedName: $branch_name) {
          target {
            ... on Commit {
              oid
            }
          }
        }
      }
    }
    """
    variables = {"owner": REPO_OWNER, "repo_name": REPO_NAME, "branch_name": f"refs/heads/{branch_name}"}
    
    # Ensure execute_github_graphql_query is an async function
    response = await execute_github_graphql_query(query, variables, GITHUB_TOKEN)
    
    if 'errors' in response:
        raise Exception(f"Query returned errors: {response['errors']}")

    data = response.get("data", {}).get("repository", {}).get("ref")

    if data is None or data.get("target") is None:
        raise Exception(f"Failed to retrieve branch information for branch '{branch_name}'. Please check the branch name and try again.")

    return data["target"]["oid"]