package random_touch

import "github.com/MaaXYZ/maa-framework-go/v4"

var _ maa.CustomActionRunner = &RandomTouch{}

// Register 注册RandomTouch custom action
func Register() {
	maa.AgentServerRegisterCustomAction("RandomTouch", &RandomTouch{})
}