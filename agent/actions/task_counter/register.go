package task_counter

import "github.com/MaaXYZ/maa-framework-go/v4"

// 确保实现 CustomActionRunner 接口
var _ maa.CustomActionRunner = &TaskCounter{}

// Register 注册 TaskCounter custom action
func Register() {
	maa.AgentServerRegisterCustomAction("TaskCounter", &TaskCounter{})
}