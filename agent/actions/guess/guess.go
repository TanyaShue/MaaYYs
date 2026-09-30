package guess

import (
	"fmt"
	"image"
	"math/rand"

	"maa-yys-agent/ocrtext"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

const (
	// 识别节点
	recognitionLeftCount  = "识别左侧人数"
	recognitionRightCount = "识别右侧人数"

	// 押注任务
	taskBetLeft  = "竞猜7_左边"
	taskBetRight = "竞猜10_右边"
)

type Guess struct{}

// Run 执行竞猜
func (a *Guess) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行自定义动作：竞猜")

	controller := ctx.GetTasker().GetController()
	if controller == nil {
		fmt.Println("获取控制器失败")
		return false
	}

	// 先截图
	controller.PostScreencap().Wait()
	img, err := controller.CacheImage()
	if err != nil {
		fmt.Printf("获取截图失败: %v\n", err)
		return false
	}

	// 识别两侧人数：人数取自识别结果的 OCR 文本，取不到才算识别失败
	leftCount, leftText, leftOK := recognizeCount(ctx, img, recognitionLeftCount)
	rightCount, rightText, rightOK := recognizeCount(ctx, img, recognitionRightCount)

	fmt.Printf("识别左侧人数 %s\n", describeCount(leftCount, leftText, leftOK))
	fmt.Printf("识别右侧人数 %s\n", describeCount(rightCount, rightText, rightOK))

	// 找出人数多的那个
	if !leftOK || !rightOK {
		fmt.Println("警告: 人数识别失败, 无法比较, 随机选择一边竞猜")
	}
	task, winner := pickBet(leftCount, leftOK, rightCount, rightOK)

	if _, err := ctx.RunTask(task, nil); err != nil {
		fmt.Printf("执行任务失败: %s, 错误: %v\n", task, err)
		return false
	}

	fmt.Println("竞猜结束")
	fmt.Printf("选择了%s\n", winner)
	return true
}

// pickBet 根据两侧人数决定押注任务与方向。
// 人数相同时押左边；有一侧识别失败时无法比较，随机押一边，避免因识别波动中断流水线。
func pickBet(leftCount int, leftOK bool, rightCount int, rightOK bool) (task, winner string) {
	if !leftOK || !rightOK {
		if rand.Intn(2) == 1 {
			return taskBetRight, "右边"
		}
		return taskBetLeft, "左边"
	}
	if rightCount > leftCount {
		return taskBetRight, "右边"
	}
	return taskBetLeft, "左边"
}

// recognizeCount 运行指定识别节点并解析出人数，返回人数、原始 OCR 文本和是否解析成功。
func recognizeCount(ctx *maa.Context, img image.Image, node string) (int, string, bool) {
	detail, err := ctx.RunRecognition(node, img, nil)
	if err != nil {
		fmt.Printf("运行识别节点 %s 失败: %v\n", node, err)
		return 0, "", false
	}
	if detail == nil {
		fmt.Printf("运行识别节点 %s 未返回识别详情\n", node)
		return 0, "", false
	}

	texts := ocrtext.Texts(detail)
	if count, text, ok := ocrtext.Number(texts); ok {
		return count, text, true
	}

	fmt.Printf("识别节点 %s 未解析出人数 (hit=%v, OCR文本=%v)\n", node, detail.Hit, texts)
	return 0, "", false
}

// describeCount 生成日志中的人数描述，解析失败时明确标出失败。
func describeCount(count int, text string, ok bool) string {
	if !ok {
		return "失败"
	}
	return ocrtext.Describe(count, text)
}
