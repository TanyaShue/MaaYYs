package co_battle_target_recognition

import (
	"encoding/json"
	"fmt"
	"slices"
	"strings"
	"sync"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

// CoBattleTargetRecognition 协战目标识别器
// 用于管理协战目标列表,支持添加目标和判断目标
type CoBattleTargetRecognition struct {
	mu      sync.RWMutex
	targets []string // 全局协战目标列表
}

// CoBattleTargetRecognitionParams 参数结构
type CoBattleTargetRecognitionParams struct {
	Action string `json:"action"` // 操作类型: "add" 添加目标, "check" 判断目标
}

// RecognitionDetail OCR识别结果详情
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

// 确保实现 CustomRecognitionRunner 接口
var _ maa.CustomRecognitionRunner = &CoBattleTargetRecognition{}

// Run 执行协战目标识别
// 参数 action:
//   - "add": 运行"悬赏封印-识别协战目标名称"识别任务,将识别的名称添加到全局变量中,打印当前所有目标,返回true
//   - "check": 运行识别任务获取当前目标名称,判断是否在目标列表中,是则返回true,不是则返回false
func (r *CoBattleTargetRecognition) Run(ctx *maa.Context, arg *maa.CustomRecognitionArg) (*maa.CustomRecognitionResult, bool) {
	// 解析参数
	var params CoBattleTargetRecognitionParams
	if arg.CustomRecognitionParam != "" {
		if err := json.Unmarshal([]byte(arg.CustomRecognitionParam), &params); err != nil {
			fmt.Printf("CoBattleTargetRecognition: 解析参数失败: %v\n", err)
			return nil, false
		}
	}

	// 获取控制器用于截图
	controller := ctx.GetTasker().GetController()
	if controller == nil {
		fmt.Println("CoBattleTargetRecognition: 获取控制器失败")
		return nil, false
	}

	switch params.Action {
	case "add":
		return r.handleAddAction(ctx, controller)
	case "check":
		return r.handleCheckAction(ctx, controller)
	default:
		fmt.Printf("CoBattleTargetRecognition: 未知的操作类型: %s\n", params.Action)
		return nil, false
	}
}

// handleAddAction 处理添加目标操作
func (r *CoBattleTargetRecognition) handleAddAction(ctx *maa.Context, controller *maa.Controller) (*maa.CustomRecognitionResult, bool) {
	// 截图
	controller.PostScreencap().Wait()
	img, err := controller.CacheImage()
	if err != nil {
		fmt.Printf("CoBattleTargetRecognition: 获取截图失败: %v\n", err)
		return nil, false
	}

	// 运行"悬赏封印-识别协战目标名称"识别任务
	detail, err := ctx.RunRecognition("悬赏封印-识别协战目标名称", img, nil)
	if err != nil {
		fmt.Printf("CoBattleTargetRecognition: 运行识别任务失败: %v\n", err)
		return nil, false
	}

	if detail == nil || !detail.Hit {
		fmt.Println("CoBattleTargetRecognition: 未识别到协战目标名称")
		return nil, false
	}

	// 从 DetailJson 中解析 OCR 文本
	targetName := ""
	var recogDetail RecognitionDetail
	if err := json.Unmarshal([]byte(detail.DetailJson), &recogDetail); err == nil {
		targetName = recogDetail.Best.Text
	}

	if targetName == "" {
		fmt.Println("CoBattleTargetRecognition: 识别结果中没有文本")
		return nil, false
	}

	// 添加到全局变量
	r.mu.Lock()
	if r.targets == nil {
		r.targets = make([]string, 0)
	}
	// 检查是否已存在,避免重复添加
	if slices.Contains(r.targets, targetName) {
		currentTargets := r.targets
		r.mu.Unlock()
		fmt.Printf("CoBattleTargetRecognition: 目标已存在: %s\n", targetName)
		fmt.Printf("当前所有协战目标: %v\n", currentTargets)
		return &maa.CustomRecognitionResult{
			Box: maa.Rect{0, 0, 0, 0},
		}, true
	}
	r.targets = append(r.targets, targetName)
	currentTargets := r.targets
	r.mu.Unlock()

	// 打印当前所有目标
	fmt.Printf("CoBattleTargetRecognition: 成功添加协战目标: %s\n", targetName)
	fmt.Printf("当前所有协战目标: %v\n", currentTargets)

	return &maa.CustomRecognitionResult{
		Box: maa.Rect{0, 0, 0, 0},
	}, true
}

// handleCheckAction 处理判断目标操作
func (r *CoBattleTargetRecognition) handleCheckAction(ctx *maa.Context, controller *maa.Controller) (*maa.CustomRecognitionResult, bool) {
	// 截图
	controller.PostScreencap().Wait()
	img, err := controller.CacheImage()
	if err != nil {
		fmt.Printf("CoBattleTargetRecognition: 获取截图失败: %v\n", err)
		return nil, false
	}

	// 运行"悬赏封印-识别协战目标名称"识别任务获取当前目标
	detail, err := ctx.RunRecognition("悬赏封印-识别协战目标名称", img, nil)
	if err != nil {
		fmt.Printf("CoBattleTargetRecognition: 运行识别任务失败: %v\n", err)
		return nil, false
	}

	if detail == nil || !detail.Hit {
		fmt.Println("CoBattleTargetRecognition: 未识别到协战目标名称,判断结果: 不是协战目标")
		return nil, false
	}

	// 从 DetailJson 中解析 OCR 文本
	targetName := ""
	var recogDetail RecognitionDetail
	if err := json.Unmarshal([]byte(detail.DetailJson), &recogDetail); err == nil {
		targetName = recogDetail.Best.Text
	}

	if targetName == "" {
		fmt.Println("CoBattleTargetRecognition: 识别结果中没有文本,判断结果: 不是协战目标")
		return nil, false
	}

	// 判断是否在目标列表中(使用子串匹配,避免OCR识别不全的问题)
	r.mu.RLock()
	isTarget := slices.ContainsFunc(r.targets, func(t string) bool {
		return strings.Contains(targetName, t)
	})
	r.mu.RUnlock()

	if isTarget {
		fmt.Printf("CoBattleTargetRecognition: 目标 '%s' 是协战目标\n", targetName)
		return &maa.CustomRecognitionResult{
			Box: detail.Box,
		}, true
	} else {
		fmt.Printf("CoBattleTargetRecognition: 目标 '%s' 不是协战目标\n", targetName)
		return nil, false
	}
}

// ClearTargets 清除所有目标(可选的辅助方法)
func (r *CoBattleTargetRecognition) ClearTargets() {
	r.mu.Lock()
	r.targets = make([]string, 0)
	r.mu.Unlock()
	fmt.Println("CoBattleTargetRecognition: 已清除所有协战目标")
}

// GetTargets 获取当前所有目标(可选的辅助方法)
func (r *CoBattleTargetRecognition) GetTargets() []string {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.targets
}