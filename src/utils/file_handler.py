"""
文件处理工具模块
提供文件读写、格式转换等功能
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)


class FileHandler:
    """文件处理器"""

    @staticmethod
    def read_text_file(file_path: Union[str, Path], encoding: str = "utf-8") -> str:
        """
        读取文本文件

        Args:
            file_path: 文件路径
            encoding: 编码格式

        Returns:
            文件内容
        """
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
            logger.info(f"成功读取文件: {file_path}")
            return content
        except FileNotFoundError:
            logger.error(f"文件不存在: {file_path}")
            raise
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            raise

    @staticmethod
    def read_json_file(file_path: Union[str, Path], encoding: str = "utf-8") -> Any:
        """
        读取JSON文件

        Args:
            file_path: 文件路径
            encoding: 编码格式

        Returns:
            解析后的JSON对象
        """
        try:
            with open(file_path, "r", encoding=encoding) as f:
                data = json.load(f)
            logger.info(f"成功读取JSON文件: {file_path}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败 {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"读取JSON文件失败 {file_path}: {e}")
            raise

    @staticmethod
    def write_text_file(
        file_path: Union[str, Path], content: str, encoding: str = "utf-8", create_dirs: bool = True
    ) -> None:
        """
        写入文本文件

        Args:
            file_path: 文件路径
            content: 文件内容
            encoding: 编码格式
            create_dirs: 是否自动创建目录
        """
        try:
            file_path = Path(file_path)

            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding=encoding) as f:
                f.write(content)

            logger.info(f"成功写入文件: {file_path}")
        except Exception as e:
            logger.error(f"写入文件失败 {file_path}: {e}")
            raise

    @staticmethod
    def write_json_file(
        file_path: Union[str, Path],
        data: Any,
        encoding: str = "utf-8",
        ensure_ascii: bool = False,
        indent: int = 2,
        create_dirs: bool = True,
    ) -> None:
        """
        写入JSON文件

        Args:
            file_path: 文件路径
            data: 要写入的数据
            encoding: 编码格式
            ensure_ascii: 是否转义非ASCII字符
            indent: 缩进空格数
            create_dirs: 是否自动创建目录
        """
        try:
            file_path = Path(file_path)

            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding=encoding) as f:
                json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)

            logger.info(f"成功写入JSON文件: {file_path}")
        except Exception as e:
            logger.error(f"写入JSON文件失败 {file_path}: {e}")
            raise

    @staticmethod
    def list_files(
        directory: Union[str, Path], pattern: str = "*", recursive: bool = False
    ) -> List[Path]:
        """
        列出目录中的文件

        Args:
            directory: 目录路径
            pattern: 文件模式（如 "*.txt"）
            recursive: 是否递归搜索

        Returns:
            文件路径列表
        """
        directory = Path(directory)

        if not directory.exists():
            logger.warning(f"目录不存在: {directory}")
            return []

        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))

        # 只返回文件，不包含目录
        files = [f for f in files if f.is_file()]

        logger.info(f"在 {directory} 中找到 {len(files)} 个文件")
        return files

    @staticmethod
    def ensure_directory(directory: Union[str, Path]) -> Path:
        """
        确保目录存在，不存在则创建

        Args:
            directory: 目录路径

        Returns:
            目录Path对象
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @staticmethod
    def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            文件信息字典
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        stat = file_path.stat()

        return {
            "name": file_path.name,
            "path": str(file_path.absolute()),
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified": stat.st_mtime,
            "is_file": file_path.is_file(),
            "is_dir": file_path.is_dir(),
            "extension": file_path.suffix,
        }


class ScriptLoader:
    """剧本文件加载器"""

    @staticmethod
    def load_script_pair(
        script_file: Union[str, Path], json_file: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        加载剧本文本和对应的JSON

        Args:
            script_file: 剧本文本文件路径
            json_file: JSON文件路径

        Returns:
            包含script_text和extracted_json的字典
        """
        handler = FileHandler()

        script_text = handler.read_text_file(script_file)
        extracted_json = handler.read_json_file(json_file)

        return {
            "script_text": script_text,
            "extracted_json": extracted_json,
            "script_file": str(Path(script_file).name),
            "json_file": str(Path(json_file).name),
        }

    @staticmethod
    def load_test_cases_from_directory(
        directory: Union[str, Path], script_pattern: str = "*.txt", scene_type: str = "standard"
    ) -> List[Dict[str, Any]]:
        """
        从目录加载测试用例

        假设文件命名规则：
        - sample_01.txt 对应 sample_01.json
        - outline_01.txt 对应 outline_01.json

        Args:
            directory: 目录路径
            script_pattern: 剧本文件模式
            scene_type: 场景类型

        Returns:
            测试用例列表
        """
        directory = Path(directory)
        handler = FileHandler()

        script_files = handler.list_files(directory, script_pattern)
        test_cases = []

        for script_file in script_files:
            # 查找对应的JSON文件
            json_file = script_file.with_suffix(".json")

            if not json_file.exists():
                logger.warning(f"未找到对应的JSON文件: {json_file}")
                continue

            try:
                test_case = ScriptLoader.load_script_pair(script_file, json_file)
                test_case["scene_type"] = scene_type
                test_case["source_file"] = str(script_file.name)
                test_cases.append(test_case)
            except Exception as e:
                logger.error(f"加载测试用例失败 {script_file}: {e}")

        logger.info(f"从 {directory} 加载了 {len(test_cases)} 个测试用例")
        return test_cases


# 使用示例
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)

    # 测试文件处理
    handler = FileHandler()

    # 写入测试文件
    test_data = {"scene_id": "S01", "setting": "测试场景", "characters": ["角色A", "角色B"]}

    handler.write_json_file("test_output.json", test_data)

    # 读取文件
    loaded_data = handler.read_json_file("test_output.json")
    print("加载的数据:", loaded_data)

    # 清理测试文件
    os.remove("test_output.json")
