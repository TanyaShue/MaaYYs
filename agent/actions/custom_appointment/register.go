package custom_appointment

import "github.com/MaaXYZ/maa-framework-go/v4"

func Register() {
	maa.AgentServerRegisterCustomAction("CustomAppointment", &CustomAppointment{})
}