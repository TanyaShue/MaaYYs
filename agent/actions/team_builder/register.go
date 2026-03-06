package team_builder

import "github.com/MaaXYZ/maa-framework-go/v4"

func Register() {
	maa.AgentServerRegisterCustomAction("TeamBuilder", &TeamBuilder{})
}