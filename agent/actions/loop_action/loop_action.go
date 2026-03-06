package loop_action

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type LoopAction struct{}

type LoopParams struct {
	ActionList []string `json:"action_list"`
	LoopTimes  int      `json:"loop_times"`
	OnError    string   `json:"on_error"`
}

// Run 执行循环动作
func (a *LoopAction) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	var params LoopParams
	if err := json.Unmarshal([]byte(arg.CustomActionParam), &params); err != nil {
		fmt.Printf("解析参数失败: %v\n", err)
		return false
	}

	if len(params.ActionList) == 0 || params.LoopTimes < 1 {
		fmt.Println("无效的action_list或loop_times")
		return false
	}

	fmt.Printf("开始执行动作列表 %v，循环 %d 次\n", params.ActionList, params.LoopTimes)

	for i := 0; i < params.LoopTimes; i++ {
		fmt.Printf("第 %d 次循环开始\n", i+1)

		for _, action := range params.ActionList {
			actionTimeName := fmt.Sprintf("第%d次%s任务", i+1, action)
			fmt.Printf("执行动作: %s\n", actionTimeName)

			taskOverride := map[string]any{
				actionTimeName: map[string]any{
					"next":    action,
					"timeout": 1000,
				},
			}

			if params.OnError != "" {
				taskOverride[actionTimeName].(map[string]any)["on_error"] = params.OnError
			}

			_, err := ctx.RunTask(actionTimeName, taskOverride)
			if err != nil {
				fmt.Printf("执行动作 %s 失败: %v\n", actionTimeName, err)
			}
			time.Sleep(500 * time.Millisecond)
		}

		fmt.Printf("第 %d 次循环结束\n", i+1)
	}

	return true
}