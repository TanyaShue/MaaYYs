package main

import (
	"fmt"

	"maa-yys-agent/actions/auto_battle"
	"maa-yys-agent/actions/auto_foster"
	"maa-yys-agent/actions/battle_team"
	"maa-yys-agent/actions/bonus_toggle"
	"maa-yys-agent/actions/bounty_monster_recognition"
	"maa-yys-agent/actions/challenge_dungeon_boss"
	"maa-yys-agent/actions/clear_hit_count"
	"maa-yys-agent/actions/count_action"
	"maa-yys-agent/actions/guess"
	"maa-yys-agent/actions/human_touch"
	"maa-yys-agent/actions/kun28"
	"maa-yys-agent/actions/loop_action"
	"maa-yys-agent/actions/question_matcher"
	"maa-yys-agent/actions/random_swipe"
	"maa-yys-agent/actions/random_task"
	"maa-yys-agent/actions/random_touch"
	"maa-yys-agent/actions/random_wait"
	"maa-yys-agent/actions/repeat_challenge_n_times"
	"maa-yys-agent/actions/restart"
	"maa-yys-agent/actions/restartgame"
	"maa-yys-agent/actions/switch_soul"
	"maa-yys-agent/actions/task_counter"
	"maa-yys-agent/actions/task_list"
	"maa-yys-agent/actions/team_builder"
	"maa-yys-agent/actions/time_check"
	"maa-yys-agent/recognition/co_battle_target_recognition"
	"maa-yys-agent/recognition/config_value_recognition"
	"maa-yys-agent/recognition/my_recognizer"
	"maa-yys-agent/recognition/task_counter_recognition"

	maa "github.com/MaaXYZ/maa-framework-go/v4"
	"github.com/rs/zerolog/log"
)

var customActions = []struct {
	name   string
	runner maa.CustomActionRunner
}{
	{"RandomTouch", &random_touch.RandomTouch{}},
	{"RandomSwipe", &random_swipe.RandomSwipe{}},
	{"RandomTask", &random_task.RandomTask{}},
	{"RandomWait", &random_wait.RandomWait{}},
	{"HumanTouch", &human_touch.HumanTouch{}},
	{"ClearHitCount", &clear_hit_count.ClearHitCount{}},
	{"CountAction", &count_action.CountAction{}},
	{"LoopAction", &loop_action.LoopAction{}},
	{"TaskCounter", &task_counter.TaskCounter{}},
	{"TaskList", &task_list.TaskList{}},
	{"ReStart", &restart.ReStart{}},
	{"ReStartGame", &restartgame.ReStartGame{}},
	{"AutoBattle", &auto_battle.AutoBattle{}},
	{"AutoFoster", &auto_foster.AutoFoster{}},
	{"BattleTeam", &battle_team.BattleTeam{}},
	{"SwitchSoul", &switch_soul.SwitchSoul{}},
	{"TeamBuilder", &team_builder.TeamBuilder{}},
	{"BountyMonsterRecognition", &bounty_monster_recognition.BountyMonsterRecognition{}},
	{"ChallengeDungeonBoss", &challenge_dungeon_boss.ChallengeDungeonBoss{}},
	{"RepeatChallengeNTimes", &repeat_challenge_n_times.RepeatChallengeNTimes{}},
	{"Kun28", &kun28.Kun28{}},
	{"BonusToggleAction", &bonus_toggle.BonusToggleAction{}},
	{"QuestionMatcher", &question_matcher.QuestionMatcher{}},
	{"Guess", &guess.Guess{}},
	{"TimeCheck", &time_check.TimeCheck{}},
}

var customRecognitions = []struct {
	name   string
	runner maa.CustomRecognitionRunner
}{
	{"ConfigValueWriteRecognition", &config_value_recognition.ConfigValueWriteRecognition{}},
	{"ConfigValueCheckRecognition", &config_value_recognition.ConfigValueCheckRecognition{}},
	{"CoBattleTargetRecognition", &co_battle_target_recognition.CoBattleTargetRecognition{}},
	{"MyRecognizer", &my_recognizer.MyRecognizer{}},
	{"TaskCounterRecognition", &task_counter_recognition.TaskCounterRecognition{}},
}

func registerAll() error {
	for _, action := range customActions {
		if err := maa.AgentServerRegisterCustomAction(action.name, action.runner); err != nil {
			return fmt.Errorf("register custom action %q: %w", action.name, err)
		}
	}
	for _, recognition := range customRecognitions {
		if err := maa.AgentServerRegisterCustomRecognition(recognition.name, recognition.runner); err != nil {
			return fmt.Errorf("register custom recognition %q: %w", recognition.name, err)
		}
	}

	log.Info().
		Int("actions", len(customActions)).
		Int("recognitions", len(customRecognitions)).
		Msg("Custom runners registered")
	return nil
}
