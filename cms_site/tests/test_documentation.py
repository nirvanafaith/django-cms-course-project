"""课程交付文档的一致性合同测试。"""

import os
from pathlib import Path
from typing import Final

from django.conf import settings
from django.test import SimpleTestCase

REQUIRED_DOCUMENTS: Final = (
    "01_需求分析文档.md",
    "02_详细设计文档.md",
    "03_PostgreSQL测试说明.md",
    "04_概要设计文档.md",
    "05_PostgreSQL测试报告.md",
    "06_系统部署说明书.md",
    "07_AI使用说明_2026.md",
    "08_PostgreSQL技术报告.md",
    "09_CMS管理员操作说明.md",
    "10_人工验收流程.md",
    "11_核心模块答辩说明.md",
    "12_北交大官网素材来源与许可.md",
    "13_作业要求符合性矩阵.md",
)
PLAINTEXT_PASSWORDS: Final = (
    "User-pass-2026!",
    "Admin-pass-2026!",
    "ctx/1234321",
)
MATRIX_COLUMNS: Final = ("作业要求", "实现文件", "自动化测试", "人工验收证据", "状态")


class DocumentationTests(SimpleTestCase):
    """确保课程交付文档与 PostgreSQL 实现保持同步。"""

    @property
    def repository_root(self) -> Path:
        """返回本地或 Compose 测试环境中的仓库根目录。"""
        configured_root = os.environ.get("CMS_PROJECT_ROOT")
        return Path(configured_root) if configured_root else Path(settings.BASE_DIR).parent

    @property
    def documentation_directory(self) -> Path:
        """返回仓库级交付文档目录。"""
        return self.repository_root / "docs"

    def document_text(self, filename: str) -> str:
        """读取一份受合同约束的 UTF-8 交付文档。"""
        return (self.documentation_directory / filename).read_text(encoding="utf-8")

    def test_required_delivery_documents_exist(self) -> None:
        """Given 课程交付物，When 审核文档链，Then 每份必需文档均存在。"""
        for filename in REQUIRED_DOCUMENTS:
            with self.subTest(filename=filename):
                self.assertTrue((self.documentation_directory / filename).is_file())

    def test_readme_describes_postgresql_only_runtime(self) -> None:
        """Given README，When 审核运行指南，Then 仅描述 PostgreSQL 18.6。"""
        readme = (self.repository_root / "README.md").read_text(encoding="utf-8")

        self.assertIn("PostgreSQL 18.6", readme)
        self.assertNotIn("MySQL", readme)
        self.assertNotIn("SQLite", readme)

    def test_delivery_documents_do_not_publish_demo_passwords(self) -> None:
        """Given 发布文档，When 扫描演示凭据，Then 不含任何明文密码。"""
        delivery_text = "\n".join(
            (self.repository_root / "README.md").read_text(encoding="utf-8"),
        )
        document_text = "\n".join(
            self.document_text(filename)
            for filename in REQUIRED_DOCUMENTS
            if (self.documentation_directory / filename).is_file()
        )

        for password in PLAINTEXT_PASSWORDS:
            with self.subTest(password=password):
                self.assertNotIn(password, delivery_text)
                self.assertNotIn(password, document_text)

    def test_compliance_matrix_covers_traceability_columns(self) -> None:
        """Given 符合性矩阵，When 检查追溯字段，Then 覆盖实现、测试和验收证据。"""
        matrix_path = self.documentation_directory / "13_作业要求符合性矩阵.md"
        self.assertTrue(matrix_path.is_file())
        matrix = matrix_path.read_text(encoding="utf-8")

        for column in MATRIX_COLUMNS:
            with self.subTest(column=column):
                self.assertIn(column, matrix)
