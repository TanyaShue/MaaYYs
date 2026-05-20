package co_battle_target_recognition

import "github.com/MaaXYZ/maa-framework-go/v4"

// 确保实现 CustomRecognitionRunner 接口
var _ maa.CustomRecognitionRunner = &CoBattleTargetRecognition{}

// Register 注册 CoBattleTargetRecognition 自定义识别器
func Register() {
	maa.AgentServerRegisterCustomRecognition("CoBattleTargetRecognition", &CoBattleTargetRecognition{})
}