"""
YAML 提示词构建器：按五段式拼装 system prompt
"""
import os

import yaml

# 提示词缓存：文件名 → 拼装好的 prompt（避免每次重复读文件）
_cache: dict[str, str] = {}


class BuilderPromptYaml:
    @staticmethod
    def get_prompt(file_name: str) -> str:
        """
        从 YAML 文件读取配置，拼装成五段式 system prompt。

        YAML 结构：
            role: 角色描述
            task: [任务1, 任务2, ...]
            rule: [规则1, 规则2, ...]
            output: [输出要求1, ...]
            example: [示例1, ...]
        """
        if file_name in _cache:
            return _cache[file_name]

        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, file_name)
        with open(file_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        prompt = (
            f"一 角色:{config['role']}\n"
            f"二 任务:\n" + "\n".join(config["task"]) + "\n"
            f"三 规则:\n" + "\n".join(config["rule"]) + "\n"
            f"四 输出:\n" + "\n".join(config["output"]) + "\n"
            f"五 示例:\n" + "\n".join(config["example"]) + "\n"
        ).strip()

        _cache[file_name] = prompt
        return prompt
