package challenge_dungeon_boss

import (
	"encoding/json"
	"fmt"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type ChallengeDungeonBoss struct{}

type ChallengeParams struct {
	Count    int  `json:"count"`
	IsReward bool `json:"isReward"` // 是否挑战悬赏
}

// Run 自动挑战地鬼
func (a *ChallengeDungeonBoss) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行自定义动作: 自动挑战地鬼")

	params := ChallengeParams{
		Count:    1,
		IsReward: false,
	}

	if arg.CustomActionParam != "" {
		_ = json.Unmarshal([]byte(arg.CustomActionParam), &params)
	}

	fmt.Printf("挑战地鬼数: %d\n", params.Count)
	fmt.Printf("是否挑战悬赏: %v\n", params.IsReward)

	for i := 0; i < params.Count; i++ {
		fmt.Printf("开始挑战第 %d 只地鬼\n", i+1)

		var (
			r   any
			err error
		)

		// 地鬼-点击筛选
		if params.IsReward {
			if i == 0 {
				// 第一次不带参数
				r, err = ctx.RunTask("地鬼-点击筛选", nil)
			} else {
				// 后续 index 从 0 开始
				r, err = ctx.RunTask("地鬼-点击筛选", map[string]any{
					"地鬼-识别挑战位置": map[string]any{
						"index": i - 1,
					},
				})
			}
		} else {
			// 普通模式：index 从 0 开始
			r, err = ctx.RunTask("地鬼-点击筛选", map[string]any{
				"地鬼-识别挑战位置": map[string]any{
					"index": i,
				},
			})
		}

		if err != nil || r == nil {
			return false
		}

		// 自动挑战
		r, err = ctx.RunTask("自动地鬼3", nil)
		if err != nil || r == nil {
			return false
		}
	}

	fmt.Println("自动地鬼挑战完成")
	return true
}
