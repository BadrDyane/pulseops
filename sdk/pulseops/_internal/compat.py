def is_async_openai_client(client: object) -> bool:
    return type(client).__name__ == "AsyncOpenAI"


def is_sync_openai_client(client: object) -> bool:
    return type(client).__name__ == "OpenAI"