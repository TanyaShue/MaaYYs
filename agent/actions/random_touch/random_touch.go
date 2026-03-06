package random_touch

import (
	"fmt"
	"math/rand"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type RandomTouch struct{}

// Run 执行随机点击操作
func (a *RandomTouch) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行自定义动作：随机点击")

	x := arg.Box.X()
	y := arg.Box.Y()
	w := arg.Box.Width()
	h := arg.Box.Height()

	centerX := float64(x) + float64(w)/2
	centerY := float64(y) + float64(h)/2

	// 使用正态分布生成随机点
	r := rand.New(rand.NewSource(time.Now().UnixNano()))
	randomX := r.NormFloat64()*(float64(w)/6) + centerX
	randomY := r.NormFloat64()*(float64(h)/6) + centerY

	// 边界检查
	minVal := func(a, b float64) float64 {
		if a < b {
			return a
		}
		return b
	}
	maxVal := func(a, b float64) float64 {
		if a > b {
			return a
		}
		return b
	}

	randomX = maxVal(float64(x), minVal(randomX, float64(x+w)))
	randomY = maxVal(float64(y), minVal(randomY, float64(y+h)))

	// 执行点击
	controller := ctx.GetTasker().GetController()
	if controller != nil {
		controller.PostClick(int32(randomX), int32(randomY)).Wait()
	}

	fmt.Printf("随机生成的点: (%.2f, %.2f)\n", randomX, randomY)
	return true
}