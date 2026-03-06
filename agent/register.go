package main

import (
	"maa-yys-agent/actions/auto_battle"
	"maa-yys-agent/actions/auto_foster"
	"maa-yys-agent/actions/bonus_toggle"
	"maa-yys-agent/actions/bounty_monster_recognition"
	"maa-yys-agent/actions/challenge_dungeon_boss"
	"maa-yys-agent/actions/count_action"
	"maa-yys-agent/actions/custom_appointment"
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
	"maa-yys-agent/actions/task_list"
	"maa-yys-agent/actions/team_builder"
	"maa-yys-agent/actions/time_check"
	"maa-yys-agent/recognition/my_recognizer"

	"github.com/rs/zerolog/log"
)

func registerAll() {
	// 基础操作类
	random_touch.Register()
	random_swipe.Register()
	random_task.Register()
	random_wait.Register()
	human_touch.Register()

	// 流程控制类
	count_action.Register()
	loop_action.Register()
	task_list.Register()
	restart.Register()
	restartgame.Register()

	// 游戏功能类
	auto_battle.Register()
	auto_foster.Register()
	switch_soul.Register()
	team_builder.Register()
	bounty_monster_recognition.Register()
	challenge_dungeon_boss.Register()
	repeat_challenge_n_times.Register()
	kun28.Register()
	bonus_toggle.Register()
	question_matcher.Register()
	guess.Register()
	custom_appointment.Register()
	time_check.Register()

	// Custom Recognition
	my_recognizer.Register()

	log.Info().Msg("All custom actions and recognitions registered successfully")
}