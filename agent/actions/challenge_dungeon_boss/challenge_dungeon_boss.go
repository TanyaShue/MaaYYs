package challenge_dungeon_boss

import (
	"encoding/json"
	"fmt"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type ChallengeDungeonBoss struct{}

type ChallengeParams struct {
	Count int `json:"count"`
}

// Run 自动挑战地鬼
func (a *ChallengeDungeonBoss) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行自定义动作: 自动挑战地鬼")

	params := ChallengeParams{Count: 1}
	if arg.CustomActionParam != "" {
		json.Unmarshal([]byte(arg.CustomActionParam), &params)
	}

	fmt.Printf("挑战地鬼数: %d\n", params.Count)

	for i := 0; i < params.Count; i++ {
		fmt.Printf("开始挑战第 %d 只地鬼\n", i+1)

		r, err := ctx.RunTask("地鬼-点击筛选", map[string]any{
			"地鬼-识别挑战位置": map[string]any{"index": i},
		})
		if err != nil || r == nil {
			return false
		}

		r, err = ctx.RunTask("自动地鬼3", nil)
		if err != nil || r == nil {
			return false
		}
	}

	fmt.Println("自动地鬼挑战完成")
	return true
}