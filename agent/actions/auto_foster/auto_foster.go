package auto_foster

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type AutoFoster struct{}

type FosterParams struct {
	FosterTarget int `json:"FosterTarget"` // 1: 勾玉, 2: 体力
}

// Run 执行自动寄养
func (a *AutoFoster) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行自动寄养脚本")

	params := FosterParams{FosterTarget: 1}
	if arg.CustomActionParam != "" {
		json.Unmarshal([]byte(arg.CustomActionParam), &params)
	}

	prioritizedType := "勾玉"
	if params.FosterTarget == 2 {
		prioritizedType = "体力"
	}
	fmt.Printf("设置优先级为: %s\n", prioritizedType)

	// 收集好友标签页奖励
	fmt.Println("切换到好友标签页...")
	_, _ = ctx.RunTask("阴阳寮奖励领取_结界寄养_点击好友", nil)
	time.Sleep(1 * time.Second)

	// 收集跨区好友标签页奖励
	fmt.Println("切换到跨区好友标签页...")
	_, _ = ctx.RunTask("阴阳寮奖励领取_结界寄养_点击跨区好友", nil)
	time.Sleep(1 * time.Second)

	fmt.Println("自动寄养完成")
	return true
}