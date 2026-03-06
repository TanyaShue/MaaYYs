package restart

import "github.com/MaaXYZ/maa-framework-go/v4"

var _ maa.CustomActionRunner = &ReStart{}

// Register 注册ReStart custom action
func Register() {
	maa.AgentServerRegisterCustomAction("ReStart", &ReStart{})
}