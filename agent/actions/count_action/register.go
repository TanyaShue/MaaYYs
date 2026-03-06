package count_action

import "github.com/MaaXYZ/maa-framework-go/v4"

var _ maa.CustomActionRunner = &CountAction{}

// Register 注册CountAction custom action
func Register() {
	maa.AgentServerRegisterCustomAction("CountAction", &CountAction{})
}