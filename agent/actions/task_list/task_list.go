package task_list

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
	"maa-yys-agent/until/daily_task_tracker"
)

type TaskList struct{}

type TaskConfig struct {
	Enabled     bool `json:"enabled"`
	OncePerDay  bool `json:"once_per_day"`
}

type TaskListParams struct {
	Tasks map[string]TaskConfig `json:"tasks"`
}

// Run 执行任务列表
func (a *TaskList) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行自定义动作：任务列表 (字典版)")

	var params TaskListParams
	if err := json.Unmarshal([]byte(arg.CustomActionParam), &params); err != nil {
		fmt.Println("参数 JSON 解析失败")
		return false
	}

	if len(params.Tasks) == 0 {
		fmt.Println("未检测到有效的 'tasks' 字典配置")
		return false
	}

	tracker := daily_task_tracker.NewDailyTaskTracker()

	// 遍历字典
	for taskEntry, config := range params.Tasks {
		// 检查是否启用
		if !config.Enabled {
			fmt.Printf("[%s] 配置为禁用，跳过\n", taskEntry)
			continue
		}

		// 检查每日一次逻辑
		if config.OncePerDay {
			if tracker.HasExecutedToday(taskEntry) {
				fmt.Printf("[%s] 今日已执行过，跳过\n", taskEntry)
				continue
			}
		}

		// 执行任务
		fmt.Printf("开始执行任务: %s\n", taskEntry)
		_, err := ctx.RunTask(taskEntry)
		if err != nil {
			fmt.Printf("任务 %s 执行失败: %v\n", taskEntry, err)
		} else {
			fmt.Printf("任务 %s 执行完成\n", taskEntry)
		}

		// 记录执行状态
		if config.OncePerDay {
			tracker.RecordExecution(taskEntry)
		}

		time.Sleep(2 * time.Second)
	}

	fmt.Println("任务列表执行完毕")
	return true
}