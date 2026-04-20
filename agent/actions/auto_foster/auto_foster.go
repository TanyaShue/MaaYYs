package auto_foster

import (
	"encoding/json"
	"fmt"
	"regexp"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type AutoFoster struct {
	running bool
	mu      sync.Mutex
}

type FosterParams struct {
	FosterTarget int `json:"FosterTarget"` // 1: 勾玉, 2: 体力
}

// RewardInfo 奖励信息
type RewardInfo struct {
	YieldType  string `json:"yield_type"`
	YieldValue int    `json:"yield_value"`
}

// RecognitionDetail 识别结果详情
type RecognitionDetail struct {
	Best struct {
		Text string `json:"text"`
		Box  []int  `json:"box"`
	} `json:"best"`
	Filtered []struct {
		Text string `json:"text"`
		Box  []int  `json:"box"`
	} `json:"filtered"`
}

// 常量定义
const (
	TaskRecogTarget = "阴阳寮奖励领取_结界寄养_识别寄养目标"
	TaskRecogReward = "阴阳寮奖励领取_结界寄养_识别结界卡收益"
	TaskNextPage    = "阴阳寮奖励领取_结界寄养_识别寄养目标_下一页"
	TaskClickFriend = "阴阳寮奖励领取_结界寄养_点击好友"
	TaskClickCross  = "阴阳寮奖励领取_结界寄养_点击跨区好友"
	WaitShort       = 1 * time.Second
	WaitMedium      = 2 * time.Second
	MaxPagesScan    = 5
	MaxPagesSearch  = 10
)

// Run 执行自动寄养
func (a *AutoFoster) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行自动寄养脚本")
	a.mu.Lock()
	a.running = true
	a.mu.Unlock()

	params := FosterParams{FosterTarget: 1}
	if arg.CustomActionParam != "" {
		json.Unmarshal([]byte(arg.CustomActionParam), &params)
	}

	prioritizedType := "勾玉"
	if params.FosterTarget == 2 {
		prioritizedType = "体力"
	}
	fmt.Printf("设置优先级为: %s\n", prioritizedType)

	var allRewards []RewardInfo

	// --- 阶段 1: 收集所有奖励信息 ---
	// 收集好友标签页
	fmt.Println("切换到好友标签页...")
	_, _ = ctx.RunTask(TaskClickFriend, nil)
	time.Sleep(WaitShort)
	friendRewards := a.collectAllRewardsFromTab(ctx)
	allRewards = append(allRewards, friendRewards...)
	fmt.Printf("从好友标签页收集到 %d 个奖励信息。\n", len(friendRewards))

	if !a.isRunning() {
		return false
	}

	// 收集跨区好友标签页
	fmt.Println("切换到跨区好友标签页...")
	_, _ = ctx.RunTask(TaskClickCross, nil)
	time.Sleep(WaitShort)
	crossRewards := a.collectAllRewardsFromTab(ctx)
	allRewards = append(allRewards, crossRewards...)
	fmt.Printf("从跨区好友标签页收集到 %d 个奖励信息。\n", len(crossRewards))

	fmt.Printf("总共收集到 %d 个奖励信息。\n", len(allRewards))

	if len(allRewards) == 0 {
		fmt.Println("未在任何标签页找到可寄养的奖励。脚本结束。")
		return false
	}

	// --- 阶段 2: 依次查找并选择最佳奖励 ---
	sortedRewards := a.getSortedRewards(allRewards, prioritizedType)

	if len(sortedRewards) == 0 {
		fmt.Println("未能确定任何有效奖励。脚本结束。")
		return false
	}

	// 从最佳奖励开始，遍历所有可能性
	for _, rewardToFind := range sortedRewards {
		if !a.isRunning() {
			return false
		}

		fmt.Println(strings.Repeat("-", 25))
		fmt.Printf("==> 开始查找下一个最佳奖励: %s +%d <==\n", rewardToFind.YieldType, rewardToFind.YieldValue)

		// 首先在好友标签页查找
		fmt.Println("切换回好友标签页进行查找...")
		_, _ = ctx.RunTask(TaskClickFriend, nil)
		time.Sleep(WaitShort)
		if a.findAndSelectBestOnTab(ctx, rewardToFind) {
			fmt.Println("已成功在好友标签页选择奖励。脚本执行成功。")
			return true
		}

		if !a.isRunning() {
			return false
		}

		// 如果好友页没找到，则去跨区好友页查找
		fmt.Println("切换到跨区好友标签页进行查找...")
		_, _ = ctx.RunTask(TaskClickCross, nil)
		time.Sleep(WaitShort)
		if a.findAndSelectBestOnTab(ctx, rewardToFind) {
			fmt.Println("已成功在跨区好友标签页选择奖励。脚本执行成功。")
			return true
		}

		fmt.Printf("未能找到奖励: %s +%d。将尝试列表中的下一个。\n", rewardToFind.YieldType, rewardToFind.YieldValue)
	}

	// 如果循环完成，说明所有之前找到的奖励都无法再次定位
	fmt.Println("警告：在第二阶段未能重新找到任何之前收集到的奖励。可能列表已完全刷新。")
	return false
}

// parseRewardText 解析奖励文本，例如 '勾玉+10'
func (a *AutoFoster) parseRewardText(text string) (string, int) {
	if text == "" {
		return "", 0
	}

	// 使用正则表达式匹配 "类型+数值" 格式
	re := regexp.MustCompile(`^(.+?)\+?(\d+)$`)
	matches := re.FindStringSubmatch(text)
	if len(matches) == 3 {
		rewardType := strings.TrimSpace(matches[1])
		rewardValue := 0
		fmt.Sscanf(matches[2], "%d", &rewardValue)
		return rewardType, rewardValue
	}

	return "", 0
}

// clickTargetAndGetReward 点击目标，等待，识别并解析奖励
// box 格式: [x, y, width, height]
func (a *AutoFoster) clickTargetAndGetReward(ctx *maa.Context, box []int) (string, int) {
	controller := ctx.GetTasker().GetController()
	if controller == nil {
		return "", 0
	}

	// 安全检查 box 长度
	if len(box) < 4 {
		fmt.Printf("警告: box 长度不足: %v\n", box)
		return "", 0
	}

	// 点击目标中心
	x := box[0] + box[2]/2
	y := box[1] + box[3]/2
	controller.PostClick(int32(x), int32(y)).Wait()
	time.Sleep(WaitMedium)

	// 识别奖励
	controller.PostScreencap().Wait()
	img, err := controller.CacheImage()
	if err != nil {
		return "", 0
	}

	detail, _ := ctx.RunRecognition(TaskRecogReward, img, nil)
	if detail != nil && detail.Hit {
		var recogDetail RecognitionDetail
		if err := json.Unmarshal([]byte(detail.DetailJson), &recogDetail); err == nil {
			rewardText := recogDetail.Best.Text
			return a.parseRewardText(rewardText)
		}
	}

	return "", 0
}

// clickTargetByDetail 使用 RecognitionDetail 点击目标
func (a *AutoFoster) clickTargetByDetail(ctx *maa.Context, detail *maa.RecognitionDetail) (string, int) {
	controller := ctx.GetTasker().GetController()
	if controller == nil {
		return "", 0
	}

	// 点击目标中心
	x := detail.Box.X() + detail.Box.Width()/2
	y := detail.Box.Y() + detail.Box.Height()/2
	controller.PostClick(int32(x), int32(y)).Wait()
	time.Sleep(WaitMedium)

	// 识别奖励
	controller.PostScreencap().Wait()
	img, err := controller.CacheImage()
	if err != nil {
		return "", 0
	}

	rewardDetail, _ := ctx.RunRecognition(TaskRecogReward, img, nil)
	if rewardDetail != nil && rewardDetail.Hit {
		var recogDetail RecognitionDetail
		if err := json.Unmarshal([]byte(rewardDetail.DetailJson), &recogDetail); err == nil {
			rewardText := recogDetail.Best.Text
			return a.parseRewardText(rewardText)
		}
	}

	return "", 0
}

// collectRewardsFromCurrentPage 收集当前页面上所有目标的奖励信息
func (a *AutoFoster) collectRewardsFromCurrentPage(ctx *maa.Context) []RewardInfo {
	var pageResults []RewardInfo
	controller := ctx.GetTasker().GetController()
	if controller == nil {
		return pageResults
	}

	controller.PostScreencap().Wait()
	img, err := controller.CacheImage()
	if err != nil {
		return pageResults
	}

	detail, _ := ctx.RunRecognition(TaskRecogTarget, img, nil)
	if detail != nil && detail.Hit {
		var recogDetail RecognitionDetail
		if err := json.Unmarshal([]byte(detail.DetailJson), &recogDetail); err == nil {
			if len(recogDetail.Filtered) > 0 {
				fmt.Printf("当前页找到 %d 个目标。\n", len(recogDetail.Filtered))
				for _, target := range recogDetail.Filtered {
					// 安全检查 Box 长度
					if len(target.Box) >= 4 {
						rewardType, rewardValue := a.clickTargetAndGetReward(ctx, target.Box)
						if rewardType != "" && rewardValue > 0 {
							pageResults = append(pageResults, RewardInfo{
								YieldType:  rewardType,
								YieldValue: rewardValue,
							})
						}
					}
				}
			} else if len(recogDetail.Best.Box) >= 4 {
				// 只有一个目标
				rewardType, rewardValue := a.clickTargetAndGetReward(ctx, recogDetail.Best.Box)
				if rewardType != "" && rewardValue > 0 {
					pageResults = append(pageResults, RewardInfo{
						YieldType:  rewardType,
						YieldValue: rewardValue,
					})
				}
			}
		}
	} else {
		fmt.Println("当前页未找到目标。")
	}

	return pageResults
}

// collectAllRewardsFromTab 遍历当前标签页的所有页面，收集奖励信息
func (a *AutoFoster) collectAllRewardsFromTab(ctx *maa.Context) []RewardInfo {
	var allTabRewards []RewardInfo
	pageCount := 0

	for {
		pageCount++
		fmt.Printf("扫描当前标签页的第 %d 页...\n", pageCount)

		if !a.isRunning() {
			return allTabRewards
		}

		pageRewards := a.collectRewardsFromCurrentPage(ctx)

		// 如果某页（非第一页）没收到奖励，就认为结束了
		if len(pageRewards) == 0 && pageCount > 1 {
			fmt.Println("此页未找到奖励，假设是当前标签页末尾。")
			break
		}

		allTabRewards = append(allTabRewards, pageRewards...)

		// 检查是否有下一页
		nextResult, _ := ctx.RunTask(TaskNextPage, nil)
		if nextResult == nil {
			fmt.Println("没有下一页，停止扫描。")
			break
		}
		time.Sleep(WaitShort)

		// 添加页数限制防止意外死循环
		if pageCount > MaxPagesScan {
			fmt.Println("警告：已扫描超过5页，可能存在问题，停止扫描此标签页。")
			break
		}
	}

	return allTabRewards
}

// getSortedRewards 对收集到的所有奖励进行去重和排序
func (a *AutoFoster) getSortedRewards(allRewards []RewardInfo, prioritizedType string) []RewardInfo {
	if len(allRewards) == 0 {
		return nil
	}

	// 去重
	seen := make(map[string]bool)
	var uniqueRewards []RewardInfo
	for _, r := range allRewards {
		key := fmt.Sprintf("%s|%d", r.YieldType, r.YieldValue)
		if !seen[key] {
			seen[key] = true
			uniqueRewards = append(uniqueRewards, r)
		}
	}

	// 排序逻辑:
	// 1. 奖励类型是否为优先类型 (True > False)
	// 2. 奖励的数值
	sort.Slice(uniqueRewards, func(i, j int) bool {
		iIsPriority := uniqueRewards[i].YieldType == prioritizedType
		jIsPriority := uniqueRewards[j].YieldType == prioritizedType
		if iIsPriority != jIsPriority {
			return iIsPriority
		}
		return uniqueRewards[i].YieldValue > uniqueRewards[j].YieldValue
	})

	fmt.Printf("排序后的奖励列表: %+v\n", uniqueRewards)
	return uniqueRewards
}

// findAndSelectBestOnTab 在当前标签页查找并选择第一个匹配最佳奖励的目标
func (a *AutoFoster) findAndSelectBestOnTab(ctx *maa.Context, bestReward RewardInfo) bool {

	pageCount := 0

	for {
		pageCount++
		fmt.Printf("在当前标签页第 %d 页搜索奖励 [%s +%d]...\n", pageCount, bestReward.YieldType, bestReward.YieldValue)

		if !a.isRunning() {
			return false
		}
		controller := ctx.GetTasker().GetController()
		if controller == nil {
			return false
		}
		// 添加短暂等待，确保界面稳定
		controller.PostScreencap().Wait()
		img, err := controller.CacheImage()
		if err != nil {
			continue
		}

		detail, _ := ctx.RunRecognition(TaskRecogTarget, img, nil)
		targetsFound := false

		if detail != nil && detail.Hit {
			var recogDetail RecognitionDetail
			if err := json.Unmarshal([]byte(detail.DetailJson), &recogDetail); err == nil {
				targets := recogDetail.Filtered
				if len(targets) == 0 && len(recogDetail.Best.Box) >= 4 {
					targets = []struct {
						Text string `json:"text"`
						Box  []int  `json:"box"`
					}{{Box: recogDetail.Best.Box}}
				}

				if len(targets) > 0 {
					targetsFound = true
					fmt.Printf("找到 %d 个目标，检查是否匹配...\n", len(targets))
					for _, target := range targets {
						// 安全检查 Box 长度
						if len(target.Box) < 4 {
							continue
						}

						rewardType, rewardValue := a.clickTargetAndGetReward(ctx, target.Box)

						if rewardType == bestReward.YieldType && rewardValue == bestReward.YieldValue {
							fmt.Printf("找到并选择了匹配的奖励: %s +%d\n", rewardType, rewardValue)
							return true
						}
					}
				}
			}
		}

		// 如果当前页（非第一页）没找到目标，认为结束
		if !targetsFound && pageCount > 1 {
			fmt.Println("当前页未找到目标，假设搜索结束。")
			break
		}

		// 尝试翻页
		nextResult, _ := ctx.RunTask(TaskNextPage, nil)
		if nextResult == nil {
			fmt.Println("没有下一页，停止搜索。")
			break
		}
		time.Sleep(WaitShort)

		// 添加页数限制
		if pageCount > MaxPagesSearch {
			fmt.Println("警告：搜索时已扫描超过10页，停止搜索此标签页。")
			break
		}
	}

	fmt.Printf("在此标签页未找到奖励 [%s +%d]。\n", bestReward.YieldType, bestReward.YieldValue)
	return false
}

// isRunning 检查是否正在运行
func (a *AutoFoster) isRunning() bool {
	a.mu.Lock()
	defer a.mu.Unlock()
	return a.running
}

// Stop 停止执行
func (a *AutoFoster) Stop() {
	fmt.Println("停止执行自定义动作")
	a.mu.Lock()
	a.running = false
	a.mu.Unlock()
}