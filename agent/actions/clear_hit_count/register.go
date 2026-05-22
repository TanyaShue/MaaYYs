package clear_hit_count

import "github.com/MaaXYZ/maa-framework-go/v4"

var _ maa.CustomActionRunner = &ClearHitCount{}

// Register 注册 ClearHitCount custom action
func Register() {
	maa.AgentServerRegisterCustomAction("ClearHitCount", &ClearHitCount{})
}