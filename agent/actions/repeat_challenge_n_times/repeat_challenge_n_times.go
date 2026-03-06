package repeat_challenge_n_times

import (
	"encoding/json"
	"fmt"
	"strconv"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type RepeatChallengeNTimes struct{}

type RepeatParams struct {
	StartRepeat    bool `json:"start_repeat"`
	ExpectedNumber int  `json:"expected_number"`
}

// Run 设置挑战次数
func (a *RepeatChallengeNTimes) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	params := RepeatParams{StartRepeat: true, ExpectedNumber: 1}
	if arg.CustomActionParam != "" {
		json.Unmarshal([]byte(arg.CustomActionParam), &params)
	}

	expectedNumber := strconv.Itoa(params.ExpectedNumber)
	if expectedNumber == "" || expectedNumber == "0" {
		fmt.Println("无效的参数：expected_number")
		return false
	}

	fmt.Printf("开始点击自动允许次数设置：期望数字 %s\n", expectedNumber)

	if params.StartRepeat {
		_, _ = ctx.RunTask("通用_启动设置挑战次数", nil)
		fmt.Println("启动自动挑战")
	} else {
		_, _ = ctx.RunTask("通用_取消设置挑战次数", nil)
		fmt.Println("关闭自动挑战")
		return true
	}

	// 识别当前区域的数字
	currentNumber := a.recognizeNumber(ctx)
	fmt.Printf("当前设置次数为%s\n", currentNumber)

	if currentNumber == expectedNumber {
		fmt.Println("当前数字与期望数字相同,完成次数设置")
	} else {
		a.inputExpectedNumber(ctx, expectedNumber)
	}

	return true
}

func (a *RepeatChallengeNTimes) recognizeNumber(ctx *maa.Context) string {
	controller := ctx.GetTasker().GetController()
	if controller == nil {
		return "10"
	}

	controller.PostScreencap().Wait()
	img, err := controller.CacheImage()
	if err != nil {
		return "10"
	}

	result, _ := ctx.RunRecognition("通用_识别挑战次数", img, nil)
	if result != nil && result.Hit {
		return "10"
	}
	return "10"
}

func (a *RepeatChallengeNTimes) inputExpectedNumber(ctx *maa.Context, expectedNumber string) {
	fmt.Println("开始点击数字")
	_, _ = ctx.RunTask("设置挑战次数_点击数字编辑", nil)

	for _, n := range expectedNumber {
		fmt.Printf("开始点击数字: %c\n", n)
		_, _ = ctx.RunTask("设置挑战次数_点击目标数字", map[string]any{
			"设置挑战次数_点击目标数字": map[string]any{"expected": string(n)},
		})
	}

	fmt.Println("点击数字完成")
	nu := a.recognizeNumber(ctx)
	if nu == expectedNumber {
		_, _ = ctx.RunTask("设置挑战次数_点击确定", nil)
	}
}