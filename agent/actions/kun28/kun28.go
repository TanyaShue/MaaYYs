package kun28

import (
	"encoding/json"
	"fmt"
	"math/rand"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type Kun28 struct {
	numTupo int
	mu      sync.Mutex
}

type Kun28Params struct {
	GroupName string `json:"group_name"`
	TeamName  string `json:"team_name"`
}

// Run 执行Kun28任务
func (a *Kun28) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行自定义动作：Kun28")

	params := Kun28Params{}
	if arg.CustomActionParam != "" {
		json.Unmarshal([]byte(arg.CustomActionParam), &params)
	}

	fmt.Printf("预设队伍: %s-%s\n", params.GroupName, params.TeamName)

	// 初始准备阶段
	_, _ = ctx.RunTask("kun289", nil)
	a.recognitionStatus(ctx)

	_, _ = ctx.RunTask("返回庭院", nil)

	// 如果突破卷很多，先清一波
	if a.numTupo < 20 {
		_, _ = ctx.RunTask("kun2812", nil)
		a.recognitionStatus(ctx)
	}

	loopCount := 0
	r := rand.New(rand.NewSource(time.Now().UnixNano()))

	// 循环逻辑主体
	for {
		// 退出条件判断
		if loopCount >= 5 {
			fmt.Printf("已循环执行 %d 次，任务结束。\n", loopCount)
			break
		}

		fmt.Printf("当前状态 - 循环次数: %d, 突破卷: %d\n", loopCount, a.numTupo)

		// 行为逻辑判断
		if a.numTupo >= 20 {
			fmt.Println("突破卷 >= 20，开始清理结界...")

			tasks := []string{"返回庭院", "自动结界", "返回庭院", "kun2812"}
			for _, task := range tasks {
				if task == "自动结界" {
					_, _ = ctx.RunTask(task, map[string]any{
						"装备突破预设": map[string]any{
							"custom_action_param": map[string]any{
								"group_name": params.GroupName,
								"team_name":  params.TeamName,
							},
						},
					})
				} else {
					_, _ = ctx.RunTask(task, nil)
				}
			}

			// 随机等待
			var number int
			if r.Float64() < 0.9 {
				number = r.Intn(100) + 1
			} else {
				number = r.Intn(600) + 1
			}
			fmt.Printf("清理结界中随机休息: %d 秒\n", number)
			time.Sleep(time.Duration(number) * time.Second)
		} else {
			fmt.Println("突破卷 < 20，执行探索任务...")
			_, _ = ctx.RunTask("kun281", nil)
		}

		a.recognitionStatus(ctx)
		loopCount++
	}

	return true
}

func (a *Kun28) recognitionStatus(ctx *maa.Context) {
	controller := ctx.GetTasker().GetController()

	controller.PostScreencap().Wait()
	img, err := controller.CacheImage()
	if err != nil {
		fmt.Printf("获取截图失败: %v\n", err)
		return
	}
	result, _ := ctx.RunRecognition("kun28_识别突破卷数量", img, nil)

	// 识别突破卷数量
	if result != nil && result.Hit {
		// 从 DetailJson 中解析突破卷数量
		var detail struct {
			Best struct {
				Text string `json:"text"`
			} `json:"best"`
		}
		if err := json.Unmarshal([]byte(result.DetailJson), &detail); err == nil {
			// 文本格式为 "3/30"，需要提取分子
			text := detail.Best.Text
			if parts := strings.Split(text, "/"); len(parts) == 2 {
				if num, err := strconv.Atoi(strings.TrimSpace(parts[0])); err == nil {
					a.mu.Lock()
					a.numTupo = num
					a.mu.Unlock()
				}
			}
		}
	}
	fmt.Printf(">> 识别结果更新 | 突破卷: %d\n", a.numTupo)
}