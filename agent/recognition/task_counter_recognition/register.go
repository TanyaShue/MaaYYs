package task_counter_recognition

import "github.com/MaaXYZ/maa-framework-go/v4"

// 确保实现 CustomRecognitionRunner 接口
var _ maa.CustomRecognitionRunner = &TaskCounterRecognition{}

// Register 注册 TaskCounterRecognition 自定义识别器
func Register() {
	maa.AgentServerRegisterCustomRecognition("TaskCounterRecognition", &TaskCounterRecognition{})
}