package kun28

import (
	"encoding/json"
	"fmt"
	"strconv"
	"strings"
	"sync"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type Kun28 struct {
	numTupo  int
	lastTask string // 记录上次执行的任务
	mu       sync.Mutex
}

type Kun28Params struct {
	GroupName string `json:"group_name"`
	TeamName  string `json:"team_name"`
}

// runTask 执行任务并打印错误信息
func (a *Kun28) runTask(ctx *maa.Context, taskName string, taskParam map[string]any) {
	_, err := ctx.RunTask(taskName, taskParam)
	if err != nil {
		fmt.Printf("任务执行失败: %s, 错误: %v\n", taskName, err)
	}
}

// Run 执行Kun28任务 - 每次只执行一个任务
func (a *Kun28) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行自定义动作：Kun28")

	params := Kun28Params{}
	if arg.CustomActionParam != "" {
		json.Unmarshal([]byte(arg.CustomActionParam), &params)
	}

	fmt.Printf("预设队伍: %s-%s\n", params.GroupName, params.TeamName)

	// 初始准备阶段
	a.runTask(ctx, "kun28-进入探索", nil)
	a.recognitionStatus(ctx)
	fmt.Printf("当前突破卷: %d\n",  a.numTupo)

	// 根据突破卷数量和上次任务决定本次任务
	if a.numTupo >= 20 {
		// 突破卷 >= 20，执行自动结界
		fmt.Println("突破卷 >= 20，执行自动结界...")
		a.runAutoJieJie(ctx, params)
		a.lastTask = "自动结界"
	} else {
		// 突破卷 < 20
		if a.lastTask == "kun28-从探索开始打kun28" {
			// 上次是探索，直接继续探索（跳过装备）
			a.runTask(ctx, "kun28-从探索开始打kun28", nil)
		} else {
			// 首次或上次不是探索，先装备御魂再探索
			fmt.Println("执行装备探索御魂...")
			a.runTask(ctx, "返回庭院", nil)
			a.runTask(ctx, "kun28-装备探索御魂", nil)
			a.runTask(ctx, "kun28-从探索开始打kun28", nil)
		}
		a.lastTask = "kun28-从探索开始打kun28"
	}
	return true
}

// runAutoJieJie 执行自动结界任务
func (a *Kun28) runAutoJieJie(ctx *maa.Context, params Kun28Params) {
	tasks := []string{"自动结界", "kun28-进入探索"}
	for _, task := range tasks {
		if task == "自动结界" {
			a.runTask(ctx, task, map[string]any{
				"装备突破预设": map[string]any{
					"custom_action_param": map[string]any{
						"group_name": params.GroupName,
						"team_name":  params.TeamName,
					},
				},
			})
		} else {
			a.runTask(ctx, task, nil)
		}
	}
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