package auto_battle

import (
	"encoding/json"
	"fmt"
	"math/rand"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type AutoBattle struct{}

type AutoBattleParams struct {
	GroupName string `json:"group_name"`
	TeamName  string `json:"team_name"`
}

// Run 执行自动战斗
func (a *AutoBattle) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("2秒后开始战斗")
	time.Sleep(2 * time.Second)

	params := AutoBattleParams{}
	if arg.CustomActionParam != "" {
		json.Unmarshal([]byte(arg.CustomActionParam), &params)
	}

	// 点击预设
	if params.GroupName != "" {
		_, _ = ctx.RunTask("通用_点击预设", nil)
		fmt.Println("预设点击成功")

		// 重试机制
		maxRetries := 3
		for retry := 1; retry <= maxRetries; retry++ {
			fmt.Printf("第%d次尝试查找分组和队伍\n", retry)

			if !a.selectGroup(ctx, params.GroupName) {
				fmt.Printf("第%d次尝试：未找到分组 %s\n", retry, params.GroupName)
				if retry == maxRetries {
					fmt.Println("达到最大重试次数，查找分组失败")
					return false
				}
				continue
			}

			time.Sleep(1 * time.Second)

			if a.selectTeam(ctx, params.TeamName) {
				fmt.Printf("成功找到并选择队伍 %s\n", params.TeamName)
				break
			} else {
				fmt.Printf("第%d次尝试：未找到队伍 %s\n", retry, params.TeamName)
				if retry == maxRetries {
					fmt.Println("达到最大重试次数，查找队伍失败")
					return false
				}
				fmt.Println("重新从分组开始查找...")
				time.Sleep(1 * time.Second)
			}
		}

		// 出战队伍
		_, _ = ctx.RunTask("通用_出战队伍", nil)
	}

	// 点击准备按钮两次
	controller := ctx.GetTasker().GetController()
	if controller == nil {
		fmt.Println("获取控制器失败")
		return false
	}

	r := rand.New(rand.NewSource(time.Now().UnixNano()))
	for i := 0; i < 2; i++ {
		x := r.Intn(112) + 1125
		y := r.Intn(96) + 539
		fmt.Printf("随机点击准备按钮: %d,%d\n", x, y)
		time.Sleep(1 * time.Second)
		controller.PostClick(int32(x), int32(y)).Wait()
	}

	return true
}

func (a *AutoBattle) selectGroup(ctx *maa.Context, groupName string) bool {
	controller := ctx.GetTasker().GetController()
	if controller == nil {
		fmt.Println("获取控制器失败")
		return false
	}

	// 分组回到最上页
	for i := 0; i < 2; i++ {
		_, _ = ctx.RunTask("返回最上页分组", map[string]any{
			"返回最上页分组": map[string]any{
				"action":              "Custom",
				"custom_action":       "RandomSwipe",
				"custom_action_param": map[string]any{
					"end_roi":   []int{39, 582, 113, 36},
					"start_roi": []int{39, 270, 120, 38},
					"delay":     200,
				},
			},
		})
	}

	time.Sleep(3 * time.Second)

	// 点击分组
	for count := 1; count <= 20; count++ {
		time.Sleep(2 * time.Second)

		// 先截图
		controller.PostScreencap().Wait()
		img, err := controller.CacheImage()
		if err != nil {
			fmt.Printf("获取截图失败: %v\n", err)
			continue
		}

		// 识别并点击分组
		detail, err := ctx.RunRecognition("点击分组", img, map[string]any{
			"点击分组": map[string]any{
				"timeout":    500,
				"post_delay": 1000,
				"recognition": "OCR",
				"expected":   groupName,
				"roi":        []int{34, 241, 132, 440},
			},
		})
		if err != nil {
			fmt.Printf("识别分组失败: %v\n", err)
		}

		time.Sleep(1 * time.Second)

		if detail != nil && detail.Hit {
			r := rand.New(rand.NewSource(time.Now().UnixNano()))
			x := r.Intn(detail.Box.Height()) + detail.Box.X()
			y := r.Intn(detail.Box.Width()) + detail.Box.Y()
			controller.PostClick(int32(x), int32(y)).Wait()
			fmt.Printf("切换到分组 %s\n", groupName)
			return true
		}

		if count >= 5 {
			_, _ = ctx.RunTask("返回最上页分组", map[string]any{
				"返回最上页分组": map[string]any{
					"action":              "Custom",
					"post_delay":          1000,
					"custom_action":       "RandomSwipe",
					"custom_action_param": map[string]any{
						"end_roi":   []int{39, 582, 113, 36},
						"start_roi": []int{39, 270, 120, 38},
						"delay":     1000,
					},
				},
			})
		} else {
			_, _ = ctx.RunTask("下一页", map[string]any{
				"下一页": map[string]any{
					"action":              "Custom",
					"per_delay":           1000,
					"post_delay":          1000,
					"custom_action":       "RandomSwipe",
					"custom_action_param": map[string]any{
						"start_roi": []int{39, 582, 113, 36},
						"end_roi":   []int{39, 270, 120, 38},
						"delay":     1000,
					},
				},
			})
			time.Sleep(2 * time.Second)
		}
	}
	return false
}

func (a *AutoBattle) selectTeam(ctx *maa.Context, teamName string) bool {
	fmt.Println("开始执行自定义动作：点击队伍")

	controller := ctx.GetTasker().GetController()
	if controller == nil {
		fmt.Println("获取控制器失败")
		return false
	}

	for count := 1; count <= 10; count++ {
		// 先截图
		controller.PostScreencap().Wait()
		img, err := controller.CacheImage()
		if err != nil {
			fmt.Printf("获取截图失败: %v\n", err)
			continue
		}

		detail, err := ctx.RunRecognition("点击队伍", img, map[string]any{
			"点击队伍": map[string]any{
				"timeout":     500,
				"recognition": "OCR",
				"expected":    teamName,
				"roi":         []int{254, 235, 263, 355},
			},
		})
		if err != nil {
			fmt.Printf("识别队伍失败: %v\n", err)
		}

		time.Sleep(1 * time.Second)

		if detail != nil && detail.Hit {
			time.Sleep(1 * time.Second)
			fmt.Printf("切换到队伍 %s\n", teamName)

			r := rand.New(rand.NewSource(time.Now().UnixNano()))
			x := r.Intn(detail.Box.Height()) + detail.Box.X()
			y := r.Intn(detail.Box.Width()) + detail.Box.Y()
			controller.PostClick(int32(x), int32(y)).Wait()

			time.Sleep(1 * time.Second)
			clickX := r.Intn(132) + 359
			clickY := r.Intn(36) + 647
			controller.PostClick(int32(clickX), int32(clickY)).Wait()
			return true
		}

		if count >= 5 {
			_, _ = ctx.RunTask("返回最上页分队", map[string]any{
				"返回最上页分队": map[string]any{
					"action":              "Custom",
					"custom_action":       "RandomSwipe",
					"custom_action_param": map[string]any{
						"end_roi":   []int{328, 484, 253, 103},
						"start_roi": []int{334, 235, 300, 90},
						"delay":     1000,
					},
				},
			})
		} else {
			_, _ = ctx.RunTask("下一页", map[string]any{
				"下一页": map[string]any{
					"action":              "Custom",
					"custom_action":       "RandomSwipe",
					"custom_action_param": map[string]any{
						"start_roi": []int{328, 484, 253, 103},
						"end_roi":   []int{334, 235, 300, 90},
						"delay":     1000,
					},
				},
			})
		}
	}

	fmt.Println("队伍不存在")
	return false
}