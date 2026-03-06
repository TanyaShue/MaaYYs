package human_touch

import "github.com/MaaXYZ/maa-framework-go/v4"

var _ maa.CustomActionRunner = &HumanTouch{}

// Register 注册HumanTouch custom action
func Register() {
	maa.AgentServerRegisterCustomAction("HumanTouch", &HumanTouch{})
}