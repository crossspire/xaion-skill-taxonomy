import os
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm

from src.gpt import GPT
from src.schema import GPTArgs
from src.db import setup_db, teardown_db
from src.utils import load_sql

#
ROOT_DIR = Path(__file__).parent
CONFIG_PATH = ROOT_DIR / "config.yaml"

# .envファイルから環境変数を読み込む
success = load_dotenv(ROOT_DIR / ".env", override=True)
logger.info(f"load_dotenv: {success}")


def main():
    with open(CONFIG_PATH, "r") as config_file:
        config = yaml.safe_load(config_file)

    # 必要なデータを収集する
    if not (ROOT_DIR / config["sql"]["resume"]["output"]).exists():
        db = setup_db()
        query = load_sql(ROOT_DIR / config["sql"]["resume"]["path"])
        resume_df = db.execute_query(query)
        db.close()
        resume_df.to_csv(ROOT_DIR / config["sql"]["resume"]["output"], index=False)
    else:
        resume_df = pd.read_csv(ROOT_DIR / config["sql"]["resume"]["output"])


    # chatgpt_args = GPTArgs(
    #     api_key=str(os.getenv("AZURE_OPENAI_KEY")),
    #     azure_endpoint=str(os.getenv("AZURE_OPENAI_ENDPOINT")),
    #     api_version=str(os.getenv("AZURE_OPENAI_VERSION")),
    #     model=str(os.getenv("AZURE_OPENAI_ENGINE")),
    #     temperature=float(config["gpt"]["temperature"]),
    #     max_tokens=int(config["gpt"]["max_tokens"]),
    #     timeout=int(config["gpt"]["timeout"]),
    #     verbose=config["gpt"]["verbose"],
    # )
    # gpt = GPT(chatgpt_args)

    # prompt = yaml.safe_load(open(config["prompt"]["skill_matcher"]["path"], "r"))

    # context = prompt["contexts"]
    # messages = context + [{"role": "user", "content": "あいうえお"}]
    # gpt_response, log_info, error = gpt(messages=messages)

    # logger.info(f"gpt response: {gpt_response}")


if __name__ == "__main__":
    main()
