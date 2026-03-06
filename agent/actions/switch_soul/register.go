package switch_soul

import "github.com/MaaXYZ/maa-framework-go/v4"

func Register() {
	maa.AgentServerRegisterCustomAction("SwitchSoul", &SwitchSoul{})
}