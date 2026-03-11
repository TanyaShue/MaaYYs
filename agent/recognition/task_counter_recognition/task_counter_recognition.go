package task_counter_recognition

import (
	"encoding/json"
	"fmt"
	"sync"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

// TaskCounterRecognition 用于跟踪任务调用次数的识别器
type TaskCounterRecognition struct {
	mu sync.RWMutex
	// 记录每个任务ID的当前计数
	taskCounts map[int64]int
}

// TaskCounterRecognitionParams 参数结构
type TaskCounterRecognitionParams struct {
	TargetCount int `json:"target_count"` // 目标次数
}

// 确保实现 CustomRecognitionRunner 接口
var _ maa.CustomRecognitionRunner = &TaskCounterRecognition{}

// Run 执行计数识别
// 每次调用计数加一，未达到目标返回 true（识别成功），达到目标返回 false（识别失败）
func (r *TaskCounterRecognition) Run(ctx *maa.Context, arg *maa.CustomRecognitionArg) (*maa.CustomRecognitionResult, bool) {
	// 解析参数
	var params TaskCounterRecognitionParams
	if arg.CustomRecognitionParam != "" {
		if err := json.Unmarshal([]byte(arg.CustomRecognitionParam), &params); err != nil {
			fmt.Printf("TaskCounterRecognition: 解析参数失败: %v\n", err)
			return nil, false
		}
	}

	// 验证参数
	if params.TargetCount < 1 {
		fmt.Printf("TaskCounterRecognition: 无效的目标次数: %d\n", params.TargetCount)
		return nil, false
	}

	taskID := arg.TaskID

	// 初始化 map（如果需要）
	r.mu.Lock()
	if r.taskCounts == nil {
		r.taskCounts = make(map[int64]int)
	}
	r.mu.Unlock()

	// 获取当前计数并加一
	r.mu.Lock()
	currentCount := r.taskCounts[taskID] + 1
	r.taskCounts[taskID] = currentCount
	r.mu.Unlock()

	// 达到 5 的倍数时打印提示
	if currentCount%5 == 0 {
		fmt.Printf("已完成 %d 次\n",  currentCount)
	}

	// 判断是否达到目标
	if currentCount >= params.TargetCount {
		fmt.Printf("已达到目标次数\n")
		// 达到目标后清除计数，以便下次重新开始
		r.mu.Lock()
		delete(r.taskCounts, taskID)
		r.mu.Unlock()
		return nil, false
	}

	// 返回一个空的结果，表示识别成功但没有具体的边界框
	return &maa.CustomRecognitionResult{
		Box: maa.Rect{0, 0, 0, 0},
	}, true
}