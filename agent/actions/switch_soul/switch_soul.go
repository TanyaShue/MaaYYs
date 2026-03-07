package switch_soul

import (
	"encoding/json"
	"fmt"
	"math/rand"
	"sync"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type SwitchSoul struct {
	running bool
	mu      sync.Mutex
}

type SwitchSoulParams struct {
	GroupName string `json:"group_name"`
	TeamName  string `json:"team_name"`
}

// Run 执行御魂切换操作
func (a *SwitchSoul) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	a.mu.Lock()
	a.running = true
	a.mu.Unlock()

	params := SwitchSoulParams{}
	if arg.CustomActionParam != "" {
		if err := json.Unmarshal([]byte(arg.CustomActionParam), &params); err != nil {
			fmt.Printf("参数解析错误: %v\n", err)
			return false
		}
	}

	if params.GroupName == "" || params.TeamName == "" {
		fmt.Println("参数错误：分组名称和队伍名称不能为空")
		return false
	}

	fmt.Printf("切换御魂 - 分组：%s，队伍：%s\n", params.GroupName, params.TeamName)

	// 步骤1：点击预设按钮
	if !a.clickPreset(ctx) {
		fmt.Println("点击预设按钮失败")
		return false
	}

	// 步骤2：查找并点击指定分组
	if !a.findAndClickGroup(ctx, params.GroupName) {
		fmt.Printf("找不到指定分组: %s\n", params.GroupName)
		return false
	}

	// 步骤3：查找并装备指定队伍的御魂
	if !a.findAndEquipTeam(ctx, params.TeamName) {
		fmt.Printf("找不到指定队伍或装备失败: %s\n", params.TeamName)
		return false
	}

	fmt.Println("御魂切换完成")
	return true
}

func (a *SwitchSoul) clickPreset(ctx *maa.Context) bool {
	fmt.Println("尝试点击预设按钮")
	_, _ = ctx.RunTask("通用_切换御魂_开始", nil)
	time.Sleep(1000 * time.Millisecond)
	return true
}

func (a *SwitchSoul) findAndClickGroup(ctx *maa.Context, groupName string) bool {
	fmt.Printf("开始查找分组: %s\n", groupName)

	controller := ctx.GetTasker().GetController()
	if controller == nil {
		fmt.Println("获取控制器失败")
		return false
	}

	// 返回最上方
	_, _ = ctx.RunTask("返回最上页分组", map[string]any{
		"返回最上页分组": map[string]any{
			"action":              "Custom",
			"custom_action":       "RandomSwipe",
			"custom_action_param": map[string]any{
				"start_roi": []int{1127, 94, 82, 28},
				"end_roi":   []int{1115, 571, 100, 40},
				"delay":     500,
			},
		},
	})
	time.Sleep(2 * time.Second)

	maxAttempts := 5
	r := rand.New(rand.NewSource(time.Now().UnixNano()))

	for attempt := 1; attempt <= maxAttempts; attempt++ {
		a.mu.Lock()
		running := a.running
		a.mu.Unlock()
		if !running {
			return false
		}

		fmt.Printf("查找分组 - 第%d次尝试\n", attempt)

		// 先截图
		controller.PostScreencap().Wait()
		img, err := controller.CacheImage()
		if err != nil {
			fmt.Printf("获取截图失败: %v\n", err)
			continue
		}

		detail, _ := ctx.RunRecognition("点击分组", img, map[string]any{
			"点击分组": map[string]any{
				"timeout":     2000,
				"recognition": "OCR",
				"expected":    groupName,
				"roi":         []int{1099, 82, 140, 545},
			},
		})

		if detail != nil && detail.Hit {
			clickX := r.Intn(detail.Box.Width()) + detail.Box.X()
			clickY := r.Intn(detail.Box.Height()) + detail.Box.Y()
			controller.PostClick(int32(clickX), int32(clickY)).Wait()
			fmt.Printf("成功找到并点击分组: %s\n", groupName)
			return true
		}

		// 滑动到下一页
		if attempt%3 == 0 {
			_, _ = ctx.RunTask("返回最上页分组", map[string]any{
				"返回最上页分组": map[string]any{
					"action":              "Custom",
					"post_delay":          1000,
					"custom_action":       "RandomSwipe",
					"custom_action_param": map[string]any{
						"start_roi": []int{1127, 94, 82, 28},
						"end_roi":   []int{1115, 571, 100, 40},
						"delay":     500,
					},
				},
			})
		} else {
			_, _ = ctx.RunTask("下一页", map[string]any{
				"下一页": map[string]any{
					"action":              "Custom",
					"post_delay":          1000,
					"custom_action":       "RandomSwipe",
					"custom_action_param": map[string]any{
						"start_roi": []int{1115, 571, 100, 40},
						"end_roi":   []int{1127, 94, 82, 28},
						"delay":     1000,
					},
				},
			})
		}

		time.Sleep(2 * time.Second)
	}

	fmt.Printf("经过%d次尝试，未找到分组: %s\n", maxAttempts, groupName)
	return false
}

func (a *SwitchSoul) findAndEquipTeam(ctx *maa.Context, teamName string) bool {
	fmt.Printf("开始查找队伍: %s\n", teamName)

	controller := ctx.GetTasker().GetController()
	if controller == nil {
		fmt.Println("获取控制器失败")
		return false
	}

	maxAttempts := 8

	for attempt := 1; attempt <= maxAttempts; attempt++ {
		a.mu.Lock()
		running := a.running
		a.mu.Unlock()
		if !running {
			return false
		}

		fmt.Printf("查找队伍 - 第%d次尝试\n", attempt)
		time.Sleep(500 * time.Millisecond)

		// 先截图
		controller.PostScreencap().Wait()
		img, err := controller.CacheImage()
		if err != nil {
			fmt.Printf("获取截图失败: %v\n", err)
			continue
		}

		detail, _ := ctx.RunRecognition("点击队伍", img, map[string]any{
			"点击队伍": map[string]any{
				"timeout":     2000,
				"recognition": "OCR",
				"expected":    teamName,
				"roi":         []int{573, 128, 255, 436},
			},
		})

		time.Sleep(500 * time.Millisecond)

		if detail != nil && detail.Hit {
			roi := []int{detail.Box.X() - 30, detail.Box.Y() - 30, 500, 80}
			fmt.Printf("找到队伍: %s，尝试装备御魂\n", teamName)

			equipResult, _ := ctx.RunTask("通用_装备御魂", map[string]any{
				"通用_装备御魂-模板匹配": map[string]any{"roi": roi},
				"通用_装备御魂-特征匹配": map[string]any{"roi": roi},
			})

			if equipResult != nil {
				fmt.Printf("成功装备队伍 %s 的御魂\n", teamName)
				return true
			}
			fmt.Printf("找到队伍 %s 但装备御魂失败\n", teamName)
			return false
		}

		// 滑动
		if attempt%3 == 0 {
			_, _ = ctx.RunTask("返回最上页分队", map[string]any{
				"返回最上页分队": map[string]any{
					"action":              "Custom",
					"custom_action":       "RandomSwipe",
					"custom_action_param": map[string]any{
						"end_roi":   []int{585, 495, 273, 112},
						"start_roi": []int{588, 171, 410, 76},
						"delay":     500,
					},
				},
			})
		} else {
			_, _ = ctx.RunTask("下一页", map[string]any{
				"下一页": map[string]any{
					"action":              "Custom",
					"custom_action":       "RandomSwipe",
					"custom_action_param": map[string]any{
						"start_roi": []int{585, 495, 273, 112},
						"end_roi":   []int{588, 171, 410, 76},
						"delay":     400,
					},
				},
			})
		}

		time.Sleep(1 * time.Second)
	}

	fmt.Printf("经过%d次尝试，未找到队伍: %s\n", maxAttempts, teamName)
	return false
}