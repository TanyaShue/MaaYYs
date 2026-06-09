# This Python file uses the following encoding: utf-8
import os
import sys
from time import sleep, time

cur_path = os.path.abspath(__file__)
oas_path = cur_path.split("tasks")[0]
if oas_path not in sys.path:
    sys.path.append(oas_path)

from module.exception import TaskEnd
from module.logger import logger
from tasks.Yuhun.script_common import (
    DECISION_CONFIG_PATH,
    LOW_DECISION_CONFIG_PATH,
    MainAttribute,
    SelectSoulInfo,
    SubAttribute,
    normalize_main_attr,
)
from tasks.Yuhun.script_enhance import EnhanceScriptTask


class ResultScriptTask(EnhanceScriptTask):
    """御魂结果页脚本：识别强化结果、弃置、继续强化并循环。"""

    def run(self):
        souls = self.build_default_result_souls()
        self.run_result_page(souls)
        raise TaskEnd("Yuhun result page done")

    def build_default_result_souls(self) -> list[SelectSoulInfo]:
        """Standalone result-page debug state when selection page was not run."""
        logger.info(
            "结果页单独调试：使用默认御魂 %s %s号位 +%s",
            self.enhance_config.default_soul_set,
            self.enhance_config.default_slot + 1,
            self.enhance_config.initial_level,
        )
        return [
            SelectSoulInfo(
                slot_index=result_index,
                position=self.enhance_config.default_slot,
                soul_type=self.enhance_config.default_soul_set,
                level=self.enhance_config.initial_level,
                current_level=self.enhance_config.initial_level,
                main_attr=MainAttribute(类型="攻击", 数值="0"),
                sub_attrs=[],
                raw_type_level=self.enhance_config.default_soul_set,
                raw_main_attr="",
                raw_sub_attrs=[],
            )
            for result_index in range(1, self.TARGET_SELECT_COUNT + 1)
        ]

    def run_result_page(self, souls: list[SelectSoulInfo]) -> None:
        logger.hr("Yuhun result page")
        if not self.wait_until_appear(self.I_RESULT_ENHANCE, wait_time=15):
            raise RuntimeError("未检测到结果页继续强化入口")

        for round_index in range(1, 7):
            if round_index > 1:
                self.log_blank()
            logger.hr(f"Yuhun result round {round_index}", level=2)
            if round_index == 1:
                self.align_result_order_by_sub_attrs(souls)
            self.update_result_souls(souls)
            self.log_blank()

            discard_indexes = self.decide_result_discards(souls)
            if discard_indexes:
                self.discard_result_slots(souls, discard_indexes)
                self.log_blank()

            continue_indexes = self.decide_result_continue(souls)
            if not continue_indexes:
                logger.info("没有需要继续强化的御魂，准备返回选择页")
                break

            self.ensure_result_continue_selection(souls, continue_indexes)
            self.run_result_continue_enhance()
            self.mark_lowest_result_index_enhanced(souls, continue_indexes)
            self.reorder_result_souls_after_enhance(souls, set(continue_indexes))

            if not self.wait_until_appear(self.I_RESULT_ENHANCE, wait_time=15):
                raise RuntimeError("继续强化后未回到结果页")
        else:
            raise RuntimeError("结果页循环超过上限，请检查状态识别")

        self.return_to_select_page()

    def align_result_order_by_sub_attrs(self, souls: list[SelectSoulInfo]) -> None:
        """First result page may reorder souls, so match UI slots by original sub attrs."""
        active_souls = [soul for soul in souls if not soul.discarded]
        if not active_souls or any(not soul.sub_attrs for soul in active_souls):
            logger.info("跳过首次结果页顺序匹配：缺少选择页副属性记录")
            return

        selected_by_key: dict[tuple[tuple[str, str], ...], SelectSoulInfo] = {}
        for soul in active_souls:
            key = soul.sub_attr_key()
            if key in selected_by_key:
                raise RuntimeError(
                    "选择页存在副属性完全相同的御魂，无法匹配结果页顺序: "
                    f"slot_{selected_by_key[key].slot_index} 与 slot_{soul.slot_index}，副属性={soul.sub_attr_summary()}"
                )
            selected_by_key[key] = soul

        logger.info("按副属性匹配首次结果页御魂顺序")
        self.screenshot()
        matched_souls: list[SelectSoulInfo] = []
        result_keys: dict[tuple[tuple[str, str], ...], int] = {}
        for result_index in range(1, len(active_souls) + 1):
            raw_sub_attrs: list[str] = []
            sub_attrs: list[SubAttribute] = []
            for sub_index in range(1, 5):
                raw_sub = self.ocr_text(getattr(self, f"O_RESULT_SLOT_{result_index}_SUB_ATTR_{sub_index}"))
                raw_sub_attrs.append(raw_sub)
                sub_attr = self.parse_sub_attr(raw_sub)
                if sub_attr:
                    sub_attrs.append(sub_attr)

            key = tuple((attr.类型, self.normalize_attr_value_key(attr.数值)) for attr in sub_attrs)
            if key in result_keys:
                raise RuntimeError(
                    "结果页存在副属性完全相同的御魂，无法匹配顺序: "
                    f"result_slot_{result_keys[key]} 与 result_slot_{result_index}，"
                    f"副属性={', '.join(f'{attr.类型}{attr.数值}' for attr in sub_attrs)}"
                )
            result_keys[key] = result_index

            if key not in selected_by_key:
                raise RuntimeError(
                    "无法按副属性匹配结果页御魂: "
                    f"result_slot_{result_index} 副属性={', '.join(f'{attr.类型}{attr.数值}' for attr in sub_attrs)}，"
                    f"OCR原文={raw_sub_attrs}"
                )
            matched_soul = selected_by_key[key]
            matched_souls.append(matched_soul)
            logger.info("result_slot_%s 匹配选择页 slot_%s: %s", result_index, matched_soul.slot_index, matched_soul.sub_attr_summary())

        discarded_souls = [soul for soul in souls if soul.discarded]
        souls[:] = matched_souls + discarded_souls

    def update_result_souls(self, souls: list[SelectSoulInfo]) -> None:
        logger.hr("Yuhun result OCR")
        self.screenshot()
        for result_index, soul in enumerate(souls, start=1):
            if soul.discarded:
                logger.info("result_slot_%s 已弃置，跳过 OCR", result_index)
                continue

            if soul.sub_attrs:
                soul.sub_attrs = [
                    self.update_result_sub_attr_bonus(result_index, sub_index, sub_attr)
                    for sub_index, sub_attr in enumerate(soul.sub_attrs, start=1)
                ]
            else:
                sub_attrs: list[SubAttribute] = []
                raw_sub_attrs: list[str] = []
                for sub_index in range(1, 5):
                    raw_sub = self.ocr_text(getattr(self, f"O_RESULT_SLOT_{result_index}_SUB_ATTR_{sub_index}"))
                    raw_sub_attrs.append(raw_sub)
                    sub_attr = self.parse_result_sub_attr(result_index, sub_index, raw_sub)
                    if sub_attr:
                        sub_attrs.append(sub_attr)

                if sub_attrs:
                    soul.sub_attrs = sub_attrs
                    soul.raw_sub_attrs = raw_sub_attrs

            logger.info(
                "result_slot_%s: %s +%s 主属性=%s 副属性=%s",
                result_index,
                soul.soul_type,
                soul.current_level,
                soul.main_attr.类型,
                soul.sub_attr_summary(),
            )

    def update_result_sub_attr_bonus(
        self,
        result_index: int,
        sub_index: int,
        sub_attr: SubAttribute,
    ) -> SubAttribute:
        bonus_rule = getattr(self, f"I_RESULT_SLOT_{result_index}_SUB_ATTR_{sub_index}_BONUS")
        bonus_detected = self.appear(bonus_rule)
        if not bonus_detected:
            return sub_attr

        raw_bonus_value = self.ocr_text(
            getattr(self, f"O_RESULT_SLOT_{result_index}_SUB_ATTR_{sub_index}_BONUS_VALUE")
        )
        bonus_value = self.parse_attr_value(raw_bonus_value)
        if not bonus_value:
            return sub_attr

        if sub_attr.数值.endswith("%") and not bonus_value.endswith("%"):
            bonus_value = f"{bonus_value}%"
        logger.info(
            "result_slot_%s 副属性%s强化: %s%s -> %s%s",
            result_index,
            sub_index,
            sub_attr.类型,
            sub_attr.数值,
            sub_attr.类型,
            bonus_value,
        )
        return SubAttribute(
            类型=sub_attr.类型,
            数值=bonus_value,
            强化次数=getattr(sub_attr, "强化次数", 0) + 1,
            等效强化次数=self.calc_equivalent_count(sub_attr.类型, bonus_value),
        )

    def parse_result_sub_attr(self, result_index: int, sub_index: int, raw_sub: str) -> SubAttribute | None:
        attr_type, value = self.parse_attr_text(raw_sub)
        if not attr_type:
            return None

        bonus_rule = getattr(self, f"I_RESULT_SLOT_{result_index}_SUB_ATTR_{sub_index}_BONUS")
        if self.appear(bonus_rule):
            raw_bonus_value = self.ocr_text(
                getattr(self, f"O_RESULT_SLOT_{result_index}_SUB_ATTR_{sub_index}_BONUS_VALUE")
            )
            bonus_value = self.parse_attr_value(raw_bonus_value)
            if bonus_value:
                if value and value.endswith("%") and not bonus_value.endswith("%"):
                    bonus_value = f"{bonus_value}%"
                logger.info(
                    "result_slot_%s 副属性%s强化: %s -> %s",
                    result_index,
                    sub_index,
                    raw_sub,
                    bonus_value,
                )
                value = bonus_value

        attr_type = normalize_main_attr(attr_type)
        value = value or "0"
        return SubAttribute(
            类型=attr_type,
            数值=value,
            强化次数=0,
            等效强化次数=self.calc_equivalent_count(attr_type, value),
        )

    def evaluate_result_soul(
        self,
        soul: SelectSoulInfo,
        result_index: int,
        config_path,
        label: str,
    ):
        self.use_decision_config(config_path, label)
        equip = soul.to_equip()
        equip_config = self.yuhun_loader.load_equip_config(equip.类型)
        if not equip_config:
            raise RuntimeError(f"未找到御魂配置: {equip.类型}")
        logger.info(
            "%s判断 result_slot_%s 副属性: %s",
            label,
            result_index,
            soul.sub_attr_summary(),
        )
        route_decisions = self.log_route_decisions(equip, equip_config)
        decision = self.yuhun_engine.evaluate(equip, equip_config)
        logger.info(
            "%s决策 result_slot_%s %s +%s: %s，理由: %s",
            label,
            result_index,
            soul.soul_type,
            soul.current_level,
            decision.action,
            decision.reason,
        )
        self.log_passed_routes(route_decisions)
        return decision

    def decide_result_discards(self, souls: list[SelectSoulInfo]) -> list[int]:
        logger.info("开始弃置判断")
        discard_indexes: list[int] = []
        evaluated = False
        for result_index, soul in enumerate(souls, start=1):
            if soul.discarded:
                continue
            if evaluated:
                self.log_blank()
            evaluated = True
            decision = self.evaluate_result_soul(soul, result_index, LOW_DECISION_CONFIG_PATH, "弃置")
            if decision.action == "弃置":
                discard_indexes.append(result_index)
        return discard_indexes

    def decide_result_continue(self, souls: list[SelectSoulInfo]) -> list[int]:
        logger.info("开始继续强化判断")
        continue_indexes: list[int] = []
        evaluated = False
        for result_index, soul in enumerate(souls, start=1):
            if soul.discarded or soul.current_level >= 15:
                continue
            if evaluated:
                self.log_blank()
            evaluated = True
            decision = self.evaluate_result_soul(soul, result_index, DECISION_CONFIG_PATH, "继续强化")
            if decision.action in ("继续强化", "保留"):
                continue_indexes.append(result_index)
            else:
                logger.info(
                    "继续强化配置判定 result_slot_%s 不继续强化；是否弃置只由低阈值配置决定",
                    result_index,
                )
        return continue_indexes

    def discard_result_slots(self, souls: list[SelectSoulInfo], discard_indexes: list[int]) -> None:
        logger.info("准备弃置结果页御魂: %s", discard_indexes)
        for result_index in discard_indexes:
            self.ensure_result_slot_selected(result_index, True)

        if not self.wait_until_appear(self.I_RESULT_DISCARD, wait_time=5):
            raise RuntimeError("未检测到结果页弃置按钮")
        self.click(self.I_RESULT_DISCARD)

        discard_set = set(discard_indexes)
        for result_index in discard_indexes:
            souls[result_index - 1].discarded = True

        self.reorder_result_souls_after_discard(souls, discard_set)
        discarded_positions = [
            result_index
            for result_index, soul in enumerate(souls, start=1)
            if soul.discarded
        ]
        self.wait_result_discarded_positions(discarded_positions)
        logger.info("弃置后御魂顺序已同步，弃置位置: %s", discarded_positions)

    @staticmethod
    def reorder_result_souls_after_discard(souls: list[SelectSoulInfo], discard_set: set[int]) -> None:
        """Game moves discarded souls to the end, so keep script state in the same order."""
        active_souls = [
            soul
            for result_index, soul in enumerate(souls, start=1)
            if result_index not in discard_set and not soul.discarded
        ]
        discarded_souls = [
            soul
            for result_index, soul in enumerate(souls, start=1)
            if result_index in discard_set or soul.discarded
        ]
        souls[:] = active_souls + discarded_souls

    def wait_result_discarded_positions(self, result_indexes: list[int], timeout: float = 5) -> None:
        deadline = time() + timeout
        while time() < deadline:
            self.screenshot()
            missing = [
                result_index
                for result_index in result_indexes
                if not self.appear(getattr(self, f"I_RESULT_SOUL_DISCARDED_{result_index}"))
            ]
            if not missing:
                return
            sleep(0.5)
        raise RuntimeError(f"弃置后未检测到弃置标识: result_slot_{missing}")

    @staticmethod
    def reorder_result_souls_after_enhance(souls: list[SelectSoulInfo], continue_set: set[int]) -> None:
        """Game moves enhanced souls to the front after a continue-enhance round."""
        enhanced_souls = [
            soul
            for result_index, soul in enumerate(souls, start=1)
            if result_index in continue_set and not soul.discarded
        ]
        active_souls = [
            soul
            for result_index, soul in enumerate(souls, start=1)
            if result_index not in continue_set and not soul.discarded
        ]
        discarded_souls = [soul for soul in souls if soul.discarded]
        souls[:] = enhanced_souls + active_souls + discarded_souls
        logger.info("强化后御魂顺序已同步，强化御魂移到前方: %s", sorted(continue_set))

    def ensure_result_continue_selection(
        self,
        souls: list[SelectSoulInfo],
        continue_indexes: list[int],
    ) -> None:
        logger.info("准备继续强化结果页御魂: %s", continue_indexes)
        continue_set = set(continue_indexes)
        for result_index, soul in enumerate(souls, start=1):
            if soul.discarded:
                continue
            self.ensure_result_slot_selected(result_index, result_index in continue_set)

    def ensure_result_slot_selected(self, result_index: int, selected: bool) -> None:
        self.screenshot()
        selected_rule = getattr(self, f"I_RESULT_SOUL_SELECTED_{result_index}")
        current = self.appear(selected_rule)
        if current == selected:
            return

        self.click(getattr(self, f"C_RESULT_SLOT_{result_index}"))
        sleep(0.5)
        self.screenshot()
        current = self.appear(selected_rule)
        if current != selected:
            raise RuntimeError(
                f"result_slot_{result_index} 选中状态校验失败，期望={selected}，实际={current}"
            )

    def return_to_select_page(self) -> None:
        logger.info("返回御魂选择页")
        self.screenshot()
        if self.appear(self.I_UI_BACK_YELLOW):
            self.click(self.I_UI_BACK_YELLOW, interval=1)
        elif self.appear(self.I_UI_BACK_BLUE):
            self.click(self.I_UI_BACK_BLUE, interval=1)
        else:
            raise RuntimeError("未检测到结果页返回按钮")

        if not self.wait_until_appear(self.I_SELECT_ENHANCE_ALL, wait_time=8):
            raise RuntimeError("返回后未检测到御魂选择页全部强化按钮")
        logger.info("已返回御魂选择页")


if __name__ == "__main__":
    from module.config.config import Config
    from module.device.device import Device

    config = Config("tmp_ios")
    device = Device(config)
    ResultScriptTask(config, device).run()
