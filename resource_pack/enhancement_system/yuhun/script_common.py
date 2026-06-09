# This Python file uses the following encoding: utf-8
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

cur_path = os.path.abspath(__file__)
oas_path = cur_path.split("tasks")[0]
if oas_path not in sys.path:
    sys.path.append(oas_path)

YUHUN_RESOURCE_DIR = Path(r"D:\Software\yys\resource\yuhun")
ENHANCEMENT_SYSTEM_DIR = YUHUN_RESOURCE_DIR / "enhancement_system"
DECISION_CONFIG_PATH = ENHANCEMENT_SYSTEM_DIR / "config" / "decision_config.json"
LOW_DECISION_CONFIG_PATH = ENHANCEMENT_SYSTEM_DIR / "config" / "decision_config_low.json"
if str(ENHANCEMENT_SYSTEM_DIR) not in sys.path:
    sys.path.insert(0, str(ENHANCEMENT_SYSTEM_DIR))

from module.logger import logger
from tasks.GameUi.game_ui import GameUi
from tasks.Yuhun.assets import YuhunAssets
from tasks.Yuhun.config import YuhunEnhanceConfig

from core.data_loader import DataLoader
from core.decision_config import DecisionConfig
from core.decision_engine import Decision, DecisionEngine
from core.models import Equip, MainAttribute, SubAttribute, normalize_main_attr
from core.scoring import ATTR_RANGE


@dataclass
class SelectSoulInfo:
    slot_index: int
    position: int
    soul_type: str
    level: int
    current_level: int
    main_attr: MainAttribute
    sub_attrs: list[SubAttribute]
    raw_type_level: str
    raw_main_attr: str
    raw_sub_attrs: list[str]
    decision: Decision | None = None
    discarded: bool = False

    @property
    def should_keep(self) -> bool:
        return self.decision is not None and self.decision.action in ("继续强化", "保留")

    def to_equip(self) -> Equip:
        return Equip(
            位置=self.position,
            类型=self.soul_type,
            品质=6,
            等级=self.current_level,
            主属性=self.main_attr,
            副属性=self.sub_attrs,
        )

    def mark_enhanced(self) -> None:
        if not self.discarded:
            self.current_level = min(15, self.current_level + 3)

    def sub_attr_summary(self) -> str:
        return ", ".join(f"{attr.类型}{attr.数值}" for attr in self.sub_attrs) or "无"

    def sub_attr_key(self) -> tuple[tuple[str, str], ...]:
        return tuple((attr.类型, YuhunBase.normalize_attr_value_key(attr.数值)) for attr in self.sub_attrs)


class YuhunBase(GameUi, YuhunAssets):
    """御魂强化页面脚本共享能力。"""

    TARGET_SELECT_COUNT = 6
    SELECT_SLOT_COUNT = 16
    ATTR_TYPES = sorted(ATTR_RANGE.keys(), key=len, reverse=True)
    SOUL_TYPE_OCR_FIXES = {
        "夜啸石": "夜啼石",
        "粗之匣": "魍魉之匣",
        "唇气楼": "蜃气楼",
        "尘家": "尘冢",
        "涅之火": "涅槃之火",
        "挣": "狰"
    }

    def __init__(self, config, device):
        super().__init__(config, device)
        yuhun_config = getattr(self.config, "yuhun", None)
        self._enhance_config = (
            yuhun_config.enhance_config
            if yuhun_config is not None
            else YuhunEnhanceConfig()
        )
        self.yuhun_loader = DataLoader(YUHUN_RESOURCE_DIR)
        self.yuhun_pool = self.yuhun_loader.load_equip_pool("ios.json")
        self.yuhun_engine = DecisionEngine(self.yuhun_pool, self.yuhun_loader)
        logger.info("御魂位置暂用配置: %s号位", self.enhance_config.default_slot + 1)
        logger.info("御魂初始等级暂用配置: +%s", self.enhance_config.initial_level)

    @property
    def enhance_config(self):
        return self._enhance_config

    @staticmethod
    def log_blank() -> None:
        logger.info("")

    def ocr_text(self, rule, shrink_for_level: int | None = None) -> str:
        origin_roi = list(rule.roi)
        origin_area = list(rule.area)
        if shrink_for_level is not None and shrink_for_level >= 3 and rule.name.startswith("DETAIL_"):
            rule.roi = self.shrink_detail_roi(rule.roi)
            rule.area = self.shrink_detail_roi(rule.area)
        try:
            result = rule.ocr(self.device.image)
            return "" if result is None else str(result).strip()
        finally:
            rule.roi = origin_roi
            rule.area = origin_area

    @staticmethod
    def shrink_detail_roi(roi: list[int]) -> list[int]:
        x, y, w, h = roi
        return [x, y, max(1, w - 30), h]

    def parse_type_level(self, text: str) -> tuple[str, int]:
        normalized = (text or "").replace("＋", "+").replace(" ", "")
        match = re.search(r"(.+?)\+(\d+)", normalized)
        if match:
            return self.fix_soul_type_ocr(match.group(1)), int(match.group(2))

        level_match = re.search(r"\+(\d+)", normalized)
        soul_type = re.sub(r"\+\d+", "", normalized).strip()
        if soul_type:
            soul_type = self.fix_soul_type_ocr(soul_type)
            level = int(level_match.group(1)) if level_match else 0
            if not level_match:
                logger.warning("无法从 %s 解析等级，按 +%s 处理", text, level)
            return soul_type, level

        logger.warning("无法解析御魂类型和等级: %s，使用默认配置", text)
        return self.enhance_config.default_soul_set, self.enhance_config.initial_level

    def fix_soul_type_ocr(self, soul_type: str) -> str:
        fixed = self.SOUL_TYPE_OCR_FIXES.get(soul_type, soul_type)
        if fixed != soul_type:
            logger.info("御魂类型 OCR 修复: %s -> %s", soul_type, fixed)
        return fixed

    def parse_main_attr(self, text: str) -> MainAttribute:
        attr_type = self.parse_attr_type(text)
        if not attr_type:
            logger.warning("无法解析主属性: %s，使用 OCR 原文", text)
            attr_type = text or "未知"
        return MainAttribute(类型=normalize_main_attr(attr_type), 数值="0")

    def parse_sub_attr(self, text: str) -> SubAttribute | None:
        if self.is_set_bonus_text(text):
            return None
        attr_type, value = self.parse_attr_text(text)
        if not attr_type:
            return None
        attr_type = normalize_main_attr(attr_type)
        value = value or "0"
        return SubAttribute(
            类型=attr_type,
            数值=value,
            强化次数=0,
            等效强化次数=self.calc_equivalent_count(attr_type, value),
        )

    def parse_attr_type(self, text: str) -> str | None:
        compact = (text or "").replace(" ", "").replace("：", ":")
        for attr_type in self.ATTR_TYPES:
            aliases = [attr_type]
            if attr_type == "暴击伤害":
                aliases.append("暴伤")
            if attr_type == "效果命中":
                aliases.append("命中")
            if attr_type == "效果抵抗":
                aliases.append("抵抗")

            for alias in aliases:
                if alias in compact:
                    return attr_type
        return None

    def parse_attr_text(self, text: str) -> tuple[str | None, str | None]:
        compact = (text or "").replace(" ", "").replace("：", ":")
        for attr_type in self.ATTR_TYPES:
            aliases = [attr_type]
            if attr_type == "暴击伤害":
                aliases.append("暴伤")
            if attr_type == "效果命中":
                aliases.append("命中")
            if attr_type == "效果抵抗":
                aliases.append("抵抗")

            for alias in aliases:
                if alias not in compact:
                    continue
                tail = compact.split(alias, 1)[1]
                value_match = re.search(r"([+-]?\d+(?:\.\d+)?%?)", tail)
                return attr_type, value_match.group(1) if value_match else None
        return None, None

    @staticmethod
    def parse_attr_value(text: str) -> str | None:
        compact = (text or "").replace(" ", "").replace("＋", "+")
        value_match = re.search(r"([+-]?\d+(?:\.\d+)?%?)", compact)
        return value_match.group(1) if value_match else None

    @staticmethod
    def normalize_attr_value_key(value: str) -> str:
        value = (value or "").replace(" ", "").replace("＋", "+")
        if value.startswith("+"):
            return value[1:]
        return value

    @staticmethod
    def is_set_bonus_text(text: str) -> bool:
        compact = (text or "").replace(" ", "")
        return any(marker in compact for marker in ("2件套", "两件套", "4件套", "四件套", "套装效果"))

    @staticmethod
    def calc_equivalent_count(attr_type: str, value: str) -> float:
        if attr_type not in ATTR_RANGE:
            return 0.0
        try:
            numeric = float(value.rstrip("%"))
            if value.endswith("%"):
                numeric /= 100
        except ValueError:
            return 0.0
        _, max_value = ATTR_RANGE[attr_type]
        return round(numeric / max_value, 2)

    @staticmethod
    def use_decision_config(config_path: Path, label: str) -> None:
        logger.info("使用%s决策配置: %s", label, config_path.name)
        DecisionConfig.reload(config_path)

    def log_route_decisions(self, equip, equip_config) -> list[tuple[str, Decision]]:
        routes = equip_config.get_routes(equip.位置, equip.主属性.类型)
        if not routes:
            logger.info("未找到路线: %s %s号位 主属性=%s", equip.类型, equip.位置 + 1, equip.主属性.类型)
            return []

        logger.info(
            "路线评估: %s %s号位 +%s 主属性=%s",
            equip.类型,
            equip.位置 + 1,
            equip.等级,
            equip.主属性.类型,
        )
        decisions: list[tuple[str, Decision]] = []
        for route in routes:
            decision = self.yuhun_engine._evaluate_single_route(equip, equip_config, route)
            decisions.append((route.路线名称, decision))
        best_route_name, best_decision = max(
            decisions,
            key=lambda route_decision: (
                route_decision[1].probability or 0,
                route_decision[1].current_score,
            ),
        )
        probability = "-" if best_decision.probability is None else f"{best_decision.probability * 100:.1f}%"
        stage_threshold = "-" if best_decision.stage_threshold is None else f"{best_decision.stage_threshold * 100:.0f}%"
        logger.info(
            "最高概率路线[%s] action=%s prob=%s stage=%s score=%.2f threshold=%.2f top=%s reason=%s",
            best_route_name,
            best_decision.action,
            probability,
            stage_threshold,
            best_decision.current_score,
            best_decision.threshold_score,
            best_decision.top_n,
            best_decision.reason,
        )
        return decisions

    @staticmethod
    def log_passed_routes(route_decisions: list[tuple[str, Decision]]) -> None:
        passed = [
            (route_name, decision)
            for route_name, decision in route_decisions
            if decision.action in ("继续强化", "保留")
        ]
        if not passed:
            logger.info("没有概率满足要求的路线")
            return

        route_name, decision = max(
            passed,
            key=lambda route_decision: (
                route_decision[1].probability or 0,
                route_decision[1].current_score,
            ),
        )
        probability = "-" if decision.probability is None else f"{decision.probability * 100:.1f}%"
        stage_threshold = "-" if decision.stage_threshold is None else f"{decision.stage_threshold * 100:.0f}%"
        logger.info(
            "满足路线[%s]: prob=%s stage=%s score=%.2f threshold=%.2f top=%s",
            route_name,
            probability,
            stage_threshold,
            decision.current_score,
            decision.threshold_score,
            decision.top_n,
        )

    @staticmethod
    def mark_lowest_result_index_enhanced(souls: list[SelectSoulInfo], result_indexes: list[int]) -> None:
        candidates = [
            (result_index, souls[result_index - 1])
            for result_index in result_indexes
            if not souls[result_index - 1].discarded and souls[result_index - 1].current_level < 15
        ]
        if not candidates:
            logger.info("本轮没有可提升等级的御魂")
            return

        min_level = min(soul.current_level for _, soul in candidates)
        enhanced_indexes = []
        for result_index, soul in candidates:
            if soul.current_level != min_level:
                continue
            soul.mark_enhanced()
            enhanced_indexes.append(result_index)

        logger.info(
            "本轮强化最低等级御魂: result_slot_%s +%s -> +%s；更高等级御魂不变",
            enhanced_indexes,
            min_level,
            min(15, min_level + 3),
        )
