package restart

import (
	"fmt"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type ReStart struct{}

// Run 超时重启动作
func (a *ReStart) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("触发timeout")
	return true
}