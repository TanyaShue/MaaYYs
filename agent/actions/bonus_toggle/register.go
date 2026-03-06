package bonus_toggle

import "github.com/MaaXYZ/maa-framework-go/v4"

func Register() {
	maa.AgentServerRegisterCustomAction("BonusToggleAction", &BonusToggleAction{})
}