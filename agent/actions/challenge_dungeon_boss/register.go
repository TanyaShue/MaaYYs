package challenge_dungeon_boss

import "github.com/MaaXYZ/maa-framework-go/v4"

func Register() {
	maa.AgentServerRegisterCustomAction("ChallengeDungeonBoss", &ChallengeDungeonBoss{})
}