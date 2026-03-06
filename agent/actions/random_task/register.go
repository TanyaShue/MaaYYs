package random_task

import "github.com/MaaXYZ/maa-framework-go/v4"

var _ maa.CustomActionRunner = &RandomTask{}

// Register 注册RandomTask custom action
func Register() {
	maa.AgentServerRegisterCustomAction("RandomTask", &RandomTask{})
}