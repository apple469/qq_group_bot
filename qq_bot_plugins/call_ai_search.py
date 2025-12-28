from tavily import TavilyClient

def search(text: str,key: str):
    client = TavilyClient(key)
    for i in range(3):
        try:
            response = client.search(
                query=text
            )
            return response
        except:
            continue
    return None
