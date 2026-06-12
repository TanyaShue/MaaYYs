package battle_team

import "github.com/MaaXYZ/maa-framework-go/v4"

func Register() {
	maa.AgentServerRegisterCustomAction("BattleTeam", &BattleTeam{})
}
