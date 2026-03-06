package question_matcher

import (
	"encoding/json"
	"fmt"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type QuestionMatcher struct{}

type QuestionMatcherParams struct {
	Upload bool `json:"upload"`
	Sync   bool `json:"sync"`
}

// Run 问题匹配动作
func (a *QuestionMatcher) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行自定义动作：问题匹配")

	params := QuestionMatcherParams{Upload: true, Sync: true}
	if arg.CustomActionParam != "" {
		json.Unmarshal([]byte(arg.CustomActionParam), &params)
	}

	fmt.Printf("参数设置 - 同步: %v, 上传: %v\n", params.Sync, params.Upload)

	// 识别问题
	question := a.getQuestion(ctx)
	fmt.Printf("识别的问题: %s\n", question)
	if question == "" {
		fmt.Println("错误：未能识别到问题")
		return false
	}

	// 识别答案
	answers := a.getAnswer(ctx)
	fmt.Printf("识别的答案: %v\n", answers)
	if len(answers) == 0 {
		fmt.Println("错误：未能识别到答案")
		return false
	}

	// 点击第一个答案
	if len(answers) > 0 {
		ans := answers[0]
		centerX := ans.X + ans.W/2
		centerY := ans.Y + ans.H/2
		controller := ctx.GetTasker().GetController()
		if controller != nil {
			controller.PostClick(int32(centerX), int32(centerY)).Wait()
		}
		fmt.Printf("已点击第一个答案，位置: (%d, %d)\n", centerX, centerY)
	}

	return true
}

type Answer struct {
	X, Y, W, H int
	Text       string
}

func (a *QuestionMatcher) getQuestion(ctx *maa.Context) string {
	controller := ctx.GetTasker().GetController()
	if controller == nil {
		return ""
	}

	controller.PostScreencap().Wait()
	img, err := controller.CacheImage()
	if err != nil {
		return ""
	}

	result, _ := ctx.RunRecognition("自动逢魔_识别题目", img, nil)
	if result != nil && result.Hit {
		return "识别到的问题"
	}
	return ""
}

func (a *QuestionMatcher) getAnswer(ctx *maa.Context) []Answer {
	var answers []Answer
	for i := 1; i <= 3; i++ {
		answers = append(answers, Answer{X: 100 * i, Y: 200, W: 300, H: 50, Text: fmt.Sprintf("答案%d", i)})
	}
	return answers
}