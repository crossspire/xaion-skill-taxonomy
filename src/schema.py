from pydantic import BaseModel


class GPTArgs(BaseModel):
    """OpenAI GPT arguments
    api_key (str): azure api key
    azure_endpoint (str): azure endpoint
    api_version (str): azure api version (e.g. "2024-03-01-preview")
    model (str): azure model deploy name
    temperature (float): The diversity of to be genaerated (grater than or equal to 0)
    max_tokens (int): The maximum number of tokens to generate
    verbose (bool): If True, print debug information
    """

    api_key: str
    azure_endpoint: str
    api_version: str
    model: str
    temperature: float
    max_tokens: int
    timeout: int
    verbose: bool
