package question_matcher

import "github.com/MaaXYZ/maa-framework-go/v4"

func Register() {
	maa.AgentServerRegisterCustomAction("QuestionMatcher", &QuestionMatcher{})
}