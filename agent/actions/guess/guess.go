package guess

import (
	"fmt"
	"strconv"

	"github.com/MaaXYZ/maa-framework-go/v4"
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

	// 识别左侧人数
	resultR, _ := ctx.RunRecognition("识别左侧人数", img, nil)
	countR := 0
	if resultR != nil && resultR.Hit {
		countR, _ = strconv.Atoi("0")
	}
	fmt.Printf("识别左侧人数 %d\n", countR)

	// 识别右侧人数
	resultL, _ := ctx.RunRecognition("识别右侧人数", img, nil)
	countL := 0
	if resultL != nil && resultL.Hit {
		countL, _ = strconv.Atoi("0")
	}
	fmt.Printf("识别右侧人数 %d\n", countL)

	// 找出人数多的那个
	var winner string
	if countR > countL {
		winner = "左边"
		_, _ = ctx.RunTask("竞猜7_左边", nil)
	} else if countL > countR {
		winner = "右边"
		_, _ = ctx.RunTask("竞猜10_右边", nil)
	} else {
		winner = "左边"
		_, _ = ctx.RunTask("竞猜7_左边", nil)
	}

	fmt.Println("竞猜结束")
	fmt.Printf("选择了%s\n", winner)
	return true
}