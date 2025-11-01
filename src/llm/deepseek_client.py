"""
DeepSeek API 客户端封装
兼容OpenAI API格式，专为评估系统优化
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import openai
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DeepSeekConfig:
    """DeepSeek API配置"""

    api_key: str
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"  # 或 deepseek-coder
    temperature: float = 0.1  # 评估用低温度
    max_tokens: int = 4096
    max_retries: int = 3
    retry_delay: int = 2  # 秒


class DeepSeekClient:
    """DeepSeek API客户端"""

    def __init__(self, config: Optional[DeepSeekConfig] = None):
        if config is None:
            config = DeepSeekConfig(
                api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            )

        self.config = config
        self.client = OpenAI(api_key=config.api_key, base_url=config.base_url)

        # 用于成本追踪
        self.total_tokens = 0
        self.total_cost = 0.0

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        response_format: Optional[Dict] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        发送完成请求到DeepSeek

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度参数（覆盖默认值）
            response_format: 响应格式（如 {"type": "json_object"}）
            max_tokens: 最大token数

        Returns:
            包含响应和元数据的字典
        """

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        # 重试机制
        for attempt in range(self.config.max_retries):
            try:
                # 构建请求参数
                kwargs = {
                    "model": self.config.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }

                # 如果需要JSON响应
                if response_format:
                    kwargs["response_format"] = response_format

                # 发送请求
                response = self.client.chat.completions.create(**kwargs)

                # 提取内容
                content = response.choices[0].message.content

                # 如果期望JSON格式，尝试解析
                if response_format and response_format.get("type") == "json_object":
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON解析失败: {e}")

                # 更新token统计
                usage = response.usage
                self.total_tokens += usage.total_tokens
                self._update_cost(usage.total_tokens)

                # 返回结果
                return {
                    "content": content,
                    "raw_response": response,
                    "tokens_used": usage.total_tokens,
                    "model": response.model,
                    "finish_reason": response.choices[0].finish_reason,
                }

            except openai.RateLimitError:
                logger.warning(f"触发限流，等待{self.config.retry_delay}秒后重试...")
                time.sleep(self.config.retry_delay)

            except openai.APIError as e:
                logger.error(f"API错误 (尝试 {attempt + 1}/{self.config.max_retries}): {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)
                else:
                    raise

            except Exception as e:
                logger.error(f"未预期的错误: {e}")
                raise

        raise Exception("达到最大重试次数")

    def batch_complete(
        self, prompts: List[str], system_prompt: Optional[str] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        批量处理多个提示

        Args:
            prompts: 提示列表
            system_prompt: 统一的系统提示
            **kwargs: 传递给complete的其他参数

        Returns:
            响应列表
        """
        results = []
        for i, prompt in enumerate(prompts):
            logger.info(f"处理第 {i+1}/{len(prompts)} 个提示")
            try:
                result = self.complete(prompt, system_prompt, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"处理第 {i+1} 个提示失败: {e}")
                results.append({"error": str(e), "content": None})

        return results

    def evaluate_with_llm(
        self,
        source_text: str,
        extracted_json: Dict,
        evaluation_prompt_template: str,
        criteria: List[str],
    ) -> Dict[str, Any]:
        """
        使用LLM进行评估（专门为评估任务优化）

        Args:
            source_text: 原始文本
            extracted_json: 提取的JSON
            evaluation_prompt_template: 评估提示模板
            criteria: 评估标准列表

        Returns:
            评估结果
        """

        # 构建评估提示
        prompt = evaluation_prompt_template.format(
            source_text=source_text,
            extracted_json=json.dumps(extracted_json, ensure_ascii=False, indent=2),
            criteria="\n".join(f"- {c}" for c in criteria),
        )

        # 系统提示 - 强调客观评估
        system_prompt = """你是一个专业的剧本分析评估专家。请客观、严格地评估提取结果的质量。

评估时请遵循以下原则：
1. 基于提供的评估标准进行评分
2. 提供具体的推理过程
3. 指出具体的问题和改进建议
4. 使用0-1的评分范围，0.6以下为不合格，0.8以上为优秀

请以JSON格式返回评估结果。"""

        # 请求JSON格式响应
        response = self.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.0,  # 评估需要确定性
            response_format={"type": "json_object"},
        )

        return response

    def _update_cost(self, tokens: int):
        """
        更新成本统计

        DeepSeek定价参考（需要根据实际价格更新）：
        - 输入: ¥1 / 1M tokens
        - 输出: ¥2 / 1M tokens
        """
        # 简化计算，假设输入输出各占一半
        estimated_cost = tokens * 1.5 / 1_000_000  # ¥
        self.total_cost += estimated_cost

    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return {
            "total_tokens": self.total_tokens,
            "total_cost_rmb": round(self.total_cost, 4),
            "average_tokens_per_request": self.total_tokens / max(1, self._request_count),
        }

    @property
    def _request_count(self) -> int:
        """请求计数（基于token使用推算）"""
        # 假设平均每个请求使用1000 tokens
        return max(1, self.total_tokens // 1000)


# DeepEval集成包装器
class DeepSeekForDeepEval:
    """
    为DeepEval框架提供的LLM包装器
    继承自DeepEval的BaseLLM（需要安装deepeval）
    """

    def __init__(self, config: Optional[DeepSeekConfig] = None):
        self.client = DeepSeekClient(config)

    def generate(self, prompt: str) -> str:
        """DeepEval要求的生成方法"""
        response = self.client.complete(prompt)
        return response["content"]

    async def a_generate(self, prompt: str) -> str:
        """DeepEval要求的异步生成方法"""
        # 注意：这里简化处理，实际应使用异步客户端
        return self.generate(prompt)

    def get_model_name(self) -> str:
        """返回模型名称"""
        return self.client.config.model


# 使用示例
if __name__ == "__main__":
    # 初始化客户端
    client = DeepSeekClient()

    # 测试普通对话
    response = client.complete(
        prompt="请分析这个场景：'内景 咖啡馆 - 日\n李雷和韩梅梅坐在角落里小声交谈。'",
        system_prompt="你是一个剧本分析专家",
    )
    print("响应:", response["content"])

    # 测试JSON格式评估
    test_json = {"scene_id": "S01", "setting": "内景 咖啡馆 - 日", "characters": ["李雷", "韩梅梅"]}

    eval_response = client.evaluate_with_llm(
        source_text="内景 咖啡馆 - 日\n李雷和韩梅梅坐在角落里小声交谈。",
        extracted_json=test_json,
        evaluation_prompt_template="""
请评估以下JSON提取结果的质量：

原始文本：
{source_text}

提取的JSON：
{extracted_json}

评估标准：
{criteria}

请提供评分（0-1）和详细分析。
""",
        criteria=["场景标识的准确性", "角色识别的完整性", "场景设置的正确性"],
    )

    print("\n评估结果:", eval_response["content"])
    print("\n使用统计:", client.get_usage_stats())
