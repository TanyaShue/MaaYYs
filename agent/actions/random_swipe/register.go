package random_swipe

import "github.com/MaaXYZ/maa-framework-go/v4"

var _ maa.CustomActionRunner = &RandomSwipe{}

// Register 注册RandomSwipe custom action
func Register() {
	maa.AgentServerRegisterCustomAction("RandomSwipe", &RandomSwipe{})
}