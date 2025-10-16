# -*- coding: UTF-8 -*-
import json
import time

# 假设 maa 相关模块已正确导入
from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer

@AgentServer.custom_action("AutoFoster")
class AutoFoster(CustomAction):
    """
    自动寄养脚本：
    根据用户偏好（勾玉或体力），遍历好友和跨区好友列表，
    找到收益最高的寄养位置并进行选择。
    如果最佳奖励在选择阶段消失，会自动尝试次佳奖励。
    """
    # --- 常量定义 ---
    # MAA 任务名称 (请确保与你的 MAA 配置一致)
    TASK_RECOG_TARGET = "阴阳寮奖励领取_结界寄养_识别寄养目标"
    TASK_RECOG_REWARD = "阴阳寮奖励领取_结界寄养_识别结界卡收益"
    TASK_NEXT_PAGE = "阴阳寮奖励领取_结界寄养_识别寄养目标_下一页"
    TASK_CLICK_FRIEND_TAB = "阴阳寮奖励领取_结界寄养_点击好友"
    TASK_CLICK_CROSS_TAB = "阴阳寮奖励领取_结界寄养_点击跨区好友"

    # 等待时间 (秒)
    WAIT_SHORT = 1.0  # 切换标签页、翻页后的等待
    WAIT_MEDIUM = 2.0 # 点击目标查看收益后的等待

    # --- 辅助方法 ---

    def _parse_reward_text(self, text: str | None) -> tuple[str | None, int]:
        """解析奖励文本，例如 '勾玉+10'"""
        if not text:
            return None, 0
        try:
            if "+" in text:
                parts = text.split("+", 1)
                if len(parts) == 2:
                    reward_type = parts[0].strip()
                    reward_value = int(parts[1].strip())
                    return reward_type, reward_value
            # print(f"无法解析奖励文本: '{text}'") # 按需取消注释
            return None, 0
        except Exception as e:
            print(f"解析奖励文本 '{text}' 时出错: {e}")
            return None, 0

    def _click_target_and_get_reward(self, context: Context, target_result) -> tuple[str | None, int]:
        """点击目标，等待，识别并解析奖励"""
        # print(f"点击目标: {target_result.box}") # 按需取消注释
        # 点击目标中心
        x = target_result.box[0] + target_result.box[2] / 2
        y = target_result.box[1] + target_result.box[3] / 2
        context.tasker.controller.post_click(int(x), int(y)).wait()
        time.sleep(self.WAIT_MEDIUM)

        # 识别奖励
        img = context.tasker.controller.post_screencap().wait().get()
        earnings_recog = context.run_recognition(self.TASK_RECOG_REWARD, img)

        reward_type = None
        reward_value = 0
        # 简化处理：假设识别成功且 best_result 存在
        if earnings_recog and getattr(earnings_recog, "best_result", None):
             # 尝试获取 text 属性，兼容不同版本的 MAA 结果
            reward_text = getattr(earnings_recog.best_result, 'text', None)
            if not reward_text and isinstance(earnings_recog.best_result, str):
                 reward_text = earnings_recog.best_result

            # print(f"识别到的奖励文本: '{reward_text}'") # 按需取消注释
            reward_type, reward_value = self._parse_reward_text(reward_text)
        else:
            print("未能识别奖励或没有找到最佳结果。")

        return reward_type, reward_value

    def _collect_rewards_from_current_page(self, context: Context) -> list[dict]:
        """收集当前页面上所有目标的奖励信息"""
        page_results = []
        img = context.tasker.controller.post_screencap().wait().get()
        targets_recog = context.run_recognition(self.TASK_RECOG_TARGET, img)

        # 简化处理：假设识别成功且 filterd_results 存在
        if targets_recog and getattr(targets_recog, "filterd_results", None):
            print(f"当前页找到 {len(targets_recog.filterd_results)} 个目标。")
            for target in targets_recog.filterd_results:
                reward_type, reward_value = self._click_target_and_get_reward(context, target)
                if reward_type is not None and reward_value > 0:
                    page_results.append({
                        # 可以简化，只存必要信息
                        "yield_type": reward_type,
                        "yield_value": reward_value
                    })
        else:
            print("当前页未找到目标。")
        return page_results

    def _collect_all_rewards_from_tab(self, context: Context) -> list[dict]:
        """遍历当前标签页的所有页面，收集奖励信息"""
        all_tab_rewards = []
        page_count = 0
        while True:
            page_count += 1
            print(f"扫描当前标签页的第 {page_count} 页...")
            page_rewards = self._collect_rewards_from_current_page(context)

            # 简化判断：如果某页（非第一页）没收到奖励，就认为结束了
            if not page_rewards and page_count > 1:
                 print("此页未找到奖励，假设是当前标签页末尾。")
                 break

            all_tab_rewards.extend(page_rewards)

            next_page_task_result = context.run_task(self.TASK_NEXT_PAGE)

            time.sleep(self.WAIT_SHORT) # 翻页后等待加载

            # 添加一个基础的页数限制防止意外死循环 (可选)
            if page_count > 5: # 设定一个较大的上限
                print("警告：已扫描超过5页，可能存在问题，停止扫描此标签页。")
                break

        return all_tab_rewards

    def _get_sorted_rewards(self, all_rewards: list[dict], prioritized_type: str) -> list[dict]:
        """对收集到的所有奖励进行去重和排序"""
        if not all_rewards:
            return []

        # 将 dict 转换为可哈希的元组以进行去重
        rewards_as_tuples = {tuple(sorted(r.items())) for r in all_rewards}
        unique_rewards = [dict(t) for t in rewards_as_tuples]

        # 排序逻辑:
        # 1. 奖励类型是否为优先类型 (True > False)
        # 2. 奖励的数值
        # reverse=True 表示降序排列，即最优的在前
        sorted_unique_rewards = sorted(
            unique_rewards,
            key=lambda r: (r["yield_type"] == prioritized_type, r["yield_value"]),
            reverse=True
        )
        print(f"排序后的奖励列表: {sorted_unique_rewards}")
        return sorted_unique_rewards

    def _find_and_select_best_on_tab(self, context: Context, best_reward: dict) -> bool:
        """在当前标签页查找并选择第一个匹配最佳奖励的目标"""
        page_count = 0
        while True:
            page_count += 1
            print(f"在当前标签页第 {page_count} 页搜索奖励 [{best_reward['yield_type']} +{best_reward['yield_value']}]...")
            img = context.tasker.controller.post_screencap().wait().get()
            targets_recog = context.run_recognition(self.TASK_RECOG_TARGET, img)

            targets_found = False
            if targets_recog and getattr(targets_recog, "filterd_results", None):
                targets_found = True
                print(f"找到 {len(targets_recog.filterd_results)} 个目标，检查是否匹配...")
                for target in targets_recog.filterd_results:
                    # 再次点击并检查奖励
                    reward_type, reward_value = self._click_target_and_get_reward(context, target)

                    if reward_type == best_reward["yield_type"] and reward_value == best_reward["yield_value"]:
                        print(f"找到并选择了匹配的奖励: {reward_type} +{reward_value}")
                        return True # 成功找到并选择

            # 如果当前页（非第一页）没找到目标，认为结束
            if not targets_found and page_count > 1:
                 print("当前页未找到目标，假设搜索结束。")
                 break

            # 尝试翻页
            next_page_task_result = context.run_task(self.TASK_NEXT_PAGE)
            time.sleep(self.WAIT_SHORT)

            # 添加一个基础的页数限制 (可选)
            if page_count > 10:
                print("警告：搜索时已扫描超过10页，停止搜索此标签页。")
                break

        print(f"在此标签页未找到奖励 [{best_reward['yield_type']} +{best_reward['yield_value']}]。")
        return False # 在此标签页未找到

    # --- 主执行逻辑 ---

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """
        主执行函数：先收集所有奖励，找到最佳，再回去查找并选择。
        如果最佳奖励找不到，则依次尝试次佳奖励。
        """
        print("开始执行自动寄养脚本。")
        try:
            param = json.loads(argv.custom_action_param)
            foster_target_pref = param.get("FosterTarget", 1) # 1: 勾玉, 2: 体力
        except Exception as e:
            print(f"解析参数失败: {argv.custom_action_param}。错误: {e}")
            print("默认使用勾玉优先 (1)。")
            foster_target_pref = 1

        prioritized_type = "勾玉" if foster_target_pref == 1 else "体力"
        print(f"设置优先级为: {prioritized_type}")

        all_rewards = []

        # --- 阶段 1: 收集所有奖励信息 ---
        # 收集好友标签页
        print("切换到好友标签页...")
        context.run_task(self.TASK_CLICK_FRIEND_TAB)
        time.sleep(self.WAIT_SHORT)
        friend_rewards = self._collect_all_rewards_from_tab(context)
        all_rewards.extend(friend_rewards)
        print(f"从好友标签页收集到 {len(friend_rewards)} 个奖励信息。")

        # 收集跨区好友标签页
        print("切换到跨区好友标签页...")
        context.run_task(self.TASK_CLICK_CROSS_TAB)
        time.sleep(self.WAIT_SHORT)
        cross_rewards = self._collect_all_rewards_from_tab(context)
        all_rewards.extend(cross_rewards)
        print(f"从跨区好友标签页收集到 {len(cross_rewards)} 个奖励信息。")

        print(f"总共收集到 {len(all_rewards)} 个奖励信息。")

        if not all_rewards:
            print("未在任何标签页找到可寄养的奖励。脚本结束。")
            return False

        # --- 阶段 2: 依次查找并选择最佳奖励 ---
        sorted_rewards = self._get_sorted_rewards(all_rewards, prioritized_type)

        if not sorted_rewards:
            print("未能确定任何有效奖励。脚本结束。")
            return False

        # 从最佳奖励开始，遍历所有可能性
        for reward_to_find in sorted_rewards:
            print("-" * 25)
            print(f"==> 开始查找下一个最佳奖励: {reward_to_find['yield_type']} +{reward_to_find['yield_value']} <==")

            # 首先在好友标签页查找
            print("切换回好友标签页进行查找...")
            context.run_task(self.TASK_CLICK_FRIEND_TAB)
            time.sleep(self.WAIT_SHORT)
            if self._find_and_select_best_on_tab(context, reward_to_find):
                print(f"已成功在好友标签页选择奖励。脚本执行成功。")
                return True

            # 如果好友页没找到，则去跨区好友页查找
            print("切换到跨区好友标签页进行查找...")
            context.run_task(self.TASK_CLICK_CROSS_TAB)
            time.sleep(self.WAIT_SHORT)
            if self._find_and_select_best_on_tab(context, reward_to_find):
                print(f"已成功在跨区好友标签页选择奖励。脚本执行成功。")
                return True

            print(f"未能找到奖励: {reward_to_find['yield_type']} +{reward_to_find['yield_value']}。将尝试列表中的下一个。")

        # 如果循环完成，说明所有之前找到的奖励都无法再次定位
        print("警告：在第二阶段未能重新找到任何之前收集到的奖励。可能列表已完全刷新。")
        return False

    def stop(self):
        """停止执行（占位）"""
        pass