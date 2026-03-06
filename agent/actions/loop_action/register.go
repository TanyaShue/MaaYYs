package loop_action

import "github.com/MaaXYZ/maa-framework-go/v4"

var _ maa.CustomActionRunner = &LoopAction{}

// Register 注册LoopAction custom action
func Register() {
	maa.AgentServerRegisterCustomAction("LoopAction", &LoopAction{})
}