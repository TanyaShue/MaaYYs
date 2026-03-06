package task_list

import "github.com/MaaXYZ/maa-framework-go/v4"

var _ maa.CustomActionRunner = &TaskList{}

// Register 注册TaskList custom action
func Register() {
	maa.AgentServerRegisterCustomAction("TaskList", &TaskList{})
}