package task_counter

import (
	"encoding/json"
	"fmt"
	"sync"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

// TaskCounter 用于跟踪任务调用次数
type TaskCounter struct {
	mu sync.RWMutex
	// 记录每个任务ID的当前计数
	taskCounts map[int64]int
}

// TaskCounterParams 参数结构
type TaskCounterParams struct {
	TargetCount int `json:"target_count"` // 目标次数
}

// 确保实现 CustomActionRunner 接口
var _ maa.CustomActionRunner = &TaskCounter{}

// Run 执行计数动作
// 每次调用计数加一，未达到目标返回 true，达到目标返回 false
func (a *TaskCounter) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	// 解析参数
	var params TaskCounterParams
	if arg.CustomActionParam != "" {
		if err := json.Unmarshal([]byte(arg.CustomActionParam), &params); err != nil {
			fmt.Printf("TaskCounter: 解析参数失败: %v\n", err)
			return false
		}
	}

	// 验证参数
	if params.TargetCount < 1 {
		fmt.Printf("TaskCounter: 无效的目标次数: %d\n", params.TargetCount)
		return false
	}

	taskID := arg.TaskID

	// 初始化 map（如果需要）
	a.mu.Lock()
	if a.taskCounts == nil {
		a.taskCounts = make(map[int64]int)
	}
	a.mu.Unlock()

	// 获取当前计数并加一
	a.mu.Lock()
	currentCount := a.taskCounts[taskID] + 1
	a.taskCounts[taskID] = currentCount
	a.mu.Unlock()

	fmt.Printf("TaskCounter: TaskID=%d, 当前计数=%d, 目标=%d\n", taskID, currentCount, params.TargetCount)

	// 达到 5 的倍数时打印提示
	if currentCount%5 == 0 {
		fmt.Printf("TaskCounter: TaskID=%d 已完成 %d 次\n", taskID, currentCount)
	}

	// 判断是否达到目标
	if currentCount >= params.TargetCount {
		fmt.Printf("TaskCounter: TaskID=%d 已达到目标次数 %d，返回 false\n", taskID, params.TargetCount)
		// 达到目标后清除计数，以便下次重新开始
		a.mu.Lock()
		delete(a.taskCounts, taskID)
		a.mu.Unlock()
		return false
	}

	fmt.Printf("TaskCounter: TaskID=%d 未达到目标，返回 true\n", taskID)
	return true
}