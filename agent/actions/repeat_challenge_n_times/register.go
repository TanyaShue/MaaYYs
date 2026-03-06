package repeat_challenge_n_times

import "github.com/MaaXYZ/maa-framework-go/v4"

func Register() {
	maa.AgentServerRegisterCustomAction("RepeatChallengeNTimes", &RepeatChallengeNTimes{})
}