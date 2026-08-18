"""北交大风格演示数据的不可变规格。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Final
from zoneinfo import ZoneInfo


@dataclass(frozen=True, slots=True)
class CategorySpec:
    """栏目名称及正文生成所需的业务语义。"""

    name: str
    description: str
    focus: str


@dataclass(frozen=True, slots=True)
class ArticleSpec:
    """一篇可复现演示文章的完整规格。"""

    title: str
    category_name: str
    publish_time: datetime
    is_published: bool

    @property
    def content(self) -> str:
        """按标题和栏目生成三段原创正文。"""
        category = CATEGORY_BY_NAME[self.category_name]
        return (
            f"围绕“{self.title}”，学校结合近期工作安排组织了专题推进。"
            f"本项内容归入“{category.name}”栏目，重点回应师生关心的{category.focus}，"
            "相关信息均为原创演示所用素材。\n\n"
            f"工作组已明确时间节点、参与范围和协同方式，并将关键成果纳入{category.description}。"
            "各单位依照公开流程提交材料，阶段结果由责任部门统一整理，确保安排可查询、"
            "进度可跟踪、结果可复核。\n\n"
            "后续进展将在本栏目持续更新。师生如需了解具体事项，可通过校内综合服务平台"
            "向对应业务部门咨询，并以最新发布的正式通知和办理指南为准。"
        )


@dataclass(frozen=True, slots=True)
class UserSpec:
    """演示用户的用户名与角色。"""

    username: str
    is_admin: bool


CATEGORY_SPECS: Final = (
    CategorySpec("交大头条", "学校重点工作与重大成果", "学校发展和重要成果"),
    CategorySpec("通知公告", "面向师生的校级通知与服务提醒", "办事时间和服务安排"),
    CategorySpec("教学科研", "人才培养、课程建设与科研进展", "教学改革和科研训练"),
    CategorySpec("校园动态", "校园文化、学生发展与公共活动", "校园参与和成长体验"),
    CategorySpec("招生就业", "招生咨询、培养衔接与就业服务", "升学选择和职业发展"),
    CategorySpec("学术活动", "学术论坛、专题讲座与报告预告", "学科前沿和学术交流"),
    CategorySpec("国际交流", "国际合作、联合培养与文化互鉴", "海外学习和合作项目"),
    CategorySpec("信息公开", "规章制度、公共服务与开放数据", "信息透明和便民服务"),
)
CATEGORY_BY_NAME: Final = MappingProxyType({spec.name: spec for spec in CATEGORY_SPECS})
USER_SPECS: Final = (
    UserSpec("student", False),
    UserSpec("visitor", False),
    UserSpec("CTX", True),
)

type ArticleRow = tuple[str, str, int, int, int, bool]
ARTICLE_ROWS: Final[tuple[ArticleRow, ...]] = (
    ("交通强国建设专题研讨会在校举行", "交大头条", 2026, 8, 12, True),
    ("学校召开新学期重点工作部署会", "交大头条", 2026, 7, 18, True),
    ("轨道交通自主创新成果集中发布", "交大头条", 2026, 6, 20, True),
    ("知行育人计划启动仪式顺利举行", "交大头条", 2026, 5, 16, True),
    ("校园开放日展示学科建设新进展", "交大头条", 2026, 4, 13, True),
    ("关于秋季学期开学安排的通知", "通知公告", 2026, 8, 8, True),
    ("图书馆暑期开放时间调整公告", "通知公告", 2026, 7, 1, True),
    ("校园网络维护与服务暂停通知", "通知公告", 2025, 12, 18, True),
    ("研究生奖学金材料提交提醒", "通知公告", 2025, 10, 9, True),
    ("实验室安全检查工作通知", "通知公告", 2025, 9, 5, False),
    ("智能交通课程群完成教学改革验收", "教学科研", 2025, 8, 21, True),
    ("本科生科研训练项目开始申报", "教学科研", 2025, 6, 14, True),
    ("计算机基础课程开放实践周报名", "教学科研", 2025, 4, 22, True),
    ("教师教学能力提升工作坊举行", "教学科研", 2024, 12, 6, True),
    ("跨学科培养方案发布试行", "教学科研", 2024, 10, 17, True),
    ("校园文化节系列活动正式启动", "校园动态", 2025, 5, 11, True),
    ("学生创新创业成果展开幕", "校园动态", 2025, 3, 28, True),
    ("志愿服务项目交流会圆满结束", "校园动态", 2024, 11, 23, True),
    ("秋季运动会报名通道开放", "校园动态", 2024, 9, 12, True),
    ("社团招新服务周安排发布", "校园动态", 2024, 8, 30, False),
    ("本科招生线上咨询活动启动", "招生就业", 2024, 6, 8, True),
    ("研究生招生政策宣讲会预告", "招生就业", 2024, 5, 19, True),
    ("毕业生校园双选会参会指南", "招生就业", 2024, 3, 15, True),
    ("国际学生入学服务手册发布", "招生就业", 2024, 1, 26, True),
    ("轨道交通前沿学术论坛预告", "学术活动", 2024, 7, 4, True),
    ("人工智能与工程教育讲座举行", "学术活动", 2024, 2, 24, True),
    ("青年学者交叉论坛征集报告", "学术活动", 2023, 11, 10, True),
    ("城市交通治理专题报告会开放预约", "学术活动", 2023, 9, 16, True),
    ("国际合作伙伴周活动日程发布", "国际交流", 2023, 8, 25, True),
    ("海外交流项目线上说明会举行", "国际交流", 2023, 6, 17, True),
    ("留学生文化交流活动报名开始", "国际交流", 2023, 5, 12, True),
    ("联合培养项目申请指南更新", "国际交流", 2023, 3, 31, False),
    ("年度信息公开报告正式发布", "信息公开", 2023, 12, 22, True),
    ("校级规章制度目录完成更新", "信息公开", 2023, 10, 20, True),
    ("公共服务事项办事指南发布", "信息公开", 2023, 4, 7, True),
    ("校园数据开放目录新增资源", "信息公开", 2023, 1, 13, True),
)

SHANGHAI: Final = ZoneInfo("Asia/Shanghai")
ARTICLE_SPECS: Final = tuple(
    ArticleSpec(
        title=row[0],
        category_name=row[1],
        publish_time=datetime(row[2], row[3], row[4], 9, 0, tzinfo=SHANGHAI),
        is_published=row[5],
    )
    for row in ARTICLE_ROWS
)
