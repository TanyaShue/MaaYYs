package my_recognizer

import "github.com/MaaXYZ/maa-framework-go/v4"

func Register() {
	maa.AgentServerRegisterCustomRecognition("MyRecognizer", &MyRecognizer{})
}