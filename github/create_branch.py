from .execute_github_graphql_query import execute_github_graphql_query

async def create_branch(repository_id, base_oid, branch_name, GITHUB_TOKEN):
    """
    Creates a new branch in a GitHub repository.

    Args:
    repository_id (str): The ID of the repository.
    base_oid (str): The OID of the base commit.
    branch_name (str): The name of the new branch.
    GITHUB_TOKEN (str): A valid GitHub token.

    Returns:
    str: The name of the new branch.

    Raises:
    Exception: If the mutation returns errors.
    """

    query = """
    mutation($input: CreateRefInput!) {
      createRef(input: $input) {
        ref {
          name
        }
      }
    }
    """
    variables = {
        "input": {
            "repositoryId": repository_id,
            "name": f"refs/heads/{branch_name}",
            "oid": base_oid
        }
    }
    
    # Ensure execute_github_graphql_query is an async function
    response = await execute_github_graphql_query(query, variables, GITHUB_TOKEN)
    
    if 'errors' in response:
        raise Exception(f"Mutation returned errors: {response['errors']}")

    return response["data"]["createRef"]["ref"]["name"]