package repeat_challenge_n_times

import (
	"encoding/json"
	"fmt"
	"strconv"

	"maa-yys-agent/ocrtext"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

// recognitionChallengeCount 用于识别当前设置的自动挑战次数。
const recognitionChallengeCount = "通用_识别挑战次数"

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
	fmt.Printf("params: %+v\n", params)

	expectedNumber := strconv.Itoa(params.ExpectedNumber)
	if params.ExpectedNumber <= 0 {
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
	currentNumber, currentText, ok := a.recognizeNumber(ctx)
	if !ok {
		// 识别不到就无法比对，直接按期望数字重设，避免沿用旧值而跳过设置
		fmt.Println("警告: 未能识别当前挑战次数, 直接设置期望数字")
		a.inputExpectedNumber(ctx, expectedNumber)
		return true
	}
	fmt.Printf("当前设置次数为%s\n", ocrtext.Describe(currentNumber, currentText))

	if currentNumber == params.ExpectedNumber {
		fmt.Println("当前数字与期望数字相同,完成次数设置")
	} else {
		a.inputExpectedNumber(ctx, expectedNumber)
	}

	return true
}

// recognizeNumber 识别当前设置的挑战次数，返回次数、原始 OCR 文本和是否识别成功。
func (a *RepeatChallengeNTimes) recognizeNumber(ctx *maa.Context) (int, string, bool) {
	controller := ctx.GetTasker().GetController()
	if controller == nil {
		fmt.Println("获取控制器失败")
		return 0, "", false
	}

	controller.PostScreencap().Wait()
	img, err := controller.CacheImage()
	if err != nil {
		fmt.Printf("获取截图失败: %v\n", err)
		return 0, "", false
	}

	detail, err := ctx.RunRecognition(recognitionChallengeCount, img, nil)
	if err != nil {
		fmt.Printf("运行识别节点 %s 失败: %v\n", recognitionChallengeCount, err)
		return 0, "", false
	}
	if detail == nil {
		fmt.Printf("运行识别节点 %s 未返回识别详情\n", recognitionChallengeCount)
		return 0, "", false
	}

	texts := ocrtext.Texts(detail)
	if current, text, ok := ocrtext.Number(texts); ok {
		return current, text, true
	}

	fmt.Printf("识别节点 %s 未解析出挑战次数 (hit=%v, OCR文本=%v)\n", recognitionChallengeCount, detail.Hit, texts)
	return 0, "", false
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
	_, _ = ctx.RunTask("设置挑战次数_点击确定", nil)
}