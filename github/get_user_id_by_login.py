from .execute_github_graphql_query import execute_github_graphql_query

def get_user_id_by_login(login, token):
    query = """
    query($login: String!) {
      user(login: $login) {
        id
      }
    }
    """
    variables = {"login": login}
    result = execute_github_graphql_query(query, variables, token)
    if 'data' in result and 'user' in result['data']:
        return result['data']['user']['id']
    else:
        raise Exception(f"Cannot find user with login: {login}")