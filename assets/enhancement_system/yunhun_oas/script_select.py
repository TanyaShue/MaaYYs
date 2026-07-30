# This Python file uses the following encoding: utf-8
import os
import re
import sys
from time import sleep

cur_path = os.path.abspath(__file__)
oas_path = cur_path.split("tasks")[0]
if oas_path not in sys.path:
    sys.path.append(oas_path)

from module.exception import TaskEnd
from module.logger import logger
from tasks.Yuhun.script_common import SelectSoulInfo, YuhunBase


class SelectScriptTask(YuhunBase):
    """御魂选择页脚本：逐个 OCR 并选出 6 个值得强化的御魂。"""

    def run(self):
        self.run_select_page()
        raise TaskEnd("Yuhun select page done")

    def run_select_page(self) -> list[SelectSoulInfo]:
        logger.hr("Yuhun select page")
        if not self.wait_until_appear(self.I_SELECT_ENHANCE_ALL, wait_time=5):
            raise RuntimeError("未检测到御魂选择页的全部强化按钮，请先进入批量强化选择页")

        kept: list[SelectSoulInfo] = []
        visual_selected_count = self.count_selected_slots(skip_first_screenshot=True)
        selected_count = visual_selected_count
        logger.info("当前已选中御魂数量: %s", selected_count)

        for slot_index in range(1, self.SELECT_SLOT_COUNT + 1):
            if selected_count >= self.TARGET_SELECT_COUNT:
                break

            self.screenshot()
            if self.is_slot_selected(slot_index, skip_first_screenshot=True):
                logger.info("slot_%s 已选中，跳过", slot_index)
                continue

            soul = self.inspect_select_slot(slot_index)
            self.confirm_select_soul(soul)
            soul.decision = self.evaluate_select_soul(soul)
            logger.info(
                "slot_%s 决策: %s，理由: %s",
                slot_index,
                soul.decision.action,
                soul.decision.reason,
            )

            if soul.should_keep:
                kept.append(soul)
                selected_count += 1
                logger.info("slot_%s 保持选中", slot_index)
            else:
                logger.info("slot_%s 取消选中", slot_index)
                self.click(self.slot_click_rule(slot_index), interval=0.8)

            sleep(0.4)
            visual_selected_count = self.count_selected_slots()
            if visual_selected_count != selected_count:
                logger.warning(
                    "画面选中模板计数 %s 与脚本状态计数 %s 不一致，暂以脚本状态为准",
                    visual_selected_count,
                    selected_count,
                )
            logger.info("当前选中数量: %s/%s", selected_count, self.TARGET_SELECT_COUNT)

        if selected_count < self.TARGET_SELECT_COUNT:
            raise RuntimeError(f"选择页只选中 {selected_count} 个御魂，未达到 {self.TARGET_SELECT_COUNT} 个")

        self.check_select_counter(selected_count)
        logger.info("已选满 %s 个御魂，点击全部强化", selected_count)
        self.click(self.I_SELECT_ENHANCE_ALL)
        return kept

    def inspect_select_slot(self, slot_index: int) -> SelectSoulInfo:
        self.log_blank()
        logger.hr(f"Inspect yuhun slot {slot_index}", level=2)
        self.click(self.slot_click_rule(slot_index), interval=0.8)
        sleep(0.5)
        self.screenshot()

        raw_type_level = self.ocr_text(self.O_SOUL_TYPE_LEVEL)
        soul_type, level = self.parse_type_level(raw_type_level)

        raw_main_attr = self.ocr_text(self.O_DETAIL_MAIN_ATTR, shrink_for_level=level)
        main_attr = self.parse_main_attr(raw_main_attr)

        raw_sub_attrs = []
        sub_attrs = []
        for index in range(1, 5):
            rule = getattr(self, f"O_DETAIL_SUB_ATTR_{index}")
            raw = self.ocr_text(rule, shrink_for_level=level)
            raw_sub_attrs.append(raw)
            sub_attr = self.parse_sub_attr(raw)
            if sub_attr:
                sub_attrs.append(sub_attr)

        return SelectSoulInfo(
            slot_index=slot_index,
            position=self.enhance_config.default_slot,
            soul_type=soul_type,
            level=level,
            current_level=level,
            main_attr=main_attr,
            sub_attrs=sub_attrs,
            raw_type_level=raw_type_level,
            raw_main_attr=raw_main_attr,
            raw_sub_attrs=raw_sub_attrs,
        )

    def evaluate_select_soul(self, soul: SelectSoulInfo):
        equip = soul.to_equip()
        equip_config = self.yuhun_loader.load_equip_config(equip.类型)
        if not equip_config:
            raise RuntimeError(f"未找到御魂配置: {equip.类型}")
        self.log_route_decisions(equip, equip_config)
        return self.yuhun_engine.evaluate(equip, equip_config)

    def confirm_select_soul(self, soul: SelectSoulInfo) -> None:
        logger.info("OCR 原文: %s", soul.raw_type_level)
        logger.info("主属性: %s -> %s", soul.raw_main_attr, soul.main_attr.类型)
        parsed_index = 0
        for raw in soul.raw_sub_attrs:
            if self.is_set_bonus_text(raw):
                continue
            parsed = self.parse_sub_attr(raw)
            if parsed:
                parsed_index += 1
                logger.info("副属性%s: %s -> %s %s", parsed_index, raw, parsed.类型, parsed.数值)
            else:
                logger.info("副属性候选: %s -> 未解析", raw)

        if not self.enhance_config.confirm_each_step:
            return
        answer = input("本次 OCR 是否正确？输入 y/n，直接回车默认 y: ").strip().lower()
        if answer not in ("", "y"):
            raise RuntimeError("用户确认 OCR 不正确，请重新调整 bbox / OCR 配置")

    def check_select_counter(self, selected_count: int) -> None:
        self.screenshot()
        counter_text = self.ocr_text(self.O_SELECT_CONFIRM_COUNT)
        logger.info("确认区计数 OCR: %s", counter_text)
        match = re.search(r"\d+", counter_text or "")
        if not match:
            logger.warning("未能解析确认区计数，使用模板选中数量继续")
            return
        counter = int(match.group(0))
        if counter != selected_count:
            logger.warning("确认区计数 %s 与脚本状态计数 %s 不一致，暂以脚本状态为准", counter, selected_count)

    def count_selected_slots(self, skip_first_screenshot: bool = False) -> int:
        if not skip_first_screenshot:
            self.screenshot()
        return sum(
            1
            for slot_index in range(1, self.SELECT_SLOT_COUNT + 1)
            if self.is_slot_selected(slot_index, skip_first_screenshot=True)
        )

    def is_slot_selected(self, slot_index: int, skip_first_screenshot: bool = False) -> bool:
        if not skip_first_screenshot:
            self.screenshot()
        return self.appear(getattr(self, f"I_SELECT_SLOT_{slot_index}_SELECTED"))

    def slot_click_rule(self, slot_index: int):
        return getattr(self, f"C_SLOT_{slot_index}")


if __name__ == "__main__":
    from module.config.config import Config
    from module.device.device import Device

    config = Config("tmp_ios")
    device = Device(config)
    SelectScriptTask(config, device).run()
