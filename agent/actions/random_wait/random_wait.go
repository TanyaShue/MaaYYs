package random_wait

import (
	"encoding/json"
	"fmt"
	"math/rand"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type RandomWait struct{}

type WaitParams struct {
	Min interface{} `json:"min"`
	Max interface{} `json:"max"`
}

// Run 根据传入参数随机等待一段时间
func (a *RandomWait) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	paramStr := arg.CustomActionParam

	// 如果参数为空字符串，直接跳过
	if paramStr == "" {
		return true
	}

	var params WaitParams
	if err := json.Unmarshal([]byte(paramStr), &params); err != nil {
		fmt.Printf("参数JSON解析失败: %v\n", err)
		return false
	}

	minWait := toFloat(params.Min, 0.0)
	maxWait := toFloat(params.Max, 0.0)

	// 校验
	if minWait < 0 || maxWait < 0 {
		return false
	}

	// 自动交换大小值
	if minWait > maxWait {
		minWait, maxWait = maxWait, minWait
	}

	if maxWait <= 0 {
		return true
	}

	// 生成随机时间
	waitTime := minWait + rand.Float64()*(maxWait-minWait)
	time.Sleep(time.Duration(waitTime * float64(time.Second)))

	return true
}

// toFloat 安全转换为float64
func toFloat(value interface{}, defaultVal float64) float64 {
	switch v := value.(type) {
	case float64:
		return v
	case float32:
		return float64(v)
	case int:
		return float64(v)
	case int64:
		return float64(v)
	case string:
		var f float64
		fmt.Sscanf(v, "%f", &f)
		if f != 0 {
			return f
		}
		return defaultVal
	default:
		return defaultVal
	}
}