package config_value_recognition

import "github.com/MaaXYZ/maa-framework-go/v4"

func Register() {
	maa.AgentServerRegisterCustomRecognition("ConfigValueWriteRecognition", &ConfigValueWriteRecognition{})
	maa.AgentServerRegisterCustomRecognition("ConfigValueCheckRecognition", &ConfigValueCheckRecognition{})
}
