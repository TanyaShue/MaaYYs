package human_touch

import (
	"encoding/json"
	"fmt"
	"math/rand"
	"strconv"
	"sync"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

// FlexibleFloat 可以接受字符串或数字类型的JSON值
type FlexibleFloat float64

func (f *FlexibleFloat) UnmarshalJSON(data []byte) error {
	// 尝试解析为数字
	var num float64
	if err := json.Unmarshal(data, &num); err == nil {
		*f = FlexibleFloat(num)
		return nil
	}

	// 尝试解析为字符串
	var str string
	if err := json.Unmarshal(data, &str); err != nil {
		return fmt.Errorf("无法将 %s 解析为 float64 或 string", string(data))
	}

	// 将字符串转换为 float64
	val, err := strconv.ParseFloat(str, 64)
	if err != nil {
		return fmt.Errorf("无法将字符串 '%s' 转换为 float64: %v", str, err)
	}
	*f = FlexibleFloat(val)
	return nil
}

type HumanTouch struct {
	count int
	mu    sync.Mutex
}

type HumanTouchParams struct {
	ROI1              []interface{} `json:"ROI_1"`
	ShortWaitMin      FlexibleFloat `json:"short_wait_min"`
	ShortWaitMax      FlexibleFloat `json:"short_wait_max"`
	LongWaitMin       FlexibleFloat `json:"long_wait_min"`
	LongWaitMax       FlexibleFloat `json:"long_wait_max"`
	ShortWaitWeight   FlexibleFloat `json:"short_wait_weight"`
	LongWaitWeight    FlexibleFloat `json:"long_wait_weight"`
	SingleClickWeight FlexibleFloat `json:"single_click_weight"`
	DoubleClickWeight FlexibleFloat `json:"double_click_weight"`
}

// Run 执行模拟人类点击
func (a *HumanTouch) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	params := HumanTouchParams{
		ShortWaitMin:      1,
		ShortWaitMax:      20,
		LongWaitMin:       100,
		LongWaitMax:       200,
		ShortWaitWeight:   95,
		LongWaitWeight:    5,
		SingleClickWeight: 50,
		DoubleClickWeight: 50,
	}
	if arg.CustomActionParam != "" {
		if err := json.Unmarshal([]byte(arg.CustomActionParam), &params); err != nil {
			fmt.Printf("警告: 解析JSON参数失败。将使用默认值。错误: %v\n", err)
		}
	}

	// 解析ROI参数
	xMin, yMin, xMax, yMax := 148, 517, 930, 197
	if len(params.ROI1) == 4 {
		xMin = toInt(params.ROI1[0])
		yMin = toInt(params.ROI1[1])
		w := toInt(params.ROI1[2])
		h := toInt(params.ROI1[3])
		xMax = xMin + w
		yMax = yMin + h
	}
	// 安全检查
	if xMin > xMax {
		xMin, xMax = xMax, xMin
	}
	if yMin > yMax {
		yMin, yMax = yMax, yMin
	}

	// 等待时间决策
	totalWaitWeight := float64(params.ShortWaitWeight + params.LongWaitWeight)
	waitRandNum := rand.Float64() * totalWaitWeight

	var waitTime float64
	if waitRandNum < float64(params.LongWaitWeight) {
		waitTime = float64(params.LongWaitMin) + rand.Float64()*(float64(params.LongWaitMax)-float64(params.LongWaitMin))
		fmt.Printf("开始长等待: %.2f秒\n", waitTime)
	} else {
		waitTime = float64(params.ShortWaitMin) + rand.Float64()*(float64(params.ShortWaitMax)-float64(params.ShortWaitMin))
		fmt.Printf("开始短等待: %.2f秒\n", waitTime)
	}

	time.Sleep(time.Duration(waitTime * float64(time.Second)))

	// 点击类型决策
	totalClickWeight := float64(params.SingleClickWeight + params.DoubleClickWeight)
	clickRandNum := rand.Float64() * totalClickWeight

	x := rand.Intn(xMax-xMin) + xMin
	y := rand.Intn(yMax-yMin) + yMin

	controller := ctx.GetTasker().GetController()
	if controller == nil {
		fmt.Println("获取控制器失败")
		return false
	}

	if clickRandNum < float64(params.DoubleClickWeight) {
		// 双击
		controller.PostClick(int32(x), int32(y)).Wait()
		controller.PostClick(int32(x), int32(y)).Wait()
	} else {
		// 单击
		controller.PostClick(int32(x), int32(y)).Wait()
	}

	return true
}

func toInt(value interface{}) int {
	switch v := value.(type) {
	case int:
		return v
	case float64:
		return int(v)
	case float32:
		return int(v)
	case int64:
		return int(v)
	default:
		return 0
	}
}
