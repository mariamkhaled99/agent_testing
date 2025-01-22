from .execute_github_graphql_query import execute_github_graphql_query

async def get_latest_commit_oid(repo_owner, repo_name, branch_name, token):
    """
    Retrieves the OID of the latest commit in a GitHub repository branch.

    Args:
    repo_owner (str): The owner of the repository.
    repo_name (str): The name of the repository.
    branch_name (str): The name of the branch.
    token (str): A valid GitHub token.

    Returns:
    str: The OID of the latest commit.

    Raises:
    Exception: If the query returns errors or if the branch does not exist.
    """

    query = """
    query($repoOwner: String!, $repoName: String!, $branchName: String!) {
      repository(owner: $repoOwner, name: $repoName) {
        ref(qualifiedName: $branchName) {
          target {
            oid
          }
        }
      }
    }
    """
    variables = {
        "repoOwner": repo_owner,
        "repoName": repo_name,
        "branchName": branch_name
    }
    
    # Ensure execute_github_graphql_query is an async function
    response = await execute_github_graphql_query(query, variables, token)
    
    if "errors" in response:
        raise Exception(f"Query returned errors: {response['errors']}")

    ref = response["data"]["repository"]["ref"]
    if ref is None:
        raise Exception(f"Branch '{branch_name}' does not exist")

    return ref["target"]["oid"]