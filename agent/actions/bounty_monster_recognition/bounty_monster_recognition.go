package bounty_monster_recognition

import (
	"fmt"
	"math/rand"
	"regexp"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type BountyMonsterRecognition struct{}

// Run 识别悬赏妖怪
func (a *BountyMonsterRecognition) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行自定义动作：识别悬赏妖怪")
	attempts := 0

	controller := ctx.GetTasker().GetController()
	if controller == nil {
		fmt.Println("获取控制器失败")
		return false
	}

	for attempts < 3 {
		_, _ = ctx.RunTask("悬赏封印_开始领取宝箱奖励", nil)
		_, _ = ctx.RunTask("悬赏封印_关闭章节界面", nil)

		// 先截图
		controller.PostScreencap().Wait()
		img, err := controller.CacheImage()
		if err != nil {
			fmt.Printf("获取截图失败: %v\n", err)
			continue
		}

		// 识别妖怪
		detail, _ := ctx.RunRecognition("悬赏封印_识别妖怪", img, nil)
		detail1, _ := ctx.RunRecognition("悬赏封印_识别挑战次数", img, nil)
		detail2, _ := ctx.RunRecognition("悬赏封印_识别妖怪_图片识别", img, nil)

		if (detail != nil && detail.Hit) || (detail1 != nil && detail1.Hit) || (detail2 != nil && detail2.Hit) {
			// 处理识别结果
			fmt.Println("识别到妖怪")
			r := rand.New(rand.NewSource(time.Now().UnixNano()))

			// 随机点击识别到的妖怪位置
			if detail != nil && detail.Hit {
				x := r.Intn(detail.Box.Width()) + detail.Box.X()
				y := r.Intn(detail.Box.Height()) + detail.Box.Y()
				controller.PostClick(int32(x), int32(y)).Wait()
				time.Sleep(1 * time.Second)

				// 检查是否在线索界面
				controller.PostScreencap().Wait()
				img2, _ := controller.CacheImage()
				clickDetail, _ := ctx.RunRecognition("悬赏_线索界面", img2, nil)
				if clickDetail == nil || !clickDetail.Hit {
					fmt.Println("未处于线索界面，尝试重新识别妖怪")
					_, _ = ctx.RunTask("悬赏封印_关闭章节界面", nil)
					_, _ = ctx.RunTask("悬赏封印_关闭线索界面", nil)
					continue
				}

				// 识别是否为未发现
				controller.PostScreencap().Wait()
				img3, _ := controller.CacheImage()
				notFoundDetail, _ := ctx.RunRecognition("识别未发现妖怪", img3, nil)
				if notFoundDetail != nil && notFoundDetail.Hit {
					time.Sleep(1 * time.Second)
					_, _ = ctx.RunTask("悬赏封印_关闭线索界面", nil)
					continue
				}

				_, _ = ctx.RunTask("悬赏_开始识别探索", nil)
				attempts = 0
				break
			}
		} else {
			fmt.Println("未识别到妖怪")
		}

		_, _ = ctx.RunTask("识别探索目标_向上滑动", nil)
		attempts++
		fmt.Printf("尝试次数 attempts=: %d\n", attempts)
	}

	fmt.Println("识别悬赏妖怪结束")
	return true
}

func (a *BountyMonsterRecognition) matchesRegex(text string) bool {
	pattern := `^(\d+)/(\1)$|^(\d+)7(\3)$`
	matched, _ := regexp.MatchString(pattern, text)
	return matched
}