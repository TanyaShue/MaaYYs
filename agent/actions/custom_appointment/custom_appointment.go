package custom_appointment

import (
	"encoding/json"
	"fmt"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type CustomAppointment struct{}

var DefaultTasks = map[string]bool{
	"樱饼配方":  false,
	"奇怪的痕迹": false,
	"接送弥助":  false,
	"伊吹的藤球": false,
	"捡到的宝石": false,
	"以鱼为礼":  false,
	"帮忙搬运":  false,
	"猫老大":   false,
	"寻找耳环":  false,
	"弥助的画":  false,
}

// Run 执行式神委派
func (a *CustomAppointment) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	// 复制默认任务
	tasksToRunIntent := make(map[string]bool)
	for k, v := range DefaultTasks {
		tasksToRunIntent[k] = v
	}

	// 解析参数
	if arg.CustomActionParam != "" {
		var params map[string]bool
		if err := json.Unmarshal([]byte(arg.CustomActionParam), &params); err == nil {
			for k, v := range params {
				tasksToRunIntent[k] = v
			}
		}
	}

	// 识别屏幕上实际存在的任务列表
	onScreenTasks := make(map[string]bool)
	controller := ctx.GetTasker().GetController()
	if controller != nil {
		controller.PostScreencap().Wait()
		img, err := controller.CacheImage()
		if err == nil {
			detail, _ := ctx.RunRecognition("识别当前存在任务列表", img, nil)
			if detail != nil && detail.Hit {
				// 处理识别结果
				fmt.Printf("识别到的屏幕任务: %v\n", onScreenTasks)
			}
		}
	}

	// 遍历意图要执行的任务
	for taskName, shouldRun := range tasksToRunIntent {
		if shouldRun && onScreenTasks[taskName] {
			fmt.Printf("任务 '%s' 符合执行条件，开始委派...\n", taskName)
			_, _ = ctx.RunTask("式神委派8", map[string]any{
				"式神委派8-点击对应委派": map[string]any{"expected": taskName},
			})
			fmt.Println("任务执行完成")
		} else if shouldRun {
			fmt.Printf("式神委派8 '%s'，但未在屏幕上找到。\n", taskName)
		}
	}

	return true
}