package count_action

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type CountAction struct {
	shouldStop bool
	mu         sync.Mutex
}

type CountParams struct {
	NextTask    string  `json:"next_task"`
	CountTarget int     `json:"count_target"`
	Interval    float64 `json:"interval"`
	TaskToCount string  `json:"task_to_count"`
}

// Run 执行计数动作，当达到目标计数时执行next任务
func (a *CountAction) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	// 重置停止标志
	a.mu.Lock()
	a.shouldStop = false
	a.mu.Unlock()

	var params CountParams
	if err := json.Unmarshal([]byte(arg.CustomActionParam), &params); err != nil {
		fmt.Printf("解析参数失败: %v\n", err)
		return false
	}

	// 设置默认值
	if params.CountTarget < 1 {
		params.CountTarget = 1
	}
	if params.Interval == 0 {
		params.Interval = 1.0
	}

	// 验证参数
	if params.NextTask == "" || params.TaskToCount == "" {
		fmt.Printf("无效的参数: next_task=%s, count_target=%d, task_to_count=%s\n",
			params.NextTask, params.CountTarget, params.TaskToCount)
		return false
	}

	fmt.Printf("开始计数动作: 目标=%d, 间隔=%.1f秒, 计数任务=%s, 下一任务=%s\n",
		params.CountTarget, params.Interval, params.TaskToCount, params.NextTask)

	currentCount := 0

	// 开始计数循环
	for currentCount < params.CountTarget {
		a.mu.Lock()
		stop := a.shouldStop
		a.mu.Unlock()
		if stop {
			break
		}

		fmt.Printf("当前计数: %d/%d\n", currentCount, params.CountTarget)

		// 截图并执行识别
		controller := ctx.GetTasker().GetController()
		if controller == nil {
			fmt.Println("获取控制器失败")
			return false
		}
		controller.PostScreencap().Wait()
		img, err := controller.CacheImage()
		if err != nil {
			fmt.Printf("获取截图失败: %v\n", err)
			return false
		}
		result, err := ctx.RunRecognition(params.TaskToCount, img, nil)
		if err != nil {
			fmt.Printf("识别任务 %s 执行失败: %v\n", params.TaskToCount, err)
		}

		if result != nil && result.Hit {
			currentCount++
			fmt.Printf("任务 %s 执行成功，计数增加到 %d\n", params.TaskToCount, currentCount)
		} else {
			fmt.Printf("任务 %s 执行失败，计数保持 %d\n", params.TaskToCount, currentCount)
		}

		// 如果达到目标计数，退出循环
		if currentCount >= params.CountTarget {
			break
		}

		// 等待指定的间隔时间
		a.mu.Lock()
		stop = a.shouldStop
		a.mu.Unlock()
		if !stop && params.Interval > 0 {
			fmt.Printf("等待 %.1f 秒...\n", params.Interval)
			time.Sleep(time.Duration(params.Interval * float64(time.Second)))
		}
	}

	// 检查是否因为达到目标退出循环
	a.mu.Lock()
	stop := a.shouldStop
	a.mu.Unlock()

	if currentCount >= params.CountTarget && !stop {
		fmt.Printf("达到目标计数 %d，执行下一任务: %s\n", params.CountTarget, params.NextTask)
		_, err := ctx.RunTask(params.NextTask)
		if err != nil {
			fmt.Printf("执行下一任务 %s 失败: %v\n", params.NextTask, err)
			return false
		}
		return true
	} else if stop {
		fmt.Println("计数动作被手动停止")
		return false
	}

	fmt.Println("计数未达到目标但循环已结束")
	return false
}