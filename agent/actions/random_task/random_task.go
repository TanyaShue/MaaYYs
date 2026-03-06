package random_task

import (
	"encoding/json"
	"fmt"
	"math/rand"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type RandomTask struct{}

// Run 根据权重随机选择并执行一个任务
func (a *RandomTask) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行自定义动作：随机任务")

	// 解析参数
	var taskWeightsMap map[string]float64
	if err := json.Unmarshal([]byte(arg.CustomActionParam), &taskWeightsMap); err != nil {
		fmt.Printf("参数JSON解析失败: %v\n", err)
		return false
	}

	if len(taskWeightsMap) == 0 {
		fmt.Println("传入的任务列表为空")
		return false
	}

	// 分离任务和权重
	tasks := make([]string, 0, len(taskWeightsMap))
	weights := make([]float64, 0, len(taskWeightsMap))
	for task, weight := range taskWeightsMap {
		if weight < 0 {
			fmt.Printf("错误：权重值不能为负数。发现无效权重: %f\n", weight)
			return false
		}
		tasks = append(tasks, task)
		weights = append(weights, weight)
	}

	// 校验权重总和
	var totalWeight float64
	for _, w := range weights {
		totalWeight += w
	}
	if totalWeight <= 0 {
		fmt.Println("错误：所有任务的权重总和必须大于0。")
		return false
	}

	// 随机选择任务
	fmt.Printf("任务池: %v\n", tasks)
	fmt.Printf("对应权重: %v\n", weights)

	chosenIdx := weightedRandomChoice(weights)
	chosenTask := tasks[chosenIdx]
	fmt.Printf("随机选择的任务是: %s\n", chosenTask)

	// 执行任务
	_, err := ctx.RunTask(chosenTask)
	if err != nil {
		fmt.Printf("任务 '%s' 执行失败: %v\n", chosenTask, err)
		return false
	}
	fmt.Printf("任务 '%s' 执行成功。\n", chosenTask)

	return true
}

// weightedRandomChoice 根据权重随机选择索引
func weightedRandomChoice(weights []float64) int {
	var totalWeight float64
	for _, w := range weights {
		totalWeight += w
	}

	r := rand.Float64() * totalWeight
	var sum float64
	for i, w := range weights {
		sum += w
		if r <= sum {
			return i
		}
	}
	return len(weights) - 1
}