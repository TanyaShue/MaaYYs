package clear_hit_count

import (
	"encoding/json"
	"fmt"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type ClearHitCount struct{}

type ClearHitCountParams struct {
	NodeName  string   `json:"node_name"`
	NodeNames []string `json:"node_names"`
}

// Run 执行清除节点计数
func (a *ClearHitCount) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	params := ClearHitCountParams{}
	if arg.CustomActionParam != "" {
		if err := json.Unmarshal([]byte(arg.CustomActionParam), &params); err != nil {
			fmt.Printf("警告: 解析JSON参数失败。错误: %v\n", err)
			return false
		}
	}

	// 收集所有需要清除的节点名称
	nodeNames := make([]string, 0, len(params.NodeNames)+1)
	if params.NodeName != "" {
		nodeNames = append(nodeNames, params.NodeName)
	}
	nodeNames = append(nodeNames, params.NodeNames...)

	if len(nodeNames) == 0 {
		fmt.Println("警告: 未提供任何节点名称")
		return false
	}

	// 清除每个节点的计数
	success := true
	for _, name := range nodeNames {
		if err := ctx.ClearHitCount(name); err != nil {
			fmt.Printf("清除节点计数失败: %s, 错误: %v\n", name, err)
			success = false
		} else {
			fmt.Printf("已清除节点计数: %s\n", name)
		}
	}

	return success
}