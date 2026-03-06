package bounty_monster_recognition

import "github.com/MaaXYZ/maa-framework-go/v4"

func Register() {
	maa.AgentServerRegisterCustomAction("BountyMonsterRecognition", &BountyMonsterRecognition{})
}