package restartgame

import (
	"fmt"
	"sync"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type ReStartGame struct {
	count int
	mu    sync.Mutex
}

// Run 重启游戏
func (a *ReStartGame) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	a.mu.Lock()
	count := a.count
	a.mu.Unlock()

	if count < 5 {
		fmt.Println("即将重启游戏并跳过任务")
		r, err := ctx.RunTask("关闭阴阳师")
		if err != nil || r == nil {
			fmt.Printf("关闭游戏失败: %v, 检测游戏区服是否正确\n", err)
			return false
		}

		time.Sleep(3 * time.Second)
		_, _ = ctx.RunTask("启动游戏")
		fmt.Println("重启完成,跳过任务")

		a.mu.Lock()
		a.count++
		count = a.count
		a.mu.Unlock()

		fmt.Printf("当前重启次数为: %d\n", count)
		return true
	}

	_, _ = ctx.RunTask("StopTask")
	return true
}