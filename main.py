import json
import os
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm

from src.db import setup_db
from src.gpt import GPT
from src.schema import GPTArgs
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

    # resume_dfを整形する
    formatted_resume_df = []
    for _, row in tqdm(resume_df.iterrows()):
        json_str = row["resume"].strip('"').replace('\\"', '"')
        try:
            data_dict = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSONのデコードに失敗: {row['integration_id']}")
            continue
        skill_str = ""
        for skill in data_dict["skills"]:
            skill_str += skill["name"] + ","
        if 0 < len(skill_str):
            skill_str = skill_str[:-1]

        summary = data_dict["summary"]
        if summary is None:
            summary = ""

        formatted_resume_df.append(
            {
                "name": row["name"],
                "linkedin_id": row["linkedin_id"],
                "skills": skill_str,
                "summary": summary,
                "resume": row["resume"],
            }
        )
    formatted_resume_df = pd.DataFrame(formatted_resume_df)

    # GPTを使ってスキルマッチングを行う
    chatgpt_args = GPTArgs(
        api_key=str(os.getenv("AZURE_OPENAI_KEY")),
        azure_endpoint=str(os.getenv("AZURE_OPENAI_ENDPOINT")),
        api_version=str(os.getenv("AZURE_OPENAI_VERSION")),
        model=str(os.getenv("AZURE_OPENAI_ENGINE")),
        temperature=float(config["gpt"]["temperature"]),
        max_tokens=int(config["gpt"]["max_tokens"]),
        timeout=int(config["gpt"]["timeout"]),
        verbose=config["gpt"]["verbose"],
    )
    gpt = GPT(chatgpt_args)

    prompt = yaml.safe_load(open(config["prompt"]["skill_matcher"]["path"], "r"))

    result_list = []
    for _, row in tqdm(formatted_resume_df.iterrows()):
        context = prompt["contexts"]
        messages = context + [{"role": "user", "content": row["resume"]}]
        gpt_response, log_info, error = gpt(messages=messages)

        if error != "":
            logger.error(f"error: ({row['linkedin_id']}){error}")
            continue

        extracted_skills = {}
        skill_name_set = set()
        try:
            for extract_result in gpt_response.splitlines():
                extract_result = extract_result[:-1] if (extract_result.count("$") == 4 and extract_result[-1] == "$") else extract_result
                name, score, basis, linkedin_skills = extract_result.split("$")
                extracted_skills[name] = {"score": score, "basis": basis, "linkedin_skills": linkedin_skills.split(",")}
                extracted_skills[name]["linkedin_skills"] = [""if skill == " " else skill for skill in extracted_skills[name]["linkedin_skills"]]
                extracted_skills[name]["linkedin_skills"] = [skill if (skill in row["skills"].split(",") or skill == "") else f"({skill})" for skill in extracted_skills[name]["linkedin_skills"]]
                skill_name_set.add(name)
        except ValueError as e:
            logger.error(f"抽出結果のパースに失敗: {row['linkedin_id']}: {extract_result}")
            continue

        result = {
            "name": row["name"],
            "linkedin_id": row["linkedin_id"],
            "linkedin_skills": row["skills"],
            "linkedin_summary": row["summary"],
            "linkedin_resume": row["resume"],
            "completion_tokens": log_info["gpt_used_tokens"].completion_tokens,
            "prompt_tokens": log_info["gpt_used_tokens"].prompt_tokens,
            "total_tokens": log_info["gpt_used_tokens"].total_tokens,
        }
        for i, skill_name in enumerate(sorted(list(skill_name_set))):
            result[f"skill_{i}_name"] = skill_name
            result[f"skill_{i}_score"] = extracted_skills[skill_name]["score"]
            result[f"skill_{i}_basis"] = extracted_skills[skill_name]["basis"]
            result[f"skill_{i}_linkedin_skills"] = extracted_skills[skill_name]["linkedin_skills"]
        result_list.append(result)

        if len(result_list) == config["target"]["n"]:
            break
    result_df = pd.DataFrame(result_list)
    result_df.to_csv(
        ROOT_DIR / config["output"]["extracted_skills"]["path"], index=False
    )

    # 出力結果を解析する
    INPUT_COST_PER_TOKEN = 0.150 / 10**6  # 0.150 USD per 10^6 tokens
    OUTPUT_COST_PER_TOKEN = 0.6 / 10**6  # 0.6 USD per 10^6 tokens

    target_num = len(result_df)
    completion_tokens = result_df["completion_tokens"].sum()
    prompt_tokens = result_df["prompt_tokens"].sum()
    total_tokens = result_df["total_tokens"].sum()
    token_per_person = total_tokens / target_num
    completion_cost = completion_tokens * OUTPUT_COST_PER_TOKEN
    prompt_cost = prompt_tokens * INPUT_COST_PER_TOKEN
    total_cost = completion_cost + prompt_cost
    cost_per_person = total_cost / target_num

    statistics = {
        "target_candidate_num": int(target_num),
        "target_skill_num": int(len(skill_name_set)),
        "completion_tokens": int(completion_tokens),
        "prompt_tokens": int(prompt_tokens),
        "total_tokens": int(total_tokens),
        "token_per_person": float(token_per_person),
        "completion_cost": float(completion_cost),
        "prompt_cost": float(prompt_cost),
        "total_cost": float(total_cost),
        "cost_per_person": float(cost_per_person),
    }
    with open(
        ROOT_DIR / config["output"]["statistics"]["path"], "w", encoding="utf-8"
    ) as f:
        json.dump(statistics, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
