package switch_soul

import (
	"encoding/json"
	"fmt"
	"image"
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

// RecognitionDetail 识别结果详情
type RecognitionDetail struct {
	Best struct {
		Text string `json:"text"`
		Box  []int  `json:"box"`
	} `json:"best"`
}

// ROI 定义
var (
	groupBaseROI = []int{1099, 82, 140, 545}
	teamBaseROI  = []int{573, 128, 255, 436}
)

const (
	NumParts         = 20
	MaxGroupAttempts = 5
	MaxTeamAttempts  = 8
)

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
	result, _ := ctx.RunTask("通用_切换御魂_开始", nil)
	time.Sleep(500 * time.Millisecond)
	return result != nil
}

func (a *SwitchSoul) findAndClickGroup(ctx *maa.Context, groupName string) bool {
	fmt.Printf("开始查找分组: %s\n", groupName)

	controller := ctx.GetTasker().GetController()
	if controller == nil {
		fmt.Println("获取控制器失败")
		return false
	}

	r := rand.New(rand.NewSource(time.Now().UnixNano()))

	// 返回最上方
	a.swipeToTopGroup(ctx)
	time.Sleep(2 * time.Second)

	for attempt := 1; attempt <= MaxGroupAttempts; attempt++ {
		if !a.isRunning() {
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

		// 第一次直接识别
		detail, _ := ctx.RunRecognition("点击分组", img, map[string]any{
			"点击分组": map[string]any{
				"timeout":     2000,
				"recognition": "OCR",
				"expected":    groupName,
				"roi":         groupBaseROI,
			},
		})

		if detail != nil && detail.Hit {
			a.clickRecognitionResult(controller, detail, r)
			fmt.Printf("成功找到并点击分组: %s\n", groupName)
			return true
		}

		fmt.Println("初步未找到，进入分块识别模式…")

		// 分块识别模式
		found := a.fineGrainedRecognitionGroup(ctx, img, groupName, r)
		if found {
			return true
		}

		// 未找到分组，尝试滑动
		if attempt%3 == 0 {
			fmt.Println("返回顶部重新查找")
			a.swipeToTopGroup(ctx)
		} else {
			fmt.Println("向下滑动继续查找")
			a.swipeDownGroup(ctx)
		}

		time.Sleep(2 * time.Second)
	}

	fmt.Printf("经过%d次尝试，未找到分组: %s\n", MaxGroupAttempts, groupName)
	return false
}

// fineGrainedRecognitionGroup 分块识别分组
func (a *SwitchSoul) fineGrainedRecognitionGroup(ctx *maa.Context, img image.Image, groupName string, r *rand.Rand) bool {
	x, y, w, h := groupBaseROI[0], groupBaseROI[1], groupBaseROI[2], groupBaseROI[3]
	step := float64(h) / float64(NumParts+1)

	for i := 0; i < NumParts; i++ {
		// 带重叠的ROI
		subY := int(float64(y) + float64(i)*step)
		subH := int(step * 3) // 高度覆盖3段，制造重叠

		detail, _ := ctx.RunRecognition(fmt.Sprintf("点击分组_精细_%d", i+1), img, map[string]any{
			fmt.Sprintf("点击分组_精细_%d", i+1): map[string]any{
				"timeout":     2000,
				"recognition": "OCR",
				"expected":    groupName,
				"roi":         []int{x, subY, w, subH},
			},
		})

		if detail != nil && detail.Hit {
			controller := ctx.GetTasker().GetController()
			if controller != nil {
				a.clickRecognitionResult(controller, detail, r)
			}
			fmt.Printf("精细识别第%d段成功找到并点击分组: %s\n", i+1, groupName)
			return true
		}
	}

	return false
}

func (a *SwitchSoul) findAndEquipTeam(ctx *maa.Context, teamName string) bool {
	fmt.Printf("开始查找队伍: %s\n", teamName)

	controller := ctx.GetTasker().GetController()
	if controller == nil {
		fmt.Println("获取控制器失败")
		return false
	}

	r := rand.New(rand.NewSource(time.Now().UnixNano()))

	for attempt := 1; attempt <= MaxTeamAttempts; attempt++ {
		if !a.isRunning() {
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

		// 第一次直接识别
		detail, _ := ctx.RunRecognition("点击队伍", img, map[string]any{
			"点击队伍": map[string]any{
				"timeout":     2000,
				"recognition": "OCR",
				"expected":    teamName,
				"roi":         teamBaseROI,
			},
		})

		time.Sleep(500 * time.Millisecond)

		if detail != nil && detail.Hit {
			return a.tryEquipSoul(ctx, detail, teamName, true)
		}

		fmt.Println("初步未找到，将进行细致查找")

		// 分块识别模式
		found := a.fineGrainedRecognitionTeam(ctx, img, teamName, r)
		if found {
			return true
		}

		// 滑动
		if attempt%3 == 0 {
			fmt.Println("返回顶部重新查找队伍")
			a.swipeToTopTeam(ctx)
		} else {
			fmt.Println("向下滑动继续查找队伍")
			a.swipeDownTeam(ctx)
		}

		time.Sleep(1 * time.Second)
	}

	fmt.Printf("经过%d次尝试，未找到队伍: %s\n", MaxTeamAttempts, teamName)
	return false
}

// fineGrainedRecognitionTeam 分块识别队伍
func (a *SwitchSoul) fineGrainedRecognitionTeam(ctx *maa.Context, img image.Image, teamName string, r *rand.Rand) bool {
	x, y, w, h := teamBaseROI[0], teamBaseROI[1], teamBaseROI[2], teamBaseROI[3]
	step := float64(h) / float64(NumParts+1)

	for i := 0; i < NumParts; i++ {
		// 带重叠的ROI
		subY := int(float64(y) + float64(i)*step)
		subH := int(step * 3) // 每段高度覆盖3段

		detail, _ := ctx.RunRecognition(fmt.Sprintf("点击队伍_精细_%d", i+1), img, map[string]any{
			fmt.Sprintf("点击队伍_精细_%d", i+1): map[string]any{
				"timeout":     2000,
				"recognition": "OCR",
				"expected":    teamName,
				"roi":         []int{x, subY, w, subH},
			},
		})

		if detail != nil && detail.Hit {
			return a.tryEquipSoul(ctx, detail, teamName, false)
		}
	}

	fmt.Println("分块识别也未找到队伍")
	return false
}

// tryEquipSoul 尝试装备御魂
func (a *SwitchSoul) tryEquipSoul(ctx *maa.Context, detail *maa.RecognitionDetail, teamName string, isFirstFind bool) bool {
	var recogDetail RecognitionDetail
	if err := json.Unmarshal([]byte(detail.DetailJson), &recogDetail); err == nil {
		if len(recogDetail.Best.Box) >= 4 {
			roi := []int{recogDetail.Best.Box[0] - 30, recogDetail.Best.Box[1] - 30, 500, 80}
			return a.equipSoulWithROI(ctx, roi, teamName, isFirstFind)
		}
	}

	// 如果解析失败，使用 detail.Box
	roi := []int{detail.Box.X() - 30, detail.Box.Y() - 30, 500, 80}
	return a.equipSoulWithROI(ctx, roi, teamName, isFirstFind)
}

// equipSoulWithROI 使用指定ROI装备御魂
func (a *SwitchSoul) equipSoulWithROI(ctx *maa.Context, roi []int, teamName string, isFirstFind bool) bool {
	findText := "找到队伍"
	if !isFirstFind {
		findText = "精细识别找到队伍"
	}
	fmt.Printf("%s: %s，尝试装备御魂\n", findText, teamName)

	equipResult, _ := ctx.RunTask("通用_装备御魂", map[string]any{
		"通用_装备御魂-模板匹配": map[string]any{"roi": roi},
		"通用_装备御魂-特征匹配": map[string]any{"roi": roi},
	})

	if equipResult != nil {
		fmt.Printf("成功装备队伍 %s 的御魂\n", teamName)
		return true
	}

	failText := "找到队伍但装备御魂失败"
	if !isFirstFind {
		failText = "精细识别找到队伍但装备御魂失败"
	}
	fmt.Printf("%s: %s\n", failText, teamName)
	return false
}

// clickRecognitionResult 点击识别结果
func (a *SwitchSoul) clickRecognitionResult(controller *maa.Controller, detail *maa.RecognitionDetail, r *rand.Rand) {
	clickX := r.Intn(detail.Box.Width()) + detail.Box.X()
	clickY := r.Intn(detail.Box.Height()) + detail.Box.Y()
	controller.PostClick(int32(clickX), int32(clickY)).Wait()
}

// swipeToTopGroup 滑动到分组最上方
func (a *SwitchSoul) swipeToTopGroup(ctx *maa.Context) {
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
}

// swipeDownGroup 向下滑动分组
func (a *SwitchSoul) swipeDownGroup(ctx *maa.Context) {
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

// swipeToTopTeam 滑动到队伍最上方
func (a *SwitchSoul) swipeToTopTeam(ctx *maa.Context) {
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
}

// swipeDownTeam 向下滑动队伍
func (a *SwitchSoul) swipeDownTeam(ctx *maa.Context) {
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

// isRunning 检查是否正在运行
func (a *SwitchSoul) isRunning() bool {
	a.mu.Lock()
	defer a.mu.Unlock()
	return a.running
}

// Stop 停止执行
func (a *SwitchSoul) Stop() {
	fmt.Println("停止执行自定义动作")
	a.mu.Lock()
	a.running = false
	a.mu.Unlock()
}