package random_wait

import "github.com/MaaXYZ/maa-framework-go/v4"

var _ maa.CustomActionRunner = &RandomWait{}

// Register 注册RandomWait custom action
func Register() {
	maa.AgentServerRegisterCustomAction("RandomWait", &RandomWait{})
}