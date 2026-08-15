"""北交大授权静态素材合同测试。"""

import os
from pathlib import Path
from typing import Final

from django.conf import settings
from django.test import SimpleTestCase

ASSET_SOURCES: Final = {
    "logo.png": "https://www.bjtu.edu.cn/images/img2019/logo_01.png",
    "hero-01.jpg": ("https://www.bjtu.edu.cn/images/2026-04/af3631c78c334f56815b33f3ac98fb31.jpg"),
    "hero-02.jpg": ("https://www.bjtu.edu.cn/images/2025-11/1327f795cea4469db03602c44d8b7bea.jpg"),
    "hero-03.jpg": ("https://www.bjtu.edu.cn/images/2026-07/604735a54f1746748c24b4ef06a1965c.jpg"),
    "hero-04.jpg": ("https://www.bjtu.edu.cn/images/2026-08/9a48dba706854b5889db46577e353173.jpg"),
    "hero-05.jpg": ("https://www.bjtu.edu.cn/images/2024-09/a7e2d85be52f44b68d10a21c2a1a08d4.jpg"),
}
PNG_SIGNATURE: Final = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE: Final = b"\xff\xd8\xff"


class StaticAssetTests(SimpleTestCase):
    """验证运行时素材均为可追溯的本地文件。"""

    @property
    def asset_directory(self) -> Path:
        """返回北交大素材目录。"""
        return Path(settings.BASE_DIR) / "static" / "img" / "bjtu"

    @property
    def provenance_document(self) -> Path:
        """返回素材来源与许可文档路径。"""
        configured_root = os.environ.get("CMS_PROJECT_ROOT")
        repository_root = (
            Path(configured_root) if configured_root else Path(settings.BASE_DIR).parent
        )
        return repository_root / "docs" / "12_北交大官网素材来源与许可.md"

    def test_approved_assets_exist_and_are_not_empty(self) -> None:
        """六个批准素材均存在且包含文件内容。"""
        for filename in ASSET_SOURCES:
            with self.subTest(filename=filename):
                asset = self.asset_directory / filename
                self.assertTrue(asset.is_file(), f"缺少本地素材：{filename}")
                self.assertGreater(asset.stat().st_size, 0, f"素材为空：{filename}")

    def test_assets_use_expected_binary_signatures(self) -> None:
        """校名标识为 PNG，五张轮播图为 JPEG。"""
        logo = self.asset_directory / "logo.png"
        self.assertTrue(logo.is_file(), "缺少本地素材：logo.png")
        self.assertEqual(logo.read_bytes()[: len(PNG_SIGNATURE)], PNG_SIGNATURE)

        for filename in ASSET_SOURCES:
            if filename == "logo.png":
                continue
            with self.subTest(filename=filename):
                hero = self.asset_directory / filename
                self.assertTrue(hero.is_file(), f"缺少本地素材：{filename}")
                self.assertEqual(hero.read_bytes()[: len(JPEG_SIGNATURE)], JPEG_SIGNATURE)

    def test_provenance_document_records_every_source_url(self) -> None:
        """来源文档覆盖全部批准 URL。"""
        self.assertTrue(self.provenance_document.is_file())
        provenance = self.provenance_document.read_text(encoding="utf-8")

        for source_url in ASSET_SOURCES.values():
            with self.subTest(source_url=source_url):
                self.assertIn(source_url, provenance)
