package time_check

import "github.com/MaaXYZ/maa-framework-go/v4"

func Register() {
	maa.AgentServerRegisterCustomAction("TimeCheck", &TimeCheck{})
}