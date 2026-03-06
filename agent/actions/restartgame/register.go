package restartgame

import "github.com/MaaXYZ/maa-framework-go/v4"

var _ maa.CustomActionRunner = &ReStartGame{}

// Register 注册ReStartGame custom action
func Register() {
	maa.AgentServerRegisterCustomAction("ReStartGame", &ReStartGame{})
}