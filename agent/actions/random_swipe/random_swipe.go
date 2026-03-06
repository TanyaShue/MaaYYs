package random_swipe

import (
	"encoding/json"
	"fmt"
	"math/rand"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type RandomSwipe struct{}

type SwipeParams struct {
	StartROI []int `json:"start_roi"`
	EndROI   []int `json:"end_roi"`
	Delay    int   `json:"delay"`
}

// Run 执行随机滑动操作
func (a *RandomSwipe) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行自定义动作: 随机滑动")

	var params SwipeParams
	if err := json.Unmarshal([]byte(arg.CustomActionParam), &params); err != nil {
		fmt.Printf("解析参数失败: %v\n", err)
		return false
	}

	// 随机生成start点
	startX := rand.Intn(params.StartROI[2]) + params.StartROI[0]
	startY := rand.Intn(params.StartROI[3]) + params.StartROI[1]

	// 随机生成end点
	endX := rand.Intn(params.EndROI[2]) + params.EndROI[0]
	endY := rand.Intn(params.EndROI[3]) + params.EndROI[1]

	duration := params.Delay
	if duration == 0 {
		duration = 200
	}

	// 执行滑动
	controller := ctx.GetTasker().GetController()
	if controller != nil {
		controller.PostSwipe(int32(startX), int32(startY), int32(endX), int32(endY), time.Duration(duration)*time.Millisecond).Wait()
	}

	return true
}