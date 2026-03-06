package auto_foster

import "github.com/MaaXYZ/maa-framework-go/v4"

func Register() {
	maa.AgentServerRegisterCustomAction("AutoFoster", &AutoFoster{})
}