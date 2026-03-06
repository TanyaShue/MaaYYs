package bonus_toggle

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type BonusToggleAction struct{}

var BonusType = map[string]string{
	"exp_100%":  "战斗胜利获得的经验增加100%",
	"exp_50%":   "战斗胜利获得的经验增加50%",
	"gold_100%": "战斗胜利获得的金币增加100%",
	"gold_50%":  "战斗胜利获得的金币增加50%",
	"drop_awake": "觉醒副本掉落额外的觉醒材料",
	"drop_soul":  "八岐大蛇掉落额外的御魂材料",
}

// Run 执行加成开关控制
func (a *BonusToggleAction) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行加成开关控制动作")

	var jsonData map[string]bool
	if err := json.Unmarshal([]byte(arg.CustomActionParam), &jsonData); err != nil {
		fmt.Printf("解析参数失败: %v\n", err)
		return false
	}

	// 验证所有键是否为有效的加成类型
	for bonusType := range jsonData {
		if _, ok := BonusType[bonusType]; !ok {
			fmt.Printf("无效的加成类型: %s\n", bonusType)
			return false
		}
	}

	success := true
	fmt.Printf("开始设置 %d 个加成:\n", len(jsonData))

	for bonusType, enable := range jsonData {
		if !a.toggleSingleBonus(ctx, bonusType, enable) {
			success = false
			fmt.Printf("设置 %s 加成失败\n", bonusType)
		}
		time.Sleep(500 * time.Millisecond)
	}

	if success {
		fmt.Println("所有加成设置完成")
	} else {
		fmt.Println("部分加成设置失败")
	}

	return success
}

func (a *BonusToggleAction) toggleSingleBonus(ctx *maa.Context, bonusType string, enable bool) bool {
	expectedText, ok := BonusType[bonusType]
	if !ok {
		fmt.Printf("未找到加成类型 %s 对应的文本\n", bonusType)
		return false
	}

	action := "启用"
	nextTask := "通用_打开加成"
	if !enable {
		action = "关闭"
		nextTask = "通用_关闭加成"
	}

	fmt.Printf("  - %s %s 加成: %s\n", action, bonusType, expectedText)

	_, _ = ctx.RunTask("通用_识别加成", map[string]any{
		"通用_识别加成": map[string]any{
			"expected": expectedText,
			"next":     nextTask,
		},
	})

	return true
}