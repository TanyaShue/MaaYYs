package switch_soul

import (
	"encoding/json"
	"fmt"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type SwitchSoul struct{}

type SwitchSoulParams struct {
	GroupName string `json:"group_name"`
	TeamName  string `json:"team_name"`
}

// Run 直接执行装备御魂任务，并通过 pipeline 覆盖传入分组和队伍名称。
func (a *SwitchSoul) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	params := SwitchSoulParams{}
	if arg.CustomActionParam != "" {
		if err := json.Unmarshal([]byte(arg.CustomActionParam), &params); err != nil {
			fmt.Printf("切换御魂参数解析失败: %v\n", err)
			return false
		}
	}

	result, err := ctx.RunTask("装备御魂", map[string]any{
		"装备御魂-识别目标分组": map[string]any{
			"expected": params.GroupName,
		},
		"装备御魂-识别队伍名称": map[string]any{
			"expected": params.TeamName,
		},
	})
	if err != nil {
		fmt.Printf("执行任务 装备御魂 失败: %v\n", err)
		return false
	}

	return result != nil
}
