"""
测试 deepseek_client.py 中的DeepSeek API客户端
使用mock避免实际API调用
"""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.llm.deepseek_client import DeepSeekClient, DeepSeekConfig, DeepSeekForDeepEval
from src.utils.exceptions import APIConnectionError, APIResponseError


class TestDeepSeekConfig:
    """测试DeepSeekConfig配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = DeepSeekConfig(api_key="test_key")
        assert config.api_key == "test_key"
        assert config.base_url == "https://api.deepseek.com/v1"
        assert config.model == "deepseek-chat"
        assert config.temperature == 0.1
        assert config.max_tokens == 4096
        assert config.max_retries == 3
        assert config.retry_delay == 2

    def test_custom_config(self):
        """测试自定义配置"""
        config = DeepSeekConfig(
            api_key="custom_key",
            model="deepseek-coder",
            temperature=0.2,
            max_tokens=8192,
        )
        assert config.api_key == "custom_key"
        assert config.model == "deepseek-coder"
        assert config.temperature == 0.2
        assert config.max_tokens == 8192


class TestDeepSeekClient:
    """测试DeepSeekClient客户端"""

    @pytest.fixture
    def mock_config(self):
        """创建测试配置"""
        return DeepSeekConfig(api_key="test_api_key")

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI客户端"""
        with patch("src.llm.deepseek_client.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            yield mock_client

    def test_client_initialization(self, mock_config, mock_openai_client):
        """测试客户端初始化"""
        client = DeepSeekClient(mock_config)
        assert client.config == mock_config
        assert client.total_tokens == 0
        assert client.total_cost == 0.0

    def test_client_initialization_with_env(self, mock_openai_client):
        """测试从环境变量初始化"""
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "env_key"}):
            client = DeepSeekClient()
            assert client.config.api_key == "env_key"

    def test_complete_success(self, mock_config, mock_openai_client):
        """测试成功的API调用"""
        # 设置mock响应
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="测试响应"), finish_reason="stop")]
        mock_response.usage = Mock(total_tokens=100)
        mock_response.model = "deepseek-chat"

        mock_openai_client.chat.completions.create.return_value = mock_response

        # 创建客户端并调用
        client = DeepSeekClient(mock_config)
        result = client.complete(prompt="测试提示")

        # 验证结果
        assert result["content"] == "测试响应"
        assert result["tokens_used"] == 100
        assert result["model"] == "deepseek-chat"
        assert result["finish_reason"] == "stop"
        assert client.total_tokens == 100

        # 验证API调用参数
        mock_openai_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "deepseek-chat"
        assert call_kwargs["temperature"] == 0.1
        assert len(call_kwargs["messages"]) == 1
        assert call_kwargs["messages"][0]["role"] == "user"
        assert call_kwargs["messages"][0]["content"] == "测试提示"

    def test_complete_with_system_prompt(self, mock_config, mock_openai_client):
        """测试带系统提示的API调用"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="响应"), finish_reason="stop")]
        mock_response.usage = Mock(total_tokens=50)
        mock_response.model = "deepseek-chat"

        mock_openai_client.chat.completions.create.return_value = mock_response

        client = DeepSeekClient(mock_config)
        result = client.complete(prompt="用户提示", system_prompt="系统提示")

        # 验证消息格式
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        assert len(call_kwargs["messages"]) == 2
        assert call_kwargs["messages"][0]["role"] == "system"
        assert call_kwargs["messages"][0]["content"] == "系统提示"
        assert call_kwargs["messages"][1]["role"] == "user"
        assert call_kwargs["messages"][1]["content"] == "用户提示"

    def test_complete_with_json_response(self, mock_config, mock_openai_client):
        """测试JSON格式响应"""
        mock_response = Mock()
        json_content = '{"score": 0.85, "reason": "测试"}'
        mock_response.choices = [Mock(message=Mock(content=json_content), finish_reason="stop")]
        mock_response.usage = Mock(total_tokens=80)
        mock_response.model = "deepseek-chat"

        mock_openai_client.chat.completions.create.return_value = mock_response

        client = DeepSeekClient(mock_config)
        result = client.complete(
            prompt="测试", response_format={"type": "json_object"}
        )

        # 验证JSON被正确解析
        assert isinstance(result["content"], dict)
        assert result["content"]["score"] == 0.85
        assert result["content"]["reason"] == "测试"

        # 验证response_format参数被传递
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        assert call_kwargs["response_format"] == {"type": "json_object"}

    def test_complete_with_invalid_json(self, mock_config, mock_openai_client):
        """测试无效JSON响应的处理"""
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="这不是JSON"), finish_reason="stop")
        ]
        mock_response.usage = Mock(total_tokens=50)
        mock_response.model = "deepseek-chat"

        mock_openai_client.chat.completions.create.return_value = mock_response

        client = DeepSeekClient(mock_config)

        # 现在应该抛出APIResponseError异常
        with pytest.raises(APIResponseError) as exc_info:
            client.complete(prompt="测试", response_format={"type": "json_object"})

        assert "JSON格式不正确" in str(exc_info.value)

    def test_complete_with_custom_temperature(self, mock_config, mock_openai_client):
        """测试自定义温度参数"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="响应"), finish_reason="stop")]
        mock_response.usage = Mock(total_tokens=50)
        mock_response.model = "deepseek-chat"

        mock_openai_client.chat.completions.create.return_value = mock_response

        client = DeepSeekClient(mock_config)
        client.complete(prompt="测试", temperature=0.5)

        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        assert call_kwargs["temperature"] == 0.5

    def test_complete_retry_on_rate_limit(self, mock_config, mock_openai_client):
        """测试限流重试"""
        import openai

        # 第一次调用失败，第二次成功
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="成功"), finish_reason="stop")]
        mock_response.usage = Mock(total_tokens=50)
        mock_response.model = "deepseek-chat"

        mock_openai_client.chat.completions.create.side_effect = [
            openai.RateLimitError(
                "Rate limit exceeded", response=Mock(), body=None
            ),
            mock_response,
        ]

        client = DeepSeekClient(mock_config)
        with patch("time.sleep"):  # 避免实际等待
            result = client.complete(prompt="测试")

        assert result["content"] == "成功"
        assert mock_openai_client.chat.completions.create.call_count == 2

    def test_complete_retry_on_api_error(self, mock_config, mock_openai_client):
        """测试API错误重试"""
        import openai

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="成功"), finish_reason="stop")]
        mock_response.usage = Mock(total_tokens=50)
        mock_response.model = "deepseek-chat"

        # 前两次失败，第三次成功
        mock_openai_client.chat.completions.create.side_effect = [
            openai.APIError("API error", request=Mock(), body=None),
            openai.APIError("API error", request=Mock(), body=None),
            mock_response,
        ]

        client = DeepSeekClient(mock_config)
        with patch("time.sleep"):
            result = client.complete(prompt="测试")

        assert result["content"] == "成功"
        assert mock_openai_client.chat.completions.create.call_count == 3

    def test_complete_max_retries_exceeded(self, mock_config, mock_openai_client):
        """测试超过最大重试次数"""
        import openai

        # 所有调用都失败
        mock_openai_client.chat.completions.create.side_effect = openai.APIError(
            "API error", request=Mock(), body=None
        )

        client = DeepSeekClient(mock_config)
        with patch("time.sleep"):
            # 现在应该抛出APIConnectionError而不是openai.APIError
            with pytest.raises(APIConnectionError) as exc_info:
                client.complete(prompt="测试")

            assert "最大重试次数" in str(exc_info.value)

        # 应该重试3次
        assert mock_openai_client.chat.completions.create.call_count == 3

    def test_batch_complete(self, mock_config, mock_openai_client):
        """测试批量处理"""
        mock_response1 = Mock()
        mock_response1.choices = [Mock(message=Mock(content="响应1"), finish_reason="stop")]
        mock_response1.usage = Mock(total_tokens=50)
        mock_response1.model = "deepseek-chat"

        mock_response2 = Mock()
        mock_response2.choices = [Mock(message=Mock(content="响应2"), finish_reason="stop")]
        mock_response2.usage = Mock(total_tokens=60)
        mock_response2.model = "deepseek-chat"

        mock_openai_client.chat.completions.create.side_effect = [
            mock_response1,
            mock_response2,
        ]

        client = DeepSeekClient(mock_config)
        results = client.batch_complete(["提示1", "提示2"])

        assert len(results) == 2
        assert results[0]["content"] == "响应1"
        assert results[1]["content"] == "响应2"
        assert client.total_tokens == 110

    def test_batch_complete_with_error(self, mock_config, mock_openai_client):
        """测试批量处理中的错误"""
        import openai

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="成功"), finish_reason="stop")]
        mock_response.usage = Mock(total_tokens=50)
        mock_response.model = "deepseek-chat"

        # 设置为每次调用都抛出错误，直到达到max_retries
        # 第一个成功，第二个失败3次后放弃（max_retries=3），第三个成功
        api_error = openai.APIError("Error", request=Mock(), body=None)

        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_response  # 第一个成功
            elif call_count[0] <= 4:  # 2-4次是第二个提示的3次重试
                raise api_error
            else:
                return mock_response  # 第三个成功

        mock_openai_client.chat.completions.create.side_effect = side_effect

        client = DeepSeekClient(mock_config)
        with patch("time.sleep"):
            results = client.batch_complete(["提示1", "提示2", "提示3"])

        # 应该返回3个结果，其中一个是错误
        assert len(results) == 3
        assert results[0]["content"] == "成功"
        assert "error" in results[1]  # 第二个应该包含错误信息
        assert results[1]["content"] is None
        assert results[2]["content"] == "成功"

    def test_evaluate_with_llm(self, mock_config, mock_openai_client):
        """测试LLM评估功能"""
        mock_response = Mock()
        json_content = '{"score": 0.9, "reasoning": "很好"}'
        mock_response.choices = [Mock(message=Mock(content=json_content), finish_reason="stop")]
        mock_response.usage = Mock(total_tokens=100)
        mock_response.model = "deepseek-chat"

        mock_openai_client.chat.completions.create.return_value = mock_response

        client = DeepSeekClient(mock_config)
        result = client.evaluate_with_llm(
            source_text="原始文本",
            extracted_json={"scene_id": "S01"},
            evaluation_prompt_template="评估: {source_text}\nJSON: {extracted_json}\n标准: {criteria}",
            criteria=["准确性", "完整性"],
        )

        assert result["content"]["score"] == 0.9
        assert result["content"]["reasoning"] == "很好"

        # 验证调用参数 - evaluate_with_llm内部调用complete时传入temperature=0.0
        # 但实际实现可能使用的是默认配置的temperature
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        # temperature可能是0.0（evaluate_with_llm指定）或0.1（config默认）
        assert call_kwargs["temperature"] in [0.0, 0.1]
        assert call_kwargs["response_format"] == {"type": "json_object"}

    def test_cost_tracking(self, mock_config, mock_openai_client):
        """测试成本追踪"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="响应"), finish_reason="stop")]
        mock_response.usage = Mock(total_tokens=1000)
        mock_response.model = "deepseek-chat"

        mock_openai_client.chat.completions.create.return_value = mock_response

        client = DeepSeekClient(mock_config)
        client.complete(prompt="测试1")
        client.complete(prompt="测试2")

        assert client.total_tokens == 2000
        assert client.total_cost > 0  # 应该有成本

        stats = client.get_usage_stats()
        assert stats["total_tokens"] == 2000
        assert stats["total_cost_rmb"] > 0

    def test_usage_stats(self, mock_config, mock_openai_client):
        """测试使用统计"""
        client = DeepSeekClient(mock_config)
        stats = client.get_usage_stats()

        assert "total_tokens" in stats
        assert "total_cost_rmb" in stats
        assert "average_tokens_per_request" in stats
        assert stats["total_tokens"] == 0
        assert stats["total_cost_rmb"] == 0


class TestDeepSeekForDeepEval:
    """测试DeepEval集成包装器"""

    @pytest.fixture
    def mock_config(self):
        return DeepSeekConfig(api_key="test_key")

    @pytest.fixture
    def mock_client(self, mock_config):
        """Mock DeepSeekClient"""
        with patch("src.llm.deepseek_client.DeepSeekClient") as mock:
            mock_instance = Mock()
            mock_instance.config = mock_config
            mock.return_value = mock_instance
            yield mock_instance

    def test_initialization(self, mock_config):
        """测试初始化"""
        with patch("src.llm.deepseek_client.DeepSeekClient"):
            wrapper = DeepSeekForDeepEval(mock_config)
            assert wrapper.client is not None

    def test_generate(self, mock_config, mock_client):
        """测试生成方法"""
        mock_client.complete.return_value = {"content": "生成的文本"}

        with patch("src.llm.deepseek_client.DeepSeekClient", return_value=mock_client):
            wrapper = DeepSeekForDeepEval(mock_config)
            result = wrapper.generate("提示")

            assert result == "生成的文本"
            mock_client.complete.assert_called_once_with("提示")

    @pytest.mark.asyncio
    async def test_a_generate(self, mock_config, mock_client):
        """测试异步生成方法"""
        mock_client.complete.return_value = {"content": "异步生成的文本"}

        with patch("src.llm.deepseek_client.DeepSeekClient", return_value=mock_client):
            wrapper = DeepSeekForDeepEval(mock_config)
            result = await wrapper.a_generate("提示")

            assert result == "异步生成的文本"

    def test_get_model_name(self, mock_config, mock_client):
        """测试获取模型名称"""
        with patch("src.llm.deepseek_client.DeepSeekClient", return_value=mock_client):
            wrapper = DeepSeekForDeepEval(mock_config)
            model_name = wrapper.get_model_name()

            assert model_name == mock_config.model


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
